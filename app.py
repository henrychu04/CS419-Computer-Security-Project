from client import client

Client = client()
loggedIn = False

def options():
    print('\n\tEnter "1 <host> <port>" to connect to a host')
    print('\tEnter "2 <username> <password>" to login')
    print('\tEnter "3" to view all available recipients')
    print('\tEnter "4" to send a new message to a user')
    print('\tEnter "5" to view all past message recipient')
    print('\tEnter "6" to view message history between you and a recipient')
    print('\tEnter "9" to diconnect\n')

def connect(args):
    argsArray = args.split()
    # if len(argsArray) != 3:
    #     print('Please provide a host and port number')
    #     return
    # newClient.connect(argsArray[1], int(argsArray[2]))
    Client.connect('127.0.0.1', 12345)

def login(args):
    global loggedIn
    argsArray = args.split()
    # if len(argsArray) != 3:
    #     print('Please provide a username and password')
    #     return
    # logginIn = newClient.login(argsArray[1], argsArray[2])
    loggedIn = Client.login('jio', 'jio')

def getGroups():
    groups = Client.getGroups()
    print('All past message recipients are ' + groups)

def getUsers():
    users = Client.getAvailableUsers()
    print('Available users are: ' + users)

def sendMessage(args):
    argsArray = args.split()
    if len(argsArray) < 2:
        print('Please provide a user and message')
        return
    user = argsArray[1]
    i = 2
    message = []

    while i < len(argsArray) - 1:
        message.append(argsArray[i])

    messageString = ''.join(message)
    Client.sendMessage(user, messageString)

def getMessageHistory(args):
    argsArray = args.split()
    if len(argsArray) != 2:
        print('Please provide a recipient to view history')
        return
    user = argsArray[1]
    message = Client.getMessageHistory(user, 1) # 1 as default iteration
    print(message)

def disconnect():
    Client.disconnect()

def main():
    print('Welcome to Priv, a secure messaging application')
    print('What would you like to do?')

    while True:
        options()
        args = input()

        if args.startswith('1'):
            connect(args)
        elif args.startswith('2'):
            login(args)
        elif args.startswith('3'):
            getUsers()
        elif args.startswith('4'):
            if loggedIn is False:
                print('\tPlease login first')
                continue
            sendMessage(args)
        elif args.startswith('5'):
            if loggedIn is False:
                print('\tPlease login first')
                continue
            getGroups()
        elif args.startswith('6'):
            if loggedIn is False:
                print('\tPlease login first')
                continue
            getMessageHistory(args)
        elif args.startswith('9'):
            disconnect()
        else:
            print('\tInvalid command')

if __name__=="__main__":
    main()