from flask import Flask, render_template, request, session, url_for, redirect
from flask_socketio import SocketIO, join_room, leave_room, send, emit
from random import randrange
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
    def __init__(self, cargo=None, parent=None, nextNodes=[]):
        self.parent = parent
        self.data = cargo 
        self.adj = nextNodes
    def __str__(self): 
        return str(self.data + " | Neighbors : " + self.adj)
    def __dict__(self):
        adjDicts = []
        for n in self.adj:
            adjDicts.append(dict(n))
        ret = {
            'next': adjDicts,
            'data': self.data     
        }
        return ret
    def randomIndex(self):
        return randrange(0,len(self.adj))
      


# Globals ============================================
# Schema: dictionary: keys are room names, entries are dictionaries
# active: [<activeUsernames>]
# status: [<phase>]
# host  : [<hostUsername>]
# threads : [<StormData>]
# threads contains "root": root Node - model : pass indices in list
# client holds all data
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
    roomlistPre = list(filter(lambda key: allRooms[key]["status"] == 0, allRooms.keys()))
    roomList = [{'name': key} for key in roomlistPre]
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
        allRooms['lobby']['active'].append(username)
        userRooms[username] = 'lobby'

#clear traces
@socketio.on('user_disconnect')
def user_disconnect(data):
    username = data['name']
    print "User disconnected"
    del allUsers[username]
    leaveRoom(userRooms[username])
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
        #pop from lobby
        allRooms['lobby']['active'].pop(session['username'])
        userRooms[session['username']] = data['name']
        join_room(data['name'])
        socketio.emit('confirm_new_room', data, room=request.sid)
        socketio.emit('registered_room', json.dumps({"name": data['name']}))

        
@socketio.on('init_room')
def init_room():
    print "Testing \n\n\n"
    host = getCurRoom()['host']
    join_room(userRooms[session["username"]])
    state = getCurRoom()["status"]
    if state == 0:
        socketio.emit('pre-storm-init', room=request.sid)
        if session["username"] == host:
            socketio.emit('release-phase-button', room=request.sid)
        print "pre-storm room init"
    elif state == 1:
        data = getCurRoom()["threads"] #pass cur game data
        #pass root and data
        socketio.emit('storm-init', dict(data), room=request.sid)
        print "storm room init"
    else:
        socketio.emit('post-storm-init', room=request.sid)
        print "post-storm room init"        

@socketio.on('start_storm')
def start_storm(data):
    if data['root'] == "":
        root = "Ideate!"
    else:
        root = data['root']
    print root
    print "debug\n\n"
    #track with nodes
    getCurRoom()["threads"]["root"] = Node(root)
    getCurRoom()["status"] = 1
    socketio.emit('lock_room', {'name' : userRooms[session['username']]})
    #room = getCurRoom or something
    socketio.emit('storm-init', {'name': root, "path":[]}, room = userRooms[session['username']])

@socketio.on('end_storm')
def end_storm():
    getCurRoom()['status'] = 2
    socketio.emit('post-storm-init', room = userRooms[session['username']])
    print 'end storm'

@socketio.on('close_storm')
def close_storm():
    print 'close_storm'
    #eject all of those folks
    socketio.emit('eject-to-lobby', room = userRooms[session['username']])
    #get list of users
    roomName = userRooms[session['username']]
    for player in allRooms[roomName]['active']:
        userRooms[player] = 'lobby'
    allRooms.pop(roomName, None)

# Phase listeners ----------------------------------------------
@socketio.on('new_message')
def new_message(data):
    data["name"] = session["username"]
    print userRooms
    socketio.emit('chat-message', data, room=userRooms[session["username"]])
    
# Helpers ------------------------------------------------------
def getCurRoom():
    return allRooms[userRooms[session['username']]]

    
if __name__ == "__main__":
    app.debug = True
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host = '0.0.0.0', port = port)
