// @vitest-environment happy-dom
import { afterEach, expect, it, vi } from 'vitest';
import { AccountView } from '../../../src/features/account/account-view';
import { DemoTransport } from '../../../src/app/demo';
import type { User } from '../../../src/shared/types';

afterEach(() => document.body.replaceChildren());

async function settings() {
  const api = new DemoTransport();
  const view = new AccountView();
  view.api = api;
  view.user = await api.request<User>('/auth/me');
  document.body.append(view);
  await view.updateComplete;
  const form = view.querySelector('form')!;
  form.querySelector<HTMLSelectElement>('[name=unit]')!.value = 'lb';
  form.querySelector<HTMLSelectElement>('[name=effort_scale]')!.value = 'rir';
  form.querySelector<HTMLInputElement>('[name=rounding_step]')!.value = '5';
  form.querySelector<HTMLInputElement>('[name=timezone]')!.value = 'Europe/London';
  return { api, view, form };
}

it('saves every preference from the row layout and emits the committed user once', async () => {
  const { api, view, form } = await settings();
  const request = vi.spyOn(api, 'request');
  const changed = vi.fn();
  view.addEventListener('user-changed', changed);
  form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
  await vi.waitFor(() =>
    expect(view.querySelector('[role=status]')?.textContent).toContain('gespeichert'),
  );
  expect(request).toHaveBeenCalledOnce();
  expect(changed).toHaveBeenCalledOnce();
  const user = await api.request<User>('/auth/me');
  expect(user).toMatchObject({
    unit: 'lb',
    effort_scale: 'rir',
    rounding_step: '5',
    timezone: 'Europe/London',
  });
});

it('retains changed fields after a failed save and supports an explicit retry', async () => {
  const { api, view, form } = await settings();
  const request = vi.spyOn(api, 'request').mockRejectedValueOnce(new Error('Offline'));
  form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
  await vi.waitFor(() =>
    expect(view.querySelector('[role=alert]')?.textContent).toContain('Offline'),
  );
  expect(form.querySelector<HTMLSelectElement>('[name=unit]')!.value).toBe('lb');
  expect(form.querySelector<HTMLSelectElement>('[name=effort_scale]')!.value).toBe('rir');
  expect(form.querySelector<HTMLInputElement>('[name=rounding_step]')!.value).toBe('5');
  expect(form.querySelector<HTMLInputElement>('[name=timezone]')!.value).toBe('Europe/London');
  expect(view.querySelector('[role=status]')).toBeNull();
  form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
  await vi.waitFor(() =>
    expect(view.querySelector('[role=status]')?.textContent).toContain('gespeichert'),
  );
  expect(request).toHaveBeenCalledTimes(2);
});
