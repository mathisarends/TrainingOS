import { defineFeature, definePage } from 'lit-canon-composition';
import { shell, trainingSelectionFromSearch } from '../../app/routing';

export const trainingFeature = defineFeature({
  name: 'training',
  pages: [
    definePage({
      path: '/training',
      title: 'Training',
      load: () => import('./training-view'),
      render: () => shell('training', '', trainingSelectionFromSearch(location.search)),
    }),
    definePage({
      path: '/training/:id',
      title: 'Training',
      load: () => import('./training-view'),
      render: ({ id }) => shell('training', id),
    }),
    definePage({
      path: '/logs',
      title: 'Logs',
      load: () => import('./history-view'),
      render: () => shell('history'),
    }),
  ],
});
