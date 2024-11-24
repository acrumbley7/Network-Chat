import sys
import threading
import socket 
from signal import signal, SIGPIPE, SIG_DFL
import time   
signal(SIGPIPE,SIG_DFL) 

class User:
    def __init__(self, username: str, user_socket: socket):
        self.username = username
        self.user_socket = user_socket
        self.subscriptions = []
        self.timeline = []
        self.num_subs = 0

hashtag_subs = dict()
all_subs = set()
users = []
lock = threading.Lock()


def login(username):
    global users
    lock.acquire()
    if username not in users:
        users.append(username)
        lock.release()
        return True
    else:
        lock.release()
        return False

#    message Format
#        1 byte        2 bytes        variable       2 bytes      variable
#    +------------+----------------+-----------+----------------+-----------+
#    |  promptID  |  len(hashtag)  |  hashtag  |  len(message)  |  message  |
#    +------------+----------------+-----------+----------------+-----------+


def handle_post(user: User, buf):
    hashtag_length = int.from_bytes(buf[1:3], 'big')
    hashtag = buf[3:3+hashtag_length].decode()
    serialized_message = buf[3+hashtag_length:]
    message = []
    i = 0
    while i < len(serialized_message):
        word_length = int.from_bytes(serialized_message[i:i+2], 'big')
        word = serialized_message[i+2 : i+2+word_length]
        message.append(word.decode())
        i = i+2+word_length

    message = ' '.join(message)
    validity = validate_post(hashtag, message)
    if validity == 111:
        print("{}: {} {} sent".format(user.username, hashtag, message), flush=True)
        response = "{}: {} {} sent".format(user.username, hashtag, message)
    else:
        response = "Message: Illegal Message"
    user.user_socket.sendall(response.encode())
    if validity == 111:
        broadcast_msg = "{}: {} {}".format(user.username, hashtag, message)
        time.sleep(0.5)
        handle_broadcast(hashtag, broadcast_msg)
    
def handle_broadcast(hashtag, message):
    global users
    with lock:
        if hashtag not in hashtag_subs:
            hashtag_subs[hashtag] = set()
        subs = hashtag_subs[hashtag].union(all_subs)
        for user in subs:
            user.user_socket.sendall(message.encode())
            user.timeline.append(message)


def validate_post(hashtag, message):
    if len(hashtag) < 2 or len(hashtag.encode()) > 128:
        return 999
    elif len(message) < 1 or len(message) > 150:
        return 999
    else:
        return 111


#    SUBSCRIBE Format
#        1 byte        2 bytes        variable  
#    +------------+----------------+-----------+
#    |  promptID  |  len(hashtag)  |  hashtag  |
#    +------------+----------------+-----------+

def handle_subscribe(user: User, buf):
    global hashtag_subs
    hashtag = buf[3:].decode()
    with lock:
        if user.num_subs == 5:
            response = "subscribe: Too many Subscriptions"
        else:
            if hashtag not in hashtag_subs:
                hashtag_subs[hashtag] = set([user])
            else:
                hashtag_subs[hashtag].add(user)
            if hashtag == '#ALL':
                all_subs.add(user)
            if hashtag not in user.subscriptions:
                user.subscriptions.append(hashtag)
                user.num_subs += 1
            print("{}: subscribed {}".format(user.username, hashtag), flush=True)
            response = "subscribe: {} added".format(hashtag)
    user.user_socket.sendall(response.encode())
    return


#    UNSUBSCRIBE Format
#        1 byte        2 bytes        variable  
#    +------------+----------------+-----------+
#    |  promptID  |  len(hashtag)  |  hashtag  |
#    +------------+----------------+-----------+

def handle_unsubscribe(user: User, buf):
    hashtag = buf[3:].decode()
    with lock:
        all_subs.discard(user)
        hashtag_subs[hashtag].discard(user)
        if hashtag in user.subscriptions:
            user.subscriptions.remove(hashtag)
            user.num_subs -= 1
            print("{}: unsubscribed {}".format(user.username, hashtag), flush=True)
            response = "unsubscribe: {} removed".format(hashtag)
        else:
            response = ''
    user.user_socket.sendall(response.encode())
    return

#    TIMELINE Format
#        1 byte    
#    +------------+
#    |  promptID  |
#    +------------+

def handle_timeline(user: User, buf):
    response = ''
    with lock:
        if len(user.timeline) == 0:
            response = "timeline: No Messages Available"
        else:
            response = '\n'.join(user.timeline)
            user.timeline.clear()
    user.user_socket.sendall(response.encode())
    return


#    EXIT Format
#        1 byte    
#    +------------+
#    |  promptID  |
#    +------------+

def handle_exit(user: User):
    global hashtag_subs
    with lock:
        for _, subs_list in hashtag_subs.items():
            subs_list.discard(user)
        users.remove(user)
    user.subscriptions.clear()
    user.timeline.clear()
    print("{} logged out".format(user.username), flush=True)
    user.username = None
    user.user_socket.sendall('exit'.encode())
    del user
    return

def handle_session(user: User):
    buf = bytearray()
    data = bytearray()
    while True:
        buf += user.user_socket.recv(4096)
        if not buf: continue
        else:
            data += buf
            prompt = data[0]
            if prompt == 2:
                handle_post(user, data)

            elif prompt == 3:
                handle_subscribe(user, data)

            elif prompt == 4:
                handle_unsubscribe(user, data)

            elif prompt == 5:
                handle_timeline(user, data)

            elif prompt == 6:
                handle_exit(user)
            buf.clear()
            data.clear()

def handle_new_client(user_socket):
    global users
    buf = bytes()
    while True:
        buf += user_socket.recv(4096)
        if len(buf) == 0:
            break
        if buf[0] == 1:
            username = buf[1:].decode()
            logged_in = login(username)
            if not logged_in:
                user_socket.sendall((999).to_bytes(4, 'big'))
                user_socket.close()
                break
            else:
                print("{} logged in".format(username), flush=True)
                user_socket.sendall((111).to_bytes(4, 'big'))
                new_user = User(username, user_socket)
                with lock:
                    users.append(new_user)
                
                handle_session(new_user)
                buf = bytes()
                continue
            

def start_server(port):
    global threads
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('localhost', port))
    server.listen(5)
    print("Server started on port {}. Accepting connections".format(port), flush=True)

    while True:
        client_sock, client_addr = server.accept()
        client_thread = threading.Thread(target=handle_new_client, args=(client_sock))
        client_thread.start()


def main():
    if len(sys.argv) < 2:
        print('Not enough command line arguments.', flush=True)
    else:
        port = int(sys.argv[1])
        start_server(port)

if __name__ == '__main__':
    main()

# Formatted Print Statements for the Server Side.

# server_started = "Server started on port {}. Accepting connections".format(port)
# user_logged_in = "{} logged in".format(username)
# user_logged_out = "{} logged out".format(username)
# subscribe_confirm = "{}: subscribed {}".format(username, hashtag)
# unsubscribe_confirm = "{}: unsubscribed {}".format(username, hashtag)
# message_received_sent = "{}: {} {} sent".format(username, hashtag, message)


