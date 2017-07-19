//Global variables
var fileSelectURL = null;
var tableData;
var tableLabels;
var template;
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

//Validate the URL using regex
function ValidateURL(fileSelectURL) {
    var Regex = /^(?:(?:(?:https?|ftp):)?\/\/)(?:\S+(?::\S*)?@)?(?:(?!(?:10|127)(?:\.\d{1,3}){3})(?!(?:169\.254|192\.168)(?:\.\d{1,3}){2})(?!172\.(?:1[6-9]|2\d|3[0-1])(?:\.\d{1,3}){2})(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5])){2}(?:\.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4]))|(?:(?:[a-z\u00a1-\uffff0-9]-*)*[a-z\u00a1-\uffff0-9]+)(?:\.(?:[a-z\u00a1-\uffff0-9]-*)*[a-z\u00a1-\uffff0-9]+)*(?:\.(?:[a-z\u00a1-\uffff]{2,})).?)(?::\d{2,5})?(?:[/?#]\S*)?$/;
    return Regex.test(fileSelectURL);
}

//Submit the URL
function ParseFileForUpload() {
    document.getElementById('msgbanner').innerHTML = "";
    template = null;
    if (document.getElementById('Samples').checked) {
        template = "SampleTemplate";
    }
    else if (document.getElementById('ChemicalAnalyses').checked) {
        template = "ChemicalAnalysesTemplate";
    }
    else if (document.getElementById('Images').checked) {
        template = "Images";
    }
    if (fileSelectURL == null || template == null) {
        return;
    }
    //Send Checked and URL as JSON using POST
    var data = {};
    data["url"] = fileSelectURL;
    data["template"] = template;
    sendTopython(data);
}

function sendTopython(data) {
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/test", true);
    xhr.setRequestHeader("Content-type", "application/json");
    xhr.onload = function (err) {
        if (xhr.readyState === 4 && xhr.status === 200) {
            var responseData = JSON.parse(xhr.responseText);
            if (responseData['results']['error']) {
                errorResponse = JSON.parse(xhr.responseText);
                var banner = document.getElementById("msgbanner");
                banner.style.color = 'red';
                banner.innerHTML = "<p>Error! " + errorResponse['results']['error'] + "<br>Please try again.</p>";
            } else {
                populateTable(responseData);
            }
        }
    }
    xhr.send(JSON.stringify(data));
}

function populateTable(data) {
    document.getElementById('content').innerHTML = "";
    tableData = data["results"];
    // Time to separate out the metadata
    console.log(tableData);
    var metadata = [];
    for (var i = 0; i < tableData.length; i++) {
        if (tableData[i].meta_header) {
            metadata = tableData[i].meta_header;
        }
    }

    tableLabels = [];
    for (var i = 0; i < metadata.length; i++) {
        tableLabels.push(metadata[i][1]);
    }

    var tableElement = document.getElementById("parsedgrid");
    // Create header row of table
    var headerRow = tableElement.tHead.insertRow();
    for (var i = 0; i < tableLabels.length; i++) {
        var cell = headerRow.insertCell(-1);
        cell.outerHTML = "<th>" + tableLabels[i] + "</th>";
    }

    var areErrors = createBanner(data['status']);

    // Create data rows for table and fill them in
    var tableBody = tableElement.getElementsByTagName("tbody")[0];
    for (var i = 0; i < tableData.length; i++) {
        var newRow = tableBody.insertRow();
        for (var j = 0; j < tableLabels.length; j++) {
            if (tableData[i].meta_header) { continue; }
            var newCell = newRow.insertCell(-1);
            newCell.className= i+','+j; //row, column
            if (Object.keys(tableData[i]['errors']).includes(tableLabels[j])) {
                newCell.style.backgroundColor = '#ff5151';
                newCell.title = tableData[i]['errors'][tableLabels[j]];
            }
            if (tableLabels[j].includes ("mineral")|| tableLabels[j] ==="element" ||tableLabels[j] ==="oxide") {
                var cellText = [];
                var tmp = [];
                if(tableLabels[j].includes ("mineral")){
                    tmp = tableData[i].hasOwnProperty('mineral') ? tableData[i]["mineral"] : tableData[i]["minerals"];
                }
                else {
                    tmp = tableData[i][tableLabels[j]];
                }
                for (var k = 0; k < tmp.length; k++) {
                    cellText.push(tmp[k].name);
                }
                newCell.innerHTML = cellText.join();
            }
            else if (tableLabels[j] === "amount"){
                newCell.innerHTML = tableData[i][tableLabels[j-1]][0]["amount"];
            }else if (tableLabels[j] === "collection_date") {
                newCell.innerHTML = moment(tableData[i][tableLabels[j]]).format("DD-MM-YYYY");
            } else if (tableLabels[j] === "location_coords") {
                if (areErrors) {
                    var latitude = tableData[i]['latitude'];
                    var longitude = tableData[i]['longitude'];
                    newCell.innerHTML = latitude + ", " + longitude;
                    var latitudeError = Object.keys(tableData[i]['errors']).includes("latitude");
                    var longitudeError = Object.keys(tableData[i]['errors']).includes("longitude");
                    if (latitudeError || longitudeError) {
                        newCell.style.backgroundColor = '#ff9999';
                        if (latitudeError) {
                            newCell.title = tableData[i]['errors']['latitude'];
                        }
                        if (longitudeError) {
                            newCell.title += "; " + tableData[i]['errors']['longitude'];
                        }
                    }
                } else {
                    var coordString = tableData[i][tableLabels[j]];
                    coordString = coordString.split(" (")[1].slice(0, -1);
                    var coords = coordString.split(" ");
                    coords[0] = parseFloat(coords[0]);
                    coords[1] = parseFloat(coords[1]);
                    newCell.innerHTML = coords[0].toFixed(5) + ", " +coords[1].toFixed(5);
                }
            } else {
                newCell.innerHTML = tableData[i][tableLabels[j]];
            }
            newCell.contentEditable = true;
            newCell.addEventListener("input", function() {
                this.style.backgroundColor = '#99b9ff';
                updateData(this.className,this.innerHTML);
            });
        }
    }
    if (areErrors) {
        createGridSubmitButton();
    }
}


function updateData(coords, change){
    var infos = coords.split(',');
    var field = tableLabels[infos[1]];
    var entry = tableData[infos[0]];

    if(field.includes("mineral")){
        field = entry.hasOwnProperty('mineral') ? 'mineral' : 'minerals';
    }
    console.log("field, ", field);
    if(field==="location_coords"){
        var changes = change.split(',');
        entry['latitude'] = parseFloat(changes[0]);
        entry['longitude'] = parseFloat(changes[1]);
    }else if(field==="amount"){
        field = tableLabels[parseInt(infos[1])-1];
        entry[field]["amount"] = change;
    }else if(Array.isArray(entry[field])){
        updateArray(entry,field,change);
        console.log(tableData);
    }else {
        entry[field] = change;
    }
}

function updateArray(entry, field, change) {
    var arr = change.split(',');
    for(var i =0; i < arr.length;i++){
        arr[i] = {"amount": 0, "name": arr[i]};
    }
    entry[field] = arr;
}

function createBanner(statusCode){
    if (statusCode >=200 && statusCode < 300 ) {
        var banner = document.getElementById("msgbanner");
        banner.style.color = 'green';
        banner.innerHTML = "No errors found!  Rows displayed below have been inserted into the database."
        return false;
    }
    var banner = document.getElementById("msgbanner");
    banner.style.color = 'red';
    banner.innerHTML = "Please fix the highlighted area and resubmit."
    return true;
}


function createGridSubmitButton() {
    var element = document.createElement("input");
    element.setAttribute("type", "button");
    element.setAttribute("value", "Submit");
    element.setAttribute("onclick", "submitJson();");
    document.getElementById("gridSubmit").appendChild(element);
}

function submitJson(){
    var data = {'template': template, 'json': JSON.stringify(tableData)};
    console.log(data);
    sendTopython(data);
    removeTableContent();
}

function removeTableContent() {
    tableData = null, tableLabels= null;
    var table = document.getElementById("parsedgrid");
    table.deleteTHead();
    table.createTHead();
    var tableBody = table.getElementsByTagName("tbody")[0];

    while(tableBody.rows.length>0){
        tableBody.deleteRow(tableBody.rows.length - 1);
    }
}
