import { LitElement, html, nothing } from 'lit';
import { trainingSessions } from '../../api/generated';
import type { TrainingSession, Transport, User } from '../../shared/types';
import { categories, dateLabel, empty, formatNumber, icon } from '../../shared/ui';
import '../../shared/value-chart';

export class RecordsView extends LitElement {
  static properties = {
    api: { attribute: false },
    user: { attribute: false },
    sessions: { state: true },
    loading: { state: true },
    error: { state: true },
  };
  api!: Transport;
  user!: User;
  private sessions: TrainingSession[] = [];
  private loading = true;
  private error = '';
  createRenderRoot() {
    return this;
  }
  connectedCallback() {
    super.connectedCallback();
    void this.load();
  }
  private async load() {
    this.loading = true;
    this.error = '';
    try {
      const all: TrainingSession[] = [];
      let more = true;
      while (more && this.isConnected) {
        const page = await trainingSessions.listTrainingSessions(
          { offset: all.length, limit: 100 },
          { transport: this.api },
        );
        all.push(...page.items);
        more = page.items.length === 100;
      }
      this.sessions = all;
    } catch (e) {
      this.error = (e as Error).message;
    } finally {
      this.loading = false;
    }
  }
  render() {
    const main = this.sessions.flatMap((session) =>
      session.slots
        .filter((s) => s.main)
        .flatMap((slot) =>
          slot.sets.map((set) => ({
            ...set,
            exercise_id: slot.exercise_id,
            exercise: slot.exercise_name,
            category: slot.category,
            session_id: session.id,
          })),
        ),
    );
    const ids = [...new Set(main.map((s) => s.exercise_id))];
    return html`${this.error ? html`<div class="notice error" role="alert">${this.error}<button class="text-button" @click=${this.load}>Erneut laden</button></div>` : nothing}${
      this.loading
        ? html`<div class="empty" role="status"><span class="loader"></span></div>`
        : html`<div class="records-grid">
              ${ids.map((id) => {
                const sets = main
                  .filter((s) => s.exercise_id === id)
                  .sort((a, b) => a.recorded_at.localeCompare(b.recorded_at));
                const best = sets.reduce((a, b) => (Number(a.e1rm) > Number(b.e1rm) ? a : b));
                return html`<section class="record-section">
                  <div class="record-heading">
                    <div>
                      <h2>${categories[best.category]} · ${best.exercise}</h2>
                      <p>
                        <strong>${formatNumber(best.e1rm)}</strong
                        ><span>${this.user.unit} e1RM</span>
                      </p>
                    </div>
                    ${icon('award')}
                  </div>
                  <value-chart
                    .items=${sets.map((s) => ({ label: dateLabel(s.recorded_at), value: Number(s.e1rm) }))}
                    .unit=${this.user.unit}
                    label="e1RM (erfasste Sätze)"
                  ></value-chart>
                  <p class="muted">
                    ${dateLabel(best.recorded_at)} · ${formatNumber(best.weight)} ${this.user.unit}
                    × ${best.reps} @ ${formatNumber(best.effort)}
                  </p>
                </section>`;
              })}
            </div>
            ${!ids.length ? empty('Noch keine Bestleistungen', 'Erfasse deine ersten Sätze in einer Hauptübung.') : nothing}`
    }`;
  }
}
customElements.define('records-view', RecordsView);
