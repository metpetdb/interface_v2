
// =========================================
//Image overlay functions

function overlay_on(e){
  overlay.style.display = "flex";
  currentImage = e;
  setCurrentImage(currentImage);
}


function setCurrentImage(currentImage){
  document.getElementById("displayImage").src = images[currentImage]["url"];
  document.getElementById("imageTypeText").innerHTML = images[currentImage]["type"];
}

function nextImage(){
  currentImage = (currentImage+1) % images.length;
  setCurrentImage(currentImage);
}

function previousImage(){
  currentImage = currentImage - 1;
  if (currentImage < 0){
    currentImage = images.length-1;
  }
  setCurrentImage(currentImage);
}


function overlay_off(){
  overlay.style.display = "none";
}


window.onclick = function(event)
{

  if (event.target == overlay){
    overlay_off();
  }
}

window.onkeydown = keyDownHandler;

function keyDownHandler(e){
    var keycode = e.keyCode;
    if (keycode == 27) overlay_off();
    else if (overlay.style.display != "none" && keycode == 37)  previousImage();
    else if (overlay.style.display != "none" && keycode == 39)  nextImage();
}

$(function(){
    $("#includeImageViewer").load("/static/includes/imageviewer.html");
});


$(document).ready(function() {
    var overlay = document.getElementById('overlay');
});



// END OF OVERLAY FUNCTIONS
// ===========================================