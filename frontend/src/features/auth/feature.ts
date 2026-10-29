import { defineFeature, definePage } from 'lit-canon-composition';
import { shell } from '../../app/routing';

export const authFeature = defineFeature({
  name: 'auth',
  pages: [
    definePage({ path: '/getting-started', title: 'TrainingOS', render: () => shell('login') }),
  ],
});
