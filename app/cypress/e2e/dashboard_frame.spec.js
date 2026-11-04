const RADIUS = '12px';

function corners() {
  return cy.document().then((doc) => {
    const head = getComputedStyle(doc.querySelector('.portui-frame-top > nav'));
    const foot = getComputedStyle(doc.querySelector('.portui-frame-bottom > nav'));
    return {
      topLeft: head.borderBottomLeftRadius,
      topRight: head.borderBottomRightRadius,
      bottomLeft: foot.borderTopLeftRadius,
      bottomRight: foot.borderTopRightRadius,
    };
  });
}

function nextFrame() {
  return cy.window().then((win) => new Cypress.Promise((resolve) => win.requestAnimationFrame(() => win.requestAnimationFrame(resolve))));
}

function layout(html) {
  cy.get('.scroll-container').then(($container) => {
    $container[0].innerHTML = html;
    $container[0].scrollTop = 0;
  });
  cy.window().invoke('portuiFrameUpdate');
  nextFrame();
}

function scrollContainerTo(top) {
  cy.get('.scroll-container').then(($container) => {
    $container[0].scrollTop = top;
    $container[0].dispatchEvent(new Event('scroll'));
  });
  nextFrame();
}

describe('Dashboard frame', () => {
  beforeEach(() => {
    cy.viewport(1440, 900);
    cy.visit('/en/');
    cy.window().should('have.property', 'portuiFrameUpdate');
  });

  it('gives header and footer side borders from one custom property', () => {
    cy.document().then((doc) => {
      doc.documentElement.style.setProperty('--portui-frame-border', 'rgb(255, 0, 0)');
    });
    cy.get('.portui-frame-top').should('have.css', 'border-left-color', 'rgb(255, 0, 0)').and('have.css', 'border-right-style', 'solid');
    cy.get('.portui-frame-bottom').should('have.css', 'border-right-color', 'rgb(255, 0, 0)');
  });

  it('draws one shadow per frame, none inside it, and the card and popup shadows from tokens', () => {
    cy.document().then((doc) => {
      const root = doc.documentElement.style;
      root.setProperty('--portui-shadow-frame', 'rgb(1, 2, 3) 0px 1px 2px 0px');
      root.setProperty('--portui-shadow-card', 'rgb(4, 5, 6) 0px 1px 2px 0px');
      root.setProperty('--portui-shadow-popup', 'rgb(7, 8, 9) 0px 1px 2px 0px');
    });
    cy.get('.portui-frame-top').should('have.css', 'box-shadow', 'rgb(1, 2, 3) 0px 1px 2px 0px');
    cy.get('.portui-frame-bottom').should('have.css', 'box-shadow', 'rgb(1, 2, 3) 0px 1px 2px 0px');
    ['header', '.portui-frame-top .navbar', '.portui-frame-bottom .navbar', 'footer', 'main', '.portui-toolbar'].forEach((selector) => {
      cy.get(selector).should('have.css', 'box-shadow', 'none');
    });
    cy.get('[data-portui-folder="coaching"] .card').should('have.css', 'box-shadow', 'rgb(4, 5, 6) 0px 1px 2px 0px');
    cy.get('#portui-search').type('co');
    cy.get('#portui-picker').should('have.css', 'box-shadow', 'rgb(7, 8, 9) 0px 1px 2px 0px');
  });

  it('rounds all four corners with R while the cards keep their distance', () => {
    nextFrame();
    corners().should('deep.equal', {
      topLeft: RADIUS,
      topRight: RADIUS,
      bottomLeft: RADIUS,
      bottomRight: RADIUS,
    });
  });

  it('squares the corner whose card touches the box and keeps the other column round', () => {
    layout(`
      <div class="row g-0">
        <div class="col-6"><div class="card" style="height:3000px"></div></div>
        <div class="col-6"><div class="card" style="height:100px;margin-top:5px"></div></div>
      </div>`);

    corners().then((radii) => {
      expect(radii.topLeft, 'flush card under the left corner').to.eq('0px');
      expect(radii.topRight, 'right column 5px away').to.eq('5px');
      expect(radii.bottomLeft, 'tall card runs under the footer').to.eq('0px');
      expect(radii.bottomRight, 'short card ends far above the footer').to.eq(RADIUS);
    });
  });

  it('grows the radius back in the gap between two card rows', () => {
    layout(`
      <div class="row g-0">
        <div class="col-12"><div class="card" style="height:500px"></div></div>
        <div class="col-12" style="margin-top:40px"><div class="card" style="height:3000px"></div></div>
      </div>`);

    scrollContainerTo(510);
    corners().its('topLeft').should('eq', RADIUS);

    scrollContainerTo(535);
    corners().its('topLeft').should('eq', '5px');

    scrollContainerTo(560);
    corners().its('topLeft').should('eq', '0px');
  });

  it('recomputes at most once per animation frame while scrolling', () => {
    layout('<div class="card" style="height:4000px"></div>');
    cy.window().then((win) => {
      const frames = cy.spy(win, 'requestAnimationFrame');
      const container = win.document.querySelector('.scroll-container');
      for (let step = 1; step <= 25; step += 1) {
        container.scrollTop = step * 10;
        container.dispatchEvent(new win.Event('scroll'));
      }
      expect(frames.callCount).to.eq(1);
    });
  });
});
