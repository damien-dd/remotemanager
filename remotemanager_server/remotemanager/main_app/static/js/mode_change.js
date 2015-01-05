(function($){   
	$(function(){
		$(document).ready(function() {
			$('#id_remotedevice_dev').after("<a href=\"#\" onclick=\"mode_change(this);return false;\"> <img src=\"/static/icons/arrow_refresh.png\" alt=\"Refresh\"/></a>");
			$('#id_remotedevice_mode').bind('change', mode_change);		   
			mode_change();
		});
});  
})(django.jQuery);

// based on the mode, dev list will be loaded

var $ = django.jQuery.noConflict();

function mode_change()
{
	var mode = $('#id_remotedevice_mode input[name=remotedevice_mode]:checked').val();

	if (mode == 'BT') {
		$('#id_remotedevice_dev').parent().hide();
		$('#id_remotedevice_serial').parent().show();
	} else {
		$('#id_remotedevice_serial').parent().hide();
		$('#id_remotedevice_dev').parent().show();
		$.ajax({
				"type"     : "GET",
				"url"      : "/dev_choices/?mode="+mode,
				"dataType" : "json",
				"cache"    : false,
				"success"  : function(json) {
					var selected_dev_val = $('#id_remotedevice_dev >option:first').val();
					var selected_dev_html = $('#id_remotedevice_dev >option:first').html();

					$('#id_remotedevice_dev >option').remove();

					if (selected_dev_val != '') {
						$('#id_remotedevice_dev').append($('<option></option>').val(selected_dev_val).html(selected_dev_html));
					}
					
					for(var j = 0; j < json.length; j++){
						if (json[j][0] != selected_dev_val) {
							$('#id_remotedevice_dev').append($('<option></option>').val(json[j][0]).html(json[j][1]));
						}
					}
					$('#id_remotedevice_dev >option').show();
				}
		})(jQuery);
	}
}
