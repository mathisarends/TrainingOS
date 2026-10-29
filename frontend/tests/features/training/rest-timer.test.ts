// @vitest-environment happy-dom
import { afterEach, expect, it, vi } from 'vitest';
import { RestTimer } from '../../../src/features/training/rest-timer';
import { DemoTransport } from '../../../src/app/demo';
import type { SetFeedback, TrainingSession } from '../../../src/shared/types';

afterEach(() => {
  document.body.replaceChildren();
  vi.restoreAllMocks();
});

it('shows the server deadline and persists a timer adjustment before emitting the new snapshot', async () => {
  const api = new DemoTransport();
  const session = await api.request<TrainingSession>('/training-sessions', 'POST', {
    plan_id: 'preview-plan',
    day_id: 'day-0',
    week: 1,
  });
  const feedback = await api.request<SetFeedback>(
    `/training-sessions/${session.id}/slots/${session.slots[0].id}/sets`,
    'POST',
    { weight: '100', reps: 5, effort: '8' },
  );
  const timer = new RestTimer();
  timer.api = api;
  timer.session = feedback.training_session;
  document.body.append(timer);
  await timer.updateComplete;
  expect(timer.querySelector('[role=timer]')!.textContent).toContain('03:00');
  const received = vi.fn();
  timer.addEventListener('timer-session-changed', received);
  timer.querySelector<HTMLButtonElement>('.rest-dock-bar')!.click();
  await timer.updateComplete;
  Array.from(timer.querySelectorAll('button'))
    .find((b) => b.textContent?.trim() === '+30 s')!
    .click();
  await vi.waitFor(() => expect(received).toHaveBeenCalledOnce());
  expect(timer.querySelector('[role=timer]')!.textContent).toContain('03:30');
  const restored = await api.request<TrainingSession>(`/training-sessions/${session.id}`);
  expect(restored.rest_remaining_seconds).toBeGreaterThan(208);
  expect(timer.textContent).toContain('Kniebeuge');
});
