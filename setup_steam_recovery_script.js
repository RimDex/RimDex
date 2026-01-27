(function () {
	if (window._rimdexSteamRecovery) {
		return;
	}
	window._rimdexSteamRecovery = true;

	function maybeReload(msg) {
		if (!msg || msg.indexOf('Failed to fetch dynamically imported module') < 0) {
			return;
		}
		if (sessionStorage.getItem('rimdex_steam_reload')) {
			return;
		}
		sessionStorage.setItem('rimdex_steam_reload', '1');
		location.reload();
	}

	window.addEventListener('unhandledrejection', function (event) {
		var message = event.reason && event.reason.message;
		maybeReload(message);
	});
})();
