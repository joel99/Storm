$(document).ready(function () {
  const socket = io();

  //onload
  socket.emit('init_room');
  
  //Button listeners --------------------------------------

  $('#lobby-button').click(function() {
    socket.emit('lobby_exit');
    window.location = "/";
  });
  

  //Socket listeners ---------------------------------------

  //Initialization listeners
  socket.on('pre-storm-init', function () {
    $('#prompt-container').toggle(false);
    $('#storm-res-container').toggle(false);
    $('#chat-container').toggle(true);

    $('#phase-button').html("Start Storm");
    $('#phase-button').click(phaseFunction(0));

    //Handle state changes
    
    
    //Handle visuals
    

    //Handle functions
    
    $('#chat-button').click(function () {
      var message = $('#chat-text').val().trim();

      if (message.length > 0) {
	socket.emit('new_message', {
          message: message
	});
      }
      $('#chat-text').val('');
      
      return false;
    });
    
  });

  socket.on('storm-init', function (data) {
    $('#chat-container').toggle(false);
    $('#storm-res-container').toggle(false);
    $('#prompt-container').toggle(true);
    $('#phase-button').html('End Storm');
    $('#phase-button').click(phaseFunction(1));

    showCard(data);
    console.log("storm inited");

    //Handle state changes
    
    
    //Handle visuals


    //Handle functions
    
    $('#scramble-storm').click(function(e){
      return false;
      //cards displayed show all stacked storm cards
      //send a request emit with data to host with data
      //replaces current with entered data
    });
    $('#submit-storm-idea').click(function(e) {
      return false;
    });
  });

  socket.on('post-storm-init', function (data) {
    $('#chat-container').toggle(false);
    $('#prompt-container').toggle(false);
    $('#storm-res-container').toggle(true);

    $('#phase-button').html('Close Storm');    
    $('#phase-button').click(phaseFunction(2));

    //Handle state changes
    
    
    //Handle visuals


    //Handle functions
    
  });

  socket.on('eject-to-lobby', function (data) {
    window.location = "/";
  });
  
  // Communication Listeners (Core) ------------------

  // Pre-storm : chat
  socket.on('chat-message', function (data) {
    console.log('received message');
    append(data['name'] + ': ' + data['message']);
  });

  socket.on('server-message', function (data) {
    append('[SERVER] ' + data['message']);
  });
  
  
  // Visual and meta Listeners -----------------------
  
  socket.on('release-phase-button', function (data) {
    $('#phase-button').toggleClass('disabled');
    console.log("nice, phase relased!");
  });
  
	    
  var showCard = function(data) {
    $('#prompt-text').html(data['name']);
  }
  
  // Misc --------------------------------------------------

  let phaseFunction = function (state) {
    switch (state) {
    case 0: //start-storm-button
      return function() {
	const rootText = $('#storm-root-text').val();
	let rootDict = {'root' : rootText ? rootText : ""};
	console.log(rootDict);
	socket.emit('start_storm', rootDict);
	return false;
      }
      break;
    case 1: //end-storm-button
      return function() {
	socket.emit('end_storm');
      }
      break;
    case 2: //close-storm-button (end game)
      return function() {
	socket.emit('close_storm');
      }
      break;
    }
  }  
  
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
