// cypress/e2e/menu.spec.js

describe('Navigation dropdowns', () => {
  beforeEach(() => {
    cy.viewport(1280, 720);
    cy.visit('/');
  });

  it('opens top-level dropdowns with explicit Bootstrap instances', () => {
    cy.get('#navbarNavheader .nav-item.dropdown > .nav-link.dropdown-toggle')
      .first()
      .as('toggle')
      .should('have.attr', 'data-bs-toggle', 'dropdown')
      .and('have.attr', 'aria-expanded', 'false');

    cy.get('@toggle').then($toggle => {
      cy.window().then(win => {
        expect(win.bootstrap.Dropdown.getInstance($toggle[0])).to.exist;
      });
    });

    cy.get('@toggle')
      .parent('.nav-item')
      .find('> .dropdown-menu')
      .as('menu')
      .should('not.have.class', 'show')
      .should('not.be.visible');

    cy.get('@toggle').click();
    cy.get('@toggle').should('have.attr', 'aria-expanded', 'true');
    cy.get('@toggle').parent('.nav-item').should('have.class', 'dropdown');
    cy.get('@menu')
      .should('have.class', 'show')
      .and('be.visible');
  });

  it('flips footer dropdowns upward where there is more space above', () => {
    cy.get('#navbarNavfooter .nav-item .nav-link.dropdown-toggle')
      .first()
      .as('toggle');

    cy.get('@toggle')
      .parent('.nav-item')
      .as('item')
      .find('> .dropdown-menu')
      .as('menu')
      .should('not.have.class', 'show');

    // Scroll the page so the footer sits at the bottom of the viewport,
    // then click without Cypress re-scrolling — otherwise the toggle could
    // land near the top of the viewport and chooseDirection would keep
    // .dropdown (more space below than above).
    cy.scrollTo('bottom');
    cy.get('@toggle').then($toggle => {
      const rect = $toggle[0].getBoundingClientRect();
      expect(rect.top, 'toggle is in the lower half of the viewport')
        .to.be.greaterThan(Cypress.config('viewportHeight') / 2);
    });
    cy.get('@toggle').click({ scrollBehavior: false });
    cy.get('@item').should('have.class', 'dropup');
    cy.get('@item').should('not.have.class', 'dropdown');
    cy.get('@menu')
      .should('have.class', 'show')
      .and('be.visible');
  });
});

describe('Dynamic Popup', () => {
  const base = {
    name: 'Test Item',
    identifier: 'ABC123',
    description: 'A simple description',
    warning: '**Be careful!**',
    info: '_Some info_',
    url: null,
    iframe: false,
    icon: { class: 'fa fa-test' },
    alternatives: [
      { name: 'Alt One', identifier: 'ALT1', icon: { class: 'fa fa-alt1' } }
    ],
    children: [
      { name: 'Child One', identifier: 'CH1', icon: { class: 'fa fa-child1' } }
    ]
  };

  beforeEach(() => {
    cy.visit('/');
    cy.window().then(win => {
      cy.stub(win.navigator.clipboard, 'writeText').resolves();
      cy.stub(win, 'alert');
    });
  });

  function open(item = {}) {
    cy.window().invoke('openDynamicPopup', { ...base, ...item });
  }

  it('renders title with icon and text', () => {
    open();
    cy.get('#dynamicModalLabel')
      .find('i.fa.fa-test')
      .should('exist');
    cy.get('#dynamicModalLabel')
      .should('contain.text', 'Test Item');
  });

  it('falls back to plain text when no icon', () => {
    open({ icon: null });
    cy.get('#dynamicModalLabel')
      .find('i')
      .should('not.exist');
    cy.get('#dynamicModalLabel')
      .should('have.text', 'Test Item');
  });

  it('shows identifier when provided and populates input', () => {
    open();
    cy.get('#dynamicIdentifierBox').should('not.have.class', 'd-none');
    cy.get('#dynamicModalContent').should('have.value', 'ABC123');
  });

  it('hides identifier box when none', () => {
    open({ identifier: null });
    cy.get('#dynamicIdentifierBox').should('have.class', 'd-none');
    cy.get('#dynamicModalContent').should('have.value', '');
  });

  it('renders warning and info via marked', () => {
    open();
    cy.get('#dynamicModalWarning')
      .should('not.have.class', 'd-none')
      .find('#dynamicModalWarningText')
      .should('contain.html', '<strong>Be careful!</strong>');
    cy.get('#dynamicModalInfo')
      .should('not.have.class', 'd-none')
      .find('#dynamicModalInfoText')
      .should('contain.html', '<em>Some info</em>');
  });

  it('hides warning/info when none provided', () => {
    open({ warning: null, info: null });
    cy.get('#dynamicModalWarning').should('have.class', 'd-none');
    cy.get('#dynamicModalInfo').should('have.class', 'd-none');
  });

  it('shows description when no URL', () => {
    open({ url: null, description: 'Only desc' });
    cy.get('#dynamicDescriptionText')
      .should('not.have.class', 'd-none')
      .and('have.text', 'Only desc');
    cy.get('#dynamicModalLink').should('have.class', 'd-none');
  });

  it('shows link when URL is provided', () => {
    open({ url: 'https://example.com', description: 'Click me' });
    cy.get('#dynamicModalLink').should('not.have.class', 'd-none');
    cy.get('#dynamicModalLinkHref')
      .should('have.attr', 'href', 'https://example.com')
      .and('have.text', 'Click me');
  });

  it('populates alternatives and children lists', () => {
    open();
    cy.get('#dynamicAlternativesSection').should('not.have.class', 'd-none');
    cy.get('#dynamicAlternativesList li')
      .should('have.length', 1)
      .first().contains('Alt One');
    cy.get('#dynamicChildrenSection').should('not.have.class', 'd-none');
    cy.get('#dynamicChildrenList li')
      .should('have.length', 1)
      .first().contains('Child One');
  });

  it('hides sections when no items', () => {
    open({ alternatives: [], children: [] });
    cy.get('#dynamicAlternativesSection').should('have.class', 'd-none');
    cy.get('#dynamicChildrenSection').should('have.class', 'd-none');
  });

  it('clicking an “Open” in list re-opens popup with that item', () => {
    open();
    cy.get('#dynamicAlternativesList button').click();
    cy.get('#dynamicModalLabel')
      .should('contain.text', 'Alt One');
  });

  it('copy button selects & copies identifier', () => {
    open();
    cy.get('#dynamicCopyButton').click();
    cy.window().its('navigator.clipboard.writeText')
      .should('have.been.calledWith', 'ABC123');
    cy.window().its('alert')
      .should('have.been.calledWith', 'Identifier copied to clipboard!');
  });
});
