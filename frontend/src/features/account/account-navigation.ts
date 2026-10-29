import { html, nothing } from 'lit';

export function accountNavigation(current: 'account' | 'settings' | 'data', demo = false) {
  return html`<nav class="account-tabs" aria-label="Kontobereiche">
    ${[
      { page: 'account', label: 'Konto', path: '/profile' },
      { page: 'settings', label: 'Einstellungen', path: '/profile/settings' },
      { page: 'data', label: 'Meine Daten', path: '/profile/data' },
    ].map(
      (item) =>
        html`<a
          href=${item.path + (demo ? '?demo=1' : '')}
          aria-current=${item.page === current ? 'page' : nothing}
          >${item.label}</a
        >`,
    )}
  </nav>`;
}
