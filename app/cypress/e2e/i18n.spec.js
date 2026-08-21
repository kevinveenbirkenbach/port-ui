// cypress/e2e/i18n.spec.js

const GERMAN_BROWSER = { headers: { 'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8' } };

describe('Language negotiation', () => {
  it('serves English to an English browser', () => {
    cy.visit('/', { headers: { 'Accept-Language': 'en-US,en;q=0.9' } });
    cy.get('html').should('have.attr', 'lang', 'en');
    cy.get('footer.footer a.iframe-link').should('contain.text', 'Imprint');
  });

  it('serves German to a German browser', () => {
    cy.visit('/', GERMAN_BROWSER);
    cy.get('html').should('have.attr', 'lang', 'de');
    cy.get('footer.footer a.iframe-link').should('contain.text', 'Impressum');
  });

  it('falls back to English for an unsupported browser language', () => {
    cy.visit('/', { headers: { 'Accept-Language': 'xx-XX' } });
    cy.get('html').should('have.attr', 'lang', 'en');
  });

  it('lets the URL prefix override the browser language', () => {
    cy.visit('/fr/', GERMAN_BROWSER);
    cy.get('html').should('have.attr', 'lang', 'fr');
    cy.get('footer.footer a.iframe-link').should('contain.text', 'Mentions légales');
  });

  it('rejects an unsupported language code', () => {
    cy.request({ url: '/xx/', failOnStatusCode: false })
      .its('status')
      .should('eq', 404);
  });

  it('does not turn unrelated single-segment paths into redirects', () => {
    ['/robots.txt', '/favicon.ico', '/sitemap.xml'].forEach(path => {
      cy.request({ url: path, failOnStatusCode: false, followRedirect: false })
        .its('status')
        .should('eq', 404);
    });
  });

  it('marks the negotiated route as varying by language', () => {
    cy.request('/')
      .its('headers.vary')
      .should('contain', 'Accept-Language');
  });
});

describe('Language switcher', () => {
  beforeEach(() => {
    cy.viewport(1280, 720);
    cy.visit('/en/');
  });

  it('names the active language and offers every ISO 639-1 code', () => {
    cy.get('#navbarDropdownLanguage')
      .should('have.attr', 'data-bs-toggle', 'dropdown')
      .and('contain.text', 'English');

    cy.get('#navbarDropdownLanguage')
      .parent('.nav-item')
      .find('> .dropdown-menu a.dropdown-item')
      .should('have.length', 184);
  });

  it('marks the active language', () => {
    cy.get('#navbarDropdownLanguage').click();
    cy.get('.dropdown-menu a.dropdown-item.active[hreflang="en"]').should('exist');
  });

  it('navigates to the chosen language', () => {
    cy.get('#navbarDropdownLanguage').click();
    cy.get('.dropdown-menu a.dropdown-item[hreflang="de"]')
      .should('have.text', 'Deutsch')
      .click();

    cy.url().should('match', /\/de\/$/);
    cy.get('html').should('have.attr', 'lang', 'de');
  });
});

describe('Translated interface strings', () => {
  it('translates the strings rendered by the templates', () => {
    cy.visit('/de/');
    cy.get('#dynamicCopyButton').should('have.text', 'Kopieren');
    cy.get('#dynamicChildrenSection h6').should('have.text', 'Optionen:');
    cy.get('#dynamicAlternativesSection h6').should('have.text', 'Alternativen:');
    cy.get('.modal-footer button').should('have.text', 'Schließen');
  });

  it('exposes the catalogue to client-side code', () => {
    cy.visit('/de/');
    cy.window().its('I18N').should('deep.include', {
      Open: 'Öffnen',
      'Open Link': 'Link öffnen',
      'Identifier copied to clipboard!': 'Kennung in die Zwischenablage kopiert!',
    });
  });

  it('leaves the catalogue untranslated in the source language', () => {
    cy.visit('/en/');
    cy.window().its('I18N').should('deep.include', { Open: 'Open' });
  });
});

