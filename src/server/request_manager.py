import base64
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
        self.pkt_to_deliver = seqno
        self.file_dir = "./files"
        self.finish_sending = False
        self.sending_rate = 2048
        self.buffer_size = 4096
        signal.signal(signal.SIGINT, self._close)
        # default logging level, if you want to see logging.info messages,
        # change level to logging.INFO.
        logging.basicConfig(level=logging.WARNING)
    
    '''
    The operation given to this thread is checked and executed in this function's body.
    If the operation's outcome is positive send a (FIN, True) message to the client, otherwise
    send an error message with (FIN, False).
    '''
    def run(self) -> None:
        if self.request_op == "LIST":
            self._send_outcome(self._listing(), "LIST")
        
        if self.request_op == "GET":
            if not self._get_file(self.request_payload, self.pkt_to_deliver):
                self._send_outcome(False, "GET")
            # Send positive outcome to client only if this thread is the last one of GET operation
            if self.finish_sending:
               self._send_outcome(True, "GET")
        
        if self.request_op == "PUT":
            # Send final outcome if PUT's sequence number is -2.
            if self.pkt_to_deliver == -2:
                self._send_outcome(self._upload_file(self.request_payload, self.pkt_to_deliver), "PUT")
            elif not self._upload_file(self.request_payload, self.pkt_to_deliver):
                self._send_outcome(False, "PUT")

        self._close()
        
    
    def _send_outcome(self, outcome : bool, op_name : str):
            if outcome:
                self._send_packet("FIN", 1)
            else:
                self._send_packet("FIN", 0)
            msg = "succeed" if outcome else "failed"
            print(f"Requested {op_name}, server {msg}")


    def _listing(self) -> bool:
        try:
            files = ""
            for file in os.listdir(self.file_dir):
                files += file + " "
            self._send_packet("LIST", files)
            return True
        except Exception as e:
            logging.error("Error: " + e)
            return False
        
    def _get_file(self, filename : str, seqno : int) -> bool:
        try:    
            if seqno == -1:
                print(f"PUT {filename} requested")
                if not os.listdir(self.file_dir).__contains__(filename):
                    logging.warning(f"File \"{filename}\" not found!")
                    return False
                
                logging.info(f"{filename} is present")
                path = self.file_dir + "/" + filename
                num_packet_to_send = math.ceil(os.path.getsize(path)/self.sending_rate)
                self._send_packet("GET", num_packet_to_send)
                return True
            else:
                self._send_block(filename, seqno)
                return True
        except Exception as e:
            logging.warning("An error occurred: " + e)
            return False

    def _upload_file(self, payload : str, seqno : str) -> bool:
        try:
            #start upload procedure, create tmp folder and tmp files.
            print(f"PUT {payload} requested")
            if seqno == -1:
                if os.listdir(self.file_dir).__contains__(payload):
                    os.remove(f"{self.file_dir}/{payload}")
                if  os.path.isdir("./tmp"):
                    shutil.rmtree("./tmp")
                
                os.mkdir("./tmp")
                filepath = "./tmp/" + payload
                Path(filepath).touch()
                #Server ready to receive
                self._send_packet("PUT", None)
            #finished upload procedure, compose file and send outcome
            elif seqno == -2:
                filename = os.listdir("./tmp")[0]
                filename = filename.replace("\'","")
                dump_path = "./tmp/dump.txt"

                if not self._compose_file(dump_path, f"./tmp/{filename}"):
                    return False
            #Save data chunck into temporary file
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

        except Exception as e:
            logging.error("An error occurred: " + e)
            return False
        
        return True
            
    # received file is succesfully saved into tmp file, now 
    # sort every chunck and create final file.
    def _compose_file(self, dump : str, path : str) -> bool:
        logging.info("COMPOSING FILE")
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

    # moving saved file from tmp folder to server's files folder 
    # and delete ./tmp/ and it's contents
    def _save_file(self, filepath):
        logging.info(f"Saving file into {self.file_dir}")
        shutil.move(filepath, self.file_dir)
        shutil.rmtree("./tmp")
        
    # send to client i-th chunck of the choosen  file.
    def _send_block(self, filename : str, seqno: int):
        path = self.file_dir + "/" + filename
        # check if current pkt is the last one
        if seqno >= math.floor(os.path.getsize(path) / self.sending_rate):
            self.finish_sending = True
        payload = base64.b64encode(self._get_chunck(path, seqno)).decode('utf-8')
        self._send_packet("GET", payload, seqno)
 
    # read a specific chucnk of bytes of choosen file, with an offset of sequence_number*sending_rate bytes.
    def _get_chunck(self, filepath : str, seqno : int) -> bytes:
        f = open(filepath, 'rb')
        f.seek(self.sending_rate*seqno, 0)
        data =  f.read(self.sending_rate)
        f.close()
        return data

    def _send_packet(self, operation : str, paylaod : str, seqno=0):
        pkt = build_packet(operation, paylaod, seqno)
        pkt["checksum"] = compute_checksum(pkt)
        self.socket.sendto(json.dumps(pkt).encode(), self.cl_addr)
    
    def _close(self):
        self.socket.close()