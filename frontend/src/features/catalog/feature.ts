import { defineFeature, definePage } from 'lit-canon-composition';
import { shell } from '../../app/routing';

export const catalogFeature = defineFeature({
  name: 'catalog',
  pages: [
    definePage({
      path: '/profile/exercises',
      title: 'Übungen',
      load: () => import('./catalog-view'),
      render: () => shell('catalog'),
    }),
  ],
});
