$(document).ready(function() {
  const socket = io();

  let activeRoomName = "";

  //work
  socket.emit('verify_name');

  let name = null;
  
  $('#name-text').focus();
    
  $('#name-form').submit(function () {
    name = $('#name-text').val();

    if (name.length > 0) {
      socket.emit('new_user', {
        name: name
      });
    }  
			 
    return false;
  });
  
  socket.on('fail_new_user', function () {
    $('#name-form-desc').html("Usertag in use, please select another:");
  });
  
  socket.on('confirm_new_user', function (data) {
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

  $('#create-room').submit(function() {
    let name = $('#room-name').val();
    //use ajax for callbacks...    
    if (name.length > 0) {
      socket.emit('new_room', {
	name: name
      });
    }
    return false;
  });

  
  socket.on('fail_new_room', function() {
    $('#room-form-desc').html("Room name in use, please select another:");
  });

  socket.on('confirm_new_room', function(data) {
    window.location = "/room/" + data['name'];
  });
		  
  //load lobby
  
  $.ajax({
    url: "/loadLobby/",
    type: "POST",
    data: {},
    datatype: "json",
    success: function(response) {
      let roomList = JSON.parse(response)["roomList"];
      for (let i = 0; i < roomList.length; i++) {
	appendLobby(roomList[i]);
      }
      if (roomList.length != 0) {
	activeRoomName = roomList[0]["name"];
	$("#roomID"+activeRoomName).toggleClass("active");
      }
    },
    error: function(data) {
      console.log("boohoo");
    }
  });
      
  
  $('#joinRoomButton').click(function() {
    if (activeRoomName != "") {//make sure it's valid with ajax?
      window.location = "/room/" + activeRoomName;
    }
  });  
  
  
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

  var deleteLobby = function (data) {
    $("#roomID"+data["name"]).remove();
  }
  
  socket.on('registered_room', function (data) {
    appendLobby(JSON.parse(data));
  });

  socket.on('delete_room', function (data) {
    deleteLobby(JSON.parse(data));
  });
  
		  
		  
});

