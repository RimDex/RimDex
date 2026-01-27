const BadgeState = $badge_state_js;

function _findModTile(modId) {
    const links = document.querySelectorAll('a[href*="filedetails/?id=' + modId + '"]');
    if (links.length === 0) return null;

    for (const link of links) {
        const collectionItem = link.closest('.collectionItem');
        if (collectionItem) return collectionItem;

        let el = link.parentElement;
        while (el && el !== document.body && el !== document.documentElement) {
            const filedetailsLinks = el.querySelectorAll('a[href*="filedetails/"]');
            const hasTitleLink = Array.from(filedetailsLinks).some(l => l.textContent.trim());
            const hasThumbImg = el.querySelector('a[href*="filedetails/"] img');
            if (hasTitleLink && hasThumbImg) return el;
            el = el.parentElement;
        }
    }
    return null;
}

function _getModTitle(tile, modId) {
    const links = tile.querySelectorAll('a[href*="filedetails/"]');
    for (const link of links) {
        const text = link.textContent.trim();
        if (text) return text;
    }
    return modId;
}

function _setBadgeVisibility(badge, tile) {
    const isDefault = badge.classList.contains('rimdex-mod-default');
    const isHovered = tile.classList.contains('rimdex-tile-hovered');
    badge.style.opacity = (!isDefault || isHovered) ? '1' : '0';
    badge.style.visibility = (!isDefault || isHovered) ? 'visible' : 'hidden';
}

function updateModBadge(modId, status) {
    const tile = _findModTile(modId);
    if (!tile) {
        console.log('Mod tile for ' + modId + ' not found.');
        return;
    }

    let badge = tile.querySelector('.rimdex-modstatus-badge');

    if (!badge) {
        badge = document.createElement('div');
        badge.className = 'rimdex-modstatus-badge';
        const modTitleText = _getModTitle(tile, modId);

        tile.addEventListener('mouseenter', () => {
            tile.classList.add('rimdex-tile-hovered');
            if (badge.classList.contains('rimdex-mod-default')) {
                badge.style.opacity = '1';
                badge.style.visibility = 'visible';
            }
        });
        tile.addEventListener('mouseleave', () => {
            tile.classList.remove('rimdex-tile-hovered');
            if (badge.classList.contains('rimdex-mod-default')) {
                badge.style.opacity = '0';
                badge.style.visibility = 'hidden';
            }
        });

        badge.addEventListener('click', () => {
            if (!window.browserBridge) return;
            badge.classList.add('pressed');
            setTimeout(() => badge.classList.remove('pressed'), 150);

            if (badge.classList.contains('rimdex-mod-default')) {
                window.browserBridge.add_mod_from_js(modId, modTitleText);
            } else if (badge.classList.contains('rimdex-mod-added')) {
                window.browserBridge.remove_mod_from_js(modId);
            }
        });

        tile.style.position = 'relative';
        tile.appendChild(badge);
    } else {
        badge.classList.remove('rimdex-mod-installed', 'rimdex-mod-added', 'rimdex-mod-default');
    }

    if (status === BadgeState.INSTALLED) {
        badge.title = 'Already installed';
        badge.innerHTML = '\u2713';
        badge.classList.add('rimdex-mod-installed');
        badge.style.backgroundColor = '#4CAF50';
    } else if (status === BadgeState.ADDED) {
        badge.title = 'Preparing to download';
        badge.innerHTML = '-';
        badge.classList.add('rimdex-mod-added');
        badge.style.backgroundColor = '#FFA500';
    } else {
        badge.title = 'Add to list';
        badge.innerHTML = '+';
        badge.classList.add('rimdex-mod-default');
        badge.style.backgroundColor = '#2196F3';
    }

    _setBadgeVisibility(badge, tile);
}

function updateAllModBadges() {
    const installedMods = $installed_mods || [];
    const addedMods = $added_mods || [];
    const seenIds = new Set();

    const links = document.querySelectorAll('a[href*="filedetails/?id="]');
    for (const link of links) {
        const title = link.textContent.trim();
        if (!title) continue;

        const match = link.href.match(/id=(\d+)/);
        if (!match) continue;

        const modId = match[1];
        if (seenIds.has(modId)) continue;
        seenIds.add(modId);

        const tile = _findModTile(modId);
        if (!tile || tile.querySelector('.rimdex-modstatus-badge')) continue;

        if (installedMods.includes(modId)) {
            updateModBadge(modId, BadgeState.INSTALLED);
        } else if (addedMods.includes(modId)) {
            updateModBadge(modId, BadgeState.ADDED);
        } else {
            updateModBadge(modId, BadgeState.DEFAULT);
        }
    }
}

let _retryTimers = [];
function _scheduleRetries() {
    [1000, 3000, 5000, 10000].forEach(delay => {
        _retryTimers.push(setTimeout(() => updateAllModBadges(), delay));
    });
}

let _debounceTimer = null;
function _scheduleUpdateAll() {
    if (_debounceTimer) clearTimeout(_debounceTimer);
    _debounceTimer = setTimeout(() => {
        _debounceTimer = null;
        updateAllModBadges();
    }, 200);
}

let _observer = null;
function _setupObserverForBadges() {
    if (_observer) return;
    const target = document.querySelector('#responsive_page_template_content')
        || document.querySelector('.responsive_page_template_content')
        || document.body;
    _observer = new MutationObserver(() => _scheduleUpdateAll());
    _observer.observe(target, { childList: true, subtree: true, attributes: false });
}

if (typeof QWebChannel !== 'undefined') {
    new QWebChannel(qt.webChannelTransport, channel => {
        window.browserBridge = channel.objects.browserBridge;
        console.log("QWebChannel bridge to Python ready!");
        updateAllModBadges();
        _scheduleRetries();
        _setupObserverForBadges();
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

    .rimdex-modstatus-badge:hover {
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
