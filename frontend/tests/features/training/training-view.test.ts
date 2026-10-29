// @vitest-environment happy-dom
import { afterEach, describe, expect, it, vi } from 'vitest';
import { TrainingView } from '../../../src/features/training/training-view';
import { DemoTransport } from '../../../src/app/demo';
import type { TrainingSession, Transport } from '../../../src/shared/types';

afterEach(() => {
  document.body.replaceChildren();
  vi.restoreAllMocks();
});
async function setup() {
  const api = new DemoTransport();
  const session = await api.request<TrainingSession>('/training-sessions', 'POST', {
    plan_id: 'preview-plan',
    day_id: 'day-0',
    week: 1,
  });
  const view = new TrainingView();
  view.api = api;
  view.session = session;
  document.body.append(view);
  await view.updateComplete;
  await view.updateComplete;
  return { api, session, view };
}
function input(view: TrainingView, name: string, value: string) {
  const element = view.querySelector<HTMLInputElement>(`[name=${name}]`)!;
  element.value = value;
  element.dispatchEvent(new Event('input', { bubbles: true }));
}
function submit(view: TrainingView) {
  view
    .querySelector('form')!
    .dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
}

describe('set entry', () => {
  it('requires explicit submission and renders only server-confirmed sets', async () => {
    const { view, api } = await setup();
    const request = vi.spyOn(api, 'request');
    input(view, 'weight', '100');
    await view.updateComplete;
    expect(request).not.toHaveBeenCalled();
    expect(view.session.slots[0].sets).toHaveLength(0);
    submit(view);
    await vi.waitFor(() => expect(view.session.slots[0].sets).toHaveLength(1));
    expect(request).toHaveBeenCalledWith(expect.stringContaining('/sets'), 'POST', {
      weight: '100',
      reps: 5,
      effort: '8',
    });
    expect(view.textContent).toContain('Satz gespeichert');
    expect(view.session.rest_remaining_seconds).toBe(180);
  });
  it('keeps entered values and records nothing after a failed save', async () => {
    const { view, api } = await setup();
    vi.spyOn(api, 'request').mockRejectedValue(new Error('Verbindung unterbrochen'));
    input(view, 'weight', '87.5');
    input(view, 'reps', '7');
    submit(view);
    await vi.waitFor(() =>
      expect(view.querySelector('[role=alert]')?.textContent).toContain('Verbindung unterbrochen'),
    );
    expect(view.session.slots[0].sets).toHaveLength(0);
    expect(view.querySelector<HTMLInputElement>('[name=weight]')!.value).toBe('87.5');
    expect(view.querySelector<HTMLInputElement>('[name=reps]')!.value).toBe('7');
  });
  it('blocks double submission while a set is being saved', async () => {
    const { view, api } = await setup();
    const request = vi.spyOn(api, 'request').mockImplementation(() => new Promise(() => {}));
    input(view, 'weight', '90');
    submit(view);
    submit(view);
    expect(request).toHaveBeenCalledOnce();
  });
  it('does not overwrite an athlete entry with late guidance', async () => {
    const { view, session } = await setup();
    let resolve!: (value: unknown) => void;
    view.remove();
    const delayed = new TrainingView();
    delayed.session = { ...session, slots: session.slots.slice(0, 1) };
    const pending = new Promise<unknown>((r) => (resolve = r));
    delayed.api = { request: async <T>() => (await pending) as T } satisfies Transport;
    document.body.append(delayed);
    await delayed.updateComplete;
    input(delayed, 'weight', '75');
    resolve({ recommended_weight: '100', backoff_weight: null, last_sets: [] });
    await delayed.updateComplete;
    await delayed.updateComplete;
    expect(delayed.querySelector<HTMLInputElement>('[name=weight]')!.value).toBe('75');
  });
});
