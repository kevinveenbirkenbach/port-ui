// cypress/e2e/fullscreen.spec.js

describe('Fullscreen Toggle', () => {
  const ROOT = '/';

  beforeEach(() => {
    cy.visit(ROOT);
  });

  it('defaults to normal mode when no fullscreen param is present', () => {
    // Body should not have fullscreen class
    cy.get('body').should('not.have.class', 'fullscreen');

    // URL should not include `fullscreen`
    cy.url().should('not.include', 'fullscreen=');

    // Header and footer should be visible (max-height > 0)
    cy.get('header').should('have.css', 'max-height').and(value => {
      expect(parseFloat(value)).to.be.greaterThan(0);
    });
    cy.get('footer').should('have.css', 'max-height').and(value => {
      expect(parseFloat(value)).to.be.greaterThan(0);
    });
  });

  it('initFullscreenFromUrl() picks up ?fullscreen=1 on load', () => {
    cy.visit(`${ROOT}?fullscreen=1`);

    cy.get('body').should('have.class', 'fullscreen');
    cy.url().should('include', 'fullscreen=1');

    // Header and footer should be collapsed (max-height == 0)
    cy.get('header').should('have.css', 'max-height', '0px');
    cy.get('footer').should('have.css', 'max-height', '0px');
  });

  it('enterFullscreen() adds fullscreen class, sets full width, and updates URL', () => {
    cy.window().then(win => {
      win.exitFullscreen(); // ensure starting state
      win.enterFullscreen();
    });

    cy.get('body').should('have.class', 'fullscreen');
    cy.url().should('include', 'fullscreen=1');
    cy.get('.container, .container-fluid')
      .should('have.class', 'container-fluid');

    cy.get('header').should('have.css', 'max-height', '0px');
    cy.get('footer').should('have.css', 'max-height', '0px');
  });

  it('exitFullscreen() removes fullscreen class, resets width, and URL param', () => {
    // start in fullscreen
    cy.window().invoke('enterFullscreen');

    // then exit
    cy.window().invoke('exitFullscreen');

    cy.get('body').should('not.have.class', 'fullscreen');
    cy.url().should('not.include', 'fullscreen=');
    cy.get('.container, .container-fluid')
      .should('have.class', 'container')
      .and('not.have.class', 'container-fluid');

    // Header and footer should be expanded again
    cy.get('header').should('have.css', 'max-height').and(value => {
      expect(parseFloat(value)).to.be.greaterThan(0);
    });
    cy.get('footer').should('have.css', 'max-height').and(value => {
      expect(parseFloat(value)).to.be.greaterThan(0);
    });
  });

  it('stops recalculating once the header has nothing left to animate', () => {
    cy.window().then(win => {
      cy.spy(win, 'adjustScrollContainerHeight').as('recalc');
      win.exitFullscreen();
    });
    cy.wait(500);
    cy.get('@recalc').then(spy => {
      const settled = spy.callCount;
      cy.wait(500).then(() => expect(spy.callCount).to.eq(settled));
    });
  });

  it('toggleFullscreen() toggles into and out of fullscreen', () => {
    // Toggle into fullscreen
    cy.window().invoke('toggleFullscreen');
    cy.get('body').should('have.class', 'fullscreen');
    cy.url().should('include', 'fullscreen=1');

    // Toggle back
    cy.window().invoke('toggleFullscreen');
    cy.get('body').should('not.have.class', 'fullscreen');
    cy.url().should('not.include', 'fullscreen=');
  });
});
