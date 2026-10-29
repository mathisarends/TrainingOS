import { trainingSessions } from '../../api/generated';
import { LitElement, html, nothing } from 'lit';
import type { TrainingSession, Transport } from '../../shared/types';
import { icon } from '../../shared/ui';
import { RestClock, clockLabel, TrainingDevice } from './timer';

export class RestTimer extends LitElement {
  static properties = {
    api: { attribute: false },
    session: { attribute: false },
    remaining: { state: true },
    expanded: { state: true },
    busy: { state: true },
    wake: { state: true },
    error: { state: true },
  };
  api!: Transport;
  session!: TrainingSession;
  private remaining = 0;
  private expanded = false;
  private busy = false;
  private wake = false;
  private error = '';
  private clock = new RestClock();
  private device = new TrainingDevice();
  private interval?: ReturnType<typeof setInterval>;
  private visible = () => {
    if (document.visibilityState === 'visible') void this.refresh();
  };
  createRenderRoot() {
    return this;
  }
  connectedCallback() {
    super.connectedCallback();
    document.addEventListener('visibilitychange', this.visible);
    this.interval = setInterval(() => {
      const next = this.clock.remaining();
      if (this.remaining > 0 && next === 0) this.device.signal();
      this.remaining = next;
    }, 500);
  }
  disconnectedCallback() {
    super.disconnectedCallback();
    clearInterval(this.interval);
    this.device.dispose();
    document.removeEventListener('visibilitychange', this.visible);
  }
  protected willUpdate(changes: Map<string, unknown>) {
    if (changes.has('session') && this.session) {
      this.clock.sync(this.session);
      this.remaining = this.clock.remaining();
    }
  }
  async enable() {
    this.wake = await this.device.enable();
  }
  private async refresh() {
    if (this.busy || !this.session) return;
    try {
      this.accept(
        await trainingSessions.getTrainingSession(this.session.id, { transport: this.api }),
      );
    } catch (e) {
      this.error = (e as Error).message;
    }
  }
  private accept(session: TrainingSession) {
    this.session = session;
    this.dispatchEvent(
      new CustomEvent('timer-session-changed', { detail: session, bubbles: true }),
    );
  }
  private async adjust(delta_seconds: number | null) {
    if (this.busy) return;
    this.busy = true;
    this.error = '';
    try {
      this.accept(
        await trainingSessions.adjustRestTimer(
          this.session.id,
          { delta_seconds },
          { transport: this.api },
        ),
      );
    } catch (e) {
      this.error = (e as Error).message;
    } finally {
      this.busy = false;
    }
  }
  render() {
    if (!this.session || this.session.ended_at) return nothing;
    const recent = this.session.slots
      .filter((s) => s.sets.length)
      .sort(
        (a, b) => Date.parse(b.sets.at(-1)!.recorded_at) - Date.parse(a.sets.at(-1)!.recorded_at),
      )[0];
    const progress = Math.min(
      100,
      (this.remaining / Math.max(1, recent?.rest_seconds || 180)) * 100,
    );
    return html`<aside
      class="rest-dock ${this.expanded ? 'expanded' : ''}"
      aria-label="Pausentimer"
    >
      ${
        this.expanded
          ? html`<div class="rest-dock-controls">
              <div class="rest-dock-title">
                <strong>Pausentimer</strong
                ><button
                  class="icon-button"
                  aria-label="Timer zuklappen"
                  @click=${() => (this.expanded = false)}
                >
                  ${icon('close')}
                </button>
              </div>
              <div class="rest-large-time">${clockLabel(this.remaining)}</div>
              <div class="rest-adjustments">
                <button
                  class="secondary"
                  ?disabled=${this.busy || !this.remaining}
                  @click=${() => this.adjust(-30)}
                >
                  −30 s</button
                ><button
                  class="secondary"
                  ?disabled=${this.busy || !this.remaining}
                  @click=${() => this.adjust(30)}
                >
                  +30 s</button
                ><button
                  class="primary"
                  ?disabled=${this.busy || !this.remaining}
                  @click=${() => this.adjust(null)}
                >
                  Überspringen
                </button>
              </div>
              <button class="text-button" @click=${this.enable}>
                ${this.wake ? 'Bildschirm bleibt an' : 'Bildschirm & Tonsignal aktivieren'}
              </button>
              <p>Signale bei gesperrtem Bildschirm sind browserabhängig.</p>
              ${this.error ? html`<p class="notice error" role="alert">${this.error}</p>` : nothing}
            </div>`
          : nothing
      }
      <button
        class="rest-dock-bar"
        aria-expanded=${this.expanded}
        aria-label="Pausentimer öffnen oder schließen"
        @click=${() => {
          this.expanded = !this.expanded;
          void this.enable();
        }}
      >
        <span class="rest-dock-icon">${icon('clock')}</span
        ><span class="rest-dock-exercise"
          ><strong>${recent?.exercise_name || this.session.day_name}</strong
          ><small>${this.remaining > 0 ? 'Satzpause' : 'Bereit für den nächsten Satz'}</small></span
        ><span class="rest-dock-time" role="timer" aria-label="Verbleibende Pause"
          >${clockLabel(this.remaining)}</span
        ><span class="rest-chevron">${icon(this.expanded ? 'chevron-down' : 'chevron-up')}</span>
      </button>
      <div class="rest-dock-track"><span style=${`width:${progress}%`}></span></div>
    </aside>`;
  }
}
customElements.define('rest-timer', RestTimer);
