# Server-Client Chat

Programming Assignment 2: Threaded Socket Programming

CS 3235 - Intro to Computer Networking

------------------------------------------------------

Aliyah Crumbley

acrumbley6@gatech.edu

------------------------------------------------------
## Files Submitted:

+ tchatcli.py
    - Upon execution, a client socket is opened and connected to the provided server ip and port, and requests a login from the server. If the server responds with a 'username taken' error, the user is notified and the program exits gracefully. If the server responds with a successful login, then three threads are created, started, and joined: one for terminal input, one for sending messages to the server, and one for receiving messages from the server. 
    - The terminal input thread waits for input from the terminal, and puts a serialized version of the input into an outgoing-message queue.
    - The server sending thread waits for messages to be added to the outgoin-message queue. It gets and sends all messages added to this queue.
    - The server receiving thread waits for messages to come in from the server. If the server responds with 'exit', the programs exits. Otherwise, the response from the server is printed on the client side.

+ tchatsrv.py
    - Upon execution, the server socket is opened and connected to the provided port. The server listens for up to 5 clients. A new thread is started for each accepted client, with the target function handling user login. If the username is already is use, a 'fail' response is sent to the client and the connection is closed. Otherwise, the client is notified of a successful login, a new User instance is created, and is added to the list of active users. 
    - The client thread is live while the user's session is active. Based on the length-value encoding protocol below, the server deserializes, parses, and handles all of the supported user prompts. For each prompt, the server response to the client with the appropriate information needed for client printing.
    - Once the 'exit' prompt is encountered, the user is removed from the list of active users and hashtag subscription lists, the client is notified of an exit, and the User instance itself is cleaned up and deleted.

+ README.md

------------------------------------------------------
## Client-Server Communication Protocol

I utilized a length-value encoding protcol to coordinate the communication between my server and client(s).

### message Format
        1 byte        2 bytes        variable       2 bytes      variable
    +------------+----------------+-----------+----------------+-----------+
    |  promptID  |  len(hashtag)  |  hashtag  |  len(message)  |  message  |
    +------------+----------------+-----------+----------------+-----------+

### (un)subscribe Format
        1 byte        2 bytes        variable  
    +------------+----------------+-----------+
    |  promptID  |  len(hashtag)  |  hashtag  |
    +------------+----------------+-----------+

### timeline Format
        1 byte    
    +------------+
    |  promptID  |
    +------------+

### exit Format
        1 byte    
    +------------+
    |  promptID  |
    +------------+

------------------------------------------------------
## Learnings, Challenges, & Process

- Learning the python threading API
- Decided to use a queue for client outgoing messages (thread safe!!)
- Creating a User class to maintain overhead for users and their associated information (server side)
- Everything became MUCH easier and straight-forward after creating the class 
- Used shared variables to handle subscriptions to specific hashtags and to #ALL
- Decided to send client-side print statements as responses from the server. This helped reduce need for passed parameters and made code more simple
- Was no aware of the .format() function before. That's a pretty nifty function. Much neater than concatenating strings
- Learned about best practices when "cleaning up" (e.g. del)

------------------------------------------------------
## Known Bugs & Limitations

- The server is programmed to handle up to 5 clients

