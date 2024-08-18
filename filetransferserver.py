import os
import socket
import threading
import struct
import time
from humanize import naturalsize

import commands

HOST = '0.0.0.0'
PORT = 61306
ADDRESS = (HOST, PORT)
SIZE = 1024
SERVER_DATA_PATH = "server_data"



def send_bool(conn: socket.socket, value: bool):
    conn.sendall(struct.pack('!?', value))

def send_int(conn: socket.socket, value: int):
    conn.sendall(struct.pack('!I', value))

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

def path_to(file_name: str):
    return os.path.join(SERVER_DATA_PATH, file_name)



def handle_client(conn: socket.socket, addr: str):
    print(f"[NEW CONNECTION] {addr}")

    try:
        while True:
            header = conn.recv(5)
            if not header:
                break
            command, data_length = struct.unpack('!BI', header)
            # print(f"[COMMAND] {command} with data length {data_length}")

            match command:
                case commands.PING:
                    # print(f"[PING] {addr}")
                    send_bool(conn, True)

                case commands.LIST:
                    print(f"[LIST] {addr}")
                    files = os.listdir(SERVER_DATA_PATH)
                    for i in range(len(files)):
                        file: str = files[i]
                        path = path_to(file)
                        creation_time: str = time.ctime(os.path.getctime(path))
                        size: str = str(os.path.getsize(path))
                        files[i] = f"{file}@{creation_time}@{size}"
                    data = '\n'.join(file_data for file_data in files).encode()
                    send_int(conn, len(data))
                    conn.sendall(data)

                case commands.REQUEST_UPLOAD:
                    file_name: str = recv_all(conn, data_length).decode()
                    path: str = os.path.join(SERVER_DATA_PATH, file_name)
                    file_exists: bool = os.path.exists(path)
                    if file_exists:
                        send_bool(conn, True)
                        break
                    send_bool(conn, False)

                    file_size: int = recv_int(conn)
                    with open(path, 'wb') as file:
                        file.seek(file_size - 1)
                        file.write(b'\0')

                    print(f"[REQUEST UPLOAD] {addr} {file_name}")
                    
                case commands.REQUEST_DOWNLOAD:
                    file_name: str = recv_all(conn, data_length).decode()
                    path: str = os.path.join(SERVER_DATA_PATH, file_name)
                    
                    if not os.path.exists(path):
                        conn.sendall(struct.pack('!?I', False, 0))
                    else:
                        conn.sendall(struct.pack('!?I', True, os.path.getsize(path)))
                    
                    print(f"[REQUEST DOWNLOAD] {addr} {file_name}")

                case commands.UPLOAD_CHUNK:
                    try:
                        file_name: str = recv_all(conn, data_length).decode()
                        path: str = path_to(file_name)
                        start_byte: int = recv_int(conn)
                        end_byte: int = recv_int(conn)
                        data: bytes = recv_all(conn, end_byte - start_byte + 1)

                        with open(path, 'r+b') as file:
                            file.seek(start_byte)
                            file.write(data)
                        
                        print(f"[UPLOAD CHUNK] {addr} {file_name} {start_byte} {end_byte}")
                    
                    except Exception as e:
                        print(f"[CHUNK UPLOAD ERROR] {addr} {e}")

                case commands.DOWNLOAD_CHUNK:
                    try:
                        file_name: str = recv_all(conn, data_length).decode()
                        start_byte: int = recv_int(conn)
                        end_byte: int = recv_int(conn)

                        path: str = path_to(file_name)
                        with open(path, 'rb') as file:
                            file.seek(start_byte)
                            data: bytes = file.read(end_byte - start_byte + 1)
                            conn.sendall(data)
                        
                        print(f"[DOWNLOAD CHUNK] {addr} {file_name} {start_byte} {end_byte}")

                    except Exception as e:
                        print(f"[CHUNK DOWNLOAD ERROR] {addr} {e}")

                case commands.DELETE:
                    file_name = recv_all(conn, data_length).decode()
                    path = os.path.join(SERVER_DATA_PATH, file_name)

                    if os.path.exists(path):
                        os.remove(path)
                        send_bool(conn, True)
                    else:
                        send_bool(conn, False)
                    
                    print(f"[DELETE] {addr} {file_name}")



    except Exception as e:
        print(f"[ERROR] {addr} {e}")

    finally:
        conn.close()
        print(f"[DISCONNECTED] {addr}")

def start_server():
    print("[STARTING] Server is starting")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDRESS)
    server.listen()
    print(f"[LISTENING] Server is listening on {HOST}:{PORT}.")

    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

if __name__ == "__main__":
    if not os.path.exists(SERVER_DATA_PATH):
        os.makedirs(SERVER_DATA_PATH)
    start_server()