describe('Strings translated by modal.js', () => {
  const item = {
    name: 'Test Item',
    identifier: 'ABC123',
    icon: { class: 'fa fa-test' },
    alternatives: [
      { name: 'Alt One', identifier: 'ALT1', icon: { class: 'fa fa-alt1' } },
    ],
  };

  beforeEach(() => {
    cy.visit('/de/');
    cy.window().then(win => {
      cy.stub(win.navigator.clipboard, 'writeText').resolves();
      cy.stub(win, 'alert');
    });
  });

  it('translates the button of a list entry', () => {
    cy.window().invoke('openDynamicPopup', item);
    cy.get('#dynamicAlternativesList button').should('have.text', 'Öffnen');
  });

  it('translates the link label when the entry has no description', () => {
    cy.window().invoke('openDynamicPopup', {
      ...item,
      url: 'https://example.com',
      description: null,
    });
    cy.get('#dynamicModalLinkHref').should('have.text', 'Link öffnen');
  });

  it('translates the clipboard confirmation', () => {
    cy.window().invoke('openDynamicPopup', item);
    cy.get('#dynamicCopyButton').click();
    cy.window()
      .its('alert')
      .should('have.been.calledWith', 'Kennung in die Zwischenablage kopiert!');
  });
});

describe('Right-to-left languages', () => {
  it('flips the document and loads the RTL stylesheet', () => {
    cy.visit('/ar/');
    cy.get('html').should('have.attr', 'dir', 'rtl');
    cy.get('link[href*="bootstrap.rtl.min.css"]').should('exist');
    cy.get('link[href*="vendor/bootstrap/css/bootstrap.min.css"]').should('not.exist');
    cy.get('body').should('have.css', 'direction', 'rtl');
  });

  it('keeps left-to-right languages on the default stylesheet', () => {
    cy.visit('/en/');
    cy.get('html').should('have.attr', 'dir', 'ltr');
    cy.get('link[href*="bootstrap.rtl.min.css"]').should('not.exist');
  });

  it('actually serves the RTL stylesheet it links to', () => {
    cy.visit('/ar/');
    cy.get('link[href*="bootstrap.rtl.min.css"]')
      .should('have.attr', 'href')
      .then(href => {
        cy.request(href).its('status').should('eq', 200);
      });
  });
});

describe('Translated interface details', () => {
  it('translates the strings only a screen reader sees', () => {
    cy.visit('/de/');

    cy.get('#dynamicModal .btn-close').should('have.attr', 'aria-label', 'Schließen');
  });

  it('translates the alert headings', () => {
    cy.visit('/fr/');

    cy.get('#dynamicModalWarning h5').should('contain.text', 'Avertissement');
    cy.get('#dynamicModalInfo h5').should('contain.text', 'Informations');
  });

  it('translates the language switcher tooltip', () => {
    cy.visit('/de/');

    cy.get('#navbarDropdownLanguage').should('have.attr', 'title', 'Sprache');
  });

  it('tags each switcher entry with its own language', () => {
    cy.visit('/en/');

    cy.get('.dropdown-menu a.dropdown-item[hreflang="ja"]').should(
      'have.attr',
      'lang',
      'ja',
    );
  });

  it('scrolls inside the language menu instead of past the page', () => {
    cy.viewport(1280, 720);
    cy.visit('/en/');
    cy.get('#navbarDropdownLanguage').click();

    cy.get('.dropdown-menu.language-menu').should($menu => {
      const menu = $menu[0];
      expect(menu.scrollHeight, 'taller than it shows').to.be.greaterThan(
        menu.clientHeight,
      );
      expect(menu.getBoundingClientRect().height).to.be.lessThan(720);
      expect(getComputedStyle(menu).overflowY).to.eq('auto');
    });
  });

  it('offers the switcher in the header only', () => {
    cy.viewport(1280, 720);
    cy.visit('/en/');

    cy.get('#navbarNavheader #navbarDropdownLanguage').should('exist');
    cy.get('#navbarNavfooter #navbarDropdownLanguage').should('not.exist');
  });
});

describe('Search engine metadata', () => {
  beforeEach(() => {
    cy.visit('/de/');
  });

  it('declares an alternate for every language plus a default', () => {
    cy.get('link[rel="alternate"][hreflang]').should('have.length', 185);
    cy.get('link[rel="alternate"][hreflang="x-default"]').should('exist');
    cy.get('link[rel="alternate"][hreflang="ja"]')
      .should('have.attr', 'href')
      .and('match', /\/ja\/$/);
  });

  it('points the canonical URL at the language actually served', () => {
    cy.get('link[rel="canonical"]').should('have.attr', 'href').and('match', /\/de\/$/);
  });
});
