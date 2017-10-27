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
            print 'room registered'
            print userRooms
            if session['username'] not in allRooms[roomName]['active']:
                allRooms[roomName]['active'].append(session['username'])
            return render_template('room.html', roomTitle = roomName)
    return redirect(url_for('root'))

@app.errorhandler(404)
def page_not_found(e):
    return redirect(url_for('root'))


# Node class...
class Node: 
    def __init__(self, cargo=None, parent=None):
        self.parent = parent
        self.data = cargo 
        self.adj = []
    def __str__(self): 
        return str("Node " + self.data + " | Neighbors : mia")
    def toDict(self):
        adjDicts = [n.toDict() for n in self.adj]
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
allRooms = {'lobby': {'active':[], 'status': -1}}
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
        userRooms[session['username']] = 'lobby'  
        if session['username'] not in allRooms['lobby']['active']:
            allRooms['lobby']['active'].append(session['username'])
        allUsers[session['username']] = request.sid #refresh it in case new one
        socketio.emit('dismiss-prompt', {'name': session['username']});
        join_room('lobby')
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
    username = session['username']
    print "User disconnected"
    #put a timer on.
    """
    del allUsers[username]
    leaveRoom(userRooms[username])
    if userRooms[username] in allRooms:
        allRooms[userRooms[username]]["active"].remove(username)
    del userRooms[username]
    """
    
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
        allRooms['lobby']['active'].remove(session['username'])
        userRooms[session['username']] = data['name']        
        leave_room('lobby')
        socketio.emit('confirm_new_room', data, room=request.sid)
        socketio.emit('registered_room', json.dumps({"name": data['name']}))
        print 'new room finished making, now userRooms is '

        
@socketio.on('init_room')
def init_room():
    print "Testing \n\n\n"
    host = getCurRoom()['host']
    join_room(userRooms[session["username"]])
    state = getCurRoom()["status"]
    if state == 0:
        print "STATE = 0"
        socketio.emit('pre-storm-init', room=request.sid)
        if session["username"] == host:
            socketio.emit('release-phase-button', room=request.sid)
        print "pre-storm room init"
    elif state == 1:
        data = getCurRoom()['threads'].toDict() #pass cur game data
        print "passing game data"
        print data
        #pass root and data
        socketio.emit('storm-init', data, room=request.sid)
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
    getCurRoom()["threads"] = Node(root)
    getCurRoom()["status"] = 1
    socketio.emit('lock_room', {'name' : userRooms[session['username']]})
    #room = getCurRoom or something
    storm_data = getCurRoom()['threads'].toDict()
    socketio.emit('storm-init', storm_data, room = userRooms[session['username']])

@socketio.on('end_storm')
def end_storm():
    getCurRoom()['status'] = 2
    socketio.emit('post-storm-init', room = userRooms[session['username']])
    print 'end storm'

@socketio.on('close_storm')
def close_storm():
    print 'close_storm'
    #eject all of those folks
    allRooms.pop(userRooms[session['username']], None)
    socketio.emit('eject-to-lobby', room = userRooms[session['username']])
    #userRooms taken care of on lobby load

    
@socketio.on('lobby_exit')
def lobby_exit():
    print 'lobby_exit'
    roomName = userRooms[session['username']]
    userRooms[session['username']] = 'lobby'
    allRooms[roomName]['active'].remove(session['username'])
    leave_room(roomName)
    
# Phase listeners ----------------------------------------------
@socketio.on('new_message')
def new_message(data):
    data["name"] = session["username"]
    print 'hello\n\n'
    print userRooms[session['username']]
    socketio.emit('chat-message', data, room=userRooms[session["username"]])

@socketio.on('new_storm_idea')
def new_storm_idea(data):
    #put into threads
    node = getCurRoom()['threads']
    route = data['route']
    newIdea = data['message']
    #traverse to node
    newNode = Node(newIdea)
    for i in range(len(route)):
        node = node.adj[route[i]]
    node.adj.append(newNode)
    
    #pass back
    socketio.emit('server-storm-idea', data, room=userRooms[session["username"]])
    data['newIndex'] = len(node.adj) - 1
    socketio.emit('swap-to-new-idea', data, room=request.sid)
    
# Helpers ------------------------------------------------------
def getCurRoom():
    return allRooms[userRooms[session['username']]]

    
if __name__ == "__main__":
    app.debug = True
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host = '0.0.0.0', port = port)
