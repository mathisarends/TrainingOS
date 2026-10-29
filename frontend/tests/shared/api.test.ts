import { afterEach, describe, expect, it, vi } from 'vitest';
import { ApiError, HttpTransport } from '../../src/shared/api';

afterEach(() => vi.unstubAllGlobals());
describe('HTTP boundary', () => {
  it('sends cookie credentials and exact decimal strings without retrying a mutation', async () => {
    const fetch = vi.fn().mockResolvedValue(Response.json({ id: 'set' }, { status: 201 }));
    vi.stubGlobal('fetch', fetch);
    await new HttpTransport().request('/training-sessions/session/slots/slot/sets', 'POST', {
      weight: '102.5000',
      reps: 5,
      effort: '8.5',
    });
    expect(fetch).toHaveBeenCalledOnce();
    expect(fetch).toHaveBeenCalledWith(
      '/api/v1/training-sessions/session/slots/slot/sets',
      expect.objectContaining({
        method: 'POST',
        credentials: 'include',
        cache: 'no-store',
        body: '{"weight":"102.5000","reps":5,"effort":"8.5"}',
      }),
    );
  });
  it('exposes Problem Details without pretending a failed write succeeded', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        Response.json(
          {
            type: 'urn:trainingos:problem/state_conflict',
            title: 'State conflict',
            status: 409,
            detail: 'The session has already ended',
          },
          {
            status: 409,
            headers: { 'Content-Type': 'application/problem+json' },
          },
        ),
      ),
    );
    await expect(
      new HttpTransport().request('/training-sessions/a/finish', 'POST'),
    ).rejects.toMatchObject({ status: 409, message: 'The session has already ended' });
  });
  it('does not retry uncertain network writes', async () => {
    const fetch = vi.fn().mockRejectedValue(new TypeError('Disconnected'));
    vi.stubGlobal('fetch', fetch);
    await expect(
      new HttpTransport().request('/training-sessions/a/slots/b/sets', 'POST', {}),
    ).rejects.toBeInstanceOf(ApiError);
    expect(fetch).toHaveBeenCalledOnce();
  });
  it('handles bodyless logout responses', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(null, { status: 204 })));
    expect(await new HttpTransport().request('/auth/logout', 'POST')).toBeUndefined();
  });
});
