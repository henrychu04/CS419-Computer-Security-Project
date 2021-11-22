import socket, hashlib, json, rsa, time, os

timeout = 0.5

class client:
    connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connection.settimeout(5) # Number of seconds before timeout

    def connect(self, host, port):
        self.host = host
        self.port = port

        try:
            self.connection.connect((self.host, self.port))
            print('Connected to: ' + self.host + ':' + str(self.port))
            return True
        except socket.error as e:
            print(str(e))
            return False

    def login(self, username, password):
        self.username = username

        data = json.dumps({"username": username, "password": hashlib.sha256(str.encode(password)).hexdigest()})
        self.connection.send(data.encode())
        
        loginResponse = self.receiveResponse()

        if loginResponse == '200':
            return True
        elif loginResponse == '201':
            try:
                os.makedirs('./privateKeys/', exist_ok=False)
            except:
                pass

            publicKey, privateKey = rsa.newkeys(512)
            privateKeyPem = privateKey.save_pkcs1().decode('utf8')

            f = open(f"./privateKeys/{self.username}PEM.pem", "w")
            f.write(privateKeyPem)
            f.close()

            publicKeyPem = publicKey.save_pkcs1().decode('utf8')
            data = json.dumps({"publicKey": publicKeyPem})
            self.connection.send(data.encode())
            
            newResponse = self.receiveResponse()

            if newResponse == '200':
                return True
            else:
                return False
        else:
            return False

    def getAvailableUsers(self):
        self.connection.send(str.encode('3'))
        self.receiveAck()

        data = self.receiveResponse()
        data = json.loads(data)
        availableUsersArray = data.get("recipients")

        return availableUsersArray

    def getGroups(self):
        self.connection.send(str.encode('4'))
        self.receiveAck()

        data = self.receiveResponse()
        data = json.loads(data)
        groups = data.get("groups")

        return groups

    def sendMessage(self, recipient, message):
        self.connection.send(str.encode('5'))
        self.receiveAck()

        data = json.dumps({"recipient": recipient})
        self.connection.send(data.encode())

        data = self.receiveResponse()

        if data == '404':
            return '404'
        elif data == '403':
            return '403'

        data = json.loads(data)
        publicKey = data.get("publicKey")

        publicKey = rsa.PublicKey.load_pkcs1(publicKey)
        encrypted = rsa.encrypt(message.encode('utf-8'), publicKey)

        self.connection.send(encrypted)

        return self.receiveResponse()

    def getMessageHistory(self, recipient, iteration):
        self.connection.send(str.encode('6'))
        self.receiveAck()

        data = json.dumps({"recipient": recipient, "iteration": iteration})
        self.connection.send(data.encode())

        data = self.receiveFullResponse()

        if data == '400':
            return 400
        elif data == '403':
            return 403
        elif data == '404':
            return 404

        data = json.loads(data)
        messages = data.get("messages")
        decryptedArray = []

        try:
            with open(f'./privateKeys/{self.username}PEM.pem', mode='rb') as privateKeyFile:
                keydata = privateKeyFile.read()
        except:
            return 500

        privateKey = rsa.PrivateKey.load_pkcs1(keydata)

        for message in messages:
            message = json.loads(message)
            if message['sentBy'] != self.username:
                decrypted = str(rsa.decrypt(message['message'], privateKey))
                message['message'] = decrypted[2:-1]
            else:
                message['message'] = '=== Message Encrypted ==='

            decryptedArray.append(message)

        end = data.get("end")

        return decryptedArray, end

    def disconnect(self):
        self.connection.send(str.encode('9'))
        self.connection.close()

    def receiveAck(self):
        ack = self.receiveResponse()
        if ack != '1':
            raise Exception('Ack not received')

    def receiveResponse(self):
        response = self.connection.recv(2048)
        return response.decode()

    def receiveFullResponse(self):
        self.connection.setblocking(0)
        total_data = [];
        data = '';
        begin = time.time()

        while 1:
            if total_data and time.time() - begin > timeout:
                break
            
            try:
                data = self.connection.recv(4096)
                if data:
                    total_data.append(data)
                    begin = time.time()
            except:
                pass
        
        self.connection.setblocking(1)
        return b''.join(total_data).decode()
