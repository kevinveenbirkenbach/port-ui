const NOW = Date.UTC(2026, 10, 3, 12, 0, 0);
const DAY = 86400000;

function param(name) {
  return cy.location('search').then((search) => new URLSearchParams(search).get(name));
}

describe('Dashboard favourites', () => {
  beforeEach(() => {
    cy.viewport(1440, 900);
  });

  it('pins a tile into a Favourites row that survives a reload', () => {
    cy.visit('/en/?folder=outdoors');
    cy.get('.portui-main > [data-portui-card="3"] .portui-star')
      .should('be.visible')
      .and('have.attr', 'aria-pressed', 'false')
      .click();
    cy.get('.portui-main > [data-portui-card="3"] .portui-star').should('have.attr', 'aria-pressed', 'true');

    cy.get('.portui-breadcrumb a').first().click();
    cy.get('.portui-favourites').should('be.visible');
    cy.get('.portui-favourites [data-portui-card="3"]').should('be.visible');

    cy.reload();
    cy.get('.portui-favourites [data-portui-card="3"]').should('be.visible');

    cy.get('.portui-favourites [data-portui-card="3"] .portui-star').click();
    cy.get('.portui-favourites').should('not.be.visible');
  });

  it('throws nothing when localStorage refuses a write', () => {
    cy.visit('/en/?folder=outdoors');
    cy.window().then((win) => {
      cy.stub(win.Storage.prototype, 'setItem').throws(new win.DOMException('full', 'QuotaExceededError'));
    });
    cy.get('.portui-main > [data-portui-card="3"] .portui-star').click();
    cy.get('.portui-density').click();
    cy.get('#portui-dashboard').should('have.class', 'portui-list');
    cy.get('.portui-main > [data-portui-card="3"] a.stretched-link').then(($link) => {
      $link[0].addEventListener('click', (event) => event.preventDefault(), { once: true });
    });
    cy.get('.portui-main > [data-portui-card="3"] a.stretched-link').click();
    cy.get('.portui-density').click();
    cy.get('#portui-dashboard').should('not.have.class', 'portui-list');
  });

  it('shows no star and throws nothing without localStorage', () => {
    cy.visit('/en/', {
      onBeforeLoad(win) {
        Object.defineProperty(win, 'localStorage', {
          get() {
            throw new win.DOMException('denied', 'SecurityError');
          },
        });
      },
    });
    cy.get('.portui-main > [data-portui-card="0"]').should('be.visible');
    cy.get('.portui-star:visible').should('have.length', 0);
    cy.get('.portui-density').click();
    cy.get('#portui-dashboard').should('have.class', 'portui-list');
  });
});

describe('Dashboard recently used', () => {
  beforeEach(() => {
    cy.viewport(1440, 900);
  });

  it('records an opened application, newest first, and clears on request', () => {
    cy.visit('/en/');
    cy.get('.portui-recent').should('not.be.visible');

    cy.get('.portui-main > [data-portui-card="0"] a.stretched-link').click();
    param('iframe').should('not.eq', null);
    cy.get('#navbar_logo').click();
    cy.get('main iframe').should('not.exist');

    cy.get('.portui-recent').should('be.visible');
    cy.get('.portui-recent [data-portui-card]').then(($tiles) => {
      expect([...$tiles].map((tile) => tile.dataset.portuiCard)).to.deep.equal(['0']);
    });

    cy.get('#portui-search').type('agile{enter}');
    param('iframe').should('not.eq', null);
    cy.get('#navbar_logo').click();
    cy.get('#portui-search').clear().type('{esc}');
    cy.get('.portui-breadcrumb a').first().click();

    cy.get('.portui-recent [data-portui-card]').then(($tiles) => {
      expect([...$tiles].map((tile) => tile.dataset.portuiCard)).to.deep.equal(['1', '0']);
    });

    cy.get('.portui-recent-clear').click();
    cy.get('.portui-recent').should('not.be.visible');
    cy.window().then((win) => {
      expect(JSON.parse(win.localStorage.getItem('portui.recent'))).to.deep.equal([]);
    });
  });

  it('holds the last eight distinct applications', () => {
    const seeded = ['agile-coach', 'personal-coach', 'yachtmaster', 'polymath', 'cybermaster', 'prompt-engineer', 'mediator', 'hypnotherapist'];
    cy.visit('/en/', {
      onBeforeLoad(win) {
        win.localStorage.setItem('portui.recent', JSON.stringify(seeded));
      },
    });
    cy.get('.portui-recent [data-portui-card]').should('have.length', 8);

    cy.get('.portui-main > [data-portui-card="0"] a.stretched-link').click();
    cy.window().then((win) => {
      const recent = JSON.parse(win.localStorage.getItem('portui.recent'));
      expect(recent).to.have.length(8);
      expect(recent[0]).to.eq('infinito-nexus');
      expect(recent).not.to.include('hypnotherapist');
    });
  });
});

