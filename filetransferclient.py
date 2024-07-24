import socket
import threading
import struct
import os
import time

import commands



HOST = socket.gethostbyname(socket.gethostname())
PORT = 1306
ADDRESS = (HOST, PORT)
SIZE = 1024
CLIENT_DATA_PATH = "client_data"



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



def ping():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect(ADDRESS)
            send_command(sock, commands.PING)
            return recv_bool(sock)
        
    except Exception as e:
        print(f"[PING ERROR] {e}")
        return False

def list_files():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect(ADDRESS)
        send_command(sock, commands.LIST)
        files = recv_all(sock, recv_int(sock))
        return files.decode()

def upload_chunk(path: str, start_byte: int, end_byte: int, chunk_number: int):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect(ADDRESS)

            file_name: bytes = os.path.basename(path).encode()
            send_command(sock, commands.UPLOAD_CHUNK, len(file_name))
            sock.sendall(file_name)
            send_int(sock, start_byte)
            send_int(sock, end_byte)

            with open(path, 'rb') as file:
                file.seek(start_byte)
                data: bytes = file.read(end_byte - start_byte + 1)
                sock.sendall(data)
            
            print(f"Chunk {chunk_number} uploaded from {start_byte} to {end_byte}")
    
    except Exception as e:
        print(f"[CHUNK UPLOAD ERROR] {e}")

def upload_file(path: str, chunk_count: int = 4):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect(ADDRESS)

            file_name = os.path.basename(path).encode()
            send_command(sock, commands.REQUEST_UPLOAD, len(file_name))
            sock.sendall(file_name)
            file_exists = recv_bool(sock)
            if file_exists:
                raise FileExistsError("File has already existed on the server")
            
            file_size = os.path.getsize(path)
            send_int(sock, file_size)
            
            chunk_size: int = file_size // chunk_count
            threads = []
            for i in range(chunk_count):
                start_byte = i * chunk_size
                end_byte = (file_size - 1) if (i == chunk_count - 1) else (start_byte + chunk_size - 1)

                thread = threading.Thread(target=upload_chunk, args=(path, start_byte, end_byte, i))
                thread.start()
                threads.append(thread)

            for thread in threads:
                thread.join()
        
    except Exception as e:
        print(f"[FILE UPLOAD ERROR]: {e}")
        
def download_chunk(file_name: str, start_byte: int, end_byte: int, chunk_number: int):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect(ADDRESS)

        send_command(sock, commands.DOWNLOAD_CHUNK, len(file_name))
        sock.sendall(file_name.encode())
        send_int(sock, start_byte)
        send_int(sock, end_byte)

        path: str = os.path.join(CLIENT_DATA_PATH, file_name)
        with open(path, 'r+b') as file:
            file.seek(start_byte)
            data = recv_all(sock, end_byte - start_byte + 1)
            file.write(data)
        print(f"Chunk {chunk_number} downloaded from {start_byte} to {end_byte}")

def download_file(file_name: str, chunk_count: int = 4):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect(ADDRESS)
        send_command(sock, commands.REQUEST_DOWNLOAD, len(file_name))
        sock.sendall(file_name.encode())
        file_exists, file_size = struct.unpack('!?I', sock.recv(5))

        if not file_exists:
            raise FileNotFoundError("File is not on the server")
        
        chunk_size = file_size // chunk_count

        path: str = os.path.join(CLIENT_DATA_PATH, file_name)
        with open(path, 'wb') as file:
            file.seek(file_size - 1)
            file.write(b'\0')

        threads: list[threading.Thread] = []
        for i in range(chunk_count):
            start_byte = i * chunk_size
            end_byte = (file_size - 1) if (i == chunk_count - 1) else (start_byte + chunk_size - 1)

            thread = threading.Thread(target=download_chunk, args=(file_name, start_byte, end_byte, i))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

def delete_file(file_name: str):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect(ADDRESS)
            send_command(sock, commands.DELETE, len(file_name))
            sock.sendall(file_name.encode())
            file_exists = recv_bool(sock)
            if not file_exists:
                raise FileNotFoundError("File is not on the server")
    
    except Exception as e:
        print(f"[FILE DELETION ERROR] {e}")

if (__name__ == '__main__'):
    delete_file("gitgud.txt")
    delete_file("dsdsd.pdf")
    time.sleep(1)
    print(ping())
    print(list_files())
    upload_file("gitgud.txt")
    upload_file("dsdsd.pdf")
    time.sleep(1)
    download_file("dsdsd.pdf")
    download_file("gitgud.txt")
    time.sleep(1)
