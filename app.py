"""
test flask_socketio
"""

from flask_socketio import SocketIO
from flask import Flask, render_template, request, abort, redirect, url_for
from flask_login import LoginManager, login_user, current_user, UserMixin, login_required

from collections import defaultdict

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
login = LoginManager(app)  # Login
login.login_view = 'loginform'


import cmd

class Client(cmd.Cmd):
    """ cmd """
    def do_msg(self, inp):
        inp = inp.split(' ')
        clientname = inp.pop(0)
        print(clientname)
        client = clients[clientname]
        if client:
            msg = f"[{self.username} => {client.username}] {' '.join(inp)}"
            self.send_msg(msg, [client])
            return msg  # sender recv msg
        else:
            return "user not connected"

    def do_add(self, inp):
        return f"Adding {'+'.join(inp.split(' '))}={sum(map(int, inp.split(' ')))}"

    def do_help(self, inp):
        return "no help"

    def default(self, line):
        return "command not found: " + line

    def process(self, inputstr):
        try:
            if inputstr[0] == '/': # process cmd
                self.send_msg(self.onecmd(inputstr[1:]), [self])
            else:  # send msg broadcast
                self.send_msg(f'[{self.username}] ' + inputstr)
        except:
            return ''

    def __init__(self, username):
        self.ids = []
        self.id_connected = False
        self.username = username

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
        return {user: client.ids for user, client in self.connected_dict.items() }

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
        if username is not None:
            login_user(User(username))
            return redirect(request.args.get('next'))
    return render_template('login.html')

@app.route('/')
@app.route('/index')
@login_required
def index():
    return render_template('index.html') # socketio in it

def send_connected(data):
    """ send connected {username:[ids]} """
    req = {"type":  "connected",
           "connected": data}
    socketio.emit('data', req)

@socketio.on('connect')
def connect():
    # linq username => socket ID
    print(f'socket connected {current_user.id} => {request.sid}')
    clients.link(current_user.id, request.sid)
    # send_msg("@console", f" + {current_user.id}")
    send_connected(clients.to_json())

@socketio.on('disconnect')
def disconnect():
    print(f'socket disconnected {current_user.id} => None')
    clients.unlink(current_user.id, request.sid)
    # send_msg("@console", f" - {current_user.id}")
    send_connected(clients.to_json())

@socketio.on('my event')
def handle_my_custom_event(data, methods=('GET', 'POST')):
    print('my event: ' + str(data))
    clients[current_user.id].process(data["rawdata"])
    # send_msg(str(current_user.id), ": " +str(data["rawdata"]))


if __name__ == '__main__':
    socketio.run(app, debug=True)
