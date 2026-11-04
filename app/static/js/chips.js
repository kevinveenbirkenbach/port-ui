(function () {
  'use strict';

  if (!document.getElementById('portui-dashboard-data')) {
    return;
  }

  const TONES = new Set(['primary', 'success', 'info', 'warning', 'danger', 'secondary']);
  const KIND = /^[a-z0-9-]+$/;
  const registry = new Map();

  function optionalString(chip, key) {
    if (chip[key] !== undefined && typeof chip[key] !== 'string') {
      throw new TypeError(`portui chip ${key} must be a string`);
    }
  }

  function validate(id, chips) {
    if (typeof id !== 'string' || id === '') {
      throw new TypeError('portui chips need a card id');
    }
    if (!Array.isArray(chips)) {
      throw new TypeError('portui chips must be a list');
    }
    chips.forEach((chip) => {
      if (!chip || typeof chip.kind !== 'string' || !KIND.test(chip.kind)) {
        throw new TypeError('portui chip kind must match [a-z0-9-]+');
      }
      if (!TONES.has(chip.tone)) {
        throw new TypeError(`portui chip tone must be one of ${[...TONES].join(', ')}`);
      }
      if (typeof chip.label !== 'string' || chip.label === '') {
        throw new TypeError('portui chip label must be a non-empty string');
      }
      ['icon', 'detail', 'href', 'state'].forEach((key) => optionalString(chip, key));
      if (chip.newTab !== undefined && typeof chip.newTab !== 'boolean') {
        throw new TypeError('portui chip newTab must be a boolean');
      }
    });
    return chips.map((chip) => ({ ...chip }));
  }

  function element(chip) {
    const href = chip.href === undefined ? null : safeUrl(chip.href);
    const node = document.createElement(href ? 'a' : 'button');
    if (href) {
      node.href = href;
      if (chip.newTab) {
        node.target = '_blank';
        node.rel = 'noopener';
      }
    } else {
      node.type = 'button';
    }
    node.className = `badge rounded-pill text-bg-${chip.tone} portui-chip portui-chip-${chip.kind}`;
    if (chip.state !== undefined) {
      node.dataset.portuiState = chip.state;
    }
    const text = t(chip.label) + (chip.detail === undefined ? '' : chip.detail);
    node.setAttribute('aria-label', text);
    node.title = text;
    if (chip.icon !== undefined) {
      const glyph = document.createElement('i');
      glyph.className = chip.icon;
      glyph.setAttribute('aria-hidden', 'true');
      node.append(glyph);
    }
    return node;
  }

  function render(id) {
    document.querySelectorAll('[data-portui-chips]').forEach((holder) => {
      if (id !== undefined && holder.dataset.portuiChips !== id) {
        return;
      }
      const chips = registry.get(holder.dataset.portuiChips) || [];
      const signature = JSON.stringify(chips);
      if (holder.dataset.portuiChipsDrawn === signature) {
        return;
      }
      holder.querySelectorAll('.portui-chip').forEach((chip) => {
        const tooltip = bootstrap.Tooltip.getInstance(chip);
        if (tooltip) {
          tooltip.dispose();
        }
      });
      holder.replaceChildren(...chips.map(element));
      holder.dataset.portuiChipsDrawn = signature;
    });
  }

  new bootstrap.Tooltip(document.body, { selector: '.portui-chip' });

  window.portuiRefreshChips = render;
  window.portui = window.portui || {};
  window.portui.chips = {
    set(id, chips) {
      registry.set(id, validate(id, chips));
      render(id);
    },
    clear(id) {
      validate(id, []);
      registry.delete(id);
      render(id);
    },
  };
})();
