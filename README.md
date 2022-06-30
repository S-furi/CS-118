# CS-118: Computer newtworking project 
## Client-Server file transfer over UDP
Requested actions are:
- Require the *list* of all files contained in the server
- *Get* a specified file from the server
- *Put* a new file on the server
- Server's *outcome messages* for all the operations above
### Instructions
First, launch the **server** with ```python3 server_runner.py``` and then run the **client** with:```python3 client_runner.py```. 
A list of all the operations will be displayed and client waits for user's input choice:
1. **Listing** 
2. **Get**, and then type in the file name to download
3. **Put**, and then type in the file name you want to upload
4. **Exit**

Server's files are in ```./src/server/files```, and uploaded files will be saved in this directory.
Client's files are in ```./src/client/upload``` and when *GET* is called, a directory named "*dowload*" will spawn in the same directory.

If you want to close the running server, just press ```ctrl+c```.