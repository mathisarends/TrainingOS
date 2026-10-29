// @vitest-environment happy-dom
import { afterEach, expect, it, vi } from 'vitest';
import { PlansView } from '../../../src/features/plans/plans-view';
import { DemoTransport } from '../../../src/app/demo';
import type { Plan, Transport, User } from '../../../src/shared/types';
import { ApiError } from '../../../src/shared/api';

afterEach(() => document.body.replaceChildren());
it('creates named days with Monday-based weekdays, without activating a partial plan', async () => {
  const demo = new DemoTransport();
  const plan = (await demo.request<{ items: Plan[] }>('/plans')).items[0];
  const view = new PlansView();
  const request = vi.fn().mockResolvedValue(plan);
  view.api = { request } as Transport;
  view.user = await demo.request<User>('/auth/me');
  document.body.append(view);
  await view.updateComplete;
  Array.from(view.querySelectorAll('button'))
    .find((b) => b.textContent?.includes('Neuer Plan'))!
    .click();
  await view.updateComplete;
  view.querySelector<HTMLInputElement>('[name=title]')!.value = 'Mein Kraftplan';
  view
    .querySelector('form')!
    .dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
  await view.updateComplete;
  expect(request).not.toHaveBeenCalled();
  expect(view.querySelector('h2')!.textContent).toBe('Kalender');
  view.querySelector<HTMLInputElement>('[name=day-0]')!.value = 'Unterkörper';
  view
    .querySelector('form')!
    .dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
  await vi.waitFor(() => expect(request).toHaveBeenCalledOnce());
  await view.updateComplete;
  expect(
    view.querySelector<HTMLSelectElement>('[aria-label="Trainingsplan auswählen"]')!.value,
  ).toBe(plan.id);
  expect(request).toHaveBeenCalledWith(
    '/plans',
    'POST',
    expect.objectContaining({
      title: 'Mein Kraftplan',
      weeks: 6,
      days: [
        { name: 'Unterkörper', weekday: 0 },
        { name: 'Mittwoch', weekday: 2 },
        { name: 'Freitag', weekday: 4 },
      ],
    }),
  );
  Array.from(view.querySelectorAll('button'))
    .find((b) => b.textContent?.includes('Neuer Plan'))!
    .click();
  await view.updateComplete;
  expect(view.querySelector('dialog h2')?.textContent?.trim()).toBe('Allgemein');
  expect(view.querySelector<HTMLInputElement>('dialog [name=title]')!.value).toBe('');
});

it('submits the preview revision and retains it for review when the backend rejects stale progression', async () => {
  const demo = new DemoTransport();
  const view = new PlansView();
  view.api = demo;
  view.user = await demo.request<User>('/auth/me');
  view.plans = (await demo.request<{ items: Plan[] }>('/plans')).items;
  document.body.append(view);
  await view.updateComplete;
  Array.from(view.querySelectorAll('button'))
    .find((b) => b.textContent?.includes('Auto-Progression'))!
    .click();
  await view.updateComplete;
  view
    .querySelector('.progression-form')!
    .dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
  await vi.waitFor(() => expect(view.querySelector('.progression-preview')).not.toBeNull());
  const request = vi
    .spyOn(demo, 'request')
    .mockRejectedValue(new ApiError(409, 'Revision changed'));
  Array.from(view.querySelectorAll('button'))
    .find((b) => b.textContent?.includes('Folgewochen ersetzen'))!
    .click();
  await vi.waitFor(() =>
    expect(view.querySelector('[role=alert]')?.textContent).toContain('Revision changed'),
  );
  expect(request).toHaveBeenCalledOnce();
  expect(request).toHaveBeenCalledWith('/plans/preview-plan/progression/apply', 'POST', {
    increment: '0.5',
    deload: true,
    expected_revision: 1,
  });
  expect(view.querySelector('.progression-preview')).not.toBeNull();
  expect(view.querySelector('[role=status]')).toBeNull();
});
