document.addEventListener('portui:ready', () => {
  window.portuiReadyCount = (window.portuiReadyCount || 0) + 1;
  window.portui.chips.set('agile-coach', [
    {
      kind: 'lock',
      tone: 'primary',
      icon: 'fa-solid fa-lock',
      label: 'Request access',
      href: 'https://access.example.org/?application=agile-coach',
      newTab: true,
      state: 'request',
    },
    {
      kind: 'health',
      tone: 'info',
      icon: 'fa-solid fa-circle-pause',
      label: 'Paused',
      detail: ' · 13:05',
      state: 'paused',
    },
  ]);
  window.portui.chips.set('cybermaster', [
    { kind: 'lock', tone: 'primary', icon: 'fa-solid fa-right-to-bracket', label: 'Sign in', state: 'signin' },
    { kind: 'health', tone: 'secondary', icon: 'fa-solid fa-circle-question', label: 'Unknown', state: 'unknown' },
  ]);
  window.portui.chips.set('infinito-nexus', [
    { kind: 'health', tone: 'success', icon: 'fa-solid fa-circle-check', label: 'Running', detail: ' · 13:05', state: 'running' },
  ]);
});
