(function () {
  'use strict';

  const block = document.getElementById('portui-dashboard-data');
  if (!block) {
    return;
  }
  const data = JSON.parse(block.textContent);
  const RECENT_LIMIT = 8;
  const DAY = 86400000;
  const ROW_CLASSES = ['col-12', 'col-md-6', 'col-lg-3'];
  const POSITION = 'portuiPosition';

  function storage(kind) {
    try {
      const store = window[kind];
      store.setItem('portui.probe', '1');
      store.removeItem('portui.probe');
      return store;
    } catch (error) {
      return null;
    }
  }

  const local = storage('localStorage');

  function store(key, value) {
    if (!local) {
      return;
    }
    try {
      local.setItem(key, value);
    } catch (error) {
      return;
    }
  }

  function readList(key) {
    if (!local) {
      return [];
    }
    try {
      const value = JSON.parse(local.getItem(key));
      return Array.isArray(value) ? value.filter((item) => typeof item === 'string') : [];
    } catch (error) {
      return [];
    }
  }

  function writeList(key, list) {
    store(key, JSON.stringify(list));
  }

  let listView = local ? local.getItem('portui.density') === 'list' : false;

  function position() {
    const state = window.history.state;
    return state && typeof state[POSITION] === 'number' ? state[POSITION] : 0;
  }

  // Forward entries are only trusted while this document made them: a reload, a restore from the back-forward cache or a same-tab navigation elsewhere can leave a non-dashboard page after the current entry.
  let newest = 0;

  function remember(value) {
    newest = value;
  }

  window.addEventListener('pageshow', (event) => {
    if (event.persisted) {
      remember(position());
      updateHistoryButtons();
    }
  });

  // Other scripts overwrite history.state wholesale; these wrappers keep the entry position the back and forward buttons rely on.
  const nativePush = window.history.pushState;
  const nativeReplace = window.history.replaceState;
  window.history.pushState = function (state, title, url) {
    const next = position() + 1;
    remember(next);
    nativePush.call(window.history, { ...state, [POSITION]: next }, title, url);
    updateHistoryButtons();
  };
  window.history.replaceState = function (state, title, url) {
    nativeReplace.call(window.history, { ...state, [POSITION]: position() }, title, url);
  };
  if (!(window.history.state && typeof window.history.state[POSITION] === 'number')) {
    window.history.replaceState(window.history.state, '', window.location.href);
  }
  remember(position());

  function root() {
    return document.getElementById('portui-dashboard');
  }

  let liveQuery = null;

  function urlState() {
    const params = new URLSearchParams(window.location.search);
    return { folder: params.get('folder') || '', q: params.get('q') || '' };
  }

  function readState() {
    const state = urlState();
    return liveQuery === null ? state : { folder: state.folder, q: liveQuery };
  }

  function urlFor(folder, q) {
    const url = new URL(window.location.href);
    if (folder) {
      url.searchParams.set('folder', folder);
    } else {
      url.searchParams.delete('folder');
    }
    if (q) {
      url.searchParams.set('q', q);
    } else {
      url.searchParams.delete('q');
    }
    url.search = url.search.replace(/([?&]folder=)([^&]*)/, (_, key, value) => key + value.replace(/%2F/gi, '/'));
    return url;
  }

  function navigate(folder, q) {
    liveQuery = null;
    const current = urlState();
    if (current.folder !== folder || current.q !== q) {
      window.history.pushState(null, '', urlFor(folder, q));
    }
    render();
  }

  function knownFolder(folder) {
    return !folder || Object.hasOwn(data.folders, folder);
  }

  function updateHistoryButtons() {
    const dashboard = root();
    if (!dashboard) {
      return;
    }
    const back = dashboard.querySelector('.portui-back');
    const forward = dashboard.querySelector('.portui-forward');
    if (back) {
      back.disabled = position() <= 0;
    }
    if (forward) {
      forward.disabled = position() >= newest;
    }
  }

  function crumb(label, folder, current) {
    const item = document.createElement('li');
    item.className = 'breadcrumb-item';
    const link = document.createElement('a');
    link.href = urlFor(folder, '').search || window.location.pathname;
    link.dataset.portuiFolderLink = folder;
    if (current) {
      item.classList.add('active');
      link.setAttribute('aria-current', 'page');
    }
    if (!folder) {
      const home = document.createElement('i');
      home.className = 'fa-solid fa-house';
      home.setAttribute('aria-hidden', 'true');
      link.append(home, ` ${label}`);
    } else {
      link.textContent = label;
    }
    item.append(link);
    return item;
  }

  function renderBreadcrumb(dashboard, folder) {
    const list = dashboard.querySelector('.portui-breadcrumb ol');
    if (!list) {
      return;
    }
    const items = [crumb(t('Applications'), '', !folder)];
    if (folder) {
      const segments = folder.split('/');
      segments.forEach((_, depth) => {
        const path = segments.slice(0, depth + 1).join('/');
        items.push(crumb(data.folders[path].name, path, path === folder));
      });
    }
    list.replaceChildren(...items);
  }

  function originals(dashboard) {
    return dashboard.querySelectorAll('.portui-main > [data-portui-card]');
  }

  function cardOf(element) {
    const holder = element.closest('[data-portui-card]');
    return holder ? data.cards[Number(holder.dataset.portuiCard)] : null;
  }

  function cloneRow(dashboard, selector, keys) {
    const section = dashboard.querySelector(selector);
    const grid = section.querySelector('.portui-grid');
    const clones = [];
    keys.forEach((key) => {
      const position = data.cards.findIndex((card) => card.key === key);
      const original = dashboard.querySelector(`.portui-main > [data-portui-card="${position}"]`);
      if (position < 0 || !original) {
        return;
      }
      const clone = original.cloneNode(true);
      clone.hidden = false;
      clone.style.order = '';
      clone.className = clone.className
        .split(/\s+/)
        .filter((name) => !/^col-/.test(name))
        .concat(ROW_CLASSES)
        .join(' ');
      clones.push(clone);
    });
    grid.replaceChildren(...clones);
    return clones.length;
  }

  function isNew(card, now) {
    if (!card.added || !data.new_days) {
      return false;
    }
    const added = Date.parse(`${card.added}T00:00:00Z`);
    return now >= added && now - added < data.new_days * DAY;
  }

  function decorate(dashboard, favourites) {
    const now = Date.now();
    dashboard.querySelectorAll('[data-portui-card]').forEach((holder) => {
      const card = data.cards[Number(holder.dataset.portuiCard)];
      const badge = holder.querySelector('.portui-new');
      if (badge) {
        badge.hidden = !isNew(card, now);
      }
      const star = holder.querySelector('.portui-star');
      if (star) {
        const pinned = favourites.includes(card.key);
        star.hidden = !local;
        star.setAttribute('aria-pressed', pinned ? 'true' : 'false');
        star.querySelector('i').className = `${pinned ? 'fa-solid' : 'fa-regular'} fa-star`;
      }
    });
  }

  function render() {
    const dashboard = root();
    if (!dashboard) {
      return;
    }
    let { folder, q } = readState();
    if (!knownFolder(folder)) {
      folder = '';
      window.history.replaceState(window.history.state, '', urlFor('', urlState().q));
    }
    const searching = q.trim() !== '';
    const hits = searching ? window.portuiSearch(q) : [];
    const rankOf = new Map(hits.map((hit, rank) => [hit, rank]));

    dashboard.querySelectorAll('.portui-main > [data-portui-folder]').forEach((tile) => {
      const path = tile.dataset.portuiFolder;
      tile.hidden = searching || data.folders[path].parent !== folder;
    });
    originals(dashboard).forEach((tile) => {
      const position = Number(tile.dataset.portuiCard);
      const card = data.cards[position];
      if (searching) {
        tile.hidden = !rankOf.has(position);
        tile.style.order = rankOf.has(position) ? String(rankOf.get(position)) : '';
      } else {
        tile.style.order = '';
        tile.hidden = data.folder_view && (folder ? !card.folders.includes(folder) : card.folders.length > 0);
      }
    });

    const atTop = !folder && !searching;
    const favourites = readList('portui.favourites');
    const recent = readList('portui.recent');
    dashboard.querySelector('.portui-favourites').hidden =
      !atTop || cloneRow(dashboard, '.portui-favourites', favourites) === 0;
    dashboard.querySelector('.portui-recent').hidden =
      !atTop || cloneRow(dashboard, '.portui-recent', recent) === 0;
    dashboard.querySelector('.portui-empty').hidden = !searching || hits.length > 0;

    dashboard.classList.toggle('portui-list', listView);
    dashboard.querySelector('.portui-density').setAttribute('aria-pressed', listView ? 'true' : 'false');

    decorate(dashboard, favourites);
    renderBreadcrumb(dashboard, folder);
    updateHistoryButtons();
    if (window.portuiSearchField) {
      window.portuiSearchField.set(q);
      if (searching) {
        window.portuiSearchField.announce(hits.length);
      }
    }
    if (window.portuiRefreshChips) {
      window.portuiRefreshChips();
    }
    if (window.portuiFrameUpdate) {
      window.portuiFrameUpdate();
    }
  }

  function toggleFavourite(card) {
    const favourites = readList('portui.favourites');
    const next = favourites.includes(card.key)
      ? favourites.filter((key) => key !== card.key)
      : [...favourites, card.key];
    writeList('portui.favourites', next);
    render();
  }

  function recordRecent(card) {
    if (!card.key) {
      return;
    }
    const recent = readList('portui.recent').filter((key) => key !== card.key);
    writeList('portui.recent', [card.key, ...recent].slice(0, RECENT_LIMIT));
  }

  document.addEventListener('click', (event) => {
    const target = event.target;
    const folderLink = target.closest('[data-portui-folder-link]');
    if (folderLink && root() && root().contains(folderLink)) {
      if (event.ctrlKey || event.metaKey || event.shiftKey || event.button !== 0) {
        return;
      }
      event.preventDefault();
      navigate(folderLink.dataset.portuiFolderLink, '');
      return;
    }
    if (target.closest('.portui-star')) {
      event.preventDefault();
      const card = cardOf(target);
      if (card) {
        toggleFavourite(card);
      }
      return;
    }
    if (target.closest('.portui-recent-clear')) {
      writeList('portui.recent', []);
      render();
      return;
    }
    if (target.closest('.portui-density')) {
      listView = !listView;
      store('portui.density', listView ? 'list' : 'tiles');
      render();
      return;
    }
    if (target.closest('.portui-back')) {
      window.history.back();
      return;
    }
    if (target.closest('.portui-forward')) {
      window.history.forward();
      return;
    }
    const open = target.closest('[data-portui-card] a.stretched-link');
    if (open) {
      const card = cardOf(open);
      if (card) {
        recordRecent(card);
      }
    }
  });

  window.addEventListener('popstate', () => {
    liveQuery = null;
    render();
  });

  document.addEventListener('portui:restored', render);

  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches && window.jQuery) {
    window.jQuery.fx.off = true;
  }

  window.portuiDashboard = {
    render,
    previewQuery(value) {
      liveQuery = value;
      render();
    },
    commitQuery(value) {
      navigate(urlState().folder, value.trim() ? value : '');
    },
    openParent() {
      const { folder } = urlState();
      if (folder && knownFolder(folder)) {
        navigate(data.folders[folder].parent, '');
      }
    },
  };

  render();
  document.dispatchEvent(new CustomEvent('portui:ready'));
})();
