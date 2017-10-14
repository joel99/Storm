$(document).ready(function () {
  const socket = io();

  //onload
  socket.emit('init_room');
  $('#prompt-container').toggle();
  //Button listeners --------------------------------------
  
  //Pre-storm
  $('#start-button').click(function () {    
    console.log("button pressed");
    const rootText = $('#storm-root-text').val();
    let rootDict = {'root' : rootText ? rootText : ""};
    socket.emit('start_storm', rootDict);
    return false;
  });
  
  $('#chat-form').click(function () {
    var message = $('#chat-text').val().trim();

    if (message.length > 0) {
      socket.emit('new_message', {
        message: message
      });
    }

    $('#chat-text').val('');
    
    return false;
  });

  //Socket listeners ---------------------------------------
  
  socket.on('release-start-button', function (data) {
    $('#start-button').toggleClass('disabled');
  });
  
  socket.on('chat_message', function (data) {
    append(data['name'] + ': ' + data['message']);
  });

  socket.on('server_message', function (data) {
    append('[SERVER] ' + data['message']);
  });

  socket.on('start_storm_all', function (data) {
    console.log("Game begins!");
    $('#chat-container').toggle();
    $('#prompt-container').toggle();    
  });
	    
  
  //Helpers ------------------------------------------------
  
  var append = function (string) {
    $('#chat-log').append(string + '\n');
    $('#chat-log').scrollTop($('#chat-log')[0].scrollHeight);
  };
  
  $(window).bind('beforeunload', function () {
    socket. emit('user_disconnect', {
      name: name
    });
  });

  
});
