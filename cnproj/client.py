import socket
import ssl
import pyaudio

CHUNK = 1024
SAMPLE_FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100

SERVER_HOST = '127.0.0.1'
CONTROL_PORT = 8000
DATA_PORT = 8001

context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE

def choose_song():
    with socket.create_connection((SERVER_HOST, CONTROL_PORT)) as sock:
        with context.wrap_socket(sock, server_hostname=SERVER_HOST) as ssock:
            while True:
                data = ssock.recv(4096).decode()
                print(data, end='')
                if "Type the number" in data:
                    break

            choice = input("Enter your choice: ")
            ssock.sendall(f"{choice}\n".encode())

            response = ssock.recv(1024).decode()
            print(response)

def play_audio():
    with socket.create_connection((SERVER_HOST, DATA_PORT)) as sock:
        with context.wrap_socket(sock, server_hostname=SERVER_HOST) as ssock:
            print("[DATA] Connected. Playing audio...")

            p = pyaudio.PyAudio()
            stream = p.open(format=SAMPLE_FORMAT,
                            channels=CHANNELS,
                            rate=RATE,
                            output=True,
                            frames_per_buffer=CHUNK)

            try:
                while True:
                    data = ssock.recv(CHUNK)
                    if not data:
                        break
                    stream.write(data)
            except Exception as e:
                print("Error during audio streaming:", e)
            finally:
                stream.stop_stream()
                stream.close()
                p.terminate()

# Step 1: Choose the song
choose_song()

# Step 2: Stream the selected song
play_audio()
