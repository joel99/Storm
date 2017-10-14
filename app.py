from flask import Flask, render_template, request, session, url_for, redirect
from flask_socketio import SocketIO, join_room, leave_room, send, emit

import os, json

app = Flask(__name__)
app.secret_key = "secrets"
socketio = SocketIO(app)

# Site Navigation / Flask Routes =====================

# Lobby
@app.route("/")
def root():
    return render_template('index.html')

# Rooms
@app.route("/room/<roomName>")
def room(roomName):

    if 'username' in session and session['username'] in allUsers.keys() and roomName in allRooms.keys():
        print roomName
        print allRooms
        if allRooms[roomName]['status'] == 0 or session['username'] in allRooms[roomName]['active']:
            userRooms[session['username']] = roomName
            if session['username'] not in allRooms[roomName]['active']:
                allRooms[roomName]['active'].append(session['username'])
            return render_template('room.html', roomTitle = roomName)
    return redirect(url_for('root'))

@app.errorhandler(404)
def page_not_found(e):
    return redirect(url_for('root'))


# Node class...
class Node: 
  def __init__(self, cargo=None, parent=None, next=[]):
    self.parent = parent
    self.data = cargo 
    self.adj = next   
  def __str__(self): 
    return str(self.data + " | Neighbors : " + self.adj)


# Globals ============================================
# Schema: dictionary: keys are room names, entries are dictionaries
# active: [<activeUsernames>]
# status: [<phase>]
# host  : [<hostUsername>]
allRooms = {}
# Schema: dictionary: keys are usernames, entries are sid
allUsers = {}
# Schema: dictionary: keys are usernames, entries are currently connected room names
userRooms = {}

        
# Lobby ===============================================
#hack for session
@app.route("/login/", methods=["POST"])
def loginWithName():
    session["username"] = request.form["username"]     
    return json.dumps({"success":True})

@socketio.on('init_lobby')
def init_lobby():
    roomList = [{"name" : key} for key in allRooms.keys()]
    socketio.emit('load-rooms-menu', json.dumps({"roomList": roomList}));    
    if 'username' in session and session['username'] in allUsers.keys():
        allUsers[session['username']] = request.sid #refresh it in case new one
        socketio.emit('dismiss-prompt', {'name': session['username']});
    else:
        print "prompting username \n\n"
        socketio.emit('prompt-username');


# Users and Rooms ===========================================
@socketio.on('try_new_user')
def new_user(data):
    if data['name'] in allUsers.keys():        
        socketio.emit('fail_new_user', room=request.sid);
    else:
        username = data['name']
        allUsers[username] = request.sid        
        session["username"] = username 
        socketio.emit('confirm_new_user', {'name': data['name']}, room=request.sid);

#clear traces
@socketio.on('user_disconnect')
def user_disconnect(data):
    username = data['name']
    print "User disconnected"
    del allUsers[username]
    if userRooms[username] in allRooms:
        allRooms[userRooms[username]]["active"].remove(username)
    del userRooms[username]

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
            "active" : [],
            "status" : 0,
            "threads" : {} #for storing game data
        }
        allRooms[data['name']] = roomDict
        userRooms[session['username']] = data['name']
        join_room(data['name'])
        socketio.emit('confirm_new_room', data, room=request.sid)
        socketio.emit('registered_room', json.dumps({"name": data['name']}))

        
@socketio.on('init_room')
def init_room():
    print "Testing \n\n\n"
    host = getCurRoom()['host']
    if session["username"] == host:
        socketio.emit('release-start-button', room=request.sid)

        
@socketio.on('new_message')
def new_message(data):
    data["name"] = session["username"]
    socketio.emit('chat_message', data)#, room=userRooms[session["username"]])

@socketio.on('start_storm')
def start_storm(data):
    if data['root'] == "":
        root = "Ideate!"
    else:
        root = data['root']
    #track with nodes
    getCurRoom()["threads"]["root"] = Node(root)
    getCurRoom()["status"] = 1
    socketio.emit('lock_room', {'name' : userRooms[session['username']]})
    #room = getCurRoom or something
    socketio.emit('start_storm_all', {'name': root, "path":[]})


# Helpers ------------------------------------------------------
def getCurRoom():
    return allRooms[userRooms[session['username']]]

    
if __name__ == "__main__":
    app.debug = True
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host = '0.0.0.0', port = port)
