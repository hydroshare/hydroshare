// Get the template HTML and remove it from the doumenthe template HTML and remove it from the doument
var previewNode = document.querySelector("#template");
previewNode.id = "";
var previewTemplate = previewNode.parentNode.innerHTML;
previewNode.parentNode.removeChild(previewNode);

//document.querySelector("#total-progress").style.opacity = "0";
var defaultInnerHTML = previewNode.getElementsByClassName("dropdown-toggle")[0].innerHTML;


var CSRF_TOKEN = document.getElementById('csrf_token').getAttribute("value");

var file_map = {};

var myDropzone = new Dropzone(document.body, { // Make the whole body a dropzone
//  url:"/hsapi/_internal/file-upload/",//"/target-url", // Set the url
  url:"/hsapi/_internal/create-hydro-program/",//"/target-url", // Set the url
  thumbnailWidth: 80,
  thumbnailHeight: 80,
  parallelUploads: 100,
  previewTemplate: previewTemplate,
  autoQueue: false, // Make sure the files aren't queued until manually added
  previewsContainer: "#previews", // Define the container to display the previews
  clickable: ".fileinput-button", // Define the element that should be used as click trigger to select files.
  headers: {"X-CSRFToken":CSRF_TOKEN},
  uploadMultiple: true
});
 
myDropzone.on("addedfile", function(file) {
  // Hookup the start button
  document.querySelector("#submitContainer .start").onclick = function() {
      //enqueue all files
      for (var i =0; i< myDropzone.files.length; i++){
        myDropzone.enqueueFile(myDropzone.files[i]);
      }
      //myDropzone.enqueueFile(file);
  };
  $(".dropdown-menu").on({"click":onDropDownClick});
  updateFileDescriptions();
});

 
// Update the total progress bar
//myDropzone.on("totaluploadprogress", function(progress) {
//  document.querySelector("#total-progress .progress-bar").style.width = progress + "%";
//});

myDropzone.on("sendingmultiple", function(file, xhr, formData) {
  xhr.setRequestHeader("X-CSRF-Token",CSRF_TOKEN);

  // get all input form elements
  //var elems = document.getElementsByTagName('input');
//  var elems = $('.form-control');
//
//  for (var i = 0; i < elems.length; i++){
//      // get the input
//      var input = elems[i];
//
//      // append to formData
//      formData.append(input.name, input.value);
//  }

//    formData.append('files',myDropzone.files);

    //myDropzone.processQueue();

//    formData.append('file_map', JSON.stringify(file_map));

   formData = buildForm(formData);

  //formData.append("_token", CSRF_TOKEN);
  // Show the total progress bar when upload starts
  //document.querySelector("#total-progress").style.opacity = "1";
  // And disable the start button
//  document.querySelector("#submitContainer .start").setAttribute("disabled", "disabled");
});

myDropzone.on("success", function(file, data){


    console.log('success');

});

// Hide the total progress bar when nothing's uploading anymore
//myDropzone.on("queuecomplete", function(progress) {
//  document.querySelector("#total-progress").style.opacity = "0";
//});

// Setup the buttons for all transfers
// The "add files" button doesn't need to be setup because the config
// `clickable` has already been specified.
document.querySelector("#submitContainer .start").onclick = function() {
  myDropzone.enqueueFiles(myDropzone.getFilesWithStatus(Dropzone.ADDED));
};
//document.querySelector("#actions .cancel").onclick = function() {
//  myDropzone.removeAllFiles(true);
//};

function updateFileDescriptions(){
  var filePreviews = $("#previews .file-row");
  for (var i = 0; i < filePreviews.length; i++){
    var button = $("#previews .file-row")[i].getElementsByClassName("dropdown-toggle");
    if (button.innerHTML == defaultInnerHTML){
      myDropzone.files[i].fileDescription = "";
    }
    else{
            var tag = button[0].getAttribute('tag');
            updateFileMap(myDropzone.files[i].name,tag);

      //myDropzone.files[i].fileDescription = description;
      //myDropzone.files[i].field_name = 'test';
        //button[0].getAttribute("data-fileDescription");
    }
  }
}

function onDropDownClick(e){
  var elem = e.target.selectedOptions[0];
  var isUnique = elem.getAttribute("data-isunique");
  var caret = ' <span class="caret"></span>';
  if (isUnique == "true"){
    var buttons = document.getElementsByClassName('btn dropdown-toggle');
    //var buttons = $("#previews .dropdown button");
    for (var i = 0; i < buttons.length; i++){
      if (buttons[i].getAttribute('tag') == elem.innerHTML){
      //if (buttons[i].innerHTML == e.target.innerHTML + caret){
        //buttons[i].innerHTML = defaultInnerHTML;
        //myDropzone.files[i].fileDescription = "";
          buttons[i].setAttribute('tag','');
          buttons[i][0].selected = 'selected'
      }
    }
  }

  var value = elem.innerHTML;
    e.target.setAttribute("tag", value);

//  var button = this.parentElement.getElementsByTagName("button")[0]
//  button.innerHTML = e.target.innerHTML + caret;
//  button.setAttribute("data-fileDescription", e.target.innerHTML);
  updateFileDescriptions();
}

function updateFileMap(file_name, tag){

    file_map[file_name] = tag;

}


$('#create_resource_button').click(function(e){


    e.preventDefault();
    e.stopPropagation();

//    var formData = new FormData($(this).closest('.form-horizontal'));



    //if (form.valid() == true) {
        if (myDropzone.getQueuedFiles().length > 0) {
            myDropzone.processQueue();
        } else {
            myDropzone.uploadFiles([]); //send empty
        }

    //}

});
function buildForm(formData){
    var elems = $('.form-control');
      for (var i = 0; i < elems.length; i++){
          // get the input
          var input = elems[i];

          // append to formData
          formData.append(input.name, input.value);
      }
    formData.append('file_map', JSON.stringify(file_map));
    formData.append('_token', '{{ csrf_token() }}');
    return formData;
}