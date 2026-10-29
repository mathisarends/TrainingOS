import { afterEach, expect, it, vi } from 'vitest';
import { QueryClient } from '@tanstack/lit-query';
import { TrainingStore } from '../../src/app/store';
import { DemoTransport } from '../../src/app/demo';
import { configurePreviewTransport } from '../../src/api/request';
import { plans } from '../../src/api/generated';
import type { TrainingSession } from '../../src/shared/types';

afterEach(() => configurePreviewTransport());

it('invalidates generated resource keys after changes and clears all cached user data', async () => {
  configurePreviewTransport(new DemoTransport());
  const client = new QueryClient({
    defaultOptions: { queries: { staleTime: Infinity, retry: false } },
  });
  const store = new TrainingStore(client);
  await store.user();
  const before = await store.dashboard();
  await plans.configurePlan(before.plans[0].id, {
    title: 'Changed plan',
    start_date: before.plans[0].start_date,
    recommendations: true,
  });
  const after = await store.dashboard();
  expect(after.plans[0].title).toBe('Changed plan');
  expect(client.getQueryCache().getAll().length).toBeGreaterThan(0);
  store.clear();
  expect(client.getQueryCache().getAll()).toEqual([]);
});

it('loads history beyond the first page so plan progress stays complete', async () => {
  const demo = new DemoTransport({ seedHistory: true });
  const sample = (await demo.request<{ items: TrainingSession[] }>('/training-sessions?limit=1'))
    .items[0];
  const sessions = Array.from({ length: 117 }, (_, i) => ({ ...sample, id: `history-${i}` }));
  const original = demo.request.bind(demo);
  vi.spyOn(demo, 'request').mockImplementation(
    async <T>(path: string, method?: string, body?: unknown) => {
      if (path.startsWith('/training-sessions?')) {
        const params = new URL(path, 'http://preview.local').searchParams;
        const offset = Number(params.get('offset') ?? 0);
        return { items: sessions.slice(offset, offset + Number(params.get('limit'))) } as T;
      }
      return original<T>(path, method, body);
    },
  );
  configurePreviewTransport(demo);
  const store = new TrainingStore(
    new QueryClient({ defaultOptions: { queries: { retry: false } } }),
  );
  const result = await store.dashboard();
  expect(result.sessions).toHaveLength(117);
  expect(result.sessions.at(-1)?.id).toBe('history-116');
  store.clear();
});
