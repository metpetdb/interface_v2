var currentImage = 0;
var images = new Array();
var overlay = document.getElementById('overlay');
var imagePanel = document.getElementById('imagePanel');
var topBox = document.getElementById("topBox");
var imageContainer = document.getElementById("imageContainer");

// =========================================
//Image overlay functions

function overlay_on(e){
  overlay.style.display = "block";
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

  if (event.target == overlay || event.target == imageContainer){
    overlay_off();
  }
}


// END OF OVERLAY FUNCTIONS
// ===========================================