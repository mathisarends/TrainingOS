// @vitest-environment happy-dom
import { afterEach, expect, it } from 'vitest';
import { HistoryView } from '../../../src/features/training/history-view';
import { DemoTransport } from '../../../src/app/demo';
import type { TrainingSession } from '../../../src/shared/types';

afterEach(() => document.body.replaceChildren());
it('crosses year boundaries when moving the calendar and returns to the current month', async () => {
  const view = new HistoryView();
  document.body.append(view);
  await view.updateComplete;
  const year = new Date().getFullYear();
  for (let i = 0; i < 12; i++) {
    view.querySelector<HTMLButtonElement>('[aria-label="Vorheriger Monat"]')!.click();
    await view.updateComplete;
  }
  expect(view.querySelector('.history-month')!.textContent).toContain(String(year - 1));
  expect(view.querySelectorAll('.calendar-day').length % 7).toBe(0);
  Array.from(view.querySelectorAll('button'))
    .find((b) => b.textContent?.trim() === 'Heute')!
    .click();
  await view.updateComplete;
  expect(view.querySelector('.history-month')!.textContent).toContain(String(year));
});

it('links calendar and list entries to the plan day and week, preserving preview mode', async () => {
  const demo = new DemoTransport({ seedHistory: true });
  const sample = (await demo.request<{ items: TrainingSession[] }>('/training-sessions?limit=1'))
    .items[0];
  const view = new HistoryView();
  view.demo = true;
  view.sessions = [sample];
  document.body.append(view);
  await view.updateComplete;
  const href = `/training?plan=${sample.plan_id}&day=${sample.day_id}&week=${sample.week}&demo=1`;
  expect(view.querySelector('.calendar-event')?.getAttribute('href')).toBe(href);
  view.querySelector<HTMLButtonElement>('[aria-label="Liste anzeigen"]')!.click();
  await view.updateComplete;
  expect(view.querySelector('.history-row')?.getAttribute('href')).toBe(href);
});

it('keeps same-date training sessions linked to their own plan day', async () => {
  const demo = new DemoTransport({ seedHistory: true });
  const [sample, second] = (
    await demo.request<{ items: TrainingSession[] }>('/training-sessions?limit=2')
  ).items;
  const view = new HistoryView();
  view.sessions = [sample, { ...second, started_at: sample.started_at }];
  document.body.append(view);
  await view.updateComplete;
  expect(
    [...view.querySelectorAll('.calendar-event')].map((link) => link.getAttribute('href')),
  ).toEqual([
    `/training?plan=${sample.plan_id}&day=${sample.day_id}&week=${sample.week}`,
    `/training?plan=${second.plan_id}&day=${second.day_id}&week=${second.week}`,
  ]);
});
