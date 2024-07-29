import socket
import threading
import struct
import os

import commands



class FileTransferClient:
    HOST = socket.gethostbyname(socket.gethostname())
    port = 1306
    address = (HOST, port)
    client_data_path = "client_data"



    def __init__(self, port: int, client_data_path: str) -> None:
        self.port = port
        self.client_data_path = client_data_path
        if not os.path.exists(client_data_path):
            os.makedirs(client_data_path)

    def send_command(sock: socket.socket, command: int, data_length: int = 0):
        sock.sendall(struct.pack('!BI', command, data_length))

    def send_int(sock: socket.socket, value: int):
        sock.sendall(struct.pack('!I', value))

    def recv_bool(sock: socket.socket) -> bool:
        return struct.unpack('!?', sock.recv(1))[0]

    def recv_int(sock: socket.socket) -> int:
        return struct.unpack('!I', sock.recv(4))[0]

    def recv_all(sock: socket.socket, length: int) -> bytes:
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
            print(f"[PING ERROR] {e}")
            return False

    def list_files(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect(self.address)
                self.send_command(sock, commands.LIST)
                files = self.recv_all(sock, self.recv_int(sock))
                return files.decode()
        
        except Exception as e:
            print(f"[FILE LISTING ERROR] {e}")

    def upload_chunk(self, path: str, start_byte: int, end_byte: int, chunk_number: int):
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
                    data: bytes = file.read(end_byte - start_byte + 1)
                    sock.sendall(data)
                
                print(f"Chunk {chunk_number} uploaded from {start_byte} to {end_byte}")
        
        except Exception as e:
            print(f"[CHUNK UPLOAD ERROR] {e}")

    def upload_file(self, path: str, chunk_count: int = 4):
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

                    thread = threading.Thread(target=self.upload_chunk, args=(path, start_byte, end_byte, i))
                    thread.start()
                    threads.append(thread)

                for thread in threads:
                    thread.join()
            
        except Exception as e:
            print(f"[FILE UPLOAD ERROR]: {e}")
            
    def download_chunk(self, file_name: str, start_byte: int, end_byte: int, chunk_number: int):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect(self.address)

                self.send_command(sock, commands.DOWNLOAD_CHUNK, len(file_name))
                sock.sendall(file_name.encode())
                self.send_int(sock, start_byte)
                self.send_int(sock, end_byte)

                path: str = os.path.join(self.client_data_path, file_name)
                with open(path, 'r+b') as file:
                    file.seek(start_byte)
                    data = self.recv_all(sock, end_byte - start_byte + 1)
                    file.write(data)
                print(f"Chunk {chunk_number} downloaded from {start_byte} to {end_byte}")
        
        except Exception as e:
            print(f"[CHUNK DOWNLOAD ERROR] {e}")

    def download_file(self, file_name: str, chunk_count: int = 4):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect(self.address)
                self.send_command(sock, commands.REQUEST_DOWNLOAD, len(file_name))
                sock.sendall(file_name.encode())
                file_exists, file_size = struct.unpack('!?I', sock.recv(5))

                if not file_exists:
                    raise FileNotFoundError("File is not on the server")
                
                chunk_size = file_size // chunk_count

                path: str = os.path.join(self.client_data_path, file_name)
                with open(path, 'wb') as file:
                    file.seek(file_size - 1)
                    file.write(b'\0')

                threads: list[threading.Thread] = []
                for i in range(chunk_count):
                    start_byte = i * chunk_size
                    end_byte = (file_size - 1) if (i == chunk_count - 1) else (start_byte + chunk_size - 1)

                    thread = threading.Thread(target=self.download_chunk, args=(file_name, start_byte, end_byte, i))
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
