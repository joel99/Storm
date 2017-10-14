from flask import Flask, render_template, request, session, url_for, redirect
from flask_socketio import SocketIO, join_room, leave_room, send, emit

import os, json

app = Flask(__name__)
app.secret_key = "secrets"
socketio = SocketIO(app)

# Site Navigation

# Lobby
@app.route("/")
def root():
    return render_template('index.html')

# Rooms
@app.route("/room/<roomName>")
def room(roomName):
    return render_template('room.html')

# Misc
@socketio.on('verify_name')
def verify_name():
    if 'username' in session and session['username'] in allUsers.keys():
        socketio.emit('confirm_new_user', {'name': data['name']}, room=request.sid);
    else:
        print session['username']
        print allUsers.keys()
    
    
# Room events
allRooms = {}
allUsers = {}
userRooms = {}

@app.route("/loadLobby/", methods=["POST"])
def loadLobby():
    return json.dumps({"roomList": allRooms.keys()})

#hack
@app.route("/login/", methods=["POST"])
def loginWithName():
    session["username"] = request.form["username"]     
    return json.dumps({"success":True})

@socketio.on('new_room')
def new_room(data):
    #assume valid user for now
    if data['name'] in allRooms.keys():
        print "Room rejected, already exists"
        socketio.emit('fail_new_room', room=request.sid);
    else:
        print "New room created with name " + data["name"]
        roomDict = {
            "host" : session["username"],
            "active" : []
        }
        allRooms[data['name']] = roomDict
        #callback=ack - do this eventually
        userRooms[session['username']] = data['name']
        print "from room creation ...\n\n"
        print userRooms.keys()
        join_room(data['name'])
        socketio.emit('confirm_new_room', data, room=request.sid)
        socketio.emit('registered_room', json.dumps({"name": data['name']}))
    
@socketio.on('start_room')
def start_room(data):
    return

@socketio.on('end_room') #on last dc
def end_room(data): #passes room name
    roomName = data["name"]
    if roomName in allRooms:
        allRooms.remove(roomName)
        socketio.emit('delete_room', json.dumps(data))
    else:
        print "That's not good"
    return


@socketio.on('new_message')
def new_message(data):
    data["name"] = session["username"]
    print "\n\n\n neww messageee"
    print session["username"]
    print userRooms[session["username"]]
    socketio.emit('chat_message', data, room=userRooms[session["username"]])
    
@socketio.on('new_user')
def new_user(data):
    if data['name'] in allUsers.values():
        socketio.emit('fail_new_user', room=request.sid);
    else:
        username = data['name']
        allUsers[username] = request.sid        
        session["username"] = username 
        socketio.emit('confirm_new_user', {'name': data['name']}, room=request.sid);

        
@socketio.on('user_disconnect')
def user_disconnect(data):
    socketio.emit('server_message', {
        'message': data['name'] + ' left'
    })

    
def getUser(uid):
    return allUsers[str(uid)]

    
if __name__ == "__main__":
    app.debug = True
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host = '0.0.0.0', port = port)


