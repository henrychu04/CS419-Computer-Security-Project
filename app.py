from client import client
import json, time, traceback

Client = client()
loggedIn = False
connected = False

def main():
    print('Welcome to Priv, a secure messaging application')
    print('What would you like to do?')

    while True:
        try:
            options()
            args = input('> ')

            if args.startswith('9'):
                disconnect()
                print('Disconnected')
                break

            if not connected:
                if args.startswith('1'):
                    connect()
                else:
                    print('Please connect to the server first')
            else:
                if not loggedIn:
                    if args.startswith('2'):
                        login(args)
                    else:
                        print('Please login first')
                else:
                    if args.startswith('3'):
                        getUsers()
                    elif args.startswith('4'):
                        getGroups()
                    elif args.startswith('5'):
                        sendMessage(args)
                    elif args.startswith('6'):
                        getMessageHistory(args)
                    else:
                        print('\tInvalid command')
        except Exception as e:
            if str(e) == 'timed out':
                print('Request timed out')
            elif str(e) == 'Decryption failed': # To prevent user from seeing where the error originated from in the stack
                print('Decryption failed')
            else:
                traceback.print_exc()

def options():
    print('\n\tEnter "1" to connect to a host')
    print('\tEnter "2 <username> <password>" to login')
    print('\tEnter "3" to view all available recipients')
    print('\tEnter "4" to view all past message recipient')
    print('\tEnter "5 <recipient> <message>" to send a new message to a user')
    print('\tEnter "6 <recipient>" to view message history between you and a recipient')
    print('\tEnter "9" to diconnect and exit\n')

def connect():
    global connected
    
    with open('config.json') as json_file:
        config = json.load(json_file)

    host = config['host']
    port = config['port']

    connected = Client.connect(host, port)

def login(args):
    global loggedIn
    argsArray = args.split()

    if len(argsArray) != 3:
        print('Please provide a username and password')
        return

    loggedIn = Client.login(argsArray[1], argsArray[2])

    if loggedIn:
        print('Successfully logged in')
    else:
        print('Password is incorrect')

def getGroups():
    groups = Client.getGroups()
    print('All past message recipients are:')

    for group in groups:
        print(f'  {group["recipient"]}')

def getUsers():
    users = Client.getAvailableUsers()
    print('Available users are:')

    for user in users:
        print(f'  {user}')

def sendMessage(args):
    argsArray = args.split()

    if len(argsArray) == 2:
        print('Cannot send empty message')
        return
    elif len(argsArray) < 2:
        print('Please provide a user and message')
        return

    user = argsArray[1]
    i = 2
    message = []

    while i < len(argsArray):
        if i < len(argsArray) - 1:
            message.append(argsArray[i] + " ")
        else:
            message.append(argsArray[i])
        i += 1

    messageString = ''.join(message)
    response = Client.sendMessage(user, messageString)

    if response == '200':
        print('Message successfully sent')
    elif response == '403':
        print('Cannot send messages to yourself')
    elif response == '404':
        print('Entered user does not exist')
    elif response == '500':
        print('Error encrypting message - recipient does not have a public key')
    else:
        print('Error sending message')

def getMessageHistory(args):
    argsArray = args.split()

    if len(argsArray) != 2:
        print('Please provide a recipient to view history')
        return

    user = argsArray[1]

    recurseMessageHistory(user, 1)

def recurseMessageHistory(user, iteration):
    response = Client.getMessageHistory(user, iteration)

    if response == 400:
        print('No message history between you and requested recipient')
        return
    elif response == 403:
        print('Cannot view message history with yourself')
        return
    elif response == 404:
        print('Entered user does not exist')
        return
    elif response == 500:
        print('User Private Key missing')
        return

    messages, end = response

    print()

    for message in messages:
        print(f'{time.strftime("  %D %H:%M", time.localtime(message["sentAt"]))} | {message["sentBy"]}: {message["message"]}')

    if end:
        print('End of message history')
    else:
        while True:
            print('-- Type <RET> for more, q to quit --')
            keyInput = input()

            if keyInput == '':
                recurseMessageHistory(user, iteration + 1)
                return
            elif keyInput == 'q':
                return
            else:
                continue

def disconnect():
    if connected:
        Client.disconnect()

if __name__=="__main__":
    main()