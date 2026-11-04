function param(name) {
  return cy.location('search').then((search) => new URLSearchParams(search).get(name));
}

function visibleKinds() {
  return cy.get('.portui-main > :not([hidden])').then(($tiles) =>
    [...$tiles].map((tile) => (tile.dataset.portuiFolder ? `folder:${tile.dataset.portuiFolder}` : `card:${tile.dataset.portuiCard}`)),
  );
}

describe('Dashboard folder view', () => {
  beforeEach(() => {
    cy.viewport(1440, 900);
  });

  it('opens at the top level with the folders that hold applications and their counts', () => {
    cy.visit('/en/');

    visibleKinds().should('deep.equal', [
      'folder:coaching',
      'folder:technology',
      'folder:outdoors',
      'card:0',
    ]);
    cy.get('[data-portui-folder="coaching"] .portui-count').should('have.text', '5');
    cy.get('[data-portui-folder="technology"] .portui-count').should('have.text', '3');
    cy.get('[data-portui-folder="outdoors"] .portui-count').should('have.text', '1');
    cy.get('[data-portui-folder="archive"]').should('not.exist');
    cy.get('[data-portui-folder="coaching"]').should('contain.text', 'Guidance for people and organisations.');
  });

  it('shows the subfolders first, then the applications, under a linked breadcrumb', () => {
    cy.visit('/en/');
    cy.get('[data-portui-folder="technology"] a').click();

    param('folder').should('eq', 'technology');
    visibleKinds().should('deep.equal', [
      'folder:technology/infrastructure',
      'folder:technology/ai',
      'card:4',
    ]);

    cy.get('[data-portui-folder="technology/ai"] a').click();
    cy.get('.portui-breadcrumb .breadcrumb-item a').then(($links) => {
      expect([...$links].map((link) => link.textContent.trim())).to.deep.equal([
        'Applications',
        'Technology',
        'Artificial Intelligence',
      ]);
    });
    cy.get('.portui-breadcrumb .breadcrumb-item a').eq(1).click();
    param('folder').should('eq', 'technology');
  });

  it('lists an application in every folder it belongs to', () => {
    cy.visit('/en/?folder=coaching/business');
    cy.get('[data-portui-card="7"]').should('be.visible');
    cy.visit('/en/?folder=coaching/personal');
    cy.get('[data-portui-card="7"]').should('be.visible');
  });

  it('steps through the same history as the browser and disables the dead ends', () => {
    cy.visit('/en/');
    cy.get('.portui-back').should('be.disabled');
    cy.get('.portui-forward').should('be.disabled');

    cy.get('[data-portui-folder="technology"] a').click();
    cy.get('[data-portui-folder="technology/ai"] a').click();
    param('folder').should('eq', 'technology/ai');
    cy.location('search').should('eq', '?folder=technology/ai');
    cy.get('.portui-forward').should('be.disabled');

    cy.get('.portui-back').click();
    param('folder').should('eq', 'technology');
    cy.get('.portui-forward').should('not.be.disabled');

    cy.go('back');
    param('folder').should('eq', null);
    cy.get('.portui-back').should('be.disabled');
    cy.get('[data-portui-folder="coaching"]').should('be.visible');

    cy.get('.portui-forward').click();
    param('folder').should('eq', 'technology');
    cy.go('forward');
    param('folder').should('eq', 'technology/ai');
    cy.get('[data-portui-card="6"]').should('be.visible');
    cy.get('.portui-forward').should('be.disabled');
  });

  it('does not offer Forward into entries a reload or a cache restore cannot vouch for', () => {
    cy.visit('/en/');
    cy.get('[data-portui-folder="technology"] a').click();
    cy.get('[data-portui-folder="technology/ai"] a').click();
    cy.go('back');
    cy.get('.portui-forward').should('not.be.disabled');

    cy.window().then((win) => {
      win.dispatchEvent(new win.PageTransitionEvent('pageshow', { persisted: true }));
    });
    cy.get('.portui-forward').should('be.disabled');

    cy.reload();
    param('folder').should('eq', 'technology');
    cy.get('.portui-back').should('not.be.disabled');
    cy.get('.portui-forward').should('be.disabled');
  });

  it('opens a folder straight from the URL', () => {
    cy.visit('/en/?folder=coaching/personal');

    visibleKinds().should('deep.equal', ['card:2', 'card:7', 'card:8']);
    cy.get('.portui-back').should('be.disabled');
  });

  it('falls back to the top level and drops an unknown folder path', () => {
    cy.visit('/en/?folder=nowhere/at-all');

    cy.location('search').should('eq', '');
    cy.get('[data-portui-folder="coaching"]').should('be.visible');
  });

  it('keeps the folder while an application is framed and returns to it', () => {
    cy.visit('/en/?folder=coaching/business');
    cy.get('[data-portui-card="1"] a.stretched-link').click();

    param('iframe').should('eq', 'https://www.agile-coach.world/');
    param('folder').should('eq', 'coaching/business');
    cy.get('main iframe').should('exist');

    cy.go('back');
    cy.get('main iframe').should('not.exist');
    param('iframe').should('eq', null);
    param('folder').should('eq', 'coaching/business');
    cy.get('[data-portui-card="1"]').should('be.visible');
    cy.get('[data-portui-card="7"]').should('be.visible');
  });

  it('keeps folder and search when the frame is closed from the navbar', () => {
    cy.visit('/en/?folder=coaching/business&q=agile');
    cy.get('.portui-main > [data-portui-card="1"] a.stretched-link').click();
    param('iframe').should('eq', 'https://www.agile-coach.world/');

    cy.get('#navbar_logo').click();
    cy.get('main iframe').should('not.exist');
    param('folder').should('eq', 'coaching/business');
    param('q').should('eq', 'agile');
    cy.get('#portui-search').should('have.value', 'agile');
  });
});
