(function ($) {
    $.fn.urlClickable = function () {
        var item = $(this);

        if (item.find(".isUrlClickable").length) {
            return this;    // Items already initiated
        }

        var originalText = item.text().trim();
        var newText = originalText;

        // Regular expression to find FTP, HTTP(S) and email URLs.
        var regexToken = /(((ftp|https?):\/\/)[\-\w@:%_\+.~#?,&\/\/=]+)|((mailto:)?[_.\w-]+@([\w][\w\-]+\.)+[a-zA-Z]{2,3})/g;

        // Extract all URL occurrences
        var matchArray;
        var urls = [];

        while ((matchArray = regexToken.exec(originalText)) !== null) {
            if (matchArray[0].slice(-1) === "." || matchArray[0].slice(-1) === ",") {
                urls.push(matchArray[0].slice(0, -1))
            }
            else {
                urls.push(matchArray[0]);
            }
        }

        // Get a list of unique URLs
        var uniqueUrls = [];
        $.each(urls, function (i, el) {
            if ($.inArray(el, uniqueUrls) === -1) {
                uniqueUrls.push(el);
            }
        });

        // Replace all URLs for links
        for (var i = 0; i < uniqueUrls.length; i++) {
            var currentUrl = uniqueUrls[i];

            var replacedString = "<span class='isUrlClickable'>" +
                "<a href=\"" + currentUrl + "\" target=\"_blank\">" + currentUrl + "</a></span>";

            var regex = new RegExp(currentUrl, "g");
            newText = newText.replace(regex, replacedString);
        }

        $(this).html(newText);

        return item;
    }
})(jQuery);

// Formats dates from "yyyy-mm-dd" to "mm/dd/yyyy"
(function ($) {
    $.fn.formatDate = function () {
        var item = $(this);
        var dateString = item.attr("data-date").trim().substr(0, 10).split("-");    // original format: yyyy-mm-dd (10 characters)
        var formattedDate = dateString[1] + "/" + dateString[2] + "/" + dateString[0];
        item.text(formattedDate);

        return item;
    }
})(jQuery);


$(document).ready(function () {
    // Search box toggle
    // =================
    $('#search-btn').on('click', function () {
        $("#search-icon").toggleClass('fa-times margin-2');
        $("#search-box").toggleClass('display-block animated fadeInUp');
    });

	// Smooth scrolling for UI elements page
	// =====================================

	$('a[href*=#buttons],a[href*=#panels], a[href*=#info-boards], a[href*=#navs], a[href*=#alerts], a[href*=#thumbnails], a[href*=#social], a[href*=#section-header],a[href*=#page-tip], a[href*=#block-header]').bind("click", function (e) {
		var anchor = $(this);
		$('html, body').stop().animate({
			scrollTop: $(anchor.attr('href')).offset().top
		}, 1000);
		e.preventDefault();
	});

    // 404 error page
    // ====================
    $('#search-404').on('click', function () {
        $("#smile").removeClass("fa-meh-o");
        $("#smile").addClass("fa-smile-o");
    });

    // Sign up popovers
    // ================
    $(function () {
        $('#exampleInputName1').popover();
    });

    $(function () {
        $('#exampleInputUsername1').popover();
    });

    $(function () {
        $('#exampleInputEmail1').popover();
    });

    $(function () {
        $('#exampleInputPassword1').popover();
    });

    $(function () {
        $('#exampleInputPassword2').popover();
    });

    // Profile - Status Update
    // =======================

    $('#update-status').on('click', function () {
        $(".user-status > p").toggleClass("show hidden");
        $(".user-status > form").toggleClass("hidden show");
        return false;
    });

    $('.user-status > form > button').on('click', function () {
        $(".user-status > p").toggleClass("show hidden");
        $(".user-status > form").toggleClass("hidden show");
        return false;
    });

    // Lost password form
    //===================

    $('.pwd-lost > .pwd-lost-q > a').on('click', function () {
        $(".pwd-lost > .pwd-lost-q").toggleClass("show hidden");
        $(".pwd-lost > .pwd-lost-f").toggleClass("hidden show");
        return false;
    });

    // Restyle keywords field
    //===================
    var keywords = $("#keywords").text().split(",");
    var list = $("#list-keywords");
    for (var i = 0; i < keywords.length; i++) {
        if (keywords[i]) {
            var li = $("<li><a class='tag'></a></li>");
            li.find('a').text(keywords[i]);
            list.append(li);
        }
    }

    $("#keywords").remove();

    // Make URLs inside text clickable
    $(".url-clickable").each(function () {
        $(this).urlClickable();
    });

    // Make apps link open in new tab
    $('a[href^="https://appsdev.hydroshare.org/apps"]').attr('target', '_blank');

	// Close buttons for notification messages
	$(".btn-close-message").click(function() {
		$(this).parent().parent().parent().parent().hide(400);
	});

	// Initialize tooltips
	$('[data-toggle="tooltip"]').tooltip();

    // Format the dates before displaying them
    $(".format-date").each(function () {
        $(this).formatDate();
    });

    $("#universalMessage a").on('click', function() {
        $("#universalMessage").slideUp();
        return false
    });

    $.ajax({
        url: "/hsapi/userInfo/",
        success: function(user) {
            if(!user.title || !user.organization) {
                var message = 'Your profile is nearly complete. ';
                message += 'Please fill in the ';
                if(!user.title && !user.organization) {
                    message += '<strong>title</strong> and <strong>organization</strong>';
                } else if (!user.title) {
                    message += '<strong>title</strong>';
                } else if (!user.organization) {
                    message += '<strong>organization</strong>';
                }
                message += ' field on the <a href="/user/'+user.id+'/">user profile</a> page';
                showUniversalMessage("warn", message, 10000)();
            }
        },
        error: showUniversalMessage()
    })
});

function showUniversalMessage(type, message, timeout) {
    return function(response,returnType,content) {
        if(!message) message = content;
        if(!type) type = returnType;
        if(!timeout) timeout = 5000;

        $("#universalMessage span").html(message);
        $("#universalMessage").attr('class','');
        $("#universalMessage").addClass(type);
        $("#universalMessage").slideDown();

        setTimeout(function() {
            $("#universalMessage a.um_close").click()
        }, timeout)
    }
}
