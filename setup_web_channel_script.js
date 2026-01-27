const BadgeState = $badge_state_js;

if (typeof QWebChannel !== 'undefined') {
	new QWebChannel(qt.webChannelTransport, function(channel) {
		window.browserBridge = channel.objects.browserBridge;
		console.log("QWebChannel bridge to Python ready!");

		window.updateModBadge = function(modId, status) {
			const tile = document.querySelector(`.workshopItem a[href*="id=$${modId}"]`)?.closest('.workshopItem');
			if (!tile) {
				console.log(`Mod tile for $${modId} not found.`);
				return;
			}

			let modStatusBadge = tile.querySelector('.rimdex-modstatus-badge');

			if (!modStatusBadge) {
				modStatusBadge = document.createElement('div');
				modStatusBadge.className = 'rimdex-modstatus-badge';

				let modTitleContainer = null;
				const collectionItemParent = tile.parentElement;
				if (collectionItemParent && collectionItemParent.classList.contains('collectionItem')) {
					modTitleContainer = collectionItemParent.querySelector('.collectionItemDetails');
				} else {
					modTitleContainer = tile;
				}

				const modTitleElement = modTitleContainer.querySelector('.workshopItemTitle');
				const modTitleText = modTitleElement ? modTitleElement.textContent.trim() : modId;

				const tileMouseoverHandler = function() {
					tile.classList.add('rimdex-tile-hovered');
					if (modStatusBadge.classList.contains('rimdex-mod-default')) {
						modStatusBadge.style.opacity = '1';
						modStatusBadge.style.visibility = 'visible';
					}
				};
				const tileMouseoutHandler = function() {
					tile.classList.remove('rimdex-tile-hovered');
					if (modStatusBadge.classList.contains('rimdex-mod-default')) {
						modStatusBadge.style.opacity = '0';
						modStatusBadge.style.visibility = 'hidden';
					}
				};
				tile.addEventListener('mouseover', tileMouseoverHandler);
				tile.addEventListener('mouseout', tileMouseoutHandler);

				const badgeMouseoverHandler = function() {
					modStatusBadge.classList.add('rimdex-badge-hovered');
				};
				const badgeMouseoutHandler = function() {
					modStatusBadge.classList.remove('rimdex-badge-hovered');
				};
				modStatusBadge.addEventListener('mouseover', badgeMouseoverHandler);
				modStatusBadge.addEventListener('mouseout', badgeMouseoutHandler);


				const badgeClickHandler = function() {
					if (!window.browserBridge) return;

					modStatusBadge.classList.add('pressed');
					setTimeout(() => {
						modStatusBadge.classList.remove('pressed');
					}, 150);

					if (modStatusBadge.classList.contains('rimdex-mod-default')) {
						window.browserBridge.add_mod_from_js(modId, modTitleText);
					} else if (modStatusBadge.classList.contains('rimdex-mod-added')) {
						window.browserBridge.remove_mod_from_js(modId);
					}
				};

				modStatusBadge.addEventListener('click', badgeClickHandler);

				tile.style.position = 'relative';
				tile.appendChild(modStatusBadge);
			}

			if (status === BadgeState.INSTALLED) {
				modStatusBadge.title = 'Already installed';
				modStatusBadge.innerHTML = '✓';
				modStatusBadge.classList.remove('rimdex-mod-added', 'rimdex-mod-default');
				modStatusBadge.classList.add('rimdex-mod-installed');
				const modTitleElement = tile.querySelector('.workshopItemTitle');
				if (modTitleElement) {
					modTitleElement.style.color = '#4CAF50';
				}
				modStatusBadge.style.opacity = '1';
				modStatusBadge.style.visibility = 'visible';
			} else if (status === BadgeState.ADDED) {
				modStatusBadge.title = 'Preparing to download';
				modStatusBadge.innerHTML = '-';
				modStatusBadge.classList.remove('rimdex-mod-installed', 'rimdex-mod-default');
				modStatusBadge.classList.add('rimdex-mod-added');
				const modTitleElement = tile.querySelector('.workshopItemTitle');
				if (modTitleElement) {
					modTitleElement.style.color = '';
				}
				modStatusBadge.style.opacity = '1';
				modStatusBadge.style.visibility = 'visible';
			} else {
				modStatusBadge.title = 'Add to list';
				modStatusBadge.innerHTML = '+';
				modStatusBadge.classList.remove('rimdex-mod-installed', 'rimdex-mod-added');
				modStatusBadge.classList.add('rimdex-mod-default');
				const modTitleElement = tile.querySelector('.workshopItemTitle');
				if (modTitleElement) {
					modTitleElement.style.color = '';
				}
				if (tile.classList.contains('rimdex-tile-hovered')) {
					modStatusBadge.style.opacity = '1';
					modStatusBadge.style.visibility = 'visible';
				} else {
					modStatusBadge.style.opacity = '0';
					modStatusBadge.style.visibility = 'hidden';
				}
			}

			if (modStatusBadge.matches(':hover')) {
				modStatusBadge.classList.add('rimdex-badge-hovered');
			} else {
				modStatusBadge.classList.remove('rimdex-badge-hovered');
			}
		};

		window.updateAllModBadges = function() {
			const modTiles = document.querySelectorAll('.workshopItem');
			const installedMods = $installed_mods || [];
			const addedMods = $added_mods || [];

			modTiles.forEach(function(tile) {
				const link = tile.querySelector('a[href*="id="]');
				if (!link) return;
				const match = link.href.match(/id=(\d+)/);
				if (!match) return;
				const modId = match[1];

				if (installedMods.includes(modId)) {
					window.updateModBadge(modId, BadgeState.INSTALLED);
				} else if (addedMods.includes(modId)) {
					window.updateModBadge(modId, BadgeState.ADDED);
				} else {
					window.updateModBadge(modId, BadgeState.DEFAULT);
				}
			});
		};

		window.updateAllModBadges();
	});
} else {
	console.error("QWebChannel is not defined. Cannot setup bridge.");
}

const style = document.createElement('style');
style.textContent = `
    .rimdex-modstatus-badge {
        position: absolute;
        top: 5px;
        right: 5px;
        color: white;
        width: 32px;
        height: 32px;
        border-radius: 6px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 20px;
        box-shadow: 0 0 4px black;
        cursor: default;
        user-select: none;
        transition: transform 0.1s ease, box-shadow 0.1s ease, opacity 0.2s ease, visibility 0.2s ease;
    }

    .rimdex-modstatus-badge.rimdex-badge-hovered {
        transform: scale(1.05);
        box-shadow: 0 0 8px rgba(0,0,0,0.4);
    }

    .rimdex-modstatus-badge.pressed {
        transform: scale(0.9);
    }

    .rimdex-mod-installed {
        background-color: #4CAF50;
    }

    .rimdex-mod-added {
        background-color: #FFA500;
        cursor: pointer;
    }

    .rimdex-mod-default {
        background-color: #2196F3;
        cursor: pointer;
        opacity: 0;
        visibility: hidden;
    }
`;
document.head.appendChild(style);
