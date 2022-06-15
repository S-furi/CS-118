# CS-118: Computer newtworking project 
## Client-Server file transfer over UDP
Required actions are (client side):
- Require the list of all files contained in the server
- Get a specified file from the server
- Put a new file on the server

### Instructions
First, launch the **server** with ```python3 server_runner.py``` and then run the **client** with:```python3 client_runner.py```. A list of all the operations is displayed and client waits for user's input choice:
1. **Listing** 
2. **Get**, and then it's required to type the correct filename
3. **Put**, and then same as above.
4. **Exit**