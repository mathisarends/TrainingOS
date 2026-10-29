import { describe, expect, it } from 'vitest';
import { RestClock } from '../../../src/features/training/timer';
import { timestampResponse } from '../../../src/shared/response-time';
import type { TrainingSession } from '../../../src/shared/types';

const session = (end: string | null) =>
  ({ server_now: '2026-10-28T12:00:00Z', rest_ends_at: end }) as TrainingSession;
describe('server-authoritative rest clock', () => {
  it('uses elapsed monotonic time even with a different device wall clock', () => {
    const clock = new RestClock();
    clock.sync(session('2026-10-28T12:03:00Z'), 1000);
    expect(clock.remaining(61000)).toBe(120);
    expect(clock.remaining(181001)).toBe(0);
  });
  it('continues a cached response after navigation instead of restarting the rest', () => {
    const snapshot = timestampResponse(session('2026-10-28T12:03:00Z'), 1000);
    const remountedClock = new RestClock();
    remountedClock.sync(snapshot);
    expect(remountedClock.remaining(91000)).toBe(90);
  });
  it('accepts server adjustments and skipped timers', () => {
    const clock = new RestClock();
    clock.sync(session('2026-10-28T12:03:30Z'), 1000);
    expect(clock.remaining(1000)).toBe(210);
    clock.sync(session(null), 2000);
    expect(clock.remaining(2000)).toBe(0);
  });
  it('does not show negative time for a deadline already passed', () => {
    const clock = new RestClock();
    clock.sync(session('2026-10-28T11:59:00Z'), 1000);
    expect(clock.remaining(1000)).toBe(0);
  });
});
