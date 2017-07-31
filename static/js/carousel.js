$(document).ready(function(){
    var thumbnail = $("#thumbnail-carousel").carousel();
    thumbnail.carousel("pause");

    var start = $(".start").index();
    var resetIndex = $("#reset").index();

    $('.right').on('click', function(){
        $(".start").removeClass("active");
        $(".start").addClass("old");
        $(".item").eq((start+1)%8).addClass("start");
        $(".item").eq((start+3)%8).addClass("active");
        $(".old").removeClass("start");
        $(".old").removeClass("old");
        start++;
        console.log("Hi", start);
        if (Math.abs(start)%5==0) {
            $("#anchor").addClass("active start");
            $("#reset").removeClass("active start");
            $(".clone").removeClass("active");
            start = 0;
            for (var i = 0; i < 3; i++) {
                $(".item").eq(i).addClass("active");
            };
        }
    });

    $('.left').on('click', function(){
        $(".start").addClass("old");
        $(".item").eq((start+2)%8).removeClass("active");
        $(".item").eq((start-1)%8).addClass("active start");
        $(".old").removeClass("start");
        $(".old").removeClass("old");
        start--;
        console.log("Ho", start);
        if (Math.abs(start)%5==1) {
            $(".item").eq(8).removeClass("active start");
            $(".item").eq(resetIndex-1).addClass("active start")
        }
    });
});