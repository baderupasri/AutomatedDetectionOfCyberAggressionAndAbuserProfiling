var socket = io();
socket.on("connect", function(){

socket.emit("join_private",{
receiver: receiver
});

});
function sendMessage(){

let input = document.getElementById("messageInput");
let message = input.value;

if(message.trim() !== ""){

socket.emit("private_message",{
receiver:receiver,
message: message,
});

input.value="";
}

}

socket.on("receive_message", function(data){

let chatBox = document.getElementById("chatBox");

let div = document.createElement("div");

if(data.type === "blocked"){

div.classList.add("blocked-message");

}else{

div.classList.add("message");

if(data.user === username){
div.classList.add("sent");
}else{
div.classList.add("received");
}

}

div.innerText = data.message;

chatBox.appendChild(div);

chatBox.scrollTop = chatBox.scrollHeight;

});

// Warning for sender
socket.on("sender_warning", function(data){

showNotification(data.msg,"warning");

});

// Alert for receiver
socket.on("receiver_alert", function(data){

showNotification(data.msg,"alert");

});
socket.on("receiver_offline", function(data){

showNotification(data.msg,"alert");

});
function showNotification(message,type){

let box = document.getElementById("notificationBox");

let div = document.createElement("div");

div.classList.add("notification");

if(type === "warning"){
div.classList.add("warning");
}

if(type === "alert"){
div.classList.add("alert");
}

div.innerText = message;

box.appendChild(div);

setTimeout(()=>{
div.remove();
},4000);

}