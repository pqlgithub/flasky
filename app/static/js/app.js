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

var checked_items_status = function () {
	var total_count = 0;
	$('input.check-one').each(function () {
		if ($(this).is(':checked')) {
			total_count += 1;
		}
	});

	if (total_count > 0) {
		$('.checked-items-status').html(total_count + ' items selected').removeClass('hidden');
		$('.btn.delete-all').removeClass('hidden');
	} else {
		$('.checked-items-status').addClass('hidden');
		$('.btn.delete-all').addClass('hidden');
	}
};

function hook_dropdown_menu (callback) {
	$('.dropdown-select-menu .option').on('click', function (cb) {
		var $this=$(this), label=$(this).text(), v=$(this).data('id'),
			target=$(this).parent().parent().data('target');

		$(this)
			.parent()
			.siblings('.active').removeClass('active')
			.end()
			.addClass('active');

		$('input[name='+ target +']').val(v);

		$(this).parent().parent().prev().find('b').text(label);

		callback();
	});
}

function hook_filter_search (callback) {
	$('input.searcher').on('keydown', function (e) {
		var ev = window.event||e;
		if (ev.keyCode == 13) {
			callback();
			return false;
		}
	});
}

function hook_all_check() {
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
		checked_items_status();
	});

	$('input.check-one').click(function () {
		// 取消全选
		if (!$(this).is(':checked')) {
			$('input.check-all')
				.prop('checked', false);
		}
		checked_items_status();
	});
}

function hook_ajax_modal() {
	// 自动绑定ajax的链接
	$('a.ajax-modal').click(function () {
		var url = $(this).attr('href'), modal_name = $(this).data('modal');
		$.get(url, function (html) {
			$('body').append('<div id="'+ modal_name +'" role="dialog" class="modal">' + html + '</div>');

			$('#'+ modal_name).modal('show');
		});
		return false;
	});
}

$(function () {
	$('[data-toggle="tooltip"]').tooltip({
		container: 'body',
		html: true,
		trigger: 'hover'
	});

	$('.select2').select2({
		'width': '100%'
	});

	hook_all_check();

	hook_ajax_modal();

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