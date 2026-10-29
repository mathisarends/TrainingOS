import type { TrainingSession } from '../../shared/types';
import { responseTime } from '../../shared/response-time';

/** Anchor to the server clock, not the phone's possibly incorrect wall clock. */
export class RestClock {
  private remainingAtSync = 0;
  private syncedAt = 0;
  sync(session: TrainingSession, monotonicNow = responseTime(session) ?? performance.now()) {
    this.remainingAtSync = session.rest_ends_at
      ? Math.max(0, Date.parse(session.rest_ends_at) - Date.parse(session.server_now))
      : 0;
    this.syncedAt = monotonicNow;
  }
  remaining(monotonicNow = performance.now()) {
    return Math.max(0, Math.ceil((this.remainingAtSync - (monotonicNow - this.syncedAt)) / 1000));
  }
}
export function clockLabel(seconds: number) {
  return `${Math.floor(seconds / 60)
    .toString()
    .padStart(2, '0')}:${(seconds % 60).toString().padStart(2, '0')}`;
}

export class TrainingDevice {
  private lock: WakeLockSentinel | null = null;
  private audio: AudioContext | null = null;
  private enabled = false;
  private onVisibility = () => {
    if (document.visibilityState === 'visible' && this.enabled) void this.acquire();
  };
  constructor() {
    document.addEventListener('visibilitychange', this.onVisibility);
  }
  async enable() {
    this.enabled = true;
    try {
      this.audio ??= new AudioContext();
      await this.audio.resume();
    } catch {
      /* Audio is optional. */
    }
    return this.acquire();
  }
  private async acquire() {
    if (!('wakeLock' in navigator)) return false;
    if (this.lock && !this.lock.released) return true;
    try {
      this.lock = await navigator.wakeLock.request('screen');
      if (!this.enabled) {
        await this.lock.release();
        return false;
      }
      return true;
    } catch {
      return false;
    }
  }
  signal() {
    navigator.vibrate?.([180, 80, 180]);
    if (this.audio?.state === 'running') {
      const oscillator = this.audio.createOscillator();
      const gain = this.audio.createGain();
      oscillator.frequency.value = 740;
      gain.gain.value = 0.12;
      oscillator.connect(gain);
      gain.connect(this.audio.destination);
      oscillator.start();
      oscillator.stop(this.audio.currentTime + 0.35);
    }
  }
  async stop() {
    this.enabled = false;
    await this.lock?.release().catch(() => {});
    this.lock = null;
  }
  dispose() {
    void this.stop();
    void this.audio?.close();
    document.removeEventListener('visibilitychange', this.onVisibility);
  }
}
