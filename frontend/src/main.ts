import 'urlpattern-polyfill';
import './style.css';
import './app/training-app';
import { html } from 'lit';
import { createApp, provide } from 'lit-canon-composition';
import { QueryClient, queryClientContext } from '@tanstack/lit-query';
import { plansFeature } from './features/plans/feature';
import { trainingFeature } from './features/training/feature';
import { catalogFeature } from './features/catalog/feature';
import { accountFeature } from './features/account/feature';
import { authFeature } from './features/auth/feature';
import { transportContext, storeContext, navigationContext } from './app/context';
import { TrainingStore } from './app/store';
import { DemoTransport } from './app/demo';
import { HttpTransport } from './shared/api';
import { configurePreviewTransport } from './api/request';
import { migrateHashRoute } from './app/routing';

const demo = new URLSearchParams(location.search).get('demo') === '1';
const transport = demo ? new DemoTransport({ seedHistory: true }) : new HttpTransport();
configurePreviewTransport(demo ? transport : undefined);
migrateHashRoute();

const app = createApp({
  root: document.querySelector('#app')!,
  features: [authFeature, plansFeature, trainingFeature, catalogFeature, accountFeature],
  providers: [
    provide(
      queryClientContext,
      () =>
        new QueryClient({
          defaultOptions: {
            queries: {
              retry: false,
              staleTime: 0,
              refetchOnWindowFocus: false,
              structuralSharing: false,
            },
            mutations: { retry: false },
          },
        }),
    ),
    provide(transportContext, () => transport),
    provide(storeContext, (container) => new TrainingStore(container.get(queryClientContext))),
    provide(navigationContext, () => ({
      navigate: (path: string) =>
        app.navigate(path + (demo ? `${path.includes('?') ? '&' : '?'}demo=1` : '')),
    })),
  ],
  notFound: () =>
    html`<div class="empty">
      <h1>Seite nicht gefunden</h1>
      <a class="secondary" href=${demo ? '/?demo=1' : '/'}>Zur Übersicht</a>
    </div>`,
  baseTitle: 'TrainingOS',
});
app.start();
