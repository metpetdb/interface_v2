$(document).ready(function(){
    var thumbnail = $("#thumbnail-carousel").carousel();
    thumbnail.carousel("pause");

    var totalImages = $("li.item").length;
    var displayedImages = 3; //This should change later;
    var totalImagesNoClones = totalImages-displayedImages;

    var start = $(".start").index();
    var resetIndex = $("#reset").index();

    console.log("Total Images with Clones: ", totalImages);
    console.log("displayed Images: ", displayedImages);
    console.log("Total Images, no clones: ", totalImagesNoClones);
    console.log("Start: ", start, ", Reset: ", resetIndex);

    if (totalImagesNoClones > displayedImages) {
        $('.right').on('click', function(){
            $(".start").removeClass("active");
            $(".start").addClass("old");
            $(".item").eq((start+1)%totalImages).addClass("start");
            $(".item").eq((start+displayedImages)%totalImages).addClass("active");
            $(".old").removeClass("start");
            $(".old").removeClass("old");
            start++;
            console.log(start);
            if (start%(totalImages-displayedImages)==0) {
                console.log("RESET BITHC")
                $("#anchor").addClass("active start");
                $("#reset").removeClass("active start");
                $(".clone").removeClass("active");
                start = 0;
                for (var i = 0; i < displayedImages; i++) {
                    $(".item").eq(i).addClass("active");
                };
            }
        });

        $('.left').on('click', function(){
            $(".start").addClass("old");
            $(".item").eq((start+(displayedImages-1))%totalImages).removeClass("active");
            $(".item").eq((start-1)%totalImages).addClass("active start");
            $(".old").removeClass("start");
            $(".old").removeClass("old");
            start--;
            if (start%(totalImages-displayedImages)==-1) {
                $(".item").eq(resetIndex-1).addClass("active start");
                $("#anchor").removeClass("active start");
                $(".clone").addClass("active");
                $("#last").removeClass("active start");
                for (var j = 0; j < displayedImages; j++) {
                    $(".item").eq(j).removeClass("active");
                };
                start = resetIndex-1;
            };
        });
    }
});