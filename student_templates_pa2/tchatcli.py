import select
import sys
import socket
import threading
import queue
import time


prompts = {
    'login': b'\x01',
    'message': b'\x02',
    'subscribe': b'\x03',
    'unsubscribe': b'\x04',
    'timeline': b'\x05',
    'exit': b'\x06'
}

message_queue = queue.Queue()

def handle_input():
    global message_queue
    print(">> ", end='', flush=True)
    while True:
        time.sleep(0.5)
        user_input = ''
        user_input = input()
        user_input = user_input.split()
        prompt = user_input[0]
        if prompt not in prompts.keys():
            print('Invalid prompt.', flush=True)
            continue
        payload_bytes = [word.encode() for word in user_input[1:]]
        payload = prompts[prompt]
        for word in payload_bytes:
            payload += len(word).to_bytes(2, 'big') + word   
        message_queue.put(payload)

        

def handle_server_send(client_socket):
    global message_queue
    while True:
        if message_queue.empty(): continue
        else:
            message = message_queue.get()
            client_socket.sendall(message)

def handle_server_recv(client_socket):
    global message_queue
    buf = bytearray()
    while True:
        buf += client_socket.recv(4096)
        if not buf: continue
        else:
            server_msg = buf
            if server_msg.decode() == 'exit':
                client_socket.close()
                sys.exit()
            print(f'\r{server_msg.decode()}', flush=True)
            print(">> ", end='', flush=True)
            buf.clear()


def start_client(server_ip, server_port, username):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_ip, server_port))
    message = prompts['login'] + username.encode()
    client_socket.sendall(message)
    res = client_socket.recv(4096)
    res = int.from_bytes(res, 'big')
    if res == 999:
        print("Connection Failed: Username Taken", flush=True)
        return
    elif res == 111:
        print("Connected to {} on port {}".format(server_ip, server_port), flush=True)
        input_thread = threading.Thread(target=handle_input)
        send_thread = threading.Thread(target=handle_server_send, args=(client_socket,))
        recv_thread = threading.Thread(target=handle_server_recv, args=(client_socket))
        input_thread.start()
        send_thread.start()
        recv_thread.start()
        input_thread.join()
        send_thread.join()
        recv_thread.join()

    else:
        print(f'ERROR: Recieved an invalid response from the server -> {res}', flush=True)

def main():

    if len(sys.argv) < 4:
        print('Not enough command line arguments.', flush=True)
    else:
        server_ip = sys.argv[1]
        server_port = int(sys.argv[2])
        username = sys.argv[3]
        start_client(server_ip, server_port, username)
        return

if __name__ == '__main__':
    main()
# client_connected = "Connected to {} on port {}".format(server_ip, port)
# connection_failed_username_taken = "Connection Failed: Username Taken"
# subscribe_added = "subscribe: {} added".format(hashtag)
# subscribe_too_many = "subscribe: Too many Subscriptions"
# message_sent = "{}: {} {} sent".format(username, hashtag, message)
# message_illegal = "Message: Illegal Message"
# unsubscribe_removed = "unsubscribe: {} removed".format(hashtag)
# timeline_no_messages = "timeline: No Messages Available"
# timeline_message = "{}: {} {}".format(sender_username, origin_hashtag, message)
# exit_message = "Exiting client"
