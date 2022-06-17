import sys
from client import Client

def display_outcome(outcome : bool, op_name : str):
    msg = "succeed" if outcome else "failed"
    print(f"\n{op_name} {msg}")

def main():
    while True:
        clnt = Client(('localhost', 8080))
        op = input("Please, select one of the following operations\n\
                    1) Listing of all the files contained in the server\n\
                    2) Get a file contained in the server\n\
                    3) Upload a file to the server\n\
                    4) EXIT\n")
        
        if op == '1':
            display_outcome(clnt.get_list(), "LIST")
        elif op == '2':
            filename = input("Insert file name: ")
            display_outcome(clnt.get_file(filename), "GET")
        elif op == '3':
            filename = input("Insert file name: ")
            display_outcome(clnt.upload_file(filename), "PUT")
        
        elif op == '4':
            print("Bye bye")
            sys.exit(0)

        cont = input("Do you want to continue?[Y,n]: ")
        cont = cont.lower()
        if not(cont == 'y' or cont == ""):
            clnt.close()
            sys.exit(0)

if __name__ == "__main__":
    main()