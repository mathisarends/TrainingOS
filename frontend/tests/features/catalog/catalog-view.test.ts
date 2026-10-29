// @vitest-environment happy-dom
import { afterEach, expect, it, vi } from 'vitest';
import { CatalogView } from '../../../src/features/catalog/catalog-view';
import { DemoTransport } from '../../../src/app/demo';
import type { Exercise, User } from '../../../src/shared/types';

afterEach(() => document.body.replaceChildren());
it('keeps a custom exercise form open with its input after a failed save', async () => {
  const demo = new DemoTransport();
  const view = new CatalogView();
  view.api = demo;
  document.body.append(view);
  await view.updateComplete;
  Array.from(view.querySelectorAll('button'))
    .find((b) => b.getAttribute('aria-label') === 'Eigene Übung')!
    .click();
  await view.updateComplete;
  const form = view.querySelector('form')!;
  form.querySelector<HTMLInputElement>('[name=name]')!.value = 'Pausenkniebeuge';
  vi.spyOn(demo, 'request').mockRejectedValue(new Error('Rejected'));
  form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
  await vi.waitFor(() =>
    expect(view.querySelector('[role=alert]')?.textContent).toContain('Rejected'),
  );
  expect(view.querySelector('dialog')?.open).toBe(true);
  expect(form.querySelector<HTMLInputElement>('[name=name]')!.value).toBe('Pausenkniebeuge');
});

async function catalog() {
  const demo = new DemoTransport();
  const view = new CatalogView();
  view.api = demo;
  view.user = await demo.request<User>('/auth/me');
  view.exercises = (await demo.request<{ items: Exercise[] }>('/exercises')).items;
  document.body.append(view);
  await vi.waitFor(() =>
    expect(view.querySelector('[aria-label="Kniebeuge Pause"]')).not.toBeNull(),
  );
  return { demo, view };
}

it('shows the stored category values on the first render without writing them', async () => {
  const { demo, view } = await catalog();
  const request = vi.spyOn(demo, 'request');
  // happy-dom reselects options while they are inserted. Assert the selected HTML contract;
  // the native selected values are also verified in the browser screenshots workflow.
  expect(
    view.querySelector<HTMLOptionElement>('[aria-label="Kniebeuge Pause"] option[selected]')!.value,
  ).toBe('240');
  expect(
    view.querySelector<HTMLOptionElement>('[aria-label="Kniebeuge Sätze"] option[selected]')!.value,
  ).toBe('3');
  expect(
    view.querySelector<HTMLOptionElement>(
      '[aria-label="Kniebeuge Wiederholungen"] option[selected]',
    )!.value,
  ).toBe('7');
  expect(
    view.querySelector<HTMLOptionElement>('[aria-label="Kniebeuge RPE"] option[selected]')!.value,
  ).toBe('7.5');
  expect(request).not.toHaveBeenCalled();
});

it('renames inline once and keeps the draft after a failed request until an explicit retry', async () => {
  const { demo, view } = await catalog();
  const input = view.querySelector<HTMLInputElement>('[aria-label="Kniebeuge Name"]')!;
  const request = vi.spyOn(demo, 'request').mockRejectedValueOnce(new Error('Offline'));
  input.value = 'Kniebeuge mit Pause';
  input.dispatchEvent(new Event('input', { bubbles: true }));
  input.dispatchEvent(new Event('blur'));
  await vi.waitFor(() =>
    expect(view.querySelector('[role=alert]')?.textContent).toContain('Offline'),
  );
  expect(input.value).toBe('Kniebeuge mit Pause');
  expect(request).toHaveBeenCalledOnce();
  expect(view.querySelector('dialog')).toBeNull();
  Array.from(view.querySelectorAll('button'))
    .find((b) => b.textContent?.includes('Erneut speichern'))!
    .click();
  await vi.waitFor(() => expect(view.exercises[0].name).toBe('Kniebeuge mit Pause'));
  expect(request).toHaveBeenCalledTimes(2);
  expect(request).toHaveBeenLastCalledWith('/exercises/exercise-0', 'PUT', {
    name: 'Kniebeuge mit Pause',
    category: 'squat',
    main: true,
  });
});

it('keeps failed default edits and retries the complete category prescription explicitly', async () => {
  const { demo, view } = await catalog();
  const request = vi.spyOn(demo, 'request').mockRejectedValueOnce(new Error('Offline'));
  const select = view.querySelector<HTMLSelectElement>('[aria-label="Kniebeuge Pause"]')!;
  select.value = '300';
  select.dispatchEvent(new Event('change', { bubbles: true }));
  await vi.waitFor(() =>
    expect(view.querySelector('[role=alert]')?.textContent).toContain('Nicht gespeichert'),
  );
  expect(select.value).toBe('300');
  expect(request).toHaveBeenCalledOnce();
  Array.from(view.querySelectorAll('button'))
    .find((b) => b.textContent?.includes('Erneut speichern'))!
    .click();
  await vi.waitFor(() =>
    expect(view.querySelector('[role=status]')?.textContent).toContain('Gespeichert'),
  );
  expect(request).toHaveBeenLastCalledWith('/exercises/category-defaults/squat', 'PUT', {
    rest_seconds: 300,
    sets: 3,
    reps: 7,
    target_effort: '7.5',
  });
  expect(select.value).toBe('300');
});

it('loads the users RIR scale and sends effort in that scale', async () => {
  const { demo, view } = await catalog();
  view.remove();
  const user = await demo.request<User>('/users/me/preferences', 'PUT', {
    ...view.user,
    effort_scale: 'rir',
  });
  view.user = user;
  document.body.append(view);
  await vi.waitFor(() =>
    expect(view.querySelector<HTMLSelectElement>('[aria-label="Kniebeuge RIR"]')?.value).toBe(
      '2.5',
    ),
  );
  const request = vi.spyOn(demo, 'request');
  const select = view.querySelector<HTMLSelectElement>('[aria-label="Kniebeuge RIR"]')!;
  select.value = '1.5';
  select.dispatchEvent(new Event('change', { bubbles: true }));
  await vi.waitFor(() =>
    expect(request).toHaveBeenCalledWith('/exercises/category-defaults/squat', 'PUT', {
      rest_seconds: 240,
      sets: 3,
      reps: 7,
      target_effort: '1.5',
    }),
  );
});
