$(document).ready(function() {
  
  const socket = io();

  let activeRoomName = "";

  //onload
  socket.emit('init_lobby');

  // Button Handlers ----------------------------------------------
  
  $('#create-room').click(function() {
    let name = $('#room-name').val();

    if (name.trim().length > 0 ) {
      console.log("Sending new room emit");
      socket.emit('new_room', {
	'name': name
      });
    }
    return false;
  });

  $('#joinRoomButton').click(function() {
    if (activeRoomName != "") {//make sure it's valid with ajax?
      window.location = "/room/" + activeRoomName;
    }
  });  
  

  // Socket Events ---------------------------------------------------

  socket.on('load-rooms-menu', function(response) {
    let roomList = JSON.parse(response)["roomList"];
    for (let i = 0; i < roomList.length; i++) {
      appendLobby(roomList[i]);
    }
    if (roomList.length != 0) {
      activeRoomName = roomList[0]["name"];
      $("#roomID"+activeRoomName).toggleClass("active");
    }
  });
  
  socket.on('prompt-username', function() {
    //Prompt for name
    let name = null;
    $('#name-text').focus();
    
    $('#name-form').submit(function () {
      name = $('#name-text').val();
      
      if (name.length > 0) {
	socket.emit('try_new_user', {
          name: name
	});
      }  
      
      return false;
    });    
  });

  socket.on('dismiss-prompt', function(data) {
    $('#name-container').fadeOut(500);
    $('#lobby-welcome').html("Welcome " + data['name'] + "!");    
  });
  
  socket.on('fail_new_user', function () {
    console.log("Failed to register");
    $('#name-form-desc').html("Usertag in use, please select another:");
  });
  
  socket.on('confirm_new_user', function (data) {
    console.log("Confirmed register");
    $('#name-form-desc').html("Welcome...");
    $('#name-container').fadeOut(500);
    $('#lobby-welcome').html("Welcome " + data['name'] + "!");
    $.ajax({
      url: "/login/",
      type: "POST",
      data: {"username" : data['name']},
      datatype: "json",      
    });
    //$('#chat-text').focus();
  });
  
  
  socket.on('fail_new_room', function() {
    $('#room-form-desc').html("Room name in use, please select another:");
  });

  socket.on('confirm_new_room', function(data) {
    window.location = "/room/" + data['name'];
  });  

  socket.on('lock_room', function (data) {
    deleteLobby(data['name']);
  });
  
  // Helper functions -------------------------------------
  // Appends room entry to lobby menu
  var appendLobby = function (newRoom) {
    var $div = $("<div>", {class:"list-group-item", id:"roomID"+newRoom["name"]});
    $div.html(newRoom["name"]);
    $div.click(function(){
      $("#roomID"+activeRoomName).toggleClass("active");
      activeRoomName = newRoom["name"];
      $("#roomID"+activeRoomName).toggleClass("active");
    });
    $("#lobby-list").append($div);
  };
  
  // Removes room entry from lobby menu
  var deleteLobby = function (roomName) {
    $("#roomID" + roomName).remove();
  }
  
		  
});