describe('Dashboard density toggle', () => {
  it('switches to a compact list and keeps the choice across a reload', () => {
    cy.viewport(1440, 900);
    cy.visit('/en/');
    cy.get('.portui-density').should('have.attr', 'aria-pressed', 'false');

    cy.get('.portui-density').click();
    cy.get('#portui-dashboard').should('have.class', 'portui-list');
    cy.get('.portui-density').should('have.attr', 'aria-pressed', 'true');
    cy.get('.portui-main > [data-portui-folder="coaching"]').then(($tile) => {
      expect($tile[0].getBoundingClientRect().height).to.be.lessThan(120);
    });

    cy.reload();
    cy.get('#portui-dashboard').should('have.class', 'portui-list');

    cy.get('.portui-density').click();
    cy.get('#portui-dashboard').should('not.have.class', 'portui-list');
  });

  function lefts(selector) {
    return cy.get('.portui-main > [data-portui-card]:not([hidden])').then(($rows) =>
      [...$rows]
        .map((row) => row.querySelector(selector))
        .filter(Boolean)
        .map((element) => Math.round(element.getBoundingClientRect().left)),
    );
  }

  function expectOneColumn(selector) {
    lefts(selector).then((xs) => {
      expect(xs.length, `${selector} rows`).to.be.greaterThan(1);
      expect(new Set(xs).size, `${selector} left edges ${xs.join(',')}`).to.eq(1);
    });
  }

  [
    { name: 'desktop', width: 1440, height: 900, selectors: ['a.stretched-link', '.portui-star', '.portui-chips', '.card-title', '.card-text'] },
    { name: 'mobile', width: 390, height: 844, selectors: ['a.stretched-link', '.portui-star', '.portui-chips', '.card-title'] },
  ].forEach((size) => {
    it(`lines every list column up across rows on ${size.name}`, () => {
      cy.viewport(size.width, size.height);
      cy.readFile('cypress/fixtures/chips-caller.js').then((source) => {
        cy.visit('/en/?q=a', {
          onBeforeLoad(win) {
            win.localStorage.setItem('portui.density', 'list');
            win.eval(source);
          },
        });
      });
      cy.get('#portui-dashboard').should('have.class', 'portui-list');
      cy.get('.portui-main [data-portui-id="agile-coach"] .portui-chip').should('have.length', 2);
      size.selectors.forEach(expectOneColumn);
      cy.get('.portui-main > [data-portui-card]:not([hidden])').each(($row) => {
        const boxes = ['.card-title', 'a.stretched-link', '.portui-new:not([hidden])', '.portui-star', '.portui-chips']
          .map((selector) => [selector, $row[0].querySelector(selector)])
          .filter(([, element]) => element)
          .map(([selector, element]) => [selector, element.getBoundingClientRect()]);
        boxes.forEach(([first, a], index) => {
          boxes.slice(index + 1).forEach(([second, b]) => {
            const overlaps = a.left < b.right - 1 && a.right > b.left + 1 && a.top < b.bottom - 1 && a.bottom > b.top + 1;
            expect(overlaps, `${first} overlaps ${second}`).to.equal(false);
          });
        });
      });
    });
  });
});

describe('Dashboard New badge', () => {
  it('marks an application during the configured days after it was added', () => {
    cy.clock(NOW, ['Date']);
    cy.visit('/en/');
    cy.get('[data-portui-card="0"] .portui-new').should('be.visible').and('have.text', 'New');
    cy.get('[data-portui-card="3"] .portui-new').should('not.be.visible');
  });

  it('drops the badge once the window has passed', () => {
    cy.clock(Date.UTC(2026, 10, 1) + 14 * DAY, ['Date']);
    cy.visit('/en/');
    cy.get('[data-portui-card="0"] .portui-new').should('not.be.visible');
  });
});

describe('Dashboard accessibility', () => {
  it('reaches folder tiles, breadcrumb, stars and picker rows with the keyboard', () => {
    cy.viewport(1440, 900);
    cy.visit('/en/');
    cy.get('[data-portui-folder="outdoors"] a').focus();
    cy.focused()
      .should('have.attr', 'data-portui-folder-link', 'outdoors')
      .and('have.attr', 'href', '?folder=outdoors')
      .and('have.css', 'outline-style', 'solid')
      .click();
    param('folder').should('eq', 'outdoors');

    cy.get('.portui-breadcrumb a').first().focus();
    cy.focused().should('have.attr', 'href').and('not.be.empty');

    cy.get('.portui-main > [data-portui-card="3"] .portui-star').focus();
    cy.focused().should('match', 'button').and('have.css', 'outline-style', 'solid');

    cy.get('#portui-search').type('yacht');
    cy.get('#portui-search').should('have.attr', 'aria-activedescendant', 'portui-hit-0');
    cy.get('#portui-hit-0').should('have.attr', 'role', 'option');
  });

  it('turns hover lifts and transitions off under reduced motion', () => {
    cy.viewport(1440, 900);
    cy.wrap(null).then(() =>
      Cypress.automation('remote:debugger:protocol', {
        command: 'Emulation.setEmulatedMedia',
        params: { features: [{ name: 'prefers-reduced-motion', value: 'reduce' }] },
      }),
    );
    cy.visit('/en/');
    cy.get('.portui-main > [data-portui-card="0"] .card')
      .should('have.css', 'transition-duration', '0s');
    cy.wrap(null).then(() =>
      Cypress.automation('remote:debugger:protocol', {
        command: 'Emulation.setEmulatedMedia',
        params: { features: [] },
      }),
    );
  });
});
