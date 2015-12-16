$(document).ready(function() {

	// Search box toggle
	// =================
	$('#search-btn').on('click', function() {
		$("#search-icon").toggleClass('fa-times margin-2');
		$("#search-box").toggleClass('display-block animated fadeInUp');
	});

	// Smooth scrolling for UI elements page
	// =====================================
	$(document).ready(function(){
	   $('a[href*=#buttons],a[href*=#panels], a[href*=#info-boards], a[href*=#navs], a[href*=#alerts], a[href*=#thumbnails], a[href*=#social], a[href*=#section-header],a[href*=#page-tip], a[href*=#block-header]').bind("click", function(e){
		  var anchor = $(this);
		  $('html, body').stop().animate({
			 scrollTop: $(anchor.attr('href')).offset().top
		  }, 1000);
		  e.preventDefault();
	   });
	   return false;
	});

	// 404 error page 
	// ====================
	$('#search-404').on('click', function() {
		$("#smile").removeClass("fa-meh-o");
		$("#smile").addClass("fa-smile-o");
	});

	// Sign up popovers
	// ================
	$(function(){
		$('#exampleInputName1').popover();
	});

	$(function(){
		$('#exampleInputUsername1').popover();
	});

	$(function(){
		$('#exampleInputEmail1').popover();
	});

	$(function(){
		$('#exampleInputPassword1').popover();
	});

	$(function(){
		$('#exampleInputPassword2').popover();
	});

	// Profile - Status Update 
	// =======================

	$('#update-status').on('click', function() {
		$(".user-status > p").toggleClass("show hidden");
		$(".user-status > form").toggleClass("hidden show");
		return false;
	});

	$('.user-status > form > button').on('click', function() {
		$(".user-status > p").toggleClass("show hidden");
		$(".user-status > form").toggleClass("hidden show");
		return false;
	});

	// Lost password form
	//===================

	$('.pwd-lost > .pwd-lost-q > a').on('click', function() {
		$(".pwd-lost > .pwd-lost-q").toggleClass("show hidden");
		$(".pwd-lost > .pwd-lost-f").toggleClass("hidden show");
		return false;
	});

    // Restyle keywords field
	//===================
    var keywords = $("#keywords").text().split(",");
    var list = $("#list-keywords");
    for (var i = 0; i < keywords.length; i++){
        if (keywords[i]){
           var li = $("<li><a class='tag'></a></li>");
            li.find('a').text(keywords[i]);
            list.append(li);

        }
//            var li = $("<li><a class='tag'></a></li>");

    }
    $("#keywords").remove();

    if ($("#citation-text").length > 0){
        // Make links in citation clickable
        //===================
        var oriCitationText = $("#citation-text").text();
        var newCitationText = oriCitationText;
        var citationUrl;

        // Regular expression to find FTP, HTTP(S) and email URLs.
        var regexToken = /(((ftp|https?):\/\/)[\-\w@:%_\+.~#?,&\/\/=]+)|((mailto:)?[_.\w-]+@([\w][\w\-]+\.)+[a-zA-Z]{2,3})/g;

        var matchArray
        // Extract the url
        while( (matchArray = regexToken.exec(oriCitationText)) !== null ){
            if (matchArray[0].slice(-1) === "." || matchArray[0].slice(-1) === ",") {
                citationUrl = matchArray[0].slice(0, -1);
            }
            else
                citationUrl = matchArray[0];

            newCitationText = newCitationText.replace(citationUrl, "<a href=\"" + citationUrl + "\" target=\"_blank\">" + citationUrl + "</a>")
        }
        $("#citation-text").html(newCitationText);
    }
});
