from server import Server
from time import sleep
from socket import *

def main():
    serv = Server('localhost', 8080)
    serv.listen()

if __name__ == "__main__":
    main()