"""
test flask_socketio
"""

from flask_socketio import SocketIO
from flask import Flask, render_template, request, abort, redirect, url_for
from flask_login import LoginManager, login_user, current_user, UserMixin, login_required
from usernames import is_safe_username


import time

from collections import defaultdict

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
login = LoginManager(app)  # Login
login.login_view = 'loginform'


import cmd
from ttt import TicTacToe

class Client(cmd.Cmd):
    """ cmd """
    def do_msg(self, inp):
        inp = inp.split(' ')
        clientname = inp.pop(0)
        client = clients[clientname]
        if client:
            msg = f"[{self.username} => {client.username}] {' '.join(inp)}"
            self.send_msg(msg, [client])
            self.stdout.write(msg) # sender recv msg
        else:
            self.stdout.write("user not connected")

    def do_add(self, inp):
        self.stdout.write(f"Adding {'+'.join(inp.split(' '))}={sum(map(int, inp.split(' ')))}")

    def do_ping(self, inp):
        self.stdout.write(str(self.latency/1e9)+'s')

    def do_ttt(self, inp):
        """ /ttt <username> <x> <y> """
        inp = inp.split(' ')
        try:
            clientname = inp.pop(0)
            client = clients[clientname]
            if not client:
                self.send_msg("user not connected", [self])
                return
            x = int(inp.pop(0))
            y = int(inp.pop(0))
            if not (  0 <= x <= 2 and  0 <= x <= 2):
                self.send_msg("wrong position", [self])
                return
        except:
            self.send_msg("wrong entry", [self])

        # init game
        if self.ttt is None or self.ttt[1] != client:
            game = TicTacToe()
            self.ttt = (game, client)
            client.ttt = (game, self)
        else:
            game = self.ttt[0]

        if game.play(x, y):
            self.send_msg("\n" + game.__str__(), [client, self])
            if game.winner is not None:
                self.send_msg(f"{self.username} won", [client, self])
                self.ttt = None
            else:
                self.send_msg(f"[TTT] do /ttt {self.username} <x> <y>", [client])
        else:
            self.send_msg(f"Invalid pos {x} {y} \n" + game.__str__(), [self])


    def default(self, line):
        self.send_msg("command not found: " + line, [self])

    def process(self, inputstr):
        # process input
        try:
            if inputstr[0] == '/': # process cmd
                self.onecmd(inputstr[1:])
                self.flush()
            else:  # send msg broadcast
                self.send_msg(f'[{self.username}] ' + inputstr)
        except:
            pass

        # update user latency
        ping(self.ids[-1])


    def __init__(self, username):
        self.ids = []
        self.id_connected = False
        self.username = username
        # own stream
        super(Client, self).__init__(stdout=self) # use self write & flush
        self.buffered_data = ''
        # ping
        self.latency = 0

        self.ttt = None

    def link(self, socketid):
        assert not socketid in self.ids
        self.ids.append(socketid)
        self.is_connected = True

    def unlink(self, socketid):
        assert socketid in self.ids
        self.ids.remove(socketid)
        self.is_connected = len(self.ids) > 0

    def send(self, req, dstclients=None):
        """ send data to clients """
        print("Send " + str(req) + " to " + str(dstclients))
        if dstclients is None:  # Broadcast
            socketio.emit('data', req)
            return True
        for client in dstclients:
            for id in client.ids:
                socketio.emit('data', req, room=id)
        return True

    def send_msg(self, msg, dstclients=None):
        req = {"type": "msg",
               "user": "",
               "msg": msg}
        self.send(req, dstclients)

    def write(self, data):
        """ IO write """
        self.buffered_data += data

    def flush(self):
        """ IO flush """
        self.send_msg(self.buffered_data, [self])
        self.buffered_data = ''

class Clients:
    """ all connected clients """
    def __init__(self):
        self.connected_dict = {}

    def link(self, username, socketid):
        """ link user => id """
        if username not in self.connected_dict.keys():
            self.connected_dict[username] = Client(username)
        self.connected_dict[username].link(socketid)

    def unlink(self, username, socketid):
        """ unlink user => id """
        self.connected_dict[username].unlink(socketid)
        if not self.connected_dict[username].is_connected:
            self.connected_dict.pop(username)

    def __getitem__(self, key):
        if key in self.connected_dict.keys():
            return self.connected_dict[key]
        return None

    def to_json(self):
        return {user: client.ids
                for user, client in self.connected_dict.items() }

clients = Clients()

@login.user_loader
def user_loader(id):
    return User(id)

class User(UserMixin):
    def __init__(self, username):
        self.id = username

@app.route('/login', methods=['GET', 'POST'])
def loginform():
    if request.method == 'POST':
        print(request.form)
        username = request.form['username']
        # password = request.form['password']
        if username is not None and is_safe_username(username):
            login_user(User(username))
            return redirect(request.args.get('next'))
    return render_template('login.html')

@app.route('/')
@app.route('/index')
@login_required
def index():
    return render_template('index.html') # socketio in it

def send_connected():
    """ send connected {username:[ids]} """
    req = {"type":  "connected",
           "connected": clients.to_json()}
    socketio.emit('data', req)

@socketio.on('connect')
def connect():
    # linq username => socket ID
    print(f'socket connected {current_user.id} => {request.sid}')
    clients.link(current_user.id, request.sid)
    send_connected()

@socketio.on('disconnect')
def disconnect():
    print(f'socket disconnected {current_user.id} => None')
    clients.unlink(current_user.id, request.sid)
    send_connected()

@socketio.on('my event')
def handle_my_custom_event(data, methods=('GET', 'POST')):
    print('my event: ' + str(data))
    clients[current_user.id].process(data["rawdata"])

def ping(id):
    socketio.emit('my_ping', str(time.time_ns()), room=id)

@socketio.on('my_pong')
def handle_pong(data, method=('GET', 'POST')):
    clients[current_user.id].latency = time.time_ns() - int(data["rawdata"])

if __name__ == '__main__':
    socketio.run(app, debug=True)
