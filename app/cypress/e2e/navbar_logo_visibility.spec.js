describe('Navbar Logo Visibility', () => {
  beforeEach(() => {
    cy.visit('/');
  });

  it('should have #navbar_logo present in the DOM', () => {
    cy.get('#navbar_logo').should('exist');
  });

  it('should be invisible (opacity 0) by default', () => {
    cy.get('#navbar_logo')
      .should('exist')
      .and('have.css', 'opacity', '0');
  });

  it('should become visible (opacity 1) after entering fullscreen', () => {
    cy.window().then(win => {
      win.enterFullscreen();
    });
    cy.get('#navbar_logo', { timeout: 4000 })
      .should('have.css', 'opacity', '1');
  });

  it('should become invisible again (opacity 0) after exiting fullscreen', () => {
    cy.window().then(win => {
      win.enterFullscreen();
      win.exitFullscreen();
    });
    cy.get('#navbar_logo', { timeout: 4000 })
      .should('have.css', 'opacity', '0');
  });
});
