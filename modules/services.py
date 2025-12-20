import socket
import os
import struct
import time
import subprocess

class Bluetooth:
    def __init__(self):
        try:
            os.system("sudo hciconfig hci0 down")
            time.sleep(1)
            os.system("sudo hciconfig hci0 up")
            os.system("sudo hciconfig hci0 piscan")
            os.system("sudo systemctl restart bluetooth")
            time.sleep(1)
            os.system("sudo sdptool add --channel=1 SP")
            os.system("sudo chmod 777 /var/run/sdp")
        except:
            pass
        
        self.server_sock = None
        self.client_sock = None
        self.start()

    def _get_mac(self):
        try:
            result = subprocess.check_output("hciconfig hci0", shell=True).decode()
            if "BD Address: " in result:
                return result.split("BD Address: ")[1].split(" ")[0].strip()
        except:
            pass

        try:
            with open('/sys/class/bluetooth/hci0/address', 'r') as f:
                return f.read().strip()
        except:
            pass
        
        return None

    def start(self):
        if self.server_sock:
            try: self.server_sock.close()
            except: pass

        try:
            self.server_sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            mac = self._get_mac()
            if mac:
                self.server_sock.bind((mac, 1))
                self.server_sock.listen(1)
                self.server_sock.setblocking(False)
            else:
                self.server_sock = None
        except:
            self.server_sock = None

    def update(self):
        if self.server_sock is None:
            self.start()
            return None

        if self.client_sock is None:
            try:
                self.client_sock, _ = self.server_sock.accept()
                self.client_sock.setblocking(False)
            except:
                pass

        if self.client_sock:
            try:
                data = self.client_sock.recv(1024)
                if not data:
                    self.close_client()
                    return None
                return data.decode('utf-8').strip()
            except BlockingIOError:
                pass
            except:
                self.close_client()
        
        return None

    def send_byte(self, value):
        if self.client_sock:
            try:
                self.client_sock.send(struct.pack('b', value))
            except:
                self.close_client()

    def close_client(self):
        if self.client_sock:
            try: self.client_sock.close()
            except: pass
            self.client_sock = None

    def cleanup(self):
        self.close_client()
        if self.server_sock:
            try: self.server_sock.close()
            except: pass