

$('#select-irods-file').on('click',function(){
    $('#file_struct').children().remove();
	store = $('#root_store').val();
	// Setting up the view tab
	$('#file_struct').attr('name',store);
	$('#irods_view_store').val(store);
	// loading file structs
	parent = $('#file_struct');
	get_store(store,parent,0)
	enable_settings();
});

function get_store(store,parent,margin){
	margin_left = $(parent).css('margin-left');
	margin_left = (parseInt(margin_left.substring(0,margin_left.length-2))-10) + 10;
	form_data = new FormData()
	form_data.append('store',store)
	$.ajax({
            mode: "queue",
			url: '/irods/store/',
			async: true,
			type: "POST",
			data: form_data,
			processData: false,
			contentType: false,
			success: function (data, status) {
				data = jQuery.parseJSON(data);
				if (data[0].length ==0 && data[1].length ==0) {
					$(parent).append("<div class='file' style='margin-left:"+margin+"px;'> -- EMPTY --</div>");
				}
				else {
					$.each(data[1],function(i,v){
						$(parent).append("<div class='folder' id = 'irods_folder_"+v+"' name='"+store+"/"+v+"' style='margin-left:"+margin+"px;'><img src='/static/img/folder.png' width='15' height='15'>&nbsp; "+v+"</div>");
					});
					
					$.each(data[0],function(i,v){
						$(parent).append("<div class='file' id='irods_file_"+v+"' name='"+store+"/"+v+"' style='margin-left:"+margin+"px;'><img src='/static/img/file.png' width='15' height='15'>&nbsp; "+v+"</div>")
						$('.file').on('click',function(e){
							$('.file').css('background','');
							$('.file').removeClass('selected');
							$(e.target).css('background','#cecece');
							$(e.target).addClass('selected');
							set_datastore($(this).parent('div')[0], 0)
							return false
						});
					});
				}
				//enable_settings();
	        },		

	        error: function(status) {
	        	return false;
	        }											
		});
	return true;
}

function enable_settings(){
	// Folder click settings

$('body').on('click', '.folder' ,function(){

		 //console.log($(this).hasClass('isOpen')); 
		 margin_left = $(this).css('margin-left');
		 margin_left = parseInt(margin_left.substring(0,margin_left.length-2)) + 10;
		if($(this).hasClass('isOpen')){
			$(this).addClass('isClose');
			$(this).removeClass('isOpen');
			$(this).children('div').hide();
			set_datastore($(this).attr('name'),'folder');
		}
		else if($(this).hasClass('isClose')) {
			$(this).addClass('isOpen');
			$(this).removeClass('isClose');
			$(this).children('div').show();
		}
		else {
			var store = $(this).attr('name');
			var parent = $(this)
			get_store(store,parent,margin_left);
			$(this).addClass('isOpen');
			set_datastore($(this).attr('name'),1);
		}
	//});
return false;
});


}

function set_datastore(store,isFolder) {
	if (!isFolder) {
		store = $(store).attr('name');
	}
	$('#irods_view_store').val(store);
}

// ### IRODS FUNCTION FOR VIEWING INPUT BOX UPON PRESSING RETURN ###

$('#irods_view_store').keypress(function(e) {
    if(e.which == 13) {
 
        store = $(this).val();
        if (store=='') {
        	store = $('#root_store').val();
        }
		// Setting up the view tab
		$('#file_struct').attr('name',store);
		$('#irods_view_store').val(store);

		// loading file structs
		parent = $('#file_struct');
		got_store = get_store(store,parent,0);
		if (got_store) {
			$('#file_struct').children().remove();
			enable_settings();
		}
		else {
			alert('Datastore does not exist');
		}
    }
});

$("#irodsContent form").bind("keypress", function (e) {
    if (e.keyCode == 13) {
        $("#btnSearch").attr('value');
        //add more buttons here
        return false;
    }
});

$('#iget_irods').on('click',function(){
	var name = '';
	name = $('.selected').attr('name');
	$('#upload_store').val(name);
	$('#irodsContent .modal-backdrop.up-load').show();
	$('#irodsContent .ajax-loader').show();
});

