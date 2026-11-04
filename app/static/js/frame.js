(function () {
  'use strict';

  const top = document.querySelector('.portui-frame-top');
  const bottom = document.querySelector('.portui-frame-bottom');
  if (!top || !bottom) {
    return;
  }
  let pending = false;

  function cardRects() {
    const rects = [];
    document.querySelectorAll('#main .card').forEach((card) => {
      const rect = card.getBoundingClientRect();
      if (rect.width > 0 && rect.height > 0) {
        rects.push(rect);
      }
    });
    return rects;
  }

  function gapBelow(rects, edge, from, to, radius) {
    return rects.reduce((gap, rect) => {
      if (rect.right <= from || rect.left >= to || rect.bottom <= edge) {
        return gap;
      }
      return Math.min(gap, Math.max(0, rect.top - edge));
    }, radius);
  }

  function gapAbove(rects, edge, from, to, radius) {
    return rects.reduce((gap, rect) => {
      if (rect.right <= from || rect.left >= to || rect.top >= edge) {
        return gap;
      }
      return Math.min(gap, Math.max(0, edge - rect.bottom));
    }, radius);
  }

  function corner(box, side, value) {
    box.style.setProperty(`--portui-corner-${side}`, `${Math.round(value)}px`);
  }

  function update() {
    pending = false;
    const radius = parseFloat(getComputedStyle(top).getPropertyValue('--portui-frame-radius'));
    if (Number.isNaN(radius)) {
      return;
    }
    const rects = cardRects();
    const head = top.getBoundingClientRect();
    const foot = bottom.getBoundingClientRect();
    corner(top, 'left', gapBelow(rects, head.bottom, head.left, head.left + radius, radius));
    corner(top, 'right', gapBelow(rects, head.bottom, head.right - radius, head.right, radius));
    corner(bottom, 'left', gapAbove(rects, foot.top, foot.left, foot.left + radius, radius));
    corner(bottom, 'right', gapAbove(rects, foot.top, foot.right - radius, foot.right, radius));
  }

  function schedule() {
    if (pending) {
      return;
    }
    pending = true;
    window.requestAnimationFrame(update);
  }

  document.addEventListener('scroll', schedule, { capture: true, passive: true });
  window.addEventListener('resize', schedule);
  window.addEventListener('load', schedule);
  window.portuiFrameUpdate = schedule;
  schedule();
})();
