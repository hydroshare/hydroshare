/**
* Created by Mauriel on 3/9/2017.
*/

// Disable carousel auto slide
$('.carousel').carousel({
    interval: 10000
});

$.fn.visible = function (partial) {
    var $t = $(this),
            $w = $(window),
            viewTop = $w.scrollTop(),
            viewBottom = viewTop + $w.height(),
            _top = $t.offset().top,
            _bottom = _top + $t.height(),
            compareTop = partial === true ? _bottom : _top,
            compareBottom = partial === true ? _top : _bottom;

    return ((compareBottom <= viewBottom) && (compareTop >= viewTop));
};

$(document).ready(function () {

    // Prevents dropdown form getting dismissed when clicking on items inside
    $('.dropdown-menu').click(function (e) {
        e.stopPropagation();
    });

    $(".slideInBlock").each(function (i, el) {
        var el = $(el);
        if (el.visible(true)) {
            el.addClass("come-in");
        }
    });

    var win = $(window);
    var allMods = $(".slideInBlock");

    // Already visible modules
    allMods.each(function (i, el) {
        var el = $(el);
        if (el.visible(true)) {
            el.addClass("already-visible");
        }
    });

    // SlideIn blocks on scroll trigger
    win.scroll(function (event) {
        allMods.each(function (i, el) {
            var el = $(el);
            if (el.visible(true)) {
                el.addClass("come-in");
            }
        });
    });
});
