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
    var tableData = a["results"];
    jQuery.noConflict(); 
    $("#jqGrid").jqGrid({
        datatype: "local",
        data: tableData,
        //rownumbers: true,
        //Speed boost but no treeGrid, subGrid, or afterInsertRow
        gridview: true,
        autowidth: true,
        cmTemplate: {sortable: true},
        colModel: [
            {name: " reference_y", editable: true},
            {name: "analysis_date", editable: true},
            {name: "analysis_method", editable: true},
            {name: "analyst", editable: true},
            {name: "comment", editable: true},
            {name: "elements", editable: true},
            {name: "mineral_id", editable: true},
            {name: "oxides", editable: true},
            {name: "reference_image", editable: true},
            {name: "reference_x", editable: true},
            {name: "spot_id", editable: true},
            {name: "stage_x", editable: true},
            {name: "stage_y", editable: true},
            {name: "subsample_id", editable: true},
            {name: "total", editable: true},
            {name: "where_done", editable: true},
        ],
        pager:'#pager',
        viewrecords: true,
        'cellEdit': true,
        'cellsubmit': 'clientArray',
        editurl: 'clientArray'
    });
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
    var a = $("#jqGrid").getChangedCells('all');
    var allRowsInGrid = $('#jqGrid').jqGrid('getGridParam','data');
    alert(JSON.stringify(allRowsInGrid));
}
//Resize the table when the window size changes
$(window).bind('resize', function() {
    $("#jqGrid").setGridWidth($("body").width())
}).trigger('resize');

//Format the data to work with the editableGrid
function formatJsonForTable(data) {
    var newData = [];
    for (var i = 0; i < data.length; i++) {
        newData.push({id: i+1, values: data[i]});
    }
    return newData;
}
