# Priv

A secure cli messaging application using RSA encryption to send and receive messages

## Installation

```bash
pip install -r requirements.txt
```

## Usage

In one terminal, run the command:

```bash
python3 server.py
```

In another terminal, run the command:

```bash
python3 app.py
```

Follow the on screen instructions to send, receive, and view messages.

The app supports sending messages between multiple clients in multiple terminals. If you want to communicate between multiple computers, change the host IP address in `config.json` on each client computer to the server computer's local IP address and run the `app.py` file normally.

`logins.txt` contains sample usernames and passwords with preset data and messages to test out the application.