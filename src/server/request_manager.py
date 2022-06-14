import base64
from fileinput import filename
import logging
import math
from shutil import ExecError
from stat import FILE_ATTRIBUTE_NORMAL
from threading import Thread
import socket as sock
import sys
import time
from utilities import *
import os
import signal

class RequestManager(Thread):
    
    def __init__(self, addr, operation : str, payload=None, seqno=0) -> None:
        super().__init__()
        self.socket = sock.socket(sock.AF_INET, sock.SOCK_DGRAM)
        self.cl_addr = addr
        self.request_op = operation
        self.request_payload = payload
        self.pakcet_to_deliver = seqno
        self.file_dir = "./files"
        self.finish_sending = False
        self.sending_buffer_size = 2048
        signal.signal(signal.SIGINT, self._close)
    
    def run(self) -> None:
        if self.request_op == "LIST":
            self._listing()
        if self.request_op == "GET":
            if self._get_file(self.request_payload, self.pakcet_to_deliver):
                if self.finish_sending:
                    print("File succefully sent!\n")
                    self._send_packet("FIN", "ok")
            else:
                self._send_packet("FIN", "failure")


    def _listing(self) -> bool:
        try:
            files = ""
            for file in os.listdir(self.file_dir):
                files += file + " "
            self._send_packet("LIST", files)
            print("LIST files sent successfully")
            return True
        except Exception as e:
            print("Error: " + e)
            return False
        finally:
            self._close()
        
        

    def _get_file(self, filename : str, seqno : int) -> bool:
        try:    
            if seqno == -1:
                if os.listdir(self.file_dir).__contains__(filename):
                    print(f"{filename} is present")
                    path = self.file_dir + "/" + filename
                    splitFile = list(self._divide_chuncks(path, self.sending_buffer_size))
                    num_packet_to_send = len(splitFile)
                    print(f'{filename} is {os.path.getsize(path)} bytes and will be divided into {num_packet_to_send} packets')
                    self._send_packet("GET", num_packet_to_send)
                    return True
                else:
                    logging.warning(f"File \"{filename}\" not found!")
                    return False
            else:
                self._send_block(filename, seqno)
                return True
        except Exception as e:
            logging.warning("An error occurred: " + e)
            return False
            
    def _send_block(self, filename : str, seqno: int):
        path = self.file_dir + "/" + filename
        if seqno >= math.floor(os.path.getsize(path) / self.sending_buffer_size):
            self.finish_sending = True
        payload = base64.b64encode(self._get_chunck(path, seqno)).decode('utf-8')
        self._send_packet("GET", payload, seqno)
 
    def _get_chunck(self, filepath : str, seqno : int) -> bytes:
        f = open(filepath, 'rb')
        f.seek(self.sending_buffer_size*seqno, 0)
        data =  f.read(self.sending_buffer_size)
        f.close()
        return data

    def _divide_chuncks(self, filename : str, size : int): 
        with open(filename, 'rb') as f:
            while content := f.read(size):
                yield content

    def _send_packet(self, operation : str, paylaod : str, seqno=0):
        pkt = build_packet(operation, paylaod, seqno)
        pkt["checksum"] = compute_checksum(pkt)
        self.socket.sendto(json.dumps(pkt).encode(), self.cl_addr)
    
    def _close(self):
        self.socket.close()