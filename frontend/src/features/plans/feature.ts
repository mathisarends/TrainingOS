import { defineFeature, definePage } from 'lit-canon-composition';
import { shell } from '../../app/routing';

export const plansFeature = defineFeature({
  name: 'plans',
  pages: [
    definePage({ path: '/', title: 'Training', render: () => shell('home') }),
    definePage({
      path: '/plans',
      title: 'Plan bearbeiten',
      load: () => import('./plans-view'),
      render: () => shell('plans'),
    }),
    definePage({
      path: '/plans/new',
      title: 'Neuer Plan',
      load: () => import('./plans-view'),
      render: () => shell('plans', 'new'),
    }),
    definePage({
      path: '/plans/:id',
      title: 'Plan bearbeiten',
      load: () => import('./plans-view'),
      render: ({ id }) => shell('plans', id),
    }),
  ],
});
