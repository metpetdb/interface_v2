//Global variables
var URL = null;

//Capture the URL from the user via a pop-up text box
function GetFileURL() {
    URL = prompt("Please enter the URL of the file you want to upload");
    //Check if an X or check mark already exist. If one does, remove it.
    var OldImage = document.getElementById('symbol');
    if (OldImage) {
        OldImage.parentNode.removeChild(OldImage); 
    }
    //Create the new image (either X or check)
    var img = document.createElement("img");
    img.alt = "image";
    img.id = "symbol";
    if (URL != null) {
        if (!ValidateURL(URL)) {
            //alert(URL + " is not a valid URL");
            img.height="20";
            img.width="20";
            img.src = "../static/images/x.jpg";
            URL = null;
            
        }
        else {
            img.height="24";
            img.width="24";
            img.src = "../static/images/check.png";
            document.getElementById('URLEntered').innerHTML = URL;
        }
        document.getElementById('CheckOrX').appendChild(img);
    }
}

//Validate the URL using regex
function ValidateURL(URL) {
    var Regex = /^(?:(?:(?:https?|ftp):)?\/\/)(?:\S+(?::\S*)?@)?(?:(?!(?:10|127)(?:\.\d{1,3}){3})(?!(?:169\.254|192\.168)(?:\.\d{1,3}){2})(?!172\.(?:1[6-9]|2\d|3[0-1])(?:\.\d{1,3}){2})(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5])){2}(?:\.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4]))|(?:(?:[a-z\u00a1-\uffff0-9]-*)*[a-z\u00a1-\uffff0-9]+)(?:\.(?:[a-z\u00a1-\uffff0-9]-*)*[a-z\u00a1-\uffff0-9]+)*(?:\.(?:[a-z\u00a1-\uffff]{2,})).?)(?::\d{2,5})?(?:[/?#]\S*)?$/;
    return Regex.test(URL);
}

//Submit the URL
function ParseFileForUpload() {
    var Checked = null;
    if (document.getElementById('Samples').checked) {
        Checked = "SampleTemplate";
    }
    else if (document.getElementById('ChemicalAnalyses').checked) {
        Checked = "ChemicalAnalysesTemplate";
    }
    else if (document.getElementById('Images').checked) {
        Checked = "Images";
    }
    if (URL == null || Checked == null) {
        return;
    }
    //Send Checked and URL as JSON using POST
    var data = {};
    data["checked"] = Checked;
    data["url"] = URL;
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/test", false);
    xhr.setRequestHeader("Content-type", "application/json");
    xhr.send(JSON.stringify(data));
    document.write(xhr.responseText);
}
