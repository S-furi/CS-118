import socket as sock
import sys
import logging as log
sys.path.insert(0, "..")
from utilities import *
class Client:
    def __init__(self, server_addr) -> None:
        self.socket = sock.socket(sock.AF_INET, sock.SOCK_DGRAM)
        self.server_addr = server_addr
        self.buffer_size = 4096

    def get_list(self) -> None:
        self._send_pkt("LIST")
        data, addr = self.socket.recvfrom(self.buffer_size)
        data = decode_package(data)
        if checksum_integrity(data):
            print("Files available for download:")
            print(data.get('payload'))

        else:
            log.error("checksum is incorrect: package may be corrupted...")
    def _send_pkt(self, operation : str) -> None:
        pkt = build_packet("LIST", None)
        pkt["checksum"] = compute_checksum(pkt)
        data = json.dumps(pkt)
        self.socket.sendto(data.encode(), self.server_addr)
        print(f"{operation} sento to server")
        