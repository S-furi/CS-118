from client import Client

clnt = Client(('localhost', 8080))
clnt.get_file("Beemovie.txt")