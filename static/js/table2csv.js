function table2csv(oTable, exportmode, tableElm) {
        var csv = '';
        var headers = [];
        var rows = [];
 
        // Get header names
        jQuery(tableElm+' thead').find('th').each(function() {
            var th = jQuery(this);
            var text = th.text();
            var header = '"' + text + '"';
            // headers.push(header); // original code
            if(text != "") headers.push(header); // actually datatables seems to copy my original headers so there ist an amount of TH cells which are empty
        });
        csv += headers.join(',') + "\n";
        
        // get table data
        if (exportmode == "full") { // total data
            var total = oTable.fnSettings().fnRecordsTotal()
            for(i = 0; i < total; i++) {
                var row = oTable.fnGetData(i);
                row = strip_tags(row);
                rows.push(row);
            }
        } else { // visible rows only
            jQuery(tableElm+' tbody tr:visible').each(function(index) {
                var row = oTable.fnGetData(this);
                row = strip_tags(row);
                rows.push(row);
            })
        }
        csv += rows.join("\n");

        console.log("table2csv used");
 
        // if a csv div is already open, delete it
        if(jQuery('.csv-data').length) jQuery('.csv-data').remove();
        // open a div with a download link
        jQuery('body').append('<div class="csv-data"><form enctype="multipart/form-data" method="post" action="/csv.php"><textarea class="form" name="csv">'+csv+'</textarea><input type="submit" class="submit" value="Download as file" /></form></div>');
 
}
 
function strip_tags(html) {
    var tmp = document.createElement("div");
    tmp.innerHTML = html;
    return tmp.textContent||tmp.innerText;
}

// $(document).ready(function () {

//     function table2CSV($table, filename) {
//     // function exportTableToCSV($table, filename) {

//         var $rows = $table.find('tr:has(td)'),

//             // Temporary delimiter characters unlikely to be typed by keyboard
//             // This is to avoid accidentally splitting the actual contents
//             tmpColDelim = String.fromCharCode(11), // vertical tab character
//             tmpRowDelim = String.fromCharCode(0), // null character

//             // actual delimiter characters for CSV format
//             colDelim = '","',
//             rowDelim = '"\r\n"',

//             // Grab text from table into CSV formatted string
//             csv = '"' + $rows.map(function (i, row) {
//                 var $row = $(row),
//                     $cols = $row.find('td');

//                 return $cols.map(function (j, col) {
//                     var $col = $(col),
//                         text = $col.text();

//                     return text.replace(/"/g, '""'); // escape double quotes

//                 }).get().join(tmpColDelim);

//             }).get().join(tmpRowDelim)
//                 .split(tmpRowDelim).join(rowDelim)
//                 .split(tmpColDelim).join(colDelim) + '"',

//             // Data URI
//             csvData = 'data:application/csv;charset=utf-8,' + encodeURIComponent(csv);

//         $(this)
//             .attr({
//             'download': filename,
//                 'href': csvData,
//                 'target': '_blank'
//         });
//     }

//     // This must be a hyperlink
//     $(".export").on('click', function (event) {
//         // CSV
//         exportTableToCSV.apply(this, [$('#dvData>table'), 'export.csv']);
        
//         // IF CSV, don't do event.preventDefault() or return false
//         // We actually need this to be a typical hyperlink
//     });
// // });