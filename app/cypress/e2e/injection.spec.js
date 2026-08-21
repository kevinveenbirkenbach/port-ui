// cypress/e2e/injection.spec.js

describe('Untrusted content in the modal', () => {
  const base = {
    name: 'Test Item',
    identifier: 'ABC123',
    icon: { class: 'fa fa-test' },
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

  describe('markdown rendered into innerHTML', () => {
    it('strips a plain script URL', () => {
      open({
        warning: '[click me](javascript:window.__xss = true)',
        info: '![x](data:text/html;base64,PHNjcmlwdD4=)',
      });

      cy.get('#dynamicModalWarningText').find('a').should('not.exist');
      cy.get('#dynamicModalWarningText').should('contain.text', 'click me');
      cy.get('#dynamicModalInfoText').find('img').should('not.exist');
      cy.window().should('not.have.property', '__xss');
    });

    it('strips a script URL hidden behind character references', () => {
      open({
        warning:
          '[a](&#106;avascript:window.__xss=1) [b](&#x6A;avascript:window.__xss=1)',
        info: '[c](java&Tab;script:window.__xss=1) [d](java&NewLine;script:window.__xss=1)',
      });

      cy.get('#dynamicModalWarningText').find('a').should('not.exist');
      cy.get('#dynamicModalInfoText').find('a').should('not.exist');
      cy.window().should('not.have.property', '__xss');
    });

    it('strips a script URL written as a reference-style link', () => {
      open({
        warning: '[click me][ref]\n\n[ref]: &#106;avascript:window.__xss=1',
      });

      cy.get('#dynamicModalWarningText').find('a').should('not.exist');
      cy.window().should('not.have.property', '__xss');
    });

    it('neutralises raw HTML', () => {
      open({
        warning: '<img src=x onerror="window.__xss = true">',
        info: '<a href="javascript:window.__xss = true">x</a>',
      });

      cy.get('#dynamicModalWarningText').find('img').should('not.exist');
      cy.get('#dynamicModalWarningText').should('contain.text', 'onerror');
      cy.get('#dynamicModalInfoText').find('a').should('not.exist');
      cy.window().should('not.have.property', '__xss');
    });

    it('neutralises raw HTML used as the text of a stripped link', () => {
      open({ warning: '[<img src=x onerror="window.__xss = true">](javascript:bad)' });

      cy.get('#dynamicModalWarningText').find('img').should('not.exist');
      cy.window().should('not.have.property', '__xss');
    });

    it('keeps ordinary markdown', () => {
      open({ warning: 'See [Matrix](https://matrix.org/) and **mind** this' });

      cy.get('#dynamicModalWarningText')
        .find('a')
        .should('have.attr', 'href', 'https://matrix.org/');
      cy.get('#dynamicModalWarningText').find('strong').should('have.text', 'mind');
    });
  });

  describe('values interpolated outside markdown', () => {
    it('does not treat the name or the icon class as markup', () => {
      open({
        name: '<img src=x onerror="window.__xss = true">',
        icon: { class: 'fa" onmouseover="window.__xss = true' },
        alternatives: [
          {
            name: '<img src=y onerror="window.__xss = true">',
            identifier: 'ALT1',
            icon: { class: 'fa-alt' },
          },
        ],
      });

      cy.get('#dynamicModalLabel').find('img').should('not.exist');
      cy.get('#dynamicModalLabel').should('contain.text', 'onerror');
      cy.get('#dynamicAlternativesList').find('img').should('not.exist');
      cy.get('#dynamicAlternativesList').should('contain.text', 'onerror');
      cy.window().should('not.have.property', '__xss');
    });
  });

  describe('the link the modal offers', () => {
    it('drops a URL that uses an unsafe scheme', () => {
      open({ url: 'javascript:window.__xss = true', description: 'Bad' });

      cy.get('#dynamicModalLinkHref').should('not.have.attr', 'href');
      cy.get('#dynamicModalLinkHref').should('have.text', 'Bad');
      cy.window().should('not.have.property', '__xss');
    });

    it('keeps an ordinary URL', () => {
      open({ url: 'https://example.com', description: 'Good' });

      cy.get('#dynamicModalLinkHref').should(
        'have.attr',
        'href',
        'https://example.com',
      );
    });

    it('keeps a mailto URL', () => {
      open({ url: 'mailto:kevin@veen.world', description: 'Write' });

      cy.get('#dynamicModalLinkHref').should(
        'have.attr',
        'href',
        'mailto:kevin@veen.world',
      );
    });

    it('restores the link after a popup whose URL was dropped', () => {
      open({ url: 'javascript:window.__xss = true', description: 'Bad' });
      cy.get('#dynamicModalLinkHref').should('not.have.attr', 'href');

      open({ url: 'https://example.com', description: 'Good' });
      cy.get('#dynamicModalLinkHref').should(
        'have.attr',
        'href',
        'https://example.com',
      );
    });

    it('does not let one popup iframe handler outlive it', () => {
      open({ url: 'https://a.test/', description: 'A', iframe: true });
      cy.get('#dynamicModalLinkHref').should('have.class', 'iframe');

      open({ url: 'https://b.test/', description: 'B' });

      cy.get('#dynamicModalLinkHref').should('not.have.class', 'iframe');
      cy.get('#dynamicModalLinkHref').should($anchor => {
        expect($anchor[0].onclick, 'stale click handler').to.equal(null);
      });
    });
  });
});

describe('Untrusted content reaching the iframe', () => {
  const AFTER_THE_FADE = 3000;

  it('refuses to open a script URL handed over by the modal', () => {
    cy.visit('/');
    cy.window().invoke('openDynamicPopup', {
      name: 'Bad',
      icon: { class: 'fa fa-test' },
      url: 'javascript:window.__xss = true',
      description: 'Watch',
      iframe: true,
    });

    cy.get('#dynamicModalLinkHref').click({ force: true });

    cy.wait(AFTER_THE_FADE);
    cy.get('#main').find('iframe').should('not.exist');
    cy.window().should('not.have.property', '__xss');
  });

  it('refuses a script URL supplied through the query string', () => {
    cy.visit('/?iframe=javascript:window.__xss%20%3D%20true');

    cy.wait(AFTER_THE_FADE);
    cy.get('#main').find('iframe').should('not.exist');
    cy.window().should('not.have.property', '__xss');
  });

  it('still opens an ordinary URL from the query string', () => {
    cy.visit('/?iframe=https://example.com/');

    cy.get('#main')
      .find('iframe', { timeout: AFTER_THE_FADE })
      .should('have.attr', 'src', 'https://example.com/');
  });
});
