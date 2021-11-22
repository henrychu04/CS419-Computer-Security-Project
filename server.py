import socket, threading, string, random, json, logging, time

logger = logging.getLogger() # Custom logging
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('[%(asctime)s:%(levelname)s] [%(threadName)s]: %(message)s', datefmt='%I:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)

userPWMutex = threading.Lock() # Every time something has to be written to a file, a mutex is needed to accomodate different threads
groupsMutex = threading.Lock()
messagesMutex = threading.Lock()
keyMutex = threading.Lock()

def handleLogin(connection, address):
    try:
        data = receiveResponse(connection)
        data = json.loads(data)
    except Exception as e:
        logging.warning(f'No login values detected {str(e)}')
        return
    
    username = data.get("username")
    password = data.get("password")

    threading.current_thread().name = f'{address[0]}:{address[1]}|{username}'

    userPWMutex.acquire()
    userPW = getUserPW()

    if username not in userPW: # Makes a new user for every username that does not exist
        userPW[username] = password
        writeUserPW(userPW)

        logging.info('Registered: ' + username)
        sendNew(connection)

        data = receiveResponse(connection)
        data = json.loads(data)
        publicKey = data.get("publicKey")

        keyMutex.acquire()

        publicKeys = getPublicKeys()
        publicKeys[username] = publicKey
        writePublicKeys(publicKeys)

        keyMutex.release()

        sendSuccess(connection)
    else:
        if userPW[username] != password: # If the password of the user is not correct
            userPWMutex.release()
            logging.info('Login Failed: ' + username)
            sendFailure(connection)
            handleLogin(connection, address)
        
        logging.info('Logged In: ' + username) # User is logged in
        sendSuccess(connection)
    
    userPWMutex.release()

    handleMessages(connection, username)

def handleMessages(connection, username):
    while True:
        method = receiveResponse(connection)

        if method == "":
            logging.warning('Connection closed, returning')
            return

        logging.info(f'Method: {method}')

        try:
            connection.send(str.encode('1')) # Send ack
        except Exception as e:
            logging.error(str(e))
            return

        if method == '3': # Returns all available users that the crnt user can send messages to
            userPW = getUserPW()
            recipients = []
            
            for user in userPW:
                if user == username: # User cannot send messages to itself
                    continue
                
                recipients.append(user)

            data = json.dumps({"recipients": recipients})
            connection.send(data.encode())

        elif method == '4': # send all historical messaging groups 
            groups = getGroups()
            groupsArray = []

            for key in groups:
                if username in groups[key]:
                    recipientArray = groups[key][:]
                    recipientArray.remove(username) # Removes crnt user's own username
                    groupsArray.append({"recipient": recipientArray[0]})

            data = json.dumps({"groups": groupsArray})
            connection.send(data.encode())
            
        elif method == '5': # Send message
            data = receiveResponse(connection)
            data = json.loads(data)
            recipient = data.get("recipient")

            if verifyUser(recipient) is False: # Checks if the requested recipient exists
                sendNotExist(connection)
                continue

            if username == recipient: # User cannot send messages to itself
                sendForbidden(connection)
                continue

            publicKeys = getPublicKeys()

            if recipient not in publicKeys: # Checks if recipient public key exists
                sendNotExist(connection)
                continue
            
            data = json.dumps({"publicKey": publicKeys[recipient]})
            connection.send(data.encode())

            group = getAvailableGroups(username, recipient)

            if group is None: # Checks if there has been messages history between both users
                group = makeNewGroup(username, recipient) # If not, creates a new message group

            message = connection.recv(4096)

            messagesMutex.acquire()

            messages = getMessages()
            messages[group]['messages'].append(json.dumps({"sentAt": int(time.time()), "sentBy": username, "message": list(message)})) # Writes the new messsage to the messages file
            writeMessages(messages)

            messagesMutex.release()

            sendSuccess(connection)

        elif method == '6': # Send message history
            data = receiveResponse(connection)

            data = json.loads(data)
            recipient = data.get("recipient")
            iteration = data.get("iteration") # Number of times that the user has seen 10 messages

            if verifyUser(recipient) is False: # Checks if the requested recipient exists
                sendNotExist(connection)
                continue

            if username == recipient: # Cannot see message history of yourself
                sendForbidden(connection)
                continue

            group = getAvailableGroups(recipient, username)

            if group is None: # Checks if message history exists between crnt user and recipient
                sendFailure(connection)
                continue

            messages = getMessages()

            i = len(messages[group]['messages']) - (10 * (iteration - 1)) - 1 # To find the next 10 messages that the user requested
            messageArray = []
            count = 0

            while i >= 0:
                messageArray.append(messages[group]['messages'][i])

                count += 1
                i -= 1

                if count == 10: # Only sends 10 messages at a time
                    break

            if i < 0: # Detects if all messages have been sent to the user
                end = True
            else:
                end = False

            data = json.dumps({"messages": messageArray, "end": end})
            connection.send(data.encode())
                
        elif method == '9': # Disconnect
            logging.info('Disconnected')
            connection.close()
            return

def main():
    ServerSocket = socket.socket(family = socket.AF_INET, type = socket.SOCK_STREAM)

    with open('config.json') as json_file:
        config = json.load(json_file)

    host = config['host']
    port = config['port']

    try:
        ServerSocket.bind((host, port))
    except Exception as e:
        logging.error(str(e))
        if str(e) == '[Errno 98] Address already in use':
            config['port'] = config['port'] + 1
            with open('config.json', 'w') as outfile:
                json.dump(config, outfile)
            logging.info('Port number increased by one')
        return

    logging.info('Waiting for a Connection ...')
    ServerSocket.listen()

    while True:
        try:
            Client, address = ServerSocket.accept()
            logging.info(f'Connected to: {address[0]}:{address[1]}')
            clientThread = threading.Thread(target = handleLogin, args = (Client, address))
            clientThread.start()
        except Exception as e:
            logging.info(str(e))

def sendSuccess(connection):
    connection.send(str.encode('200'))

def sendNew(connection):
    connection.send(str.encode('201'))

def sendFailure(connection):
    connection.send(str.encode('400'))

def sendNotExist(connection):
    connection.send(str.encode('404'))

def sendForbidden(connection):
    connection.send(str.encode('403'))

def getMessages():
    with open('messages.json') as json_file:
        return json.load(json_file)

def getGroups():
    with open('groups.json') as json_file:
        return json.load(json_file)

def getUserPW():
    with open('userPW.json') as json_file:
        return json.load(json_file)

def getPublicKeys():
    with open('publicKeys.json') as json_file:
        return json.load(json_file)

def writeMessages(messages):
    with open('messages.json', 'w') as outfile:
        json.dump(messages, outfile)

def writeGroups(groups):
    with open('groups.json', 'w') as outfile:
        json.dump(groups, outfile)

def writeUserPW(userPW):
    with open('userPW.json', 'w') as outfile:
        json.dump(userPW, outfile)

def writePublicKeys(publicKeys):
    with open('publicKeys.json', 'w') as outfile:
        json.dump(publicKeys, outfile)

def receiveResponse(connection):
    response = connection.recv(2048)
    return response.decode()

def verifyUser(user):
    userPW = getUserPW()

    if user not in userPW:
        return False
    else:
        return True

def getAvailableGroups(user1, user2):
    groups = getGroups()

    for group in groups:
        if user1 in groups[group] and user2 in groups[group]:
            return group

    return None

def makeNewGroup(user1, user2):
    newGroupName = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(20)) # for new group names
    
    groupsMutex.acquire()

    groups = getGroups()
    groups[newGroupName] = [user1, user2]
    writeGroups(groups)

    groupsMutex.release()

    messagesMutex.acquire()

    messages = getMessages()
    messages[newGroupName] = {'messages': []}
    writeMessages(messages)

    messagesMutex.release()

    return newGroupName

if __name__ == "__main__":
    main()