'use strict';
/**
 * Correctness only — eslint's recommended set, no stylistic rules.
 *
 * The browser scripts are plain <script> tags sharing one global scope: each
 * file declares some functions and calls others declared elsewhere. That is why
 * they are listed as globals and why no-redeclare is off — the declaring file
 * would otherwise be reported for defining its own function.
 */
const js = require('@eslint/js');
const globals = require('globals');

// Vendored libraries plus the functions static/js files call across each other.
// Keep this to names that really cross a file boundary. Every superfluous
// entry is a permanent no-undef blind spot for a typo of that name.
const SHARED = {
  bootstrap: 'readonly',
  marked: 'readonly',
  $: 'readonly',
  jQuery: 'readonly',
  openDynamicPopup: 'readonly',
  closeAllModals: 'readonly',
  isSafeUrl: 'readonly',
  openIframe: 'readonly',
  enterFullscreen: 'readonly',
  exitFullscreen: 'readonly',
  setFullWidth: 'readonly',
  initFullWidthFromUrl: 'readonly',
  adjustScrollContainerHeight: 'readonly',
  updateCustomScrollbar: 'readonly',
};

module.exports = [
  { ignores: ['node_modules/**', 'static/vendor/**', 'cypress/screenshots/**'] },
  {
    files: ['static/js/**/*.js'],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: 'script',
      globals: { ...globals.browser, ...SHARED },
    },
    rules: {
      ...js.configs.recommended.rules,
      'no-redeclare': 'off',
      // vars: 'local' — a top-level function here is the API other files and
      // the templates call, so only unused locals are a defect.
      'no-unused-vars': [
        'error',
        { vars: 'local', args: 'none', caughtErrors: 'none' },
      ],
    },
  },
  {
    files: ['cypress/**/*.js'],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: 'script',
      globals: {
        ...globals.browser,
        ...globals.mocha,
        cy: 'readonly',
        Cypress: 'readonly',
        expect: 'readonly',
        assert: 'readonly',
      },
    },
    rules: js.configs.recommended.rules,
  },
  {
    files: ['scripts/**/*.js', 'cypress.config.js', 'eslint.config.js'],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: 'commonjs',
      globals: globals.node,
    },
    rules: js.configs.recommended.rules,
  },
];
