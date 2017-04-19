//Global variables
var fileSelectURL = null;

//Validate a URL using regex
function ValidateURL(url) {
    var Regex = /^(?:(?:(?:https?|ftp):)?\/\/)(?:\S+(?::\S*)?@)?(?:(?!(?:10|127)(?:\.\d{1,3}){3})(?!(?:169\.254|192\.168)(?:\.\d{1,3}){2})(?!172\.(?:1[6-9]|2\d|3[0-1])(?:\.\d{1,3}){2})(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5])){2}(?:\.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4]))|(?:(?:[a-z\u00a1-\uffff0-9]-*)*[a-z\u00a1-\uffff0-9]+)(?:\.(?:[a-z\u00a1-\uffff0-9]-*)*[a-z\u00a1-\uffff0-9]+)*(?:\.(?:[a-z\u00a1-\uffff]{2,})).?)(?::\d{2,5})?(?:[/?#]\S*)?$/;
    return Regex.test(url);
}

//Capture the URL from the user via a pop-up text box
function GetFileURL() {
    fileSelectURL = prompt("Please enter the URL of the file you want to upload");
    //Check if an X or check mark already exist. If one does, remove it.
    var OldImage = document.getElementById('symbol');
    if (OldImage) {
        OldImage.parentNode.removeChild(OldImage); 
    }
    //Create the new image (either X or check)
    var img = document.createElement("img");
    img.alt = "image";
    img.id = "symbol";
    if (fileSelectURL != null) {
        if (!ValidateURL(fileSelectURL)) {
            //alert(fileSelectURL + " is not a valid URL");
            img.height="20";
            img.width="20";
            img.src = "../static/images/x.jpg";
            fileSelectURL = null;
            
        }
        else {
            img.height="24";
            img.width="24";
            img.src = "../static/images/check.png";
            document.getElementById('URLEntered').innerHTML = fileSelectURL;
        }
        document.getElementById('CheckOrX').appendChild(img);
    }
}

//Submit the URL
function ParseFileForUpload() {
    document.getElementById('errorbanner').innerHTML = "";
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
    if (fileSelectURL == null || Checked == null) {
        return;
    }
    //Send Checked and URL as JSON using POST
    var data = {};
    data["url"] = fileSelectURL;
    data["template"] = Checked;
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/test", true);
    xhr.setRequestHeader("Content-type", "application/json");
    xhr.onload = function (err) {
        if (xhr.readyState === 4 && xhr.status === 200) {
            responseData = JSON.parse(xhr.responseText);
            if (responseData['results']['error']) {
                errorResponse = JSON.parse(xhr.responseText);
                document.getElementById('errorbanner').innerHTML = "<p>Error! " + errorResponse['results']['error'] + "<br>Please try again.</p>";
            } else {
                populateTable(responseData);
            }
        }
    }
    xhr.send(JSON.stringify(data));
}

function populateTable(data) {
    document.getElementById('content').innerHTML = "";
    var tableData = data["results"];
    // Time to separate out the metadata
    var metadata = [];
    for (var i = 0; i < tableData.length; i++) {
        if (tableData[i].meta_header) {
            metadata = tableData[i].meta_header;
            tableData.splice(i, 1);
        }
    }
    var tableLabels = [];
    for (var i = 0; i < metadata.length; i++) {
        tableLabels.push(metadata[i][1]);
    }
    console.log("Metadata:")
    console.log(metadata);
    console.log("Table labels:");
    console.log(tableLabels);
    console.log("Table data:");
    console.log(tableData);
    var tableElement = document.getElementById("parsedgrid");
    // Create header row of table
    var headerRow = tableElement.tHead.insertRow();
    for (var i = 0; i < tableLabels.length; i++) {
        var cell = headerRow.insertCell(-1);
        cell.outerHTML = "<th>" + tableLabels[i] + "</th>";
    }
    // Create data rows for table and fill them in
    var tableBody = tableElement.getElementsByTagName("tbody")[0];
    for (var i = 0; i < tableData.length; i++) {
        var newRow = tableBody.insertRow();
        for (var j = 0; j < tableLabels.length; j++) {
            var newCell = newRow.insertCell(-1);
            if (tableLabels[j] === "minerals") {
                newCell.innerHTML = "<b>Under construction</b>";
            } else if (tableLabels[j] === "collection_date") {
                newCell.innerHTML = moment(tableData[i][tableLabels[j]]).format("DD-MM-YYYY");
            } else if (tableLabels[j] === "location_coords") {
                var coordString = tableData[i][tableLabels[j]];
                coordString = coordString.split(" (")[1].slice(0, -1);
                var coords = coordString.split(" ");
                console.log(coords);
                coords[0] = parseFloat(coords[0]);
                coords[1] = parseFloat(coords[1]);
                newCell.innerHTML = coords[0].toFixed(5) + ", " +coords[1].toFixed(5);
            } else {
                newCell.innerHTML = tableData[i][tableLabels[j]];
            }
            newCell.contentEditable = true;
            newCell.addEventListener("input", function() {
                console.log("Data was changed, will re-parse data to be safe");
            });
        }
    }
    createGridSubmitButton();
}

function createGridSubmitButton() {
    var element = document.createElement("input");
    element.setAttribute("type", "button");
    element.setAttribute("value", "Submit");
    element.setAttribute("onclick", "submitGrid();");
    var foo = document.getElementById("gridSubmit");
    foo.appendChild(element);
}

function submitGrid() {

}