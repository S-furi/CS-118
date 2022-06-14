import base64
import math
import socket as sock
import os
import sys
import logging
from time import sleep, time
sys.path.insert(0, "..")
from utilities import *

class Client:
    def __init__(self, server_addr):
        self.socket = sock.socket(sock.AF_INET, sock.SOCK_DGRAM)
        self.socket.settimeout(3)
        self.server_addr = server_addr
        self.buffer_size = 4096
        self.sending_rate = 2048
        self.upload_dir = "./upload"
        self.files_dir = "./downloads"
        if not os.path.isdir(self.files_dir):
            os.mkdir(self.files_dir)
        if not os.path.isdir(self.upload_dir):
            os.mkdir(self.upload_dir)

    def get_list(self) -> bool:
        self._send_pkt("LIST", None)
        try:
            data, addr = self.socket.recvfrom(self.buffer_size)
            if self._check_incoming_package(data):
                pkg = decode_package(data)
                print("Files available for download:")
                for name in pkg.get('payload').split():
                    print(f'-{name}')
                return True
        except sock.timeout:
            logging.error("TIME OUT!")
            return False

    def get_file(self, filename : str) -> bool:
        try:
            print(f"Sending request for {filename} to the server")
            self._send_pkt("GET", filename, -1)
            raw_data, addr = self.socket.recvfrom(self.buffer_size)
            data = decode_package(raw_data)
            
            if not self._check_incoming_package(raw_data) or data.get('op') == "FIN":
                logging.warning("File not found")
                return False

            expected_packets = data.get('payload')
            
            filepath = self.files_dir + "/copy_" + filename
            f = open(filepath, 'w+b')

            for i in range(expected_packets):
                self._send_pkt("GET", filename, i)
                raw_data, addr = self.socket.recvfrom(self.buffer_size)
               
                if not self._check_incoming_package(raw_data):
                    return False

                pkg = decode_package(raw_data)
                rcv_seqno = pkg.get('seqno')
                #Check if arrived package is the expected one
                if rcv_seqno != i:
                    logging.error(f'Expected #{i} but received #{rcv_seqno}, aborting operation try again')
                    return False
                
                chunck = base64.b64decode(pkg.get('payload').encode())
                f.write(chunck)
            f.close()
    
        except sock.timeout:
            logging.error("TIME OUT!")
            return False
        
        #Receiving final outcome of the operation
        data, addr = self.socket.recvfrom(self.buffer_size)
        if not self._check_incoming_package(data):
            logging.error("Something went wrong during download, please try again")
        else:
            print(f"{filename} succesfully downloaded")
        
        self.socket.close()
        return True

    def upload_file(self, filename : str) -> bool:
        filepath = self.upload_dir + "/" + filename
        if not os.path.isfile(filepath):
            logging.warning(f"{filename} does not appear to be in upload directory")
            return False
        print(f"{filename} exists, preparing to upload")

        self._send_pkt("PUT", filename, seqno=-1)

        data, addr = self.socket.recvfrom(self.buffer_size)
        #If everything is ok, server is ready to receive file chunks
        if not self._check_incoming_package(data):
            print('An error occurred, please try again')
            return False

        file_chunks = self._get_file_chunks(filepath, self.sending_rate)
        chunks_no = math.ceil(os.path.getsize(filepath)/self.sending_rate)
        print(f'{filename} is {os.path.getsize(filepath)} and will be divided into {chunks_no} chunks')

        i = 0
        for chunck in file_chunks:
            payload = base64.b64encode(chunck).decode('utf-8')
            self._send_pkt("PUT", payload, i)
            i += 1

    def _get_file_chunks(self, filepath : str, size : int):
        with open(filepath, 'rb') as f:
            while content := f.read(size):
                yield content

    def _check_incoming_package(self, raw_data : bytes) -> bool:
        pkt = decode_package(raw_data)
        if pkt.get('op') == "FIN" and pkt.get('payload') == "failure":
            logging.warning("A problem occurred, server failed sending packet, please try again")
            return False
        if checksum_integrity(pkt):
            return True
        else:
            logging.error("checksum is incorrect: package may be corrupted...")
            return False

    def _send_pkt(self, operation : str, payload, seqno=0):
        pkt = build_packet(operation, payload, seqno)
        pkt["checksum"] = compute_checksum(pkt)
        size = pkt.get('size')
        data = json.dumps(pkt)
        self.socket.sendto(data.encode(), self.server_addr)
        