describe('A page without an iframe parameter', () => {
  beforeEach(() => {
    cy.visit('/');
  });

  it('stays out of fullscreen', () => {
    cy.get('body').should('not.have.class', 'fullscreen');
  });

  it('frames nothing', () => {
    cy.get('#main').find('iframe').should('not.exist');
    cy.url().should('not.include', 'iframe=');
  });

  it('never grows an iframe parameter out of its own URL', () => {
    cy.wait(2000);

    cy.url().then((url) => {
      expect((url.match(/iframe/g) || []).length, 'iframe parameters').to.equal(0);
    });
  });

  it('treats an absent URL as unsafe', () => {
    cy.window().then((win) => {
      expect(win.safeUrl(null), 'null').to.equal(null);
      expect(win.safeUrl(''), 'empty string').to.equal(null);
      expect(win.safeUrl('javascript:alert(1)'), 'script URL').to.equal(null);
      expect(win.safeUrl('/de/'), 'relative path').to.equal(`${win.location.origin}/de/`);
    });
  });
});
