
var app = {

	init: function() {

		console.log('init()');

		//$('#front-page-link-about').on('click', function() { app.display_page('about'); });
		//$('#front-page-link-projects').on('click', function() { app.display_page('projects'); });
		//$('#front-page-link-thoughts').on('click', function() { app.display_page('thoughts'); });
		//$('#front-page-link-contacts').on('click', function() { app.display_page('contacts'); });

		window.onhashchange = function() {

			var page = location.hash.replace('#/','');

			app.display_page(page);

		}

		app.display_page(location.hash.replace('#/',''));

		//app.display_page('home');

	},

	display_page: function(page) {
		console.log('display_page()');
		$('.page').hide(300);
		switch(page) {
			case "home":
			case "about":
			case "projects":
			case "thoughts":
			case "contact":
				$('#page-' + page).show(300);
				break;
			default:
				location.hash = '#/home';
				//$('#page-home').show(300);
				break
		}
	}

}

$(document).ready(function() {

	app.init();


});