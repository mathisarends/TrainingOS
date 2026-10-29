import { LitElement, html, nothing } from 'lit';
import { users } from '../../api/generated';
import type { Transport, User } from '../../shared/types';
import { formValues } from '../../shared/ui';

export class AccountView extends LitElement {
  static properties = {
    api: { attribute: false },
    user: { attribute: false },
    busy: { state: true },
    error: { state: true },
    message: { state: true },
  };
  api!: Transport;
  user!: User;
  private busy = false;
  private error = '';
  private message = '';
  createRenderRoot() {
    return this;
  }
  private async save(e: Event) {
    const v = formValues(e);
    if (this.busy) return;
    this.busy = true;
    this.error = '';
    this.message = '';
    try {
      this.user = await users.configureUser(
        {
          unit: v.unit as 'kg' | 'lb',
          effort_scale: v.effort_scale as 'rpe' | 'rir',
          rounding_step: String(v.rounding_step),
          timezone: String(v.timezone),
        },
        { transport: this.api },
      );
      this.dispatchEvent(new CustomEvent('user-changed', { detail: this.user, bubbles: true }));
      this.message = 'Einstellungen gespeichert.';
    } catch (e) {
      this.error = (e as Error).message;
    } finally {
      this.busy = false;
    }
  }
  render() {
    return html`<div class="settings-wrapper">
      ${this.error ? html`<div class="notice error" role="alert">${this.error}</div>` : nothing}${this.message ? html`<div class="notice success" role="status">${this.message}</div>` : nothing}
      <form class="stack" @submit=${this.save}>
        <section class="settings-section" aria-labelledby="training-preferences-title">
          <div class="settings-section-heading">
            <h2 id="training-preferences-title">Training</h2>
            <p>So werden deine Gewichte und Vorgaben angezeigt.</p>
          </div>
          <div class="input-grid">
            <label
              >Gewichtseinheit<training-select
                ><select name="unit">
                  <option value="kg" ?selected=${this.user.unit === 'kg'}>Kilogramm (kg)</option>
                  <option value="lb" ?selected=${this.user.unit === 'lb'}>Pfund (lb)</option>
                </select></training-select
              ></label
            >
            <label
              >Anstrengungsskala<training-select
                ><select name="effort_scale">
                  <option value="rpe" ?selected=${this.user.effort_scale === 'rpe'}>
                    RPE · Anstrengung
                  </option>
                  <option value="rir" ?selected=${this.user.effort_scale === 'rir'}>
                    RIR · Wiederholungen in Reserve
                  </option>
                </select></training-select
              ></label
            >
            <label
              >Rundungsschritt (${this.user.unit})<input
                type="number"
                name="rounding_step"
                min="0.01"
                max="100"
                step="0.01"
                required
                .value=${this.user.rounding_step}
            /></label>
          </div>
          <p class="muted">
            RPE 8 entspricht RIR 2. Ein Wechsel ändert keine gespeicherten Trainingswerte.
          </p>
        </section>
        <section class="settings-section" aria-labelledby="regional-preferences-title">
          <div class="settings-section-heading">
            <h2 id="regional-preferences-title">Region</h2>
            <p>Für die Zuordnung deiner Trainings zum richtigen Tag.</p>
          </div>
          <label
            >Zeitzone<input name="timezone" required maxlength="100" .value=${this.user.timezone}
          /></label>
        </section>
        <button class="primary" ?disabled=${this.busy}>Einstellungen speichern</button>
      </form>
    </div>`;
  }
}
customElements.define('account-view', AccountView);
