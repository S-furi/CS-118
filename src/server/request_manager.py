import base64
import pickle
import logging
import math
from threading import Thread
import socket as sock
from utilities import *
import os
from pathlib import Path
import signal
import shutil

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
        self.receiving_buffer_size = 4096
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
        if self.request_op == "PUT":
            self._upload_file(self.request_payload, self.pakcet_to_deliver)

        self._close()
        

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
                    num_packet_to_send = math.ceil(os.path.getsize(path)/self.sending_buffer_size)
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

    def _upload_file(self, payload : str, seqno : str) -> bool:
        try:
            if seqno == -1:
                if  os.path.isdir("./tmp"):
                    shutil.rmtree("./tmp")
                os.mkdir("./tmp")
                filepath = "./tmp/" + payload
                Path(filepath).touch()
                #Server ready to receive
                self._send_packet("PUT", None)
            else:
                filename = os.listdir("./tmp")[0]
                filename = filename.replace("\'","")
                dump_path = "./tmp/dump.txt"

                chunck = {
                    "seqno" : seqno,
                    "payload" : payload
                }
                w = open(dump_path, "a")
                w.write(json.dumps(chunck))
                w.close()
                
                if sys.getsizeof(base64.b64decode(payload.encode())) < self.sending_buffer_size:
                    #last packet
                    if not self._compose_file(dump_path, f"./tmp/{filename}"):
                        return False
        except Exception as e:
            logging.error("An error occurred: " + e)
            return False
        
        return True
            

    def _compose_file(self, dump : str, path : str) -> bool:
        try:
            f = open(dump, 'r')
            chuncks = f.read().replace("}{", "};{")

            lst = []
            for c in chuncks.split(";"):
                lst.append(json.loads(c))
            lst = sorted(lst, key=lambda t : t['seqno'])

            w = open(path, 'wb')
            for obj in lst:
                load = base64.b64decode(obj.get("payload"))
                w.write(load)
            self._save_file(path)
        except Exception:
            return False
        return True

    def _save_file(self, filepath):
        shutil.move(filepath, self.file_dir)
        shutil.rmtree("./tmp")


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

    def _send_packet(self, operation : str, paylaod : str, seqno=0):
        pkt = build_packet(operation, paylaod, seqno)
        pkt["checksum"] = compute_checksum(pkt)
        self.socket.sendto(json.dumps(pkt).encode(), self.cl_addr)
    
    def _close(self):
        self.socket.close()