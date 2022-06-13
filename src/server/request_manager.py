import base64
from threading import Thread
import socket as sock
import sys
import time
from utilities import *
import os
import signal

class RequestManager(Thread):
    
    def __init__(self, addr, operation : str, payload=None) -> None:
        super().__init__()
        self.socket = sock.socket(sock.AF_INET, sock.SOCK_DGRAM)
        self.cl_addr = addr
        self.request_op = operation
        self.request_payload = payload
        self.file_dir = "./files"
        self.sending_buffer_size = 2048
        signal.signal(signal.SIGINT, self._close)
    
    def run(self) -> None:
        if self.request_op == "LIST":
            self._listing()
        if self.request_op == "GET":
            self._get_file(self.request_payload)

    def _listing(self):
        files = ""
        for file in os.listdir(self.file_dir):
            files += file + " "
        self._send_packet("LIST", files)
        print("LIST files sent successfully")
        self._close()
        

    def _get_file(self, filename : str):
        if os.listdir(self.file_dir).__contains__(filename):
            print(f"File present, dividing it into chuncks of {2048} bytes")
            filename = self.file_dir + "/" + filename
            splitFile = list(self._divide_chuncks(filename, self.sending_buffer_size))
            num_packet_to_send = len(splitFile)
            print(f'{filename} will be divided into {num_packet_to_send} packets')
            self._send_packet("GET", num_packet_to_send)
            time.sleep(3)

            for content in splitFile:
                payload = base64.b64encode(content).decode('utf-8')
                self._send_packet("GET", payload)
            print(f"Finished sending {filename}")
        else:
            print(f"\"{filename}\" not found!")
            self._send_packet("FIN", "failure")

    def _divide_chuncks(self, filename : str, size : int): 
        with open(filename, 'rb') as f:
            while content := f.read(size):
                yield content

    def _send_packet(self, operation : str, paylaod : str):
        pkt = build_packet(self.request_op, paylaod)
        pkt["checksum"] = compute_checksum(pkt)
        self.socket.sendto(json.dumps(pkt).encode(), self.cl_addr)
    
    def _close(self):
        self.socket.close()