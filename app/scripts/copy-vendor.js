'use strict';
/**
 * Copies third-party browser assets from node_modules into static/vendor/
 * so Flask can serve them without any CDN dependency.
 * Runs automatically via the "postinstall" npm hook.
 */
const fs   = require('fs');
const path = require('path');

const NM     = path.join(__dirname, '..', 'node_modules');
const VENDOR = path.join(__dirname, '..', 'static', 'vendor');

function copyFile(src, dest) {
  fs.mkdirSync(path.dirname(dest), { recursive: true });
  fs.copyFileSync(src, dest);
}

function copyDir(src, dest) {
  fs.mkdirSync(dest, { recursive: true });
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const s = path.join(src, entry.name);
    const d = path.join(dest, entry.name);
    entry.isDirectory() ? copyDir(s, d) : fs.copyFileSync(s, d);
  }
}

// Bootstrap CSS + JS bundle
copyFile(
  path.join(NM, 'bootstrap', 'dist', 'css', 'bootstrap.min.css'),
  path.join(VENDOR, 'bootstrap', 'css', 'bootstrap.min.css')
);
copyFile(
  path.join(NM, 'bootstrap', 'dist', 'js', 'bootstrap.bundle.min.js'),
  path.join(VENDOR, 'bootstrap', 'js', 'bootstrap.bundle.min.js')
);

// Bootstrap Icons CSS + embedded fonts
copyFile(
  path.join(NM, 'bootstrap-icons', 'font', 'bootstrap-icons.css'),
  path.join(VENDOR, 'bootstrap-icons', 'font', 'bootstrap-icons.css')
);
copyDir(
  path.join(NM, 'bootstrap-icons', 'font', 'fonts'),
  path.join(VENDOR, 'bootstrap-icons', 'font', 'fonts')
);

// Font Awesome Free CSS + webfonts
copyFile(
  path.join(NM, '@fortawesome', 'fontawesome-free', 'css', 'all.min.css'),
  path.join(VENDOR, 'fontawesome', 'css', 'all.min.css')
);
copyDir(
  path.join(NM, '@fortawesome', 'fontawesome-free', 'webfonts'),
  path.join(VENDOR, 'fontawesome', 'webfonts')
);

// marked – browser UMD build (path varies by version)
const markedCandidates = [
  path.join(NM, 'marked', 'marked.min.js'),              // v4.x
  path.join(NM, 'marked', 'lib', 'marked.umd.min.js'),   // v5.x
  path.join(NM, 'marked', 'dist', 'marked.min.js'),      // v9+
];
const markedSrc = markedCandidates.find(p => fs.existsSync(p));
if (!markedSrc) throw new Error('marked: no browser UMD build found in node_modules');
copyFile(markedSrc, path.join(VENDOR, 'marked', 'marked.min.js'));

// jQuery
copyFile(
  path.join(NM, 'jquery', 'dist', 'jquery.min.js'),
  path.join(VENDOR, 'jquery', 'jquery.min.js')
);
