import socket
import hashlib

class client:
    connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self, host, port):
        self.host = host
        self.port = port

        try:
            self.connection.connect((self.host, self.port))
            print('Connected to: ' + self.host + ':' + str(self.port))
        except socket.error as e:
            print(str(e))

    def login(self, username, password):
        self.username = username
        self.connection.send(str.encode(username))
        self.connection.send(str.encode(hashlib.sha256(str.encode(password)).hexdigest()))

        response = self.connection.recv(2048)
        response = response.decode()

        if response == '200':
            return True
        else:
            return False

    def getGroups(self):
        self.connection.send(str.encode('1'))
        self.receiveAck()

        groups = {}

        while True:
            key = self.connection.recv(2048)
            key = key.decode()

            if key == 'end':
                break
                
            receiver = self.connection.recv(2048)
            receiver = receiver.decode()

            groups[key] = receiver
        
        return groups

    def getMessageHistory(self, user, iteration): # Need to implement iteration
        self.connection.send(str.encode('2'))
        self.receiveAck()

        self.connection.send(str.encode(user))
        self.connection.send(str.encode(iteration))

        messages = []

        while True:
            sentAt = self.connection.recv(2048)
            sentBy = sentBy.decode()

            if sentAt == 'end':
                break

            sentBy = self.connection.recv(2048)
            messageText = self.connection.recv(2048)
            
            sentAt = sentAt.decode()
            messageText = messageText.decode()

            messages.append({'sentAt': sentAt, 'sentBy': sentBy, 'messageText': messageText})

        return messages

    def sendMessage(self, user, message): # implement either ecc or rsa
        self.connection.send(str.encode('3'))
        self.receiveAck()

        self.connection.send(str.encode(user))
        self.connection.send(str.encode(message))
    
    def getAvailableUsers(self):
        self.connection.send(str.encode('4'))
        self.receiveAck()

        availableUsersArray = []

        while True:
            user = self.connection.recv(2048)
            user = user.decode()

            if user == 'end':
                break

            availableUsersArray.append(user)

        return availableUsersArray

    def disconnect(self):
        self.connection.send(str.encode('5'))
        self.connection.close()

    def receiveAck(self):
        ack = self.connection.recv(2048)
        ack = ack.decode()
        if ack != '1':
            raise Exception('Ack not received')
