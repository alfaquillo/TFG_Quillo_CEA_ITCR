import socket
import cv2
import numpy as np
import time
import sys

def main():
    SERVER_IP = '10.20.20.172'
    PORT = 8080
    
    while True:
        try:
            print(f"Conectando a {SERVER_IP}:{PORT}...")
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(10.0)  
            client.connect((SERVER_IP, PORT))
            client.settimeout(None)  
            print("¡Conectado exitosamente!")
            
            frame_count = 0
            no_data_count = 0
            
            while True:
                try:
                    # Recibir tamaño del frame (4 bytes)
                    size_data = b''
                    while len(size_data) < 4:
                        chunk = client.recv(4 - len(size_data))
                        if not chunk:
                            print("Servidor cerró la conexión (no más datos)")
                            raise ConnectionError("Conexión cerrada")
                        size_data += chunk
                    
                    frame_size = int.from_bytes(size_data, 'big')
                    
                    if frame_size <= 0 or frame_size > 10_000_000:
                        print(f"Tamaño inválido: {frame_size}")
                        break
                    
                    # Recibir datos de la imagen
                    data = b''
                    while len(data) < frame_size:
                        chunk = client.recv(min(65536, frame_size - len(data)))
                        if not chunk:
                            raise ConnectionError("Error recibiendo datos de imagen")
                        data += chunk
                    
                    # Decodificar y mostrar
                    jpeg = np.frombuffer(data, dtype=np.uint8)
                    frame = cv2.imdecode(jpeg, cv2.IMREAD_COLOR)
                    
                    if frame is not None:
                        frame_count += 1
                        no_data_count = 0
                        
                        # Mostrar frame
                        if frame.shape[1] > 1280:
                            scale = 1280 / frame.shape[1]
                            new_w = 1280
                            new_h = int(frame.shape[0] * scale)
                            frame = cv2.resize(frame, (new_w, new_h))
                        
                        cv2.imshow("Stream RPi", frame)
                        
                        # Mostrar estado cada 30 frames
                        if frame_count % 30 == 0:
                            print(f"Frames recibidos: {frame_count}")
                        
                        key = cv2.waitKey(1) & 0xFF
                        if key == ord('q'):
                            print("Cerrando por tecla Q")
                            cv2.destroyAllWindows()
                            client.close()
                            return
                    else:
                        print("Error decodificando frame")
                        no_data_count += 1
                        if no_data_count > 5:
                            raise ConnectionError("Demasiados errores de decodificación")
                        
                except socket.timeout:
                    print("Timeout esperando datos")
                    break
                except ConnectionError as e:
                    print(f"Error de conexión: {e}")
                    break
                except Exception as e:
                    print(f"Error inesperado: {e}")
                    break
                    
        except ConnectionRefusedError:
            print("Conexión rechazada - ¿El servidor está corriendo?")
            time.sleep(2)
        except Exception as e:
            print(f"Error de conexión: {e}")
            time.sleep(2)
        finally:
            try:
                client.close()
            except:
                pass
            print("Reconectando en 2 segundos...")
            time.sleep(2)

if __name__ == "__main__":
    main()