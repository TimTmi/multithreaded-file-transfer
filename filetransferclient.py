import socket
import threading
import struct
import os

import commands



class FileTransferClient:
    address: tuple[str, int]

    def __init__(self, port: int, server_ip: str = socket.gethostbyname(socket.gethostname())) -> None:
        self.address = (server_ip, port)
        socket.setdefaulttimeout(13)

    def get_local_host(self):
        return socket.gethostbyname(socket.gethostname())

    def send_command(self, sock: socket.socket, command: int, data_length: int = 0):
        sock.sendall(struct.pack('!BI', command, data_length))

    def send_int(self, sock: socket.socket, value: int):
        sock.sendall(struct.pack('!I', value))

    def recv_bool(self, sock: socket.socket) -> bool:
        return struct.unpack('!?', sock.recv(1))[0]

    def recv_int(self, sock: socket.socket) -> int:
        return struct.unpack('!I', sock.recv(4))[0]

    def recv_all(self, sock: socket.socket, length: int) -> bytes:
        data = bytearray()
        while len(data) < length:
            packet = sock.recv(length - len(data))
            if not packet:
                raise ConnectionError("Socket connection closed before receiving all data")
            data.extend(packet)
        return bytes(data)



    def ping(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect(self.address)
                self.send_command(sock, commands.PING)
                return self.recv_bool(sock)
            
        except Exception as e:
            # print(f"[PING ERROR] {e}")
            return False

    def list_files(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect(self.address)
                self.send_command(sock, commands.LIST)
                data = self.recv_all(sock, self.recv_int(sock)).decode()
                data = data.splitlines()
                files_data: list[tuple[str, str, str]] = []
                for i in data:
                    file_data: tuple[str, str, str] = tuple(i.split('@'))
                    files_data.append(file_data)
                return files_data
        
        except Exception as e:
            print(f"[FILE LISTING ERROR] {e}")

    def upload_chunk(self, path: str, start_byte: int, end_byte: int, chunk_number: int, progress_tracker = None):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect(self.address)

                file_name: bytes = os.path.basename(path).encode()
                self.send_command(sock, commands.UPLOAD_CHUNK, len(file_name))
                sock.sendall(file_name)
                self.send_int(sock, start_byte)
                self.send_int(sock, end_byte)

                with open(path, 'rb') as file:
                    file.seek(start_byte)
                    data_length: int = end_byte - start_byte + 1
                    data: bytes = file.read(data_length)

                    total_sent: int = 0
                    while total_sent < data_length:
                        sent = sock.send(data[total_sent:])
                        if sent == 0:
                            break
                        total_sent += sent
                        if not progress_tracker is None:
                            progress_tracker(chunk_number, sent, total_sent / data_length)

                print(f"Chunk {chunk_number} uploaded from {start_byte} to {end_byte}")
        
        except Exception as e:
            print(f"[CHUNK UPLOAD ERROR] {e}")

    def upload_file(self, path: str, chunk_count: int = 4, progress_tracker = None):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect(self.address)

                file_name = os.path.basename(path).encode()
                self.send_command(sock, commands.REQUEST_UPLOAD, len(file_name))
                sock.sendall(file_name)
                file_exists = self.recv_bool(sock)
                if file_exists:
                    raise FileExistsError("File has already existed on the server")
                
                file_size = os.path.getsize(path)
                self.send_int(sock, file_size)
                
                chunk_size: int = file_size // chunk_count
                threads = []
                for i in range(chunk_count):
                    start_byte = i * chunk_size
                    end_byte = (file_size - 1) if (i == chunk_count - 1) else (start_byte + chunk_size - 1)

                    thread = threading.Thread(target=self.upload_chunk, args=(path, start_byte, end_byte, i, progress_tracker))
                    thread.start()
                    threads.append(thread)

                for thread in threads:
                    thread.join()
            
        except Exception as e:
            print(f"[FILE UPLOAD ERROR]: {e}")
            
    def download_chunk(self, file_name: str, destination: str, start_byte: int, end_byte: int, chunk_number: int, progress_tracker = None):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect(self.address)

                self.send_command(sock, commands.DOWNLOAD_CHUNK, len(file_name))
                sock.sendall(file_name.encode())
                self.send_int(sock, start_byte)
                self.send_int(sock, end_byte)

                with open(destination, 'r+b') as file:
                    file.seek(start_byte)
                    data_length = end_byte - start_byte + 1
                    # data = self.recv_all(sock, end_byte - start_byte + 1)

                    data = bytearray()
                    total_received: int = 0
                    while total_received < data_length:
                        packet = sock.recv(data_length - total_received)
                        if not packet:
                            raise ConnectionError("Socket connection closed before receiving all data")
                        data.extend(packet)
                        total_received += len(packet)

                        if not progress_tracker is None:
                            progress_tracker(chunk_number, len(packet), total_received / data_length)

                    file.write(data)
                    # if not progress_tracker is None:
                    #     progress_tracker(chunk_number)
                
                print(f"Chunk {chunk_number} downloaded from {start_byte} to {end_byte}")
        
        except Exception as e:
            print(f"[CHUNK DOWNLOAD ERROR] {e}")

    def download_file(self, file_name: str, destination: str, chunk_count: int = 4, progress_tracker = None):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect(self.address)
                self.send_command(sock, commands.REQUEST_DOWNLOAD, len(file_name))
                sock.sendall(file_name.encode())
                file_exists, file_size = struct.unpack('!?I', sock.recv(5))

                if not file_exists:
                    raise FileNotFoundError("File is not on the server")
                
                chunk_size = file_size // chunk_count

                with open(destination, 'wb') as file:
                    file.seek(file_size - 1)
                    file.write(b'\0')

                threads: list[threading.Thread] = []
                for i in range(chunk_count):
                    start_byte = i * chunk_size
                    end_byte = (file_size - 1) if (i == chunk_count - 1) else (start_byte + chunk_size - 1)

                    thread = threading.Thread(target=self.download_chunk, args=(file_name, destination, start_byte, end_byte, i, progress_tracker))
                    thread.start()
                    threads.append(thread)

                for thread in threads:
                    thread.join()

        except Exception as e:
            print(f"[FILE DOWNLOAD ERROR] {e}")


    def delete_file(self, file_name: str):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect(self.address)
                self.send_command(sock, commands.DELETE, len(file_name))
                sock.sendall(file_name.encode())
                file_exists = self.recv_bool(sock)
                if not file_exists:
                    raise FileNotFoundError("File is not on the server")
        
        except Exception as e:
            print(f"[FILE DELETION ERROR] {e}")
