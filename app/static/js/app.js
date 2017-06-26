var display_alert = function (message) {
	var html = '<div class="alert alert-warning alert-dismissible fade in" role="alert"> ';
	html += '<button class="close" type="button" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">×</span></button>';
	html += '<strong>'+ message +'</strong>';
	html += '</div>';

	return html
};

var get_url_params = function (href) {
	href = href.split('?');
	href.shift();
	href = href.join('?');
	href = href.split('&');
	var query = {};
	for (var i=0; i<href.length; i+=1) {
		var q = href[i].split('=');
		query[q[0]] = q[1];
	}
	return query;
};

$(function () {
	$('[data-toggle="tooltip"]').tooltip({
		container: 'body',
		html: true,
		trigger: 'hover'
	});

	$('.select2').select2({
		'width': '100%'
	});

	// 全选 or 反选
	$('input.check-all').bind('click', function() {
		if ($(this).is(':checked')){
			$(this)
				.parents('table')
				.find('.check-one')
				.prop('checked', true);
		} else {
			$(this)
				.parents('table')
				.find('.check-one')
				.prop('checked', false);
		}
	});

	$('input.check-one').click(function () {
		// 取消全选
		if (!$(this).is(':checked')) {
			$('input.check-all')
				.prop('checked', false);
		}
	});

	// 删除 全部 or 单个
	$('button.delete-all').click(function () {
		var form_id = $(this).data('form-id');
		swal({
			title: "Confirm to delete?",
			text: "You will not be able to recover!",
			type: "warning",
			showCancelButton: true,
			confirmButtonClass: 'btn-warning',
			confirmButtonText: "Yes, delete it!",
			closeOnConfirm: true
		}, function (is_confirm) {
			if (is_confirm) {
				// 检测是否选中
				if ($('#' + form_id).find(':checked').length){
					$('#' + form_id).submit();
				} else {
					swal("Error", "First to selected the one!!!", "error");
				}
			}
		});
	});

	$('.alert-dismissable').fadeTo(2000, 500).fadeOut(500, function(){
		$('.alert-dismissable').alert('close');
		$('.flashes').fadeOut(500, function () {
			$(this).remove();
		});
	});

});