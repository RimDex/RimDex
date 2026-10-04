const BadgeState = @badge_state_js@;
const PAGE_MODE = '@page_mode@';
const INJECT_DELAY_MS = @inject_delay_ms@;

const TILE_SELECTORS = ['.workshopItem', '[data-publishedfileid]'];

window._rimdexInstalledMods = @installed_mods@;
window._rimdexAddedMods = @added_mods@;
window._rimdexInstalledSet = new Set(window._rimdexInstalledMods);
window._rimdexAddedSet = new Set(window._rimdexAddedMods);

function _ancestorTileFromLink(link) {
    let el = link.parentElement;
    while (el && el !== document.body && el !== document.documentElement) {
        const filedetailsLinks = el.querySelectorAll('a[href*="filedetails/"]');
        const hasTitleLink = Array.from(filedetailsLinks).some(l => l.textContent.trim());
        const hasThumbImg = el.querySelector('a[href*="filedetails/"] img');
        if (hasTitleLink && hasThumbImg) return el;
        el = el.parentElement;
    }
    return null;
}

function _findModTile(modId) {
    const links = document.querySelectorAll('a[href*="filedetails/?id=' + modId + '"]');
    if (links.length === 0) return null;

    for (const selector of TILE_SELECTORS) {
        const tiles = document.querySelectorAll(selector);
        for (const tile of tiles) {
            if (tile.querySelector('a[href*="id=' + modId + '"]')) return tile;
        }
    }

    for (const link of links) {
        const collectionItem = link.closest('.collectionItem');
        if (collectionItem) return collectionItem;
    }

    for (const link of links) {
        const tile = _ancestorTileFromLink(link);
        if (tile) return tile;
    }
    return null;
}

function _getModTitle(tile, modId) {
    if (!tile) return modId;
    const legacyTitle = tile.querySelector('.workshopItemTitle');
    if (legacyTitle && legacyTitle.textContent.trim()) {
        return legacyTitle.textContent.trim();
    }
    const links = tile.querySelectorAll('a[href*="filedetails/"]');
    for (const link of links) {
        const text = link.textContent.trim();
        if (text) return text;
    }
    const img = tile.querySelector('img[alt]');
    if (img && img.alt) return img.alt;
    return modId;
}

function _recordModStatus(modId, status) {
    if (status === BadgeState.INSTALLED) {
        window._rimdexInstalledSet.add(modId);
        window._rimdexAddedSet.delete(modId);
    } else if (status === BadgeState.ADDED) {
        window._rimdexAddedSet.add(modId);
    } else {
        window._rimdexAddedSet.delete(modId);
    }
}

function _modStatus(modId) {
    if (window._rimdexInstalledSet.has(modId)) return BadgeState.INSTALLED;
    if (window._rimdexAddedSet.has(modId)) return BadgeState.ADDED;
    return BadgeState.DEFAULT;
}

function _setBadgeVisibility(badge, tile) {
    if (!badge.classList.contains('rimdex-mod-default')) {
        badge.style.opacity = '1';
        badge.style.visibility = 'visible';
        return;
    }
    const visible = PAGE_MODE === 'browse' || tile.classList.contains('rimdex-tile-hovered');
    badge.style.opacity = visible ? '1' : '0';
    badge.style.visibility = visible ? 'visible' : 'hidden';
}

function _createBadge(modId, tile) {
    const badge = document.createElement('div');
    badge.className = 'rimdex-modstatus-badge';
    const modTitleText = _getModTitle(tile, modId);

    tile.addEventListener('mouseenter', function() {
        tile.classList.add('rimdex-tile-hovered');
        if (badge.classList.contains('rimdex-mod-default')) {
            badge.style.opacity = '1';
            badge.style.visibility = 'visible';
        }
    });
    tile.addEventListener('mouseleave', function() {
        tile.classList.remove('rimdex-tile-hovered');
        if (badge.classList.contains('rimdex-mod-default')) {
            badge.style.opacity = '0';
            badge.style.visibility = 'hidden';
        }
    });

    badge.addEventListener('click', function() {
        if (!window.browserBridge) return;
        badge.classList.add('pressed');
        setTimeout(function() { badge.classList.remove('pressed'); }, 150);

        if (badge.classList.contains('rimdex-mod-default')) {
            _recordModStatus(modId, BadgeState.ADDED);
            window.browserBridge.add_mod_from_js(modId, modTitleText);
        } else if (badge.classList.contains('rimdex-mod-added')) {
            _recordModStatus(modId, BadgeState.DEFAULT);
            window.browserBridge.remove_mod_from_js(modId);
        }
    });

    tile.style.position = 'relative';
    tile.appendChild(badge);
    return badge;
}

function updateModBadge(modId, status) {
    if (PAGE_MODE === 'hub') {
        window.rimdexUpdateHubAddButton(modId, status);
        return;
    }

    _recordModStatus(modId, status);

    const tile = _findModTile(modId);
    if (!tile) {
        console.log('Mod tile for ' + modId + ' not found.');
        return;
    }

    let badge = tile.querySelector('.rimdex-modstatus-badge');
    if (!badge) {
        badge = _createBadge(modId, tile);
    } else {
        badge.classList.remove('rimdex-mod-installed', 'rimdex-mod-added', 'rimdex-mod-default');
    }

    if (status === BadgeState.INSTALLED) {
        badge.title = 'Already installed';
        badge.innerHTML = '✓';
        badge.classList.add('rimdex-mod-installed');
        badge.style.backgroundColor = '#4CAF50';
    } else if (status === BadgeState.ADDED) {
        badge.title = 'Preparing to download';
        badge.innerHTML = '-';
        badge.classList.add('rimdex-mod-added');
        badge.style.backgroundColor = '#FFA500';
    } else {
        badge.title = 'Add to list';
        badge.innerHTML = 'Add to list';
        badge.classList.add('rimdex-mod-default');
        badge.style.backgroundColor = '#2196F3';
    }

    _setBadgeVisibility(badge, tile);
}

function _collectModIds() {
    const modIds = [];
    const seen = new Set();
    const collect = function(modId) {
        if (!modId || seen.has(modId)) return;
        seen.add(modId);
        modIds.push(modId);
    };

    document.querySelectorAll('a[href*="filedetails/?id="]').forEach(function(link) {
        const match = link.href.match(/id=(\d+)/);
        if (match) collect(match[1]);
    });
    TILE_SELECTORS.forEach(function(selector) {
        document.querySelectorAll(selector).forEach(function(tile) {
            const link = tile.querySelector('a[href*="id="]');
            if (!link) return;
            const match = link.href.match(/id=(\d+)/);
            if (match) collect(match[1]);
        });
    });
    return modIds;
}

function updateAllModBadges() {
    if (PAGE_MODE !== 'browse') return;
    if (window._rimdexUpdatingBadges) return;
    window._rimdexUpdatingBadges = true;
    try {
        _collectModIds().forEach(function(modId) {
            updateModBadge(modId, _modStatus(modId));
        });
    } finally {
        window._rimdexUpdatingBadges = false;
    }
}

function rimdexFindQuickViewButtons() {
    return [...document.querySelectorAll(
        'div.Panel[role="button"] svg.SVGIcon_MagnifyingGlass'
    )].map(function(svg) {
        return svg.closest('div.Panel[role="button"]');
    }).filter(Boolean);
}

function rimdexHubCardRoot(el) {
    let current = el;
    for (let depth = 0; depth < 12 && current; depth++) {
        if (current.querySelector('a[href*="filedetails/?id="]')) return current;
        current = current.parentElement;
    }
    return null;
}

function rimdexModIdFromHubCard(quickViewEl) {
    let el = quickViewEl;
    for (let depth = 0; depth < 12 && el; depth++) {
        const link = el.querySelector('a[href*="filedetails/?id="]');
        if (link) {
            const match = link.href.match(/id=(\d+)/);
            if (match) return match[1];
        }
        el = el.parentElement;
    }
    return null;
}

function rimdexModTitleFromHubCard(quickViewEl, modId) {
    let el = quickViewEl;
    for (let depth = 0; depth < 12 && el; depth++) {
        const link = el.querySelector('a[href*="filedetails/?id="]');
        if (link) return link.getAttribute('title') || link.textContent.trim() || modId;
        el = el.parentElement;
    }
    return modId;
}

function rimdexApplyHubButtonState(btn, status) {
    btn.classList.remove('rimdex-hub-installed', 'rimdex-hub-added', 'rimdex-hub-default');
    if (status === BadgeState.INSTALLED) {
        btn.classList.add('rimdex-hub-installed');
        btn.title = 'Already installed';
        btn.textContent = '✓';
    } else if (status === BadgeState.ADDED) {
        btn.classList.add('rimdex-hub-added');
        btn.title = 'Preparing to download';
        btn.textContent = '-';
    } else {
        btn.classList.add('rimdex-hub-default');
        btn.title = 'Add to list';
        btn.textContent = 'Add to list';
    }
}

function rimdexFindHubAddButtonByModId(modId) {
    return document.querySelector('.rimdex-hub-add-btn[data-mod-id="' + modId + '"]');
}

function rimdexCleanupHubLegacyBadges(card) {
    if (!card) return;
    card.querySelectorAll('.rimdex-modstatus-badge').forEach(function(badge) {
        badge.remove();
    });
}

function rimdexCreateHubAddButton(modId, status, modTitleText) {
    const btn = document.createElement('div');
    btn.className = 'rimdex-hub-add-btn Panel';
    btn.setAttribute('role', 'button');
    btn.tabIndex = 0;
    btn.dataset.modId = modId;
    rimdexApplyHubButtonState(btn, status);

    btn.addEventListener('click', function() {
        if (!window.browserBridge) return;
        btn.classList.add('pressed');
        setTimeout(function() { btn.classList.remove('pressed'); }, 150);

        if (btn.classList.contains('rimdex-hub-default')) {
            _recordModStatus(modId, BadgeState.ADDED);
            rimdexApplyHubButtonState(btn, BadgeState.ADDED);
            window.browserBridge.add_mod_from_js(modId, modTitleText);
        } else if (btn.classList.contains('rimdex-hub-added')) {
            _recordModStatus(modId, BadgeState.DEFAULT);
            rimdexApplyHubButtonState(btn, BadgeState.DEFAULT);
            window.browserBridge.remove_mod_from_js(modId);
        }
    });

    return btn;
}

function rimdexInjectHubAddButtons() {
    for (const quickViewEl of rimdexFindQuickViewButtons()) {
        const modId = rimdexModIdFromHubCard(quickViewEl);
        if (!modId) continue;

        const card = rimdexHubCardRoot(quickViewEl);
        rimdexCleanupHubLegacyBadges(card);

        const status = _modStatus(modId);
        const existingBtn = card
            ? card.querySelector('.rimdex-hub-add-btn[data-mod-id="' + modId + '"]')
            : null;
        if (existingBtn) {
            rimdexApplyHubButtonState(existingBtn, status);
            continue;
        }

        quickViewEl.insertAdjacentElement(
            'afterend',
            rimdexCreateHubAddButton(modId, status, rimdexModTitleFromHubCard(quickViewEl, modId))
        );
    }
}
window.rimdexInjectHubAddButtons = rimdexInjectHubAddButtons;

function rimdexUpdateHubAddButton(modId, status) {
    _recordModStatus(modId, status);

    const existingBtn = rimdexFindHubAddButtonByModId(modId);
    if (existingBtn) {
        rimdexApplyHubButtonState(existingBtn, status);
        rimdexCleanupHubLegacyBadges(rimdexHubCardRoot(existingBtn));
        return;
    }
    window.rimdexInjectHubAddButtons();
}
window.rimdexUpdateHubAddButton = rimdexUpdateHubAddButton;

function rimdexFindBadgeObserverRoot() {
    return document.querySelector('.workshopBrowseRow')
        || document.querySelector('.workshopBrowseItems')
        || document.querySelector('#BrowseResultContainer')
        || document.querySelector('main')
        || document.body
        || null;
}

function rimdexMutationIsOurs(mutation) {
    const target = mutation.target;
    if (target instanceof Element && target.closest('.rimdex-modstatus-badge, .rimdex-hub-add-btn')) {
        return true;
    }
    for (const node of mutation.addedNodes) {
        if (!(node instanceof Element)) continue;
        if (
            node.classList.contains('rimdex-modstatus-badge')
            || node.classList.contains('rimdex-hub-add-btn')
            || node.querySelector('.rimdex-modstatus-badge, .rimdex-hub-add-btn')
        ) {
            return true;
        }
    }
    return false;
}

