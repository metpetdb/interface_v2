//Global variables
var fileSelectURL = null;

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

/*
$.makeTable = function (mydata) {
    var table = $('<table border=1>');
    var tblHeader = "<tr>";
    for (var k in mydata[0]) tblHeader += "<th>" + k + "</th>";
    tblHeader += "</tr>";
    $(tblHeader).appendTo(table);
    $.each(mydata, function (index, value) {
        var TableRow = "<tr>";
        $.each(value, function (key, val) {
            TableRow += "<td>" + val + "</td>";
        });
        TableRow += "</tr>";
        $(table).append(TableRow);
    });
    return ($(table));
};
*/

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
    if (fileSelectURL == null || Checked == null) {
        return;
    }
    //Send Checked and URL as JSON using POST
    var data = {};
    data["url"] = fileSelectURL;
    data["template"] = Checked;
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/test", false);
    xhr.setRequestHeader("Content-type", "application/json");
    xhr.send(JSON.stringify(data));
    var a = JSON.parse(xhr.responseText);
    //document.getElementById('content').innerHTML = JSON.stringify(a);
    document.getElementById('content').innerHTML = "";
    //drawTable(a["results"]);
    makeTable(a["results"]); 
}

function makeTable(data) {
    document.getElementById('gridHeading').innerHTML = "Editable Grid";
    var metadata = [];
    metadata.push({ name: " reference_y", label: "Ref. Y", datatype: "string", editable: true});
    metadata.push({ name: "analysis_date", label: "Analysis Data", datatype: "string", editable: true});
    metadata.push({ name: "analysis_method", label: "Analysis Meth.", datatype: "string", editable: true});
    metadata.push({ name: "analyst", label: "Analyst", datatype: "string", editable: true});
    metadata.push({ name: "comment", label: "Comment", datatype: "string", editable: true});
    metadata.push({ name: "elements", label: "Elements", datatype: "string", editable: true});
    metadata.push({ name: "errors", label: "Errors", datatype: "string", editable: true});
    metadata.push({ name: "mineral_id", label: "Min. ID", datatype: "string", editable: true});
    metadata.push({ name: "oxides", label: "Oxides", datatype: "string", editable: true});
    metadata.push({ name: "reference_image", label: "Ref. Img.", datatype: "string", editable: true});
    metadata.push({ name: "reference_x", label: "Ref. X", datatype: "string", editable: true});
    metadata.push({ name: "spot_id", label: "Spot ID", datatype: "string", editable: true});
    metadata.push({ name: "stage_x", label: "Stage X", datatype: "string", editable: true});
    metadata.push({ name: "stage_y", label: "Stage Y", datatype: "string", editable: true});
    metadata.push({ name: "subsample_id", label: "Subsample ID", datatype: "string", editable: true});
    metadata.push({ name: "total", label: "Total", datatype: "string", editable: true});
    metadata.push({ name: "where_done", label: "Where Done", datatype: "string", editable: true});
    var data = formatJsonForTable(data);
    //alert(JSON.stringify(data));
    editableGrid = new EditableGrid("SamplesGrid");
    editableGrid.load({"metadata": metadata, "data": data});
    editableGrid.renderGrid("tablecontent", "testgrid");
}

//Format the data to work with the editableGrid
function formatJsonForTable(data) {
    var newData = [];
    for (var i = 0; i < data.length; i++) {
        newData.push({id: i+1, values: data[i]});
    }
    return newData;
}

/*
function drawTable(data) {
    for (var i = 0; i < data.length; i++) {
        drawRow(data[i]);
    }
}

function drawRow(rowData) {
    var row = $("<tr />")
    $("#personDataTable").append(row); //this will append tr element to table... keep its reference for a while since we will add cels into it
    row.append($("<td>" + rowData[" reference_y"] + "</td>"));
    row.append($("<td>" + rowData["analysis_date"] + "</td>"));
    row.append($("<td>" + rowData["analysis_method"] + "</td>"));
    row.append($("<td>" + rowData["analyst"] + "</td>"));
    row.append($("<td>" + rowData["comment"] + "</td>"));
    row.append($("<td>" + rowData["elements"] + "</td>"));
    row.append($("<td>" + rowData["errors"] + "</td>"));
    row.append($("<td>" + rowData["mineral_id"] + "</td>"));
    row.append($("<td>" + rowData["oxides"] + "</td>"));
    row.append($("<td>" + rowData["reference_image"] + "</td>"));
    row.append($("<td>" + rowData["reference_x"] + "</td>"));
    row.append($("<td>" + rowData["spot_id"] + "</td>"));
    row.append($("<td>" + rowData["stage_x"] + "</td>"));
    row.append($("<td>" + rowData["stage_y"] + "</td>"));
    row.append($("<td>" + rowData["subsample_id"] + "</td>"));
    row.append($("<td>" + rowData["total"] + "</td>"));
    row.append($("<td>" + rowData["where_done"] + "</td>"));
}
*/
