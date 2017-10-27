$(document).ready(function () {
  const socket = io();

  var globalThreads = {}; //schema: {'data': <text>, 'next': [dict array]}
  var globalRoute = []; //global route for global threads woo
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
    
    globalRoute = [];
    globalThreads = data; //sounds like a good place to use promises
    showCard(data);
    console.log("storm inited");
    console.log(globalThreads);
    console.log(globalRoute);
    console.log(globalThreads);

    //Handle state changes
    
    
    //Handle visuals


    //Handle functions
    
    $('#scramble-storm').click(function(e){
      e.preventDefault();
      console.log("scrambling"); //gets you another thing on the same branch
      //travel down global route
      curLevel = getRoute(globalRoute.slice(0, globalRoute.length - 1));
      //now get a random one on global route
      if (globalRoute.length == 0) {//edge case
	showCard(globalThreads);
      } else {
	newScrambleIndex = 0;
	oldIndex = globalRoute[globalRoute.length - 1];
	if (curLevel['next'].length > 1) { //try to ensure scrambling (guarantee not the same as before)
	  newScrambleIndex = getRandomInt(0, curLevel['next'].length - 1);
	  if (newScrambleIndex >= oldIndex) newScrambleIndex += 1;
	  globalRoute[globalRoute.length - 1] = newScrambleIndex;
	}
	
	console.log(curLevel);
	showCard(curLevel['next'][newScrambleIndex]);
      }
      
      return false;
      //cards displayed show all stacked storm cards
      //send a request emit with data to host with data
      //replaces current with entered data
    });
    $('#submit-storm-idea').click(function(e) {
      e.preventDefault();
      var message = $('#storm-text-input').val().trim();

      if (message.length > 0) {
	console.log(globalRoute);
	console.log('submitting new storm idea');
	socket.emit('new_storm_idea', {
          'message': message,
	  'route': globalRoute
	});
      }
      $('#storm-text-input').val('');      
      //passes to server, server returns all
      return false;
    });
    $('#revert-up').click(function(e) {
      e.preventDefault();
      if (globalRoute.length === 0) {
	showStatus("On root level, cannot revert.");
      } else {
	globalRoute.pop();
	showGlobalRoute();
      }      
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

  socket.on('server-storm-idea', function (data) {
    //data schema: data, route
    //update global threads
    console.log('getting storm idea from server');
    console.log(getRoute(data['route']));
    getRoute(data['route'])['next'].push({'data':data['message'], 'next':[]});    
    console.log('received ' + data['message']);
  });

  socket.on('swap-to-new-idea', function (data) {
    //set route basically - unnecessary... just swap in client (circumvent validation)
    console.log('old route');
    console.log(globalRoute);
    console.log(globalThreads);
    console.log('swapping to new route');
    globalRoute.push(data['newIndex']);
    console.log(globalRoute);
    showGlobalRoute();
  });
  
  // Visual and meta Listeners -----------------------
  
  socket.on('release-phase-button', function (data) {
    $('#phase-button').toggleClass('disabled');
    console.log("nice, phase relased!");
  });
  
	    
  var showCard = function(data) {
    $('#prompt-text').html(data['data']);
    if (globalRoute.length != 0) {
      curLevel = getRoute(globalRoute.slice(0, globalRoute.length - 1));    
      showSiblingCount(curLevel['next'].length - 1);
    } else {
      showSiblingCount(0);
    }
  }

  //arr - gets dict at end of route
  var getRoute = function(route) {
    console.log('route prompt');
    console.log(route);
    let curLevel = globalThreads;
    for (let i = 0; i < route.length; i++) {
      curLevel = curLevel['next'][route[i]];
    }
    console.log('getting route');
    console.log(curLevel);
    return curLevel;
  }
  
  var showGlobalRoute = function() {
    showCard(getRoute(globalRoute));
  }

  var showStatus = function(text) {
    $('#storm-status-text').html(text);
  }

  var showSiblingCount = function(count) {
    $('#sibling-count').html(count);
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

  function getRandomInt(min, max) {
    min = Math.ceil(min);
    max = Math.floor(max);
    return Math.floor(Math.random() * (max - min)) + min; //The maximum is exclusive and the minimum is inclusive
  }
  
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
