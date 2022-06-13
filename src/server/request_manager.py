from threading import Thread
import socket as sock
import sys
from utilities import *
import os

class RequestManager(Thread):
    
    def __init__(self, addr, operation : str) -> None:
        super().__init__()
        self.socket = sock.socket(sock.AF_INET, sock.SOCK_DGRAM)
        self.cl_addr = addr
        self.request = operation
        self.file_dir = "./files"
        self.sending_buffer_size = 4096
    
    def run(self) -> None:
        if self.request == "LIST":
            self._listing()

    def _listing(self):
        files = ""
        for file in os.listdir(self.file_dir):
            files += file + " "
        self._send_packet(files)

    def _send_packet(self, paylaod : str):
        pkt = build_packet(self.request, paylaod)
        pkt["checksum"] = compute_checksum(pkt)
        self.socket.sendto(json.dumps(pkt).encode(), self.cl_addr)