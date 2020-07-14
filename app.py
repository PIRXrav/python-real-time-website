"""
test flask_socketio
"""

from flask_socketio import SocketIO
from flask import Flask, render_template, request

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('index.html') # socketio in it

connected = []

def send_connected():
    req = {"type":  "connected",
           "connected": connected}
    socketio.emit('data', req, callback=lambda _: print("DONE"))

def send_msg(user, msg):
    req = {"type": "msg",
           "user": user,
           "msg": msg}
    socketio.emit('data', req, callback=lambda _: print("DONE"))

@socketio.on('connect')
def connect():
    connected.append(request.sid)
    send_connected()
    print('Client connected')

@socketio.on('disconnect')
def disconnect():
    connected.remove(request.sid)
    send_connected()
    print('Client disconnected')

@socketio.on('my event')
def handle_my_custom_event(json, methods=['GET', 'POST']):
    print('my event: ' + str(json))
    send_msg(request.sid, str(json))


if __name__ == '__main__':
    socketio.run(app, debug=False)
