function visitWithCaller(url) {
  cy.readFile('cypress/fixtures/chips-caller.js').then((source) => {
    cy.visit(url, {
      onBeforeLoad(win) {
        win.eval(source);
      },
    });
  });
}

function tile(id) {
  return `.portui-main > [data-portui-id="${id}"]`;
}

function param(name) {
  return cy.location('search').then((search) => new URLSearchParams(search).get(name));
}

describe('Dashboard chip API', () => {
  beforeEach(() => {
    cy.viewport(1440, 900);
  });

  it('exists when portui:ready fires, and fires it once', () => {
    visitWithCaller('/en/?q=a');
    cy.window().its('portuiReadyCount').should('eq', 1);
    cy.window().then((win) => {
      expect(win.portui.chips.set).to.be.a('function');
      expect(win.portui.chips.clear).to.be.a('function');
    });
  });

  it('renders kind, tone, state, label and detail as a link or a button', () => {
    visitWithCaller('/en/?q=a');

    cy.get(`${tile('agile-coach')} .portui-chip`).should('have.length', 2);
    cy.get(`${tile('agile-coach')} .portui-chip-lock`)
      .should('match', 'a')
      .and('have.class', 'portui-chip')
      .and('have.class', 'text-bg-primary')
      .and('have.attr', 'href', 'https://access.example.org/?application=agile-coach')
      .and('have.attr', 'target', '_blank')
      .and('have.attr', 'data-portui-state', 'request')
      .and('have.attr', 'aria-label', 'Request access');
    cy.get(`${tile('agile-coach')} .portui-chip-health`)
      .should('have.class', 'text-bg-info')
      .and('have.attr', 'aria-label', 'Paused · 13:05');
    cy.get(`${tile('cybermaster')} .portui-chip-lock`)
      .should('match', 'button')
      .and('have.attr', 'type', 'button')
      .and('not.have.attr', 'href');
    cy.get(`${tile('infinito-nexus')} .portui-chip-health`).should('have.attr', 'data-portui-state', 'running');
    cy.get(`${tile('yachtmaster')} .portui-chip`).should('not.exist');
  });

  it('translates the label through the interface catalogue', () => {
    visitWithCaller('/de/?q=a');

    cy.get(`${tile('cybermaster')} .portui-chip-lock`).should('have.attr', 'aria-label', 'Anmelden');
    cy.get(`${tile('agile-coach')} .portui-chip-health`).should('have.attr', 'aria-label', 'Pausiert · 13:05');
  });

  it('follows the card into favourites, recent list, picker and list view', () => {
    visitWithCaller('/en/?folder=coaching/business');
    cy.get(`${tile('agile-coach')} .portui-star`).click();
    cy.get('.portui-breadcrumb a').first().click();
    cy.get('.portui-favourites [data-portui-id="agile-coach"] .portui-chip').should('have.length', 2);

    cy.get('.portui-density').click();
    cy.get('.portui-favourites [data-portui-id="agile-coach"] .portui-chip-lock').should('be.visible');

    cy.get('#portui-search').type('agile');
    cy.get('#portui-picker [role="option"]').first().find('.portui-chip').should('have.length', 2);
  });

  it('keeps the chips through a re-render and a set made before it', () => {
    visitWithCaller('/en/');
    cy.window().then((win) => {
      win.portui.chips.set('mediator', [{ kind: 'note', tone: 'warning', label: 'Degraded' }]);
    });
    cy.get('[data-portui-folder="coaching"] a').click();
    cy.get('[data-portui-folder="coaching/personal"] a').click();
    cy.get(`${tile('mediator')} .portui-chip-note`).should('have.attr', 'aria-label', 'Degraded');
  });

  it('never launches the application from a chip and leaves the click to the host page', () => {
    visitWithCaller('/en/?q=agile');
    cy.document().then((doc) => {
      doc.addEventListener('click', (event) => {
        if (event.target.closest('.portui-chip')) {
          doc.defaultView.chipClicks = (doc.defaultView.chipClicks || 0) + (event.defaultPrevented ? 100 : 1);
        }
      });
    });

    cy.get(`${tile('agile-coach')} .portui-chip-health`).click();
    cy.wait(300);
    param('iframe').should('eq', null);
    cy.get('main iframe').should('not.exist');

    cy.get('#portui-search').clear().type('agile');
    cy.get('#portui-picker [role="option"]').first().find('.portui-chip-health').click();
    cy.wait(300);
    param('iframe').should('eq', null);
    cy.window().its('chipClicks').should('eq', 2);
  });

  it('removes the chips of a card with an empty list and with clear', () => {
    visitWithCaller('/en/?q=a');
    cy.get(`${tile('agile-coach')} .portui-chip`).should('have.length', 2);

    cy.window().then((win) => win.portui.chips.set('agile-coach', []));
    cy.get(`${tile('agile-coach')} .portui-chip`).should('not.exist');

    cy.window().then((win) => win.portui.chips.clear('cybermaster'));
    cy.get(`${tile('cybermaster')} .portui-chip`).should('not.exist');
  });

  it('rejects malformed chips and drops an unsafe link', () => {
    visitWithCaller('/en/?q=a');
    cy.window().then((win) => {
      [
        [{ kind: 'x', tone: 'purple', label: 'A' }, 'tone'],
        [{ kind: 'x', tone: 'info' }, 'label'],
        [{ kind: 'Bad Kind', tone: 'info', label: 'A' }, 'kind'],
      ].forEach(([chip, field]) => {
        let thrown = null;
        try {
          win.portui.chips.set('polymath', [chip]);
        } catch (error) {
          thrown = error;
        }
        expect(thrown, field).to.have.property('name', 'TypeError');
        expect(thrown.message).to.include(field);
      });
      win.portui.chips.set('polymath', [{ kind: 'x', tone: 'info', label: 'A', href: 'javascript:alert(1)' }]);
    });
    cy.get(`${tile('polymath')} .portui-chip-x`).should('match', 'button').and('not.have.attr', 'href');
  });

  it('shows the label as a tooltip on keyboard focus', () => {
    visitWithCaller('/en/?q=agile');
    cy.get(`${tile('agile-coach')} .portui-chip-lock`).focus();
    cy.get('.tooltip.show').should('contain.text', 'Request access');
  });

  it('keeps the chip group clear of title, text and open button', () => {
    visitWithCaller('/en/?q=agile');
    cy.get(`${tile('agile-coach')} .portui-chip`).should('have.length', 2);
    cy.get(tile('agile-coach')).then(($tile) => {
      const chips = $tile[0].querySelector('.portui-chips').getBoundingClientRect();
      ['.card-title', '.card-text', 'a.stretched-link'].forEach((selector) => {
        const other = $tile[0].querySelector(selector).getBoundingClientRect();
        const overlaps = chips.left < other.right && chips.right > other.left && chips.top < other.bottom && chips.bottom > other.top;
        expect(overlaps, `chips overlap ${selector}`).to.equal(false);
      });
    });
  });

  it('shows no chip without a caller', () => {
    cy.visit('/en/?q=a');
    cy.get(`${tile('agile-coach')} .portui-chips`).should('exist');
    cy.get('.portui-chip').should('not.exist');
  });

  it('keeps a focused chip when an unchanged list is set again', () => {
    visitWithCaller('/en/?q=agile');
    cy.get(`${tile('agile-coach')} .portui-chip-lock`).focus();
    cy.window().then((win) => {
      const focused = win.document.activeElement;
      win.portui.chips.set('agile-coach', [
        {
          kind: 'lock',
          tone: 'primary',
          icon: 'fa-solid fa-lock',
          label: 'Request access',
          href: 'https://access.example.org/?application=agile-coach',
          newTab: true,
          state: 'request',
        },
        { kind: 'health', tone: 'info', icon: 'fa-solid fa-circle-pause', label: 'Paused', detail: ' · 13:05', state: 'paused' },
      ]);
      win.portuiDashboard.render();
      expect(win.document.activeElement, 'same focused chip').to.equal(focused);
      expect(focused.isConnected).to.equal(true);
    });
  });

  it('removes the tooltip of a chip it takes away', () => {
    visitWithCaller('/en/?q=agile');
    cy.get(`${tile('agile-coach')} .portui-chip-lock`).focus();
    cy.get('.tooltip.show').should('contain.text', 'Request access');

    cy.window().then((win) => win.portui.chips.set('agile-coach', []));
    cy.get('.tooltip').should('not.exist');
  });
});
