import base64
import socket as sock
import os
import sys
import logging
from time import sleep
sys.path.insert(0, "..")
from utilities import *

class Client:
    def __init__(self, server_addr):
        self.socket = sock.socket(sock.AF_INET, sock.SOCK_DGRAM)
        self.socket.settimeout(3)
        self.server_addr = server_addr
        self.buffer_size = 4096
        self.sending_rate = 2048
        self.files_dir = "./downloads"
        if not os.path.isdir(self.files_dir):
            os.mkdir(self.files_dir)
        
    def get_list(self):
        self._send_pkt("LIST", None)
        data, addr = self.socket.recvfrom(self.buffer_size)
        if self._check_incoming_package(data):
            pkg = decode_package(data)
            print("Files available for download:")
            for name in pkg.get('payload').split():
                print(f'-{name}')

    def get_file(self, filename : str):
        try:
            print(f"Sending request for {filename} to the server")
            self._send_pkt("GET", filename, -1)
            raw_data, addr = self.socket.recvfrom(self.buffer_size)
            sleep(1)    
            data = decode_package(raw_data)
            if self._check_incoming_package(raw_data) and not (data.get('op') == "FIN"):
                
                expected_packets = data.get('payload')
                
                filepath = self.files_dir + "/copy_" + filename
                
                f = open(filepath, 'w+b')
                for i in range(expected_packets):
                    self._send_pkt("GET", filename, i)
                    raw_data, addr = self.socket.recvfrom(self.buffer_size)
                    pkg = decode_package(raw_data)
                    rcv_seqno = pkg.get('seqno')
                    
                    if rcv_seqno != i:
                        logging.error(f'Expected #{i} but received #{rcv_seqno}, aborting operation try again')
                        return False
                    
                    chunck = base64.b64decode(pkg.get('payload').encode())
                    f.write(chunck)

                f.close()
            else:
                logging.warning("The file is not found")
        except sock.timeout:
            logging.error("TIME OUT!")
            return False
        finally:
            data, addr = self.socket.recvfrom(self.buffer_size)
            if not self._check_incoming_package(data):
                logging.error("Something went wrong during download, please try again")
            else:
                print(f"{filename} succesfully downloaded")
            self.socket.close()
        return True

    def _check_incoming_package(self, raw_data : bytes) -> bool:
        pkt = decode_package(raw_data)
        if pkt.get('op') == "FIN" and pkt.get('payload') == "failure":
            print("PACKAGE FAILED")
            return False
        if checksum_integrity(pkt):
            return True
        else:
            logging.error("checksum is incorrect: package may be corrupted...")
            return False

    def _send_pkt(self, operation : str, payload, seqno=0):
        pkt = build_packet(operation, payload, seqno)
        pkt["checksum"] = compute_checksum(pkt)
        data = json.dumps(pkt)
        self.socket.sendto(data.encode(), self.server_addr)
        