import sys
import hashlib
import json

"""
Header Composition:
    -operation (LIST, GET, PUT, FIN)
    -sequence number (Only used by GET and PUT)
    -checksum
    -payload (in case of FIN, here is stored the success of the operation)
"""

def build_packet(operation : str, payload, seqno=0) -> dict:
    pkt = {
        "op" : operation,
        "seqno" : seqno,
        "checksum" : None,
        "payload" : payload
    }
    return pkt

def compute_checksum(pkt) -> str:
    return hashlib.sha1(json.dumps(pkt).encode()).hexdigest()

def decode_package(raw_data) -> dict:
    return dict(json.loads(raw_data))

def checksum_integrity(pkt : dict) -> bool:
    original = pkt.get("checksum")
    pkt["checksum"] = None
    computed = compute_checksum(pkt)
    return computed == original
    