"""
test flask_socketio
"""

from flask_socketio import SocketIO
from flask import Flask, render_template, request, abort, redirect, url_for
from flask_login import LoginManager, login_user, current_user, UserMixin, login_required

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
login = LoginManager(app)  # Login
login.login_view = 'loginform'

connected_dict = {}

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
    req = {"type":  "connected",
           "connected": data}
    socketio.emit('data', req)

def send_msg(user, msg):
    req = {"type": "msg",
           "user": user,
           "msg": msg}
    socketio.emit('data', req)

@socketio.on('connect')
def connect():
    # emit('welcome', {'username': current_user.id})
    connected_dict[current_user.id] = request.sid # ling username => socket ID
    send_msg("@console", f" + {current_user.id}")
    send_connected(connected_dict)
    print(f'socket connected {current_user.id} => {request.sid}')

@socketio.on('disconnect')
def disconnect():
    connected_dict[current_user.id] = None
    send_msg("@console", f" - {current_user.id}")
    send_connected(connected_dict)
    print(f'socket disconnected {current_user.id} => None')

@socketio.on('my event')
def handle_my_custom_event(data, methods=['GET', 'POST']):
    print('my event: ' + str(data))
    send_msg(str(current_user.id), str(data))


if __name__ == '__main__':
    socketio.run(app, debug=True)
