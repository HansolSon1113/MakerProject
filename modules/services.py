import socket
import time
import os
import struct

class Bluetooth:
    def __init__(self):
        self.server_sock = None
        self.client_sock = None
        self.start()

    def _get_mac(self):
        try:
            with open('/sys/class/bluetooth/hci0/address', 'r') as f:
                return f.read().strip()
        except:
            return None

    def start(self):
        if self.server_sock:
            try: self.server_sock.close()
            except: pass

        try:
            self.server_sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
            self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            mac = self._get_mac()
            if not mac: raise Exception("MAC Address not found")

            self.server_sock.bind((mac, 1))
            self.server_sock.listen(1)
            self.server_sock.setblocking(False)
            
        except Exception:
            self.server_sock = None
            time.sleep(2)

    def update(self):
        if self.server_sock is None:
            self.start()
            return None

        if self.client_sock is None:
            try:
                self.client_sock, info = self.server_sock.accept()
                self.client_sock.setblocking(False)
            except BlockingIOError: pass
            except OSError: self.start()

        if self.client_sock:
            try:
                data = self.client_sock.recv(1024)
                if not data:
                    self.close_client()
                    return None
                return data.decode('utf-8').strip()
            except BlockingIOError: pass
            except Exception: self.close_client()
        
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
        if self.server_sock: self.server_sock.close()