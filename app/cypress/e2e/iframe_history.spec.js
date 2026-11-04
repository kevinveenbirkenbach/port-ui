function param(name) {
  return cy.location('search').then((search) => new URLSearchParams(search).get(name));
}

function openAgileCoach() {
  cy.get('.portui-main > [data-portui-id="agile-coach"] a.stretched-link').click();
  cy.get('main iframe').should('have.attr', 'src', 'https://www.agile-coach.world/');
}

describe('Iframe links and history', () => {
  beforeEach(() => {
    cy.viewport(1440, 900);
  });

  it('opens an iframe link inside a navigation dropdown in the frame', () => {
    cy.visit('/en/');
    cy.get('#navbarNavheader .dropdown-menu a.dropdown-item[href^="https://"]')
      .first()
      .then(($item) => {
        $item.addClass('iframe-link');
        const href = $item.prop('href');
        cy.wrap($item)
          .closest('#navbarNavheader .navbar-nav > .nav-item.dropdown')
          .find('> .dropdown-toggle')
          .click();
        cy.wrap($item).should('be.visible').click();
        param('iframe').should('eq', href);
        cy.get('main iframe').should('have.attr', 'src', href);
      });
  });

  it('closes the frame on Back and reopens it on Forward', () => {
    cy.visit('/en/?q=agile');
    openAgileCoach();

    cy.go('back');
    cy.get('main iframe').should('not.exist');
    param('iframe').should('eq', null);
    param('fullscreen').should('eq', null);
    cy.get('body').should('not.have.class', 'fullscreen');

    cy.go('forward');
    param('iframe').should('eq', 'https://www.agile-coach.world/');
    cy.get('main iframe').should('have.attr', 'src', 'https://www.agile-coach.world/');
    cy.get('body').should('have.class', 'fullscreen');
  });

  it('switches the frame when Back steps between two framed entries', () => {
    cy.visit('/en/');
    cy.document().then((doc) => {
      const menu = doc.querySelector('#navbarNavheader .navbar-nav');
      ['de', 'fr'].forEach((code) => {
        const item = doc.createElement('li');
        item.className = 'nav-item';
        item.innerHTML = `<a class="nav-link iframe-link" id="frame-${code}" href="/${code}/">${code}</a>`;
        menu.prepend(item);
      });
    });
    cy.location('origin').then((origin) => {
      cy.get('#frame-de').click();
      cy.get('main iframe').should('have.attr', 'src', `${origin}/de/`);
      cy.wait(1600);

      cy.get('#frame-fr').click();
      param('iframe').should('eq', `${origin}/fr/`);
      cy.get('main iframe').should('have.attr', 'src', `${origin}/fr/`);
      cy.wait(1600);

      cy.go('back');
      param('iframe').should('eq', `${origin}/de/`);
      cy.get('main iframe').should('have.attr', 'src', `${origin}/de/`);
    });
  });

  it('cancels an open still fading in when Back is pressed', () => {
    cy.visit('/en/?q=agile');
    cy.get('.portui-main > [data-portui-id="agile-coach"] a.stretched-link').click();
    cy.go('back');

    cy.wait(2500);
    cy.get('main iframe').should('not.exist');
    param('iframe').should('eq', null);
    cy.get('.portui-main > [data-portui-id="agile-coach"]').should('be.visible');
  });

  it('closes the frame on Back without the dashboard scripts', () => {
    cy.intercept('GET', '/en/', (request) => {
      request.continue((response) => {
        response.body = response.body.replace(/<script src="[^"]*js\/(frame|chips|search|dashboard)\.js"><\/script>/g, '');
      });
    });
    cy.visit('/en/');
    cy.window().should('not.have.property', 'portuiDashboard');
    cy.get('.portui-main > [data-portui-id="infinito-nexus"] a.stretched-link').click();
    cy.get('main iframe').should('have.attr', 'src', 'https://infinito.nexus/');

    cy.go('back');
    cy.get('main iframe').should('not.exist');
    param('iframe').should('eq', null);
  });
});
