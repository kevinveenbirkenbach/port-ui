(function () {
  'use strict';

  const block = document.getElementById('portui-dashboard-data');
  if (!block) {
    return;
  }
  const data = JSON.parse(block.textContent);
  const PICKER_ROWS = 8;
  const FUZZY_MIN_LENGTH = 5;

  function fold(text) {
    return String(text || '').normalize('NFD').replace(/\p{M}/gu, '').toLowerCase();
  }

  function words(text) {
    return fold(text).split(/[^\p{L}\p{N}]+/u).filter(Boolean);
  }

  const index = data.cards.map((card, position) => ({
    position,
    titles: [fold(card.title), fold(card.title_en)],
    titleWords: [...words(card.title), ...words(card.title_en)],
    haystack: card.search.map(fold).join('\n'),
    words: [...new Set(card.search.flatMap(words))],
  }));

  function withinOneEdit(a, b) {
    if (a === b) {
      return true;
    }
    if (Math.abs(a.length - b.length) > 1) {
      return false;
    }
    let i = 0;
    while (i < a.length && i < b.length && a[i] === b[i]) {
      i += 1;
    }
    if (a.length === b.length) {
      return (
        a.slice(i + 1) === b.slice(i + 1) ||
        (a[i] === b[i + 1] && a[i + 1] === b[i] && a.slice(i + 2) === b.slice(i + 2))
      );
    }
    return a.length > b.length ? a.slice(i + 1) === b.slice(i) : a.slice(i) === b.slice(i + 1);
  }

  function fuzzy(token, entry) {
    if (token.length < FUZZY_MIN_LENGTH) {
      return false;
    }
    return entry.words.some(
      (word) =>
        withinOneEdit(token, word) ||
        [token.length - 1, token.length, token.length + 1].some(
          (length) => length < word.length && withinOneEdit(token, word.slice(0, length)),
        ),
    );
  }

  function rank(entry, query, tokens) {
    let typo = false;
    for (const token of tokens) {
      if (entry.haystack.includes(token)) {
        continue;
      }
      if (!fuzzy(token, entry)) {
        return null;
      }
      typo = true;
    }
    if (entry.titles.some((title) => title.startsWith(query))) {
      return 0;
    }
    if (entry.titleWords.some((word) => word.startsWith(tokens[0]))) {
      return 1;
    }
    return typo ? 3 : 2;
  }

  function search(query) {
    const folded = fold(query).trim();
    const tokens = folded.split(/\s+/).filter(Boolean);
    if (tokens.length === 0) {
      return [];
    }
    return index
      .map((entry) => ({ entry, score: rank(entry, folded, tokens) }))
      .filter((hit) => hit.score !== null)
      .sort(
        (left, right) =>
          left.score - right.score || left.entry.titles[0].localeCompare(right.entry.titles[0]),
      )
      .map((hit) => hit.entry.position);
  }

  window.portuiSearch = search;

  const field = document.getElementById('portui-search');
  const picker = document.getElementById('portui-picker');
  const live = document.getElementById('portui-live');
  if (!field || !picker) {
    return;
  }

  let hits = [];
  let selected = -1;

  function folderPath(card) {
    if (!card.folders.length) {
      return '';
    }
    const segments = card.folders[0].split('/');
    return segments
      .map((_, depth) => data.folders[segments.slice(0, depth + 1).join('/')])
      .filter(Boolean)
      .map((folder) => folder.name)
      .join(' › ');
  }

  function tileOf(position) {
    return document.querySelector(`.portui-main > [data-portui-card="${position}"]`);
  }

  function row(position, rowIndex) {
    const card = data.cards[position];
    const item = document.createElement('li');
    item.id = `portui-hit-${rowIndex}`;
    item.className = 'dropdown-item portui-hit';
    item.setAttribute('role', 'option');
    item.setAttribute('aria-selected', 'false');
    item.dataset.portuiHit = String(position);

    const iconHolder = document.createElement('span');
    iconHolder.className = 'portui-hit-icon';
    const tile = tileOf(position);
    const tileIcon = tile ? tile.querySelector('.card-img-top') : null;
    if (tileIcon) {
      iconHolder.innerHTML = tileIcon.innerHTML;
      iconHolder.querySelectorAll('[id]').forEach((node) => node.removeAttribute('id'));
    }

    const text = document.createElement('span');
    text.className = 'portui-hit-text';
    const title = document.createElement('span');
    title.className = 'portui-hit-title';
    title.textContent = card.title;
    const path = document.createElement('span');
    path.className = 'portui-hit-path';
    path.textContent = folderPath(card);
    text.append(title, path);

    item.append(iconHolder, text);
    if (card.key) {
      const chips = document.createElement('span');
      chips.className = 'portui-chips';
      chips.dataset.portuiChips = card.key;
      item.append(chips);
    }
    return item;
  }

  function announce(count) {
    if (live) {
      live.textContent = count ? `${t('Results')}: ${count}` : t('No applications found');
    }
  }

  function select(next) {
    const rows = picker.querySelectorAll('[role="option"]');
    selected = rows.length ? (next + rows.length) % rows.length : -1;
    rows.forEach((item, position) => {
      const active = position === selected;
      item.setAttribute('aria-selected', active ? 'true' : 'false');
      item.classList.toggle('active', active);
      if (active) {
        item.scrollIntoView({ block: 'nearest' });
      }
    });
    if (selected >= 0) {
      field.setAttribute('aria-activedescendant', rows[selected].id);
    } else {
      field.removeAttribute('aria-activedescendant');
    }
  }

  function open() {
    picker.hidden = false;
    field.setAttribute('aria-expanded', 'true');
    picker.parentElement.classList.add('portui-search-open');
  }

  function close() {
    picker.hidden = true;
    field.setAttribute('aria-expanded', 'false');
    picker.parentElement.classList.remove('portui-search-open');
    field.removeAttribute('aria-activedescendant');
    selected = -1;
  }

  function fill() {
    const query = field.value.trim();
    if (!query) {
      hits = [];
      picker.replaceChildren();
      close();
      if (live) {
        live.textContent = '';
      }
      return;
    }
    hits = search(query);
    if (hits.length === 0) {
      const empty = document.createElement('li');
      empty.className = 'dropdown-item-text portui-no-hits';
      empty.textContent = t('No applications found');
      picker.replaceChildren(empty);
    } else {
      picker.replaceChildren(...hits.slice(0, PICKER_ROWS).map(row));
    }
    if (window.portuiRefreshChips) {
      window.portuiRefreshChips();
    }
    open();
    select(hits.length ? 0 : -1);
    announce(hits.length);
  }

  function launch(position) {
    const tile = tileOf(position);
    const link = tile ? tile.querySelector('a.stretched-link') : null;
    close();
    field.blur();
    if (window.portuiDashboard) {
      window.portuiDashboard.commitQuery(field.value);
    }
    if (link) {
      link.click();
    }
  }

  field.addEventListener('input', () => {
    fill();
    if (window.portuiDashboard) {
      window.portuiDashboard.previewQuery(field.value);
    }
  });

  field.addEventListener('focus', () => {
    if (field.value.trim()) {
      fill();
    }
  });

  field.addEventListener('change', () => {
    if (window.portuiDashboard) {
      window.portuiDashboard.commitQuery(field.value);
    }
  });

  field.addEventListener('keydown', (event) => {
    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      event.preventDefault();
      if (picker.hidden) {
        fill();
      }
      select(selected + (event.key === 'ArrowDown' ? 1 : -1));
    } else if (event.key === 'Enter') {
      event.preventDefault();
      if (!picker.hidden && selected >= 0) {
        launch(hits[selected]);
      } else if (window.portuiDashboard) {
        window.portuiDashboard.commitQuery(field.value);
      }
    } else if (event.key === 'Escape') {
      event.preventDefault();
      if (!picker.hidden) {
        close();
      } else if (field.value) {
        field.value = '';
        fill();
        if (window.portuiDashboard) {
          window.portuiDashboard.commitQuery('');
        }
      }
    } else if (event.key === 'Backspace' && field.value === '' && window.portuiDashboard) {
      event.preventDefault();
      window.portuiDashboard.openParent();
    }
  });

  picker.addEventListener('mousedown', (event) => {
    event.preventDefault();
  });

  picker.addEventListener('click', (event) => {
    if (event.target.closest('.portui-chip')) {
      return;
    }
    const item = event.target.closest('[data-portui-hit]');
    if (item) {
      launch(Number(item.dataset.portuiHit));
    }
  });

  field.addEventListener('blur', close);

  document.addEventListener('keydown', (event) => {
    const target = event.target;
    const typing =
      target instanceof HTMLElement &&
      (target.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName));
    const shortcut = event.key === '/' || ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k');
    if (shortcut && !typing) {
      event.preventDefault();
      field.focus();
      field.select();
    }
  });

  window.portuiSearchField = {
    set(value) {
      if (field.value !== value) {
        field.value = value;
      }
      if (document.activeElement !== field) {
        close();
      }
    },
    announce,
  };
})();
