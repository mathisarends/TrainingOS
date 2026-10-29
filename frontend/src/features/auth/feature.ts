import { defineFeature, definePage } from 'lit-canon-composition';
import { shell } from '../../app/routing';

export const authFeature = defineFeature({
  name: 'auth',
  pages: [
    definePage({ path: '/login', title: 'Anmelden', render: () => shell('login') }),
    definePage({ path: '/register', title: 'Registrieren', render: () => shell('register') }),
    definePage({ path: '/getting-started', title: 'Anmelden', render: () => shell('login') }),
  ],
});
