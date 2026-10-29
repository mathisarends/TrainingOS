// @vitest-environment happy-dom
import { afterEach, expect, it, vi } from 'vitest';
import { ContextProvider } from '@lit/context';
import { QueryClient } from '@tanstack/lit-query';
import { TrainingApp } from '../../src/app/training-app';
import { TrainingStore } from '../../src/app/store';
import { DemoTransport } from '../../src/app/demo';
import { configurePreviewTransport } from '../../src/api/request';
import { transportContext, storeContext, navigationContext } from '../../src/app/context';
import {
  trainingOverviewHref,
  trainingSelectionFromSearch,
  type TrainingSelection,
} from '../../src/app/routing';
import type { Plan, TrainingSession } from '../../src/shared/types';

const clients: QueryClient[] = [];
afterEach(() => {
  document.body.replaceChildren();
  clients.splice(0).forEach((client) => client.clear());
  configurePreviewTransport();
  history.replaceState(null, '', '/');
});

async function overview(deletedPlan = false) {
  const api = new DemoTransport({ seedHistory: true });
  const plans = (await api.request<{ items: Plan[] }>('/plans')).items;
  const sessions = (await api.request<{ items: TrainingSession[] }>('/training-sessions?limit=100'))
    .items;
  const recorded = sessions.find(
    (session) => session.day_name === 'Ganzkörper B' && session.week === 1,
  )!;
  const selection = { planId: recorded.plan_id, dayId: recorded.day_id, week: recorded.week };
  if (deletedPlan) await api.request(`/plans/${recorded.plan_id}`, 'DELETE');
  const select = (target: TrainingSelection) => {
    history.replaceState(null, '', trainingOverviewHref(target, true));
    app.trainingSelection = trainingSelectionFromSearch(location.search);
  };
  history.replaceState(null, '', trainingOverviewHref(selection, true));
  configurePreviewTransport(api);
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  clients.push(client);
  const host = document.createElement('div');
  const app = new TrainingApp();
  app.page = 'training';
  app.trainingSelection = trainingSelectionFromSearch(location.search);
  const navigate = vi.fn(async (path: string) => {
    history.pushState(null, '', path);
    app.trainingSelection = trainingSelectionFromSearch(location.search);
  });
  const providers = [
    new ContextProvider(host, { context: storeContext, initialValue: new TrainingStore(client) }),
    new ContextProvider(host, { context: transportContext, initialValue: api }),
    new ContextProvider(host, { context: navigationContext, initialValue: { navigate } }),
  ];
  document.body.append(host);
  providers.forEach((provider) => provider.hostConnected());
  host.append(app);
  await vi.waitFor(() =>
    expect(
      app.querySelector(deletedPlan ? '.empty h3' : '.training-context-title h1'),
    ).not.toBeNull(),
  );
  return { app, api, navigate, plans, recorded, select, selection };
}

it('opens the normal overview at the calendar entry’s exact plan, day and week', async () => {
  const { app, recorded } = await overview();
  expect(app.querySelector('.training-context-title h1')?.textContent).toContain('Ganzkörper B');
  expect(app.querySelector('.training-context-title h1')?.textContent).toContain('Woche 1 von 6');
  expect(app.querySelector('[aria-pressed=true]')?.textContent?.trim()).toBe('B');
  expect(app.querySelector('.overview-start')?.textContent).toContain('Training ansehen');
  expect(app.querySelector('training-view')).toBeNull();
  expect(new URLSearchParams(location.search).get('day')).toBe(recorded.day_id);
});

it('updates query-only selections and keeps day/week navigation in the URL', async () => {
  const { app, select, plans, navigate } = await overview();
  const other = plans[1];
  select({ planId: other.id, dayId: other.days[2].id, week: 4 });
  await app.updateComplete;
  expect(app.querySelector('.training-context-title .eyebrow')?.textContent).toBe(other.title);
  expect(app.querySelector('.training-context-title h1')?.textContent).toContain(
    other.days[2].name,
  );
  expect(app.querySelector('.training-context-title h1')?.textContent).toContain('Woche 4 von 6');
  app.querySelector<HTMLButtonElement>('[aria-label="Nächste Woche"]')!.click();
  await app.updateComplete;
  expect(new URLSearchParams(location.search).get('week')).toBe('5');
  expect(app.querySelector('.training-context-title h1')?.textContent).toContain('Woche 5 von 6');
  expect(navigate).toHaveBeenCalledOnce();
  app.querySelector<HTMLButtonElement>('.day-pagination button')!.click();
  await app.updateComplete;
  expect(new URLSearchParams(location.search).get('day')).toBe(other.days[0].id);
  expect(app.querySelector('[aria-pressed=true]')?.textContent?.trim()).toBe('A');
});

it.each(['plan', 'day', 'week'] as const)(
  'never falls back to a different training day for an unavailable %s',
  async (key) => {
    const { app, select, selection } = await overview();
    select({
      ...selection,
      ...(key === 'plan'
        ? { planId: 'removed-plan' }
        : key === 'day'
          ? { dayId: 'removed-day' }
          : { week: 99 }),
    });
    await app.updateComplete;
    expect(app.querySelector('.empty h3')?.textContent).toContain('Trainingstag nicht verfügbar');
    expect(app.querySelector('.training-context')).toBeNull();
    expect(app.querySelector('.overview-start')).toBeNull();
  },
);

it('keeps recorded data explicitly accessible when the original plan was deleted', async () => {
  const { app, recorded } = await overview(true);
  expect(app.querySelector('.empty h3')?.textContent).toContain('Trainingstag nicht verfügbar');
  expect(app.querySelector(`a[href="/training/${recorded.id}?demo=1"]`)?.textContent).toContain(
    'Gespeichertes Training ansehen',
  );
  expect(app.querySelector('.training-context')).toBeNull();
});
