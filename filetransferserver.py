import os
import socket
import threading
import struct
import commands

HOST = socket.gethostbyname(socket.gethostname())
PORT = 1306
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
    print(f"[NEW CONNECTION] {addr} connected.")

    try:
        while True:
            header = conn.recv(5)
            if not header:
                break
            command, data_length = struct.unpack('!BI', header)
            print(f"[COMMAND] {command} with data length {data_length}")

            match command:
                case commands.PING:
                    send_bool(conn, True)

                case commands.LIST:
                    files = os.listdir(SERVER_DATA_PATH)
                    data = '\n'.join(file for file in files).encode()
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
                    
                case commands.REQUEST_DOWNLOAD:
                    file_name: str = recv_all(conn, data_length).decode()
                    path: str = os.path.join(SERVER_DATA_PATH, file_name)
                    
                    if not os.path.exists(path):
                        conn.sendall(struct.pack('!?I', False, 0))
                    else:
                        conn.sendall(struct.pack('!?I', True, os.path.getsize(path)))

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
                    
                    except Exception as e:
                        print(f"[CHUNK UPLOAD ERROR] {e}")

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

                    except Exception as e:
                        print(f"[CHUNK DOWNLOAD ERROR] {e}")

                case commands.DELETE:
                    file_name = recv_all(conn, data_length).decode()
                    path = os.path.join(SERVER_DATA_PATH, file_name)

                    if os.path.exists(path):
                        os.remove(path)
                        send_bool(conn, True)
                    else:
                        send_bool(conn, False)


    except Exception as e:
        print(f"[ERROR] {e}")

    finally:
        conn.close()
        print(f"[DISCONNECTED] {addr} disconnected.")

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
