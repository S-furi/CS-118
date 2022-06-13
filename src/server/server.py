import socket as sock
import sys
sys.path.insert(0,"..")
from utilities import *
from request_manager import RequestManager
import logging as log

class Server:
    def __init__(self, address, port) -> None:
        self.buffer_size = 4096
        self.address = address
        self.port = port
        self.socket = sock.socket(sock.AF_INET, sock.SOCK_DGRAM)
        self.socket.bind((address, port))
    
    def close(self):
        self.socket.close()
        sys.exit(0)
    
    def listen(self):
        print(f"Server up on port {self.port} ready to receive")
        while True:
            data, addr = self.socket.recvfrom(self.buffer_size)
            print(f"received data from {addr}")
            pkt = decode_package(data)
            if not checksum_integrity(pkt):
                print("Checksum failed")
            req_manger = RequestManager(addr, pkt["op"])
            req_manger.start()
