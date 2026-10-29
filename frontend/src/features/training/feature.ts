import { defineFeature, definePage } from 'lit-canon-composition';
import { shell } from '../../app/routing';

export const trainingFeature = defineFeature({
  name: 'training',
  pages: [
    definePage({
      path: '/training',
      title: 'Training',
      load: () => import('./training-view'),
      render: () => shell('training'),
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
