// @vitest-environment happy-dom
import { afterEach, expect, it, vi } from 'vitest';
import { BodyweightView } from '../../../src/features/account/bodyweight-view';
import { DemoTransport } from '../../../src/app/demo';
import type { User } from '../../../src/shared/types';

afterEach(() => document.body.replaceChildren());
it('retains the bodyweight entry and shows no success after a rejected write', async () => {
  const demo = new DemoTransport();
  const view = new BodyweightView();
  view.api = demo;
  view.user = await demo.request<User>('/auth/me');
  document.body.append(view);
  await view.updateComplete;
  await vi.waitFor(() => expect(view.querySelector('.add-row')).not.toBeNull());
  await Promise.resolve();
  await view.updateComplete;
  view.querySelector<HTMLButtonElement>('.add-row')!.click();
  await view.updateComplete;
  const form = view.querySelector<HTMLFormElement>('.weight-add-form')!;
  form.querySelector<HTMLInputElement>('[name=weight]')!.value = '82.7';
  vi.spyOn(demo, 'request').mockRejectedValue(new Error('Not saved'));
  form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
  await vi.waitFor(() =>
    expect(view.querySelector('[role=alert]')?.textContent).toContain('Not saved'),
  );
  expect(form.querySelector<HTMLInputElement>('[name=weight]')!.value).toBe('82.7');
  expect(view.querySelector('[role=status]')).toBeNull();
});
