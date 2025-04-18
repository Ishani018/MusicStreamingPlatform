import socket
import ssl
import threading
import os
import wave
import time

CERT_FILE = r'C:\Users\jahnv\OneDrive\Desktop\cnproj\certs\server.crt'
KEY_FILE = r'C:\Users\jahnv\OneDrive\Desktop\cnproj\certs\server.key'

HOST = '0.0.0.0'
CONTROL_PORT = 8000
DATA_PORT = 8001
CHUNK_SIZE = 1024
AUDIO_DIR = '.'  # All WAV files are in the current directory

# Global to store song choice per client
client_song_map = {}

def list_songs():
    songs = [f for f in os.listdir(AUDIO_DIR) if f.endswith('.wav')]
    songs.sort()
    return songs

def handle_control(connstream, addr, client_id):
    print(f"[CONTROL] {addr} connected.")

    try:
        connstream.send(b"Welcome to MusicStream!\nAvailable songs:\n")

        songs = list_songs()
        for idx, song in enumerate(songs, 1):
            connstream.send(f"{idx}. {song}\n".encode())

        connstream.send(b"\nType the number of the song you want to play: ")

        data = connstream.recv(1024)
        if not data:
            return
        choice = int(data.decode().strip())

        if 1 <= choice <= len(songs):
            selected_song = songs[choice - 1]
            client_song_map[client_id] = selected_song
            connstream.send(f"\nStreaming '{selected_song}' shortly...\n".encode())
        else:
            connstream.send(b"Invalid selection. Closing connection.\n")
            connstream.close()
            return
    except Exception as e:
        print(f"[CONTROL ERROR] {addr}: {e}")
    finally:
        connstream.close()
        print(f"[CONTROL] {addr} disconnected.")

def handle_data(client_sock, addr, client_id):
    print(f"[DATA] {addr} connected. Playing audio...")
    song = client_song_map.get(client_id)
    if not song:
        print("[DATA ERROR] No song selected for this client.")
        client_sock.close()
        return

    try:
        with wave.open(song, 'rb') as wf:
            data = wf.readframes(CHUNK_SIZE)
            while data:
                try:
                    client_sock.sendall(data)
                except Exception as e:
                    print(f"[DATA ERROR] {addr}: {e}")
                    break
                data = wf.readframes(CHUNK_SIZE)
                time.sleep(0.01)
    except Exception as e:
        print(f"[STREAM ERROR] {addr}: {e}")
    finally:
        client_sock.close()
        print(f"[DATA] {addr} disconnected.")

def start_server():
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)

    control_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    control_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    control_sock.bind((HOST, CONTROL_PORT))
    control_sock.listen(5)
    print(f"[CONTROL SERVER] Listening on port {CONTROL_PORT}...")

    data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    data_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    data_sock.bind((HOST, DATA_PORT))
    data_sock.listen(5)
    print(f"[DATA SERVER] Listening on port {DATA_PORT}...")

    client_id_counter = 0

    while True:
        control_conn, control_addr = control_sock.accept()
        control_stream = context.wrap_socket(control_conn, server_side=True)

        client_id = client_id_counter
        client_id_counter += 1

        threading.Thread(target=handle_control, args=(control_stream, control_addr, client_id)).start()

        # Wait for the client to connect to data server
        data_conn, data_addr = data_sock.accept()
        data_stream = context.wrap_socket(data_conn, server_side=True)
        threading.Thread(target=handle_data, args=(data_stream, data_addr, client_id)).start()

try:
    start_server()
except KeyboardInterrupt:
    print("\n[SHUTDOWN] Server terminated gracefully.")
