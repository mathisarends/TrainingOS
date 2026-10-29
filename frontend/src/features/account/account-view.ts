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
          target_weight: v.target_weight ? String(v.target_weight) : null,
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
        <label
          >Gewichtseinheit<select name="unit">
            <option value="kg" ?selected=${this.user.unit === 'kg'}>Kilogramm (kg)</option>
            <option value="lb" ?selected=${this.user.unit === 'lb'}>Pfund (lb)</option>
          </select></label
        >
        <label
          >Anstrengungsskala<select name="effort_scale">
            <option value="rpe" ?selected=${this.user.effort_scale === 'rpe'}>
              RPE · Anstrengung
            </option>
            <option value="rir" ?selected=${this.user.effort_scale === 'rir'}>
              RIR · Wiederholungen in Reserve
            </option>
          </select></label
        >
        <label
          >Rundungsschritt<input
            type="number"
            name="rounding_step"
            min="0.01"
            max="100"
            step="0.01"
            required
            .value=${this.user.rounding_step}
        /></label>
        <label
          >Zielgewicht (${this.user.unit})<input
            type="number"
            name="target_weight"
            min="0.1"
            max="1000"
            step="0.1"
            placeholder="Optional"
            .value=${this.user.target_weight ?? ''}
        /></label>
        <label
          >Zeitzone<input name="timezone" required maxlength="100" .value=${this.user.timezone}
        /></label>
        <p class="muted">
          RPE 8 entspricht RIR 2. Ein Wechsel ändert keine gespeicherten Trainingswerte.
        </p>
        <button class="primary" ?disabled=${this.busy}>Einstellungen speichern</button>
      </form>
    </div>`;
  }
}
customElements.define('account-view', AccountView);