function rimdexSetupPageObserver(callback) {
    if (window._rimdexObserver) return;
    const root = rimdexFindBadgeObserverRoot();
    if (!root) return;

    let observerDebounce = null;
    window._rimdexObserver = new MutationObserver(function(mutations) {
        if (window._rimdexUpdatingBadges) return;
        if (mutations.every(rimdexMutationIsOurs)) return;
        if (observerDebounce) clearTimeout(observerDebounce);
        observerDebounce = setTimeout(callback, 500);
    });
    window._rimdexObserver.observe(root, { childList: true, subtree: true });
}

function rimdexInstallHistoryUrlSync() {
    if (window._rimdexHistoryUrlSync) return;
    window._rimdexHistoryUrlSync = true;

    const notify = function() {
        if (!window.browserBridge || typeof window.browserBridge.on_url_changed !== 'function') {
            return;
        }
        window.browserBridge.on_url_changed(window.location.href);
    };

    const wrapHistory = function(methodName) {
        const original = history[methodName];
        if (typeof original !== 'function') return;
        history[methodName] = function() {
            const result = original.apply(this, arguments);
            notify();
            return result;
        };
    };

    wrapHistory('pushState');
    wrapHistory('replaceState');
    window.addEventListener('popstate', notify);
    notify();
}

function _refreshForPageMode() {
    if (PAGE_MODE === 'browse') {
        document.body.classList.add('rimdex-grid-page');
        updateAllModBadges();
        rimdexSetupPageObserver(updateAllModBadges);
    } else if (PAGE_MODE === 'hub') {
        rimdexInjectHubAddButtons();
        rimdexSetupPageObserver(rimdexInjectHubAddButtons);
    }
}

function _setupBridge() {
    if (window._rimdexBridgeReady) {
        rimdexInstallHistoryUrlSync();
        _refreshForPageMode();
        return;
    }
    new QWebChannel(qt.webChannelTransport, function(channel) {
        window.browserBridge = channel.objects.browserBridge;
        window._rimdexBridgeReady = true;
        console.log("QWebChannel bridge to Python ready!");
        rimdexInstallHistoryUrlSync();
        _refreshForPageMode();
    });
}

function _scheduleWorkshopSetup() {
    const run = function() {
        if (PAGE_MODE !== 'other') {
            if (typeof QWebChannel !== 'undefined' && typeof qt !== 'undefined' && qt.webChannelTransport) {
                _setupBridge();
            } else {
                _refreshForPageMode();
            }
        }
    };
    if (document.readyState === 'complete') {
        setTimeout(run, INJECT_DELAY_MS);
    } else {
        window.addEventListener('load', function() {
            setTimeout(run, INJECT_DELAY_MS);
        }, { once: true });
    }
}

_scheduleWorkshopSetup();

if (!document.getElementById('rimdex-workshop-badge-style')) {
    const style = document.createElement('style');
    style.id = 'rimdex-workshop-badge-style';
    style.textContent = `
    .rimdex-modstatus-badge {
        position: absolute;
        top: 5px;
        right: 5px;
        color: white;
        width: auto;
        min-width: 32px;
        height: 32px;
        padding: 0 8px;
        border-radius: 6px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 12px;
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

    body.rimdex-grid-page .rimdex-mod-default {
        opacity: 1;
        visibility: visible;
    }

    .rimdex-hub-add-btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 32px;
        height: 32px;
        padding: 0 10px;
        margin-left: 6px;
        margin-right: 6px;
        margin-bottom: 6px;
        border-radius: 6px;
        color: white;
        font-weight: bold;
        font-size: 12px;
        box-shadow: 0 0 4px black;
        user-select: none;
        cursor: default;
        transition: transform 0.1s ease, box-shadow 0.1s ease;
    }

    .rimdex-hub-add-btn.rimdex-hub-default,
    .rimdex-hub-add-btn.rimdex-hub-added {
        cursor: pointer;
    }

    .rimdex-hub-add-btn.rimdex-hub-installed {
        background-color: #4CAF50;
    }

    .rimdex-hub-add-btn.rimdex-hub-added {
        background-color: #FFA500;
    }

    .rimdex-hub-add-btn.rimdex-hub-default {
        background-color: #2196F3;
    }

    .rimdex-hub-add-btn.pressed {
        transform: scale(0.9);
    }
`;
    document.head.appendChild(style);
}