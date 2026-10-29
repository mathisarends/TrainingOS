import { afterEach, expect, it, vi } from 'vitest';
import { plans, trainingSessions } from '../../src/api/generated';
import { configurePreviewTransport } from '../../src/api/request';
import { ApiError } from '../../src/shared/api';

afterEach(() => {
  configurePreviewTransport();
  vi.unstubAllGlobals();
});

it('uses generated parameter encoding and preserves decimal strings at the HTTP boundary', async () => {
  const fetch = vi.fn().mockResolvedValue(Response.json({}));
  vi.stubGlobal('fetch', fetch);
  await trainingSessions.recordWorkSet('session/a', 'slot/b', {
    weight: '102.5000',
    reps: 5,
    effort: '8.5',
  });
  expect(fetch).toHaveBeenCalledOnce();
  expect(fetch).toHaveBeenCalledWith(
    '/api/v1/training-sessions/session%2Fa/slots/slot%2Fb/sets',
    expect.objectContaining({
      credentials: 'include',
      method: 'POST',
      body: '{"weight":"102.5000","reps":5,"effort":"8.5"}',
    }),
  );
});

it('forwards generated query cancellation without retrying or translating an abort into a failed write', async () => {
  const controller = new AbortController();
  controller.abort();
  const fetch = vi.fn().mockRejectedValue(new DOMException('Cancelled', 'AbortError'));
  vi.stubGlobal('fetch', fetch);
  const query = trainingSessions.listTrainingSessionsQuery({ offset: 50, limit: 100 });
  await expect(
    trainingSessions.listTrainingSessions(
      { offset: 50, limit: 100 },
      { signal: controller.signal },
    ),
  ).rejects.toMatchObject({ name: 'AbortError' });
  expect(query.queryKey).toEqual(
    trainingSessions.trainingSessionsKeys.listTrainingSessions({ offset: 50, limit: 100 }),
  );
  expect(fetch).toHaveBeenCalledOnce();
  expect(fetch).toHaveBeenCalledWith(
    '/api/v1/training-sessions?offset=50&limit=100',
    expect.objectContaining({ signal: controller.signal }),
  );
});

it('recognizes backend Problem Details through the generated resource guard', async () => {
  const problem = {
    type: 'urn:trainingos:problem/state_conflict',
    title: 'State conflict',
    status: 409,
    code: 'state_conflict',
    detail: 'Plan revision changed',
  };
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue(
      Response.json(problem, {
        status: 409,
        headers: { 'Content-Type': 'application/problem+json' },
      }),
    ),
  );
  try {
    await plans.applyProgression('plan', { expected_revision: 4 });
    throw new Error('Expected conflict');
  } catch (error) {
    expect(error).toBeInstanceOf(ApiError);
    expect(plans.isPlansError(error)).toBe(true);
    expect((error as ApiError).problem).toEqual(problem);
  }
});
