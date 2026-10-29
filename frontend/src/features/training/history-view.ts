import { LitElement, html, nothing } from 'lit';
import { trainingSessions } from '../../api/generated';
import type { TrainingSession, Transport } from '../../shared/types';
import { dateLabel, empty, icon, today } from '../../shared/ui';

export class HistoryView extends LitElement {
  static properties = {
    api: { attribute: false },
    sessions: { attribute: false },
    more: { attribute: false },
    month: { state: true },
    year: { state: true },
    busy: { state: true },
    error: { state: true },
    list: { state: true },
  };
  api!: Transport;
  sessions: TrainingSession[] = [];
  more = false;
  private month = new Date().getMonth();
  private year = new Date().getFullYear();
  private busy = false;
  private error = '';
  private list = false;
  createRenderRoot() {
    return this;
  }
  connectedCallback() {
    super.connectedCallback();
    void this.loadRemaining();
  }
  private async loadRemaining() {
    if (!this.more || this.busy) return;
    this.busy = true;
    try {
      while (this.more && this.isConnected) {
        const page = await trainingSessions.listTrainingSessions(
          { offset: this.sessions.length, limit: 100 },
          { transport: this.api },
        );
        this.sessions = [...this.sessions, ...page.items];
        this.more = page.items.length === 100;
      }
    } catch (e) {
      this.error = (e as Error).message;
    } finally {
      this.busy = false;
    }
  }
  private move(delta: number) {
    const date = new Date(this.year, this.month + delta, 1);
    this.month = date.getMonth();
    this.year = date.getFullYear();
  }
  private open(id: string) {
    this.dispatchEvent(new CustomEvent('open-training', { detail: id, bubbles: true }));
  }
  private monthList(sessions: TrainingSession[]) {
    return html`<div class="history-list month-history-list">
      ${sessions.map((s) => {
        const date = new Date(s.started_at);
        return html`<button class="history-row" @click=${() => this.open(s.id)}>
          <span class="history-date"
            ><small
              >${date.toLocaleDateString('de-DE', { weekday: 'short' }).replace('.', '')}</small
            ><strong>${date.getDate()}</strong></span
          >
          <span class="history-name">${s.day_name}</span
          ><span
            class="history-completion ${s.ended_at ? 'completed' : ''}"
            aria-label=${s.ended_at ? 'Abgeschlossen' : 'Läuft'}
            >${icon(s.ended_at ? 'check' : 'activity')}</span
          >
        </button>`;
      })}
    </div>`;
  }
  render() {
    const first = new Date(this.year, this.month, 1);
    const offset = (first.getDay() + 6) % 7;
    const length = new Date(this.year, this.month + 1, 0).getDate();
    const cells = Math.ceil((length + offset) / 7) * 7;
    const monthSessions = this.sessions
      .filter((s) => {
        const date = new Date(s.started_at);
        return date.getFullYear() === this.year && date.getMonth() === this.month;
      })
      .sort((a, b) => Date.parse(b.started_at) - Date.parse(a.started_at));
    return html`<div class="history-toolbar">
        <h1>${first.toLocaleDateString('de-DE', { month: 'long', year: 'numeric' })}</h1>
        <div class="history-controls">
          <button
            class="secondary today-button"
            @click=${() => {
              this.month = new Date().getMonth();
              this.year = new Date().getFullYear();
            }}
          >
            Heute
          </button>
          <button class="bare-icon" aria-label="Vorheriger Monat" @click=${() => this.move(-1)}>
            ${icon('chevron-left')}
          </button>
          <button class="bare-icon" aria-label="Nächster Monat" @click=${() => this.move(1)}>
            ${icon('chevron-right')}
          </button>
          <button
            class="bare-icon"
            aria-label=${this.list ? 'Kalender anzeigen' : 'Liste anzeigen'}
            aria-pressed=${this.list}
            @click=${() => {
              this.list = !this.list;
            }}
          >
            ${icon(this.list ? 'plans' : 'list')}
          </button>
        </div>
      </div>
      ${this.error ? html`<div class="notice error" role="alert">${this.error}<button class="text-button" @click=${this.loadRemaining}>Erneut laden</button></div>` : nothing}
      ${
        this.list
          ? this.monthList(monthSessions)
          : html`<div class="log-calendar" aria-label="Trainingskalender">
                ${['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'].map((label) => html`<div class="calendar-day-name">${label}</div>`)}
                ${Array.from({ length: cells }, (_, i) => {
                  const date = new Date(this.year, this.month, i - offset + 1);
                  const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
                  const sessions = this.sessions.filter(
                    (s) => new Date(s.started_at).toLocaleDateString('sv-SE') === key,
                  );
                  return html`<div
                    class="calendar-day ${date.getMonth() !== this.month ? 'other-month' : ''}"
                  >
                    <span
                      class="calendar-day-number ${key === today() ? 'current-day' : ''}"
                      aria-current=${key === today() ? 'date' : nothing}
                      >${date.getDate()}</span
                    >
                    <div class="calendar-events">
                      ${sessions.map((s) => html`<button class="calendar-event ${s.ended_at ? 'completed' : ''}" @click=${() => this.open(s.id)} aria-label=${`${s.day_name}, ${dateLabel(s.started_at)}`}>${icon(s.ended_at ? 'check' : 'activity')}<span>${s.day_name}</span></button>`)}
                    </div>
                  </div>`;
                })}
              </div>
              <div class="mobile-month-history">
                <p class="month-session-count">
                  ${monthSessions.length} ${monthSessions.length === 1 ? 'Einheit' : 'Einheiten'} im
                  ${first.toLocaleDateString('de-DE', { month: 'long' })}
                </p>
                ${monthSessions.length ? this.monthList(monthSessions) : nothing}
              </div>`
      }
      ${!monthSessions.length && !this.busy ? empty('Keine Trainings in diesem Monat', 'Wechsle den Monat oder starte dein nächstes Training.') : nothing}`;
  }
}
customElements.define('history-view', HistoryView);
