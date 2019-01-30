(function ($) {
    // Used to instantiate clickable urls in dynamically generated items
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
            if(!user.organization) {
                // Disable publishing resources
                if ($("#publish").length) {
                    $("#publish").toggleClass("disabled", true);
                    $("#publish").removeAttr("data-toggle");   // Disable the agreement modal
                    $("#publish > [data-toggle='tooltip']").attr("data-original-title",
                        "Your profile information must be complete before you can formally publish resources.");
                }

                var message = 'Your profile is nearly complete. Please fill in the '
                    + '<strong>Organization</strong> field'
                    + ' on the <a href="/user/' + user.id + '/">User Profile</a> page';
                showUniversalMessage("warn", message, 10000)();
            }
        },
        error: showUniversalMessage()
    });

    // Event trigger for profile preview
    $(".profile-preview").click(function () {
        // Move the profile card below the clicked item
        var profileCard = $(this).parent().find(".profile-card");
        profileCard.css("top", ($(this).position().top + 30) + "px");
        profileCard.css("left", ($(this).position().left - 175 + $(this).width()/2) + "px");

        var fields = ["name", "email", "country", "state", "organization", "title", "subjectareas", "joined", "contributions"];
        var identifiers = ["googlescholarid", "orcid", "researchgateid", "researcerid"];

        resetProfilePreview(profileCard);
        var data = jQuery.extend(true, {}, $(this).data());

        // Populate subject areas
        var areas = data.subjectareas.split(",");
        for (var i = 0; i < areas.length; i++) {
            profileCard.find("[data-subjectareas]").append("<span class='label label-info'>" + areas[i] + "</span> ");
        }

        // Populate profile button url
        profileCard.find("[data-name]").attr("href", data.profileUrl);
        profileCard.find("[data-url]").attr("href", data.profileUrl);

        // Populate profile picture
        var pic = profileCard.find(".dropdown-profile-pic-thumbnail");
        if (data.profilePicture) {
            pic.toggleClass("dropdown-user-icon", false);
            pic.css("background-image", "url('" + data.profilePicture + "')");
        }
        else {
            pic.toggleClass("dropdown-user-icon", true);
            pic.css("background-image", "none");
        }

        // Toggle wrappers visibility:

        // State and Country
        if ((data["country"] && data["country"] != "Unspecified") || (data["state"] && data["state"] != "Unspecified")) {
            $(".location-wrapper").show();
        }

        // Organization and Title
        if ((data["organization"] && data["organization"] != "Unspecified") || (data["title"] && data["title"] != "Unspecified")) {
            $(".org-wrapper").show();
        }

        // Rest of the fields
        for (var item in data) {
            if ($.inArray(item, fields) != -1) {
                var content = data[item];
                var field = profileCard.find("[data-" + item + "]");
                if (content && content != "Unspecified") {
                    field.text(content);
                    field.show();
                }
                else {
                    profileCard.find("." + item + "-wrapper").hide();
                    field.hide();
                }
            }
            else if ($.inArray(item, identifiers) != -1) {
                var ident = profileCard.find("[data-" + item + "]");
                ident.show();
                profileCard.find(".externalprofiles-wrapper").show();
                ident.attr("href", data[item]);
            }
        }
    });

    function resetProfilePreview(profileCard) {
        var fields = ["name", "email", "country", "state", "organization", "title", "subjectareas", "joined", "contributions"];
        fields.forEach(function (f) {
            profileCard.find("[data-" + f + "]").text("");
            profileCard.find("." + f + "-wrapper").show();
        });
        profileCard.find(".identifier-icon").hide();
        $(".profile-card .externalprofiles-wrapper").hide();
        $(".profile-card .location-wrapper").hide();
        $(".profile-card .org-wrapper").hide();
    }

    $(".author-preview").click(function() {
        resetAuthorPreview();
        var preview = $("#view-author-modal");
        var data = jQuery.extend(true, {}, $(this).data());
        var identifiers = ["googlescholarid", "orcid", "researchgateid", "researcerid"];
        var fields = ["name", "organization", "email", "address", "phone"];

        // If entry is an organization, hide name and profile rows
        preview.find("[data-name]").closest("tr").toggleClass("hidden", !data["name"]);
        preview.find("[data-profileurl]").closest("tr").toggleClass("hidden", !data["profileurl"]);

        // Populate profile url
        if (data["profileurl"]) {
            preview.find("[data-profileurl]").attr("href", data["profileurl"]);
        }
        delete data["profileurl"];

        // Populate homepage url
        if (data["homepage"]) {
            preview.find("[data-homepage]").attr("href", data["homepage"]);
            preview.find("[data-homepage]").text(data["homepage"]);
            preview.find("[data-homepage]").show();
        }
        delete data["homepage"];

        // Populate rest of the fields
        for (var item in data) {
            if ($.inArray(item, fields) != -1) {
                var content = data[item];
                var field = preview.find("[data-" + item + "]");
                field.text(content);
            }
            else if ($.inArray(item, identifiers) != -1) {
                var ident = preview.find("[data-" + item + "]");
                ident.show();
                preview.find(".externalprofiles-wrapper").show();
                ident.attr("href", data[item]);
            }
        }
    });

    function resetAuthorPreview(){
        var preview = $("#view-author-modal");
        preview.find(".identifier-icon").hide();
        preview.find("[data-name]").parent().show();
        preview.find("[data-profileurl]").parent().show();
    }

    $(".submenu-trigger").click(function (e) {
        $(this).next('ul').toggle();
        e.stopPropagation();
        e.preventDefault();
    });

    $(".profile-card").click(function (e) {
        e.stopPropagation();    // Prevents the dropdown from closing while clicking on items inside
    });

    // Abstract collapse toggle
    $(".toggle-abstract").click(function () {
        if ($(this).parent().find(".activity-description").css("max-height") == "50px") {
            var block = $(this).parent().find(".activity-description");

            block.css("max-height", "initial"); // Set max-height to initial temporarily.
            var maxHeight = block.height();    // Save the max height
            block.css("max-height", "50px");    // Restore

            block.animate({'max-height': maxHeight}, 300); // Animate to max height
        }
        else {
            $(this).parent().find(".activity-description").animate({'max-height': "50px"}, 300);
        }
    });

    // Toggle for stats button
    $(".btn-show-more").click(function() {
        var caption = ["Show Less", "Show More"];
        var current = $(this).text() == caption[0] ? 1 : 0;
        $(this).text(caption[current]);
    });

    // Fixes positioning of user and group autocomplete input.
    // Solution found here: https://github.com/yourlabs/django-autocomplete-light/issues/253#issuecomment-35863432
    yourlabs.Autocomplete.prototype.fixPosition = function (html) {
        // Make sure overflow won't hide the select
        this.input.parents().filter(function () {
            return $(this).css('overflow') === 'hidden';
        }).first().css('overflow', 'visible');

        this.box.insertAfter(this.input).css({top: 35, left: 0});
    };

    // Can be used to obtain an element's HTML including itself and not just its content
    jQuery.fn.outerHTML = function () {
        return jQuery('<div />').append(this.eq(0).clone()).html();
    };
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
