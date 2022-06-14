import sys
from client import Client

while True:
    clnt = Client(('localhost', 8080))
    op = input("Please, select one of the following operations\n\
                1) Listing of all the files contained in the server\n\
                2) Get a file contained in the server\n\
                3) EXIT\n")
    
    if op == '1':
        clnt.get_list()
    elif op == '2':
        filename = input("Insersci il nome del file: ")
        filename = filename.lower()
        if not clnt.get_file(filename):
            print("Client failed")
            sys.exit(0)
    elif op == '3':
        print("Bye bye")
        sys.exit(0)

    cont = input("Do you want to continue?[Y,n]: ")
    cont = cont.lower()
    if not(cont == 'y' or cont == ""):
        sys.exit(0)