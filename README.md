# Python-SFTP-Client-and-Server
Python SFTP client and Server for examination of SFTP server performance 

I needed a way to test the preformance of a known SFTP server while uploading a certain file to it in Chunks of data. The common tools known for testing performance like "JMeter" for example, are only able to test SFTP server's performance for uploading the entire file at once, but because the data to the server only being uploaded in chunks and the chunks are reletivly small to the entire file's size therefore testing the server's performance for entire file uploads wouldn't represent the real performance of the SFTP server. Therfore I had to find a way to upload files to the server in chunks simultaneously while checking the upload time of chunks and the overall upload time of the all file for different amount of users uploading simultaneously and in that way get an overview for the SFTP server performance.
For that reason I built two programs in python, SFTP_Client.py and SFTP_Server.py

# SFTP
SFTP stand for "SSH File Transfer Protocol". It is commanly used for a secure way to tranfering file from a client to server.

Both of my programs use the python paramiko module in order to create and handle the SFTP connections.

#  My SFTP Server
The Server program I build is used for testing my client program for bugs and errors before using it on the on the real SFTP Server. 
It contains a threading class that handles each client call simultaneously in a different thread.
The program also contains a parser, that way the user can change the program parameters to his needs.


# SFTP Client
The SFTP clients is a bit more advanced than the my SFTP server program, the client program contains several functions and classes.
The first class is the "FileHandlerWithHeader" class. Because normal log file do not support headers in them this class replaces the normal log handler of the python loggin module. The header of the log file will contain the file size, the packet size, the number of threads uploading (users), the delay time in seconds between each upload and if the uploads are executed with closing and opening the connection of the client with the server after each upload or keeping the connection opent at all times and only after uploading the entire file closing the connection.
The second class is the threading class and it is used to handle the users uploads in different threads.
In addition there are the "start_clients" and "main" functions. The start_clients function initialize the log file header and starts a number of uploads in different threads according to the giving values.
And the main function initializes the parser and his defualt values so it will be posible for the user to change those values while executing the client from the command prompt according to his needs.     
