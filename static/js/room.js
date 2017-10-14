$(document).ready(function () {
  const socket = io();
  
  
  $('#chat-form').submit(function () {
    var message = $('#chat-text').val();

    if (message.length > 0) {
      socket.emit('new_message', {
        message: message
      });
    }

    $('#chat-text').val('');
    
    return false;
  });

  var append = function (string) {
    $('#chat-log').append(string + '\n');
    $('#chat-log').scrollTop($('#chat-log')[0].scrollHeight);
  };
  
  socket.on('chat_message', function (data) {
    console.log('liberty');
    append(data['name'] + ': ' + data['message']);
  });

  socket.on('server_message', function (data) {
    append('[SERVER] ' + data['message']);
  });

  $(window).bind('beforeunload', function () {
    socket. emit('user_disconnect', {
      name: name
    });
  });
});
