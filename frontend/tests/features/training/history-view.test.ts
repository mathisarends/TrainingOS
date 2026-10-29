// @vitest-environment happy-dom
import { afterEach, expect, it } from 'vitest';
import { HistoryView } from '../../../src/features/training/history-view';

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
  expect(view.querySelector('h1')!.textContent).toContain(String(year - 1));
  expect(view.querySelectorAll('.calendar-day').length % 7).toBe(0);
  Array.from(view.querySelectorAll('button'))
    .find((b) => b.textContent?.trim() === 'Heute')!
    .click();
  await view.updateComplete;
  expect(view.querySelector('h1')!.textContent).toContain(String(year));
});
