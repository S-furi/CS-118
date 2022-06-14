import base64
import socket as sock
import os
import sys
import logging
sys.path.insert(0, "..")
from utilities import *

class Client:
    def __init__(self, server_addr):
        self.socket = sock.socket(sock.AF_INET, sock.SOCK_DGRAM)
        self.socket.settimeout(4)
        self.server_addr = server_addr
        self.buffer_size = 4096
        self.files_dir = "./downloads"
        if not os.path.isdir(self.files_dir):
            os.mkdir(self.files_dir)
        
    def get_list(self):
        self._send_pkt("LIST", None)
        data, addr = self.socket.recvfrom(self.buffer_size)
        if self._check_incoming_package(data):
            print("Files available for download:")
            for name in data.get('payload').split():
                print(f'-{name}')

    def get_file(self, filename : str):
        self._send_pkt("GET", filename)
        data, addr = self.socket.recvfrom(self.buffer_size)
        #First message that server sends is how many packets it will send to the client
        data = self._check_incoming_package(data)
        if data:
            expected_packages = data.get('payload')
            file = self.files_dir + "/" +"copy_"+ filename
            file_to_write = open(file, 'wb')
            bytes_count = 0
            for i in range(int(expected_packages)):
                data, addr = self.socket.recvfrom(self.buffer_size)
                bytes_count = sys.getsizeof(data)
                data = self._check_incoming_package(data)
                payload = data.get('payload')
                data_chunk = base64.b64decode(payload.encode())
                file_to_write.write(data_chunk)
            print(f"received {i} packages and {bytes_count} bytes in total")
            data, addr = self.socket.recvfrom(self.buffer_size)
            data = decode_package(data)
            if i+1 == expected_packages and (data.get('op') == "FIN" and data.get('payload') == "ok") :
                print(f"\n*** SUCCESFULLY DOWNLOADED \'{filename}\' ***\n")
            else:
                print("something went wrong during download, try again")
            

    def _check_incoming_package(self, raw_data : bytes) -> dict:
        data = decode_package(raw_data)
        if data.get('op') == "FIN" and data.get('payload') == "failure":
            print("PACKAGE FAILED")
            return None
        if checksum_integrity(data):
            return data
        else:
            logging.error("checksum is incorrect: package may be corrupted...")
            return None

    def _send_pkt(self, operation : str, payload):
        pkt = build_packet(operation, payload)
        pkt["checksum"] = compute_checksum(pkt)
        data = json.dumps(pkt)
        self.socket.sendto(data.encode(), self.server_addr)
        print(f"{operation} sento to server")
        