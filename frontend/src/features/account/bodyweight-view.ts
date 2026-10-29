import { LitElement, html, nothing } from 'lit';
import { bodyweight } from '../../api/generated';
import type { Bodyweight, Transport, User } from '../../shared/types';
import { formValues, icon, today, formatNumber } from '../../shared/ui';
import '../../shared/value-chart';

export class BodyweightView extends LitElement {
  static properties = {
    api: { attribute: false },
    user: { attribute: false },
    data: { state: true },
    adding: { state: true },
    busy: { state: true },
    error: { state: true },
    message: { state: true },
  };
  api!: Transport;
  user!: User;
  private data: Bodyweight | null = null;
  private adding = false;
  private busy = false;
  private error = '';
  private message = '';
  createRenderRoot() {
    return this;
  }
  connectedCallback() {
    super.connectedCallback();
    void this.act(async () => this.load());
  }
  private async load() {
    this.data = await bodyweight.listBodyweight({ transport: this.api });
  }
  private async act(action: () => Promise<void>) {
    if (this.busy) return;
    this.busy = true;
    this.error = '';
    this.message = '';
    try {
      await action();
    } catch (e) {
      this.error = (e as Error).message;
    } finally {
      this.busy = false;
    }
  }
  private save(e: Event, date?: string) {
    const values = formValues(e);
    void this.act(async () => {
      await bodyweight.recordBodyweight(
        { date: date ?? String(values.date), weight: String(values.weight) },
        { transport: this.api },
      );
      await this.load();
      this.adding = false;
      this.message = 'Körpergewicht gespeichert.';
    });
  }
  render() {
    if (!this.data && this.busy)
      return html`<div class="empty" role="status"><span class="loader"></span></div>`;
    const items = [...(this.data?.items ?? [])].sort((a, b) => a.date.localeCompare(b.date));
    return html`${this.error ? html`<div role="alert" class="notice error">${this.error}</div>` : nothing}${this.message ? html`<div role="status" class="notice success">${this.message}</div>` : nothing}
      <div class="bodyweight-layout">
        <section>
          <div class="weight-table-heading">
            <span>Datum</span><span>Körpergewicht (${this.user.unit})</span>
          </div>
          ${[...items].reverse().map(
            (entry) =>
              html`<form class="weight-table-row" @submit=${(e: Event) => this.save(e, entry.date)}>
                <span>${new Date(`${entry.date}T12:00:00`).toLocaleDateString('de-DE')}</span>
                <div class="inline-weight">
                  <input
                    name="weight"
                    type="number"
                    min="0.1"
                    max="1000"
                    step="0.1"
                    required
                    aria-label=${`Körpergewicht am ${entry.date}`}
                    .value=${entry.weight}
                  /><button
                    class="bare-icon"
                    ?disabled=${this.busy}
                    aria-label=${`Gewicht am ${entry.date} speichern`}
                  >
                    ${icon('save')}</button
                  ><button
                    type="button"
                    class="bare-icon"
                    ?disabled=${this.busy}
                    aria-label=${`Gewicht am ${entry.date} löschen`}
                    @click=${() =>
                      this.act(async () => {
                        await bodyweight.deleteBodyweight(entry.id, { transport: this.api });
                        await this.load();
                      })}
                  >
                    ${icon('close')}
                  </button>
                </div>
              </form>`,
          )}
          ${
            this.adding
              ? html`<form
                  class="weight-table-row weight-add-form"
                  @submit=${(e: Event) => this.save(e)}
                >
                  <input type="date" name="date" required .value=${today()} aria-label="Datum" />
                  <div class="inline-weight">
                    <input
                      type="number"
                      name="weight"
                      required
                      min="0.1"
                      max="1000"
                      step="0.1"
                      placeholder="0,0"
                      aria-label="Neues Körpergewicht"
                    /><button
                      class="bare-icon"
                      ?disabled=${this.busy}
                      aria-label="Körpergewicht speichern"
                    >
                      ${icon('check')}</button
                    ><button
                      type="button"
                      class="bare-icon"
                      @click=${() => {
                        this.adding = false;
                      }}
                      aria-label="Abbrechen"
                    >
                      ${icon('close')}
                    </button>
                  </div>
                </form>`
              : nothing
          }
          <button
            class="add-row"
            aria-label="Körpergewicht hinzufügen"
            @click=${() => {
              this.adding = true;
            }}
          >
            ${icon('plus')}</button
          >${this.data?.target_weight ? html`<p class="muted weight-target">Zielgewicht ${formatNumber(this.data.target_weight)} ${this.user.unit}</p>` : nothing}
        </section>
        <value-chart
          .items=${items.map((i) => ({ label: new Date(`${i.date}T12:00:00`).toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit' }), value: Number(i.weight) }))}
          .unit=${this.user.unit}
          label="Körpergewicht (Verlauf)"
        ></value-chart>
      </div>`;
  }
}
customElements.define('bodyweight-view', BodyweightView);
