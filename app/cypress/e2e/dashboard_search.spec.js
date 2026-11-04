function param(name) {
  return cy.location('search').then((search) => new URLSearchParams(search).get(name));
}

function pickerTitles() {
  return cy.get('#portui-picker .portui-hit-title').then(($titles) => [...$titles].map((title) => title.textContent));
}

describe('Dashboard search', () => {
  beforeEach(() => {
    cy.viewport(1440, 900);
    cy.visit('/en/');
  });

  it('sits in the header navigation bar', () => {
    cy.get('nav.menu-header #portui-search').should('be.visible');
  });

  [
    { name: 'desktop', width: 1440, height: 900 },
    { name: 'mobile', width: 390, height: 844 },
  ].forEach((size) => {
    it(`attaches the picker to the field on ${size.name}`, () => {
      cy.viewport(size.width, size.height);
      cy.get('#portui-search').type('co');
      cy.get('#portui-picker').should('be.visible');
      cy.get('#portui-search').should(($field) => {
        const field = $field[0].getBoundingClientRect();
        const picker = $field[0].ownerDocument.getElementById('portui-picker').getBoundingClientRect();
        expect(Math.abs(picker.left - field.left), 'same left edge').to.be.lessThan(1);
        expect(Math.abs(picker.width - field.width), 'same width').to.be.lessThan(1);
        expect(Math.abs(picker.top - field.bottom), 'no gap').to.be.lessThan(1);
      });
      cy.get('#portui-search')
        .should('have.css', 'border-bottom-left-radius', '0px')
        .and('have.css', 'border-bottom-right-radius', '0px');
      cy.get('#portui-picker')
        .should('have.css', 'border-top-left-radius', '0px')
        .and('have.css', 'border-top-right-radius', '0px');
      cy.get('#portui-search').then(($field) => {
        cy.get('#portui-picker').should('have.css', 'border-left-color', getComputedStyle($field[0]).borderLeftColor);
      });
    });
  });

  it('widens the field over the menu only while the picker is open on desktop', () => {
    cy.get('#portui-search').then(($field) => {
      const resting = $field[0].getBoundingClientRect().width;
      const menu = $field[0].ownerDocument.querySelector('#navbarNavheader .navbar-nav').getBoundingClientRect().left;
      cy.get('#portui-search').type('co');
      cy.get('#portui-search').should(($open) => {
        expect($open[0].getBoundingClientRect().width).to.be.greaterThan(resting + 50);
      });
      cy.get('#navbarNavheader .navbar-nav').should(($nav) => {
        expect($nav[0].getBoundingClientRect().left, 'menu does not move').to.be.closeTo(menu, 1);
      });
      cy.get('#portui-search').type('{esc}');
      cy.get('#portui-search').should(($closed) => {
        expect($closed[0].getBoundingClientRect().width).to.be.closeTo(resting, 1);
      });
    });
  });

  it('filters live across all folders and ranks title prefixes first', () => {
    cy.get('#portui-search').type('me');

    pickerTitles().then((titles) => {
      expect(titles[0]).to.eq('Mediator');
      expect(titles).to.include('Personal Coach');
    });
    cy.get('.portui-main > [data-portui-card="7"]').should('be.visible');
    cy.get('.portui-main > [data-portui-folder]:visible').should('have.length', 0);
    cy.location('search').should('eq', '');
  });

  it('matches tags and folder names, and shows icon, folder path and at most eight rows', () => {
    cy.get('#portui-search').type('skipper');
    pickerTitles().should('deep.equal', ['Yachtmaster']);
    cy.get('#portui-picker .portui-hit-path').should('have.text', 'Outdoors');
    cy.get('#portui-picker .portui-hit-icon').children().should('have.length.at.least', 1);

    cy.get('#portui-search').clear().type('personal growth');
    pickerTitles().should('include', 'Hypnotherapist');

    cy.get('#portui-search').clear().type('i');
    cy.get('#portui-picker [role="option"]').should('have.length', 8);
  });

  it('tolerates one typo in words of five letters or more, not in shorter ones', () => {
    cy.get('#portui-search').type('Cybermastr');
    pickerTitles().should('deep.equal', ['Cybermaster']);

    cy.get('#portui-search').clear().type('yahctmaster');
    pickerTitles().should('deep.equal', ['Yachtmaster']);

    cy.get('#portui-search').clear().type('Polx');
    cy.get('#portui-picker .portui-no-hits').should('have.text', 'No applications found');
  });

  it('shows a message instead of an empty picker and announces the hits', () => {
    cy.get('#portui-search').type('zzzzzz');
    cy.get('#portui-picker').should('be.visible');
    cy.get('#portui-picker .portui-no-hits').should('have.text', 'No applications found');
    cy.get('.portui-empty').should('be.visible');
    cy.get('#portui-live').should('have.attr', 'aria-live', 'polite').and('have.text', 'No applications found');

    cy.get('#portui-search').clear().type('coach');
    cy.get('#portui-live').should('have.text', 'Results: 5');
  });

  it('moves the selection with the arrow keys and opens the pick like its tile', () => {
    cy.get('#portui-search').type('co');
    cy.get('#portui-picker [aria-selected="true"]').should('have.length', 1).first().as('first');
    cy.get('#portui-picker [role="option"]').eq(0).should('have.attr', 'aria-selected', 'true');

    cy.get('#portui-search').type('{downarrow}');
    cy.get('#portui-picker [role="option"]').eq(1).should('have.attr', 'aria-selected', 'true');
    cy.get('#portui-search').type('{uparrow}');
    cy.get('#portui-picker [role="option"]').eq(0).should('have.attr', 'aria-selected', 'true');

    cy.get('#portui-search').clear().type('agile{enter}');
    param('q').should('eq', 'agile');
    param('iframe').should('eq', 'https://www.agile-coach.world/');
    cy.get('main iframe').should('have.attr', 'src', 'https://www.agile-coach.world/');
  });

  it('closes the picker on the first Escape and clears the field on the second', () => {
    cy.get('#portui-search').type('yacht');
    cy.get('#portui-picker').should('be.visible');

    cy.get('#portui-search').type('{esc}');
    cy.get('#portui-picker').should('not.be.visible');
    cy.get('#portui-search').should('have.value', 'yacht');

    cy.get('#portui-search').type('{esc}');
    cy.get('#portui-search').should('have.value', '');
    cy.get('[data-portui-folder="coaching"]').should('be.visible');
  });

  it('writes a committed search to ?q= and restores it on load', () => {
    cy.get('#portui-search').type('yacht{esc}{enter}');
    param('q').should('eq', 'yacht');

    cy.reload();
    cy.get('#portui-search').should('have.value', 'yacht');
    cy.get('.portui-main > [data-portui-card="3"]').should('be.visible');
    cy.get('.portui-main > [data-portui-card]:visible').should('have.length', 1);

    cy.go('back');
    param('q').should('eq', null);
  });

  it('focuses the field with / and Ctrl+K, but not from inside another input', () => {
    cy.get('body').type('/');
    cy.focused().should('have.id', 'portui-search');

    cy.get('#portui-search').blur();
    cy.get('body').type('{ctrl}k');
    cy.focused().should('have.id', 'portui-search');

    cy.document().then((doc) => {
      const other = doc.createElement('input');
      other.id = 'other-input';
      doc.querySelector('#main').prepend(other);
    });
    cy.get('#other-input').type('/');
    cy.focused().should('have.id', 'other-input');
    cy.get('#other-input').should('have.value', '/');
  });

  it('opens the parent folder on Backspace in the empty field', () => {
    cy.visit('/en/?folder=technology/ai');
    cy.get('#portui-search').type('{backspace}');
    param('folder').should('eq', 'technology');
  });
});
