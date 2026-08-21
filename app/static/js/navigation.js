document.addEventListener('DOMContentLoaded', () => {
  function getDirectChildByClass(item, className) {
    return Array.from(item.children).find(child => child.classList?.contains(className));
  }

  function getMenu(item) {
    return getDirectChildByClass(item, 'dropdown-menu');
  }

  function getToggle(item) {
    return getDirectChildByClass(item, 'dropdown-toggle');
  }

  function isTopLevelDropdown(item) {
    return (
      item.classList.contains('nav-item') &&
      (item.classList.contains('dropdown') || item.classList.contains('dropup'))
    );
  }

  function chooseDirection(item) {
    const rect = item.getBoundingClientRect();
    const spaceAbove = rect.top;
    const spaceBelow = window.innerHeight - rect.bottom;
    if (spaceAbove > spaceBelow) {
      item.classList.add('dropup');
      item.classList.remove('dropdown');
    } else {
      item.classList.add('dropdown');
      item.classList.remove('dropup');
    }
  }

  function ensureDropdownInstances(root = document) {
    const scope = root && root.querySelectorAll ? root : document;
    scope
      .querySelectorAll('.nav-item.dropdown > .dropdown-toggle, .nav-item.dropup > .dropdown-toggle')
      .forEach(toggle => {
        toggle.setAttribute('data-bs-toggle', 'dropdown');
        if (!toggle.hasAttribute('aria-expanded')) {
          toggle.setAttribute('aria-expanded', 'false');
        }
        if (window.bootstrap?.Dropdown) {
          // Use Popper strategy: 'fixed' so the menu is positioned relative
          // to the viewport and escapes ancestors with overflow:hidden
          // (e.g. <header> which clips for the fullscreen-collapse animation).
          window.bootstrap.Dropdown.getInstance(toggle)?.dispose();
          new window.bootstrap.Dropdown(toggle, {
            popperConfig(defaultBsPopperConfig) {
              return { ...defaultBsPopperConfig, strategy: 'fixed' };
            },
          });
        }
      });
  }

  function addMenuEventListeners(items, isTopLevel) {
    items.forEach(item => {
      let timeout;

      function onMouseEnter() {
        clearTimeout(timeout);
        openMenu(item, isTopLevel, 'hover');
      }

      function onMouseLeave() {
        timeout = setTimeout(() => {
          closeMenu(item);
        }, 500);
      }

      // Open on hover
      item.addEventListener('mouseenter', onMouseEnter);

      // Delayed close on mouse leave
      item.addEventListener('mouseleave', onMouseLeave);

      // Open and adjust position on click
      item.addEventListener('click', (e) => {
        const toggle = getToggle(item);
        const clickedToggle = toggle && (e.target === toggle || toggle.contains(e.target));

        if (isTopLevel && !clickedToggle) {
          e.stopPropagation();
          return;
        }

        e.stopPropagation(); // Prevents menus from closing when clicking inside
        if (isTopLevel) {
          e.preventDefault();
          if (window.bootstrap?.Dropdown) {
            if (item.dataset.openedBy === 'click') {
              closeMenu(item);
            } else if (getMenu(item)) {
              item.dataset.openedBy = 'click';
              item.classList.add('open');
              chooseDirection(item);
              window.bootstrap.Dropdown.getOrCreateInstance(toggle).show();
            }
            return;
          }
        }
        if (item.classList.contains('open')) {
          closeMenu(item);
        } else {
          openMenu(item, isTopLevel);
        }
      });
    });
  }

  const TOP_LEVEL_SELECTOR = '.nav-item.dropdown, .nav-item.dropup';

  function addAllMenuEventListeners() {
    const updatedMenuItems = document.querySelectorAll(TOP_LEVEL_SELECTOR);
    const updatedSubMenuItems = document.querySelectorAll('.dropdown-submenu');
    addMenuEventListeners(updatedMenuItems, true);
    addMenuEventListeners(updatedSubMenuItems, false);
  }

  ensureDropdownInstances();
  addAllMenuEventListeners();

  // Global click listener to close menus when clicking outside
  document.addEventListener('click', () => {
    const menuItems = document.querySelectorAll(TOP_LEVEL_SELECTOR);
    const subMenuItems = document.querySelectorAll('.dropdown-submenu');
    [...menuItems, ...subMenuItems].forEach(item => closeMenu(item));
  });

  function openMenu(item, isTopLevel, openedBy = 'script') {
    item.classList.add('open');
    const submenu = getMenu(item);
    if (!submenu) return;
    if (isTopLevel) {
      item.dataset.openedBy = openedBy;
      const toggle = getToggle(item);
      if (toggle && window.bootstrap?.Dropdown) {
        chooseDirection(item);
        window.bootstrap.Dropdown.getOrCreateInstance(toggle).show();
        return;
      }
    }
    submenu.style.display = 'block';
    submenu.style.opacity = '1';
    submenu.style.visibility = 'visible';
    adjustMenuPosition(submenu, item, isTopLevel);
  }

  function closeMenu(item) {
    item.classList.remove('open');
    delete item.dataset.openedBy;
    const submenu = getMenu(item);
    if (!submenu) return;
    if (isTopLevelDropdown(item)) {
      const toggle = getToggle(item);
      if (toggle && window.bootstrap?.Dropdown) {
        window.bootstrap.Dropdown.getOrCreateInstance(toggle).hide();
        return;
      }
    }
    submenu.style.display = 'none';
    submenu.style.opacity = '0';
    submenu.style.visibility = 'hidden';
  }

  function isSmallScreen() {
    return window.innerWidth < 992; // Bootstrap breakpoint for 'lg'
  }
    
  function adjustMenuPosition(submenu, parent, isTopLevel) {
    const parentRect = parent.getBoundingClientRect();

    const spaceAbove = parentRect.top;
    const spaceBelow = window.innerHeight - parentRect.bottom;
    const spaceLeft = parentRect.left;
    const spaceRight = window.innerWidth - parentRect.right;

    submenu.style.top = '';
    submenu.style.bottom = '';
    submenu.style.left = '';
    submenu.style.right = '';

    if (isTopLevel) {
      if (isSmallScreen() && spaceBelow < spaceAbove) {
        // For small screens: Open menu directly above the parent element
        submenu.style.top = 'auto';
        submenu.style.bottom = `${parentRect.height}px`; // Directly above the parent element
      } 
      // Top-level menu
      else if (spaceBelow < spaceAbove) {
        submenu.style.bottom = `${window.innerHeight - parentRect.bottom - parentRect.height}px`;
        submenu.style.top = 'auto';
      } else {
        submenu.style.top = `${parentRect.height}px`;
        submenu.style.bottom = 'auto';
      }
    } else {
      // Submenu
      const prefersRight = spaceRight >= spaceLeft;
      submenu.style.left = prefersRight ? '100%' : 'auto';
      submenu.style.right = prefersRight ? 'auto' : '100%';

      // Open upwards if there's no space below
      if (spaceBelow < spaceAbove) {
        submenu.style.bottom = `0`;
        submenu.style.top = `auto`;
      } else {
        submenu.style.top = `0`;
        submenu.style.bottom = `${parentRect.height}px`;
      }
    }
  }
});
