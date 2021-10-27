import socket
from threading import Thread, Lock
import string
import random
import time
import json
import sys

userPWMutex = Lock()
groupsMutex = Lock()
messagesMutex = Lock()

def handleLogin(connection):
    with open('userPW.json') as json_file:
        userPW = json.load(json_file)

    while True:
        username = connection.recv(2048)
        if username:
            username = username.decode()
            if username == '5':
                print('Received exit, returning')
                return
            break

    while True:
        password = connection.recv(2048)
        if password:
            password = password.decode()
            break

    if username not in userPW:
        userPWMutex.acquire()

        with open('userPW.json') as json_file:
            userPW = json.load(json_file)

        userPW[username] = password
        
        with open('userPW.json', 'w') as outfile:
            json.dump(userPW, outfile)

        userPWMutex.release()

        connection.send(str.encode('200')) 
        print('Registered : ', username)
        print("{:<8} {:<20}".format('USER', 'PASSWORD'))
        for k, v in userPW.items():
            label, num = k,v
            print("{:<8} {:<20}".format(label, num))
    else:
        # If already existing user, check if the entered password is correct
        if userPW[username] != password:
            connection.send(str.encode('400')) # Response code for login failed
            print('Login Failed : ', username)
            connection.close()
            return
        
        connection.send(str.encode('200')) # Response Code for successfully logged in
        print('Connected : ', username)

    handleMessages(connection, username)

def makeNewGroup(user1, user2):
    newGroupName = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(20)) # for new group names
                
    groupsMutex.acquire()

    with open('groups.json') as json_file:
        groups = json.load(json_file)

    groups[newGroupName] = [user1, user2]

    with open('groups.json', 'w') as outfile:
        json.dump(groups, outfile)

    groupsMutex.release()

    messagesMutex.acquire()

    with open('messages.json') as json_file:
        messages = json.load(json_file)

    messages[newGroupName] = {'messages': []}

    with open('message.json', 'w') as outfile:
        json.dump(messages, outfile)

    messagesMutex.release()

def getGroup(user1, user2):
    with open('groups.json') as json_file:
        groups = json.load(json_file)

    for group in groups:
        if groups[group].contains(user1) and groups[group].contains(user2):
            return group

    return None

def handleMessages(connection, username):
    while True:
        while True:
            method = connection.recv(2048)
            if method:
                break

        method = method.decode()
        print('method is ' + method)
        connection.send(str.encode('1'))

        if method == '1': # send all groups
            with open('groups.json') as json_file:
                groups = json.load(json_file)

            for key in groups:
                if username in groups[key]:
                    receiverArray = groups[key][:]
                    receiverArray.remove(username)

                    connection.send(str.encode(key))
                    connection.send(str.encode(receiverArray[0]))

            connection.send(str.encode('end'))

        elif method == '2': # Send group history
            user = connection.recv(2048) # Group that the user selected
            iteration = connection.recv(2048) # Number of times that the user has seen 10 messages
            user = user.decode()
            iteration = iteration.decode()
            
            group = getGroup(user, username)
            count = 0

            with open('messages.json') as json_file:
                messages = json.load(json_file)

            i = len(messages[group][message]) - 1

            while i >= 0:
                i -= 1
                count += 1

                if count < 10 * iteration: # Skips all messages until the next ten
                    continue
                elif count == 10 * iteration + 10: # Only sends 10 messages at a time
                    break

                m = messages[group][message][i]

                connection.send(str.encode(m['sentAt']))
                connection.send(str.encode(m['sentBy']))
                connection.send(str.encode(m['messageText']))
                
            connection.send(str.encode('end'))

        elif method == '3': # Send message
            receiver = connection.recv(2048)
            message = connection.recv(2048)
            receiver = receiver.decode()
            message = message.decode()

            group = getGroup(username, receiver)

            if not group:
                group = makeNewGroup(username, receiver)

            messagesMutex.acquire()

            with open('messages.json') as json_file:
                messages = json.load(json_file)

            messages[group]['messages'].append({'sendAt': int(time.time()), 'sentBy': username, 'messageText': message})

            with open('message.json', 'w') as outfile:
                json.dump(messages, outfile)

            messagesMutex.release()

        elif method == '4': # Returns all available users that the crnt user can send messages to
            with open('userPW.json') as json_file:
                userPW = json.load(json_file)
            
            for user in userPW:
                if user == username:
                    continue
                
                connection.send(str.encode(user))

            connection.send(str.encode('end'))

        elif method == '5': # Disconnect
            print('disconnected')
            connection.close()
            return

def main():
    ServerSocket = socket.socket(family = socket.AF_INET, type = socket.SOCK_STREAM)

    if len(sys.argv) != 3:
        sys.exit('Incorrect number of arguments, please provide a host and port number')

    host = str(sys.argv[1])
    port = int(sys.argv[2])

    try:
        ServerSocket.bind((host, port))
    except socket.error as e:
        print(str(e))

    print('Waiting for a Connection ...')
    ServerSocket.listen(5)

    while True:
        try:
            Client, address = ServerSocket.accept()
            print('Connected to: ' + address[0] + ':' + str(address[1]))
            client_handler = Thread(target = handleLogin, args = (Client,))
            client_handler.start()
            client_handler.join()
        except socket.error as e:
            print(str(e))

if __name__ == "__main__":
    main()
    
# userPW = {
#     'username': 'PW',
#     'username': 'PW'
# }

# groups = {
#     {
#         'hsduiofhsdjiof': [
#             'user',
#             'user'
#         ],
#         'shdifodjs': [
#             'user',
#             'user'
#         ]
#     }
# }

# messages = {
#     {
#         'hsduiofhsdjiof': {
#             'messages': [
#                 {
#                     'sentAt': '...',    
#                     'sentBy': '...',
#                     'messageText': '...'
#                 },
#                 {
#                     'sentAt': '...',    
#                     'sentBy': '...',
#                     'messageText': '...'
#                 }
                
#             ]
#         },
#         'shdifodjs': {
#             'messages': [
#                 {
#                     'sentAt': '...',
#                     'sentBy': '...',
#                     'messageText': '...'
#                 }
                
#             ]
#         }
#     }
# }