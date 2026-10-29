import { defineFeature, definePage } from 'lit-canon-composition';
import { shell } from '../../app/routing';

export const accountFeature = defineFeature({
  name: 'account',
  pages: [
    definePage({
      path: '/profile',
      title: 'Konto',
      load: () => import('./profile-view'),
      render: () => shell('account'),
    }),
    definePage({
      path: '/profile/best-performance',
      title: 'Bestleistungen',
      load: () => import('./records-view'),
      render: () => shell('records'),
    }),
    definePage({
      path: '/profile/settings',
      title: 'Einstellungen',
      load: () => import('./account-view'),
      render: () => shell('settings'),
    }),
    definePage({
      path: '/profile/data',
      title: 'Konto',
      load: () => import('./profile-view'),
      render: () => shell('account'),
    }),
  ],
});
