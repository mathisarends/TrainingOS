import { LitElement, html, nothing } from 'lit';
import { users } from '../../api/generated';
import type { Transport, User } from '../../shared/types';
import { formValues } from '../../shared/ui';
import { accountNavigation } from './account-navigation';

export class AccountView extends LitElement {
  static properties = {
    api: { attribute: false },
    user: { attribute: false },
    demo: { type: Boolean },
    busy: { state: true },
    error: { state: true },
    message: { state: true },
  };
  api!: Transport;
  user!: User;
  demo = false;
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
      ${accountNavigation('settings', this.demo)}
      ${this.error ? html`<div class="notice error" role="alert">${this.error}</div>` : nothing}
      ${this.message ? html`<div class="notice success" role="status">${this.message}</div>` : nothing}
      <form class="stack" @submit=${this.save}>
        <section class="settings-section" aria-labelledby="training-preferences-title">
          <div class="settings-section-heading">
            <h2 id="training-preferences-title">Training</h2>
          </div>
          <label class="settings-row"
            ><span class="settings-row-copy"
              ><strong>Gewichtseinheit</strong
              ><small>Gewichte für dein Training und deine Empfehlungen.</small></span
            >
            <training-select
              ><select aria-label="Gewichtseinheit" name="unit" ?disabled=${this.busy}>
                <option value="kg" ?selected=${this.user.unit === 'kg'}>Kilogramm (kg)</option>
                <option value="lb" ?selected=${this.user.unit === 'lb'}>Pfund (lb)</option>
              </select></training-select
            >
          </label>
          <label class="settings-row"
            ><span class="settings-row-copy"
              ><strong>Anstrengungsskala</strong
              ><small>RPE 8 entspricht zwei Wiederholungen in Reserve (RIR 2).</small></span
            >
            <training-select
              ><select aria-label="Anstrengungsskala" name="effort_scale" ?disabled=${this.busy}>
                <option value="rpe" ?selected=${this.user.effort_scale === 'rpe'}>
                  RPE · Anstrengung
                </option>
                <option value="rir" ?selected=${this.user.effort_scale === 'rir'}>
                  RIR · Wiederholungen in Reserve
                </option>
              </select></training-select
            >
          </label>
          <label class="settings-row"
            ><span class="settings-row-copy"
              ><strong>Rundungsschritt</strong
              ><small>Schrittweite für Gewichtsempfehlungen in der gewählten Einheit.</small></span
            >
            <input
              aria-label="Rundungsschritt"
              type="number"
              name="rounding_step"
              min="0.01"
              max="100"
              step="0.01"
              required
              ?disabled=${this.busy}
              .value=${this.user.rounding_step}
            />
          </label>
        </section>
        <section class="settings-section" aria-labelledby="regional-preferences-title">
          <div class="settings-section-heading">
            <h2 id="regional-preferences-title">Region</h2>
          </div>
          <label class="settings-row"
            ><span class="settings-row-copy"
              ><strong>Zeitzone</strong
              ><small>Ordnet deine Trainings dem richtigen Kalendertag zu.</small></span
            >
            <input
              aria-label="Zeitzone"
              name="timezone"
              required
              maxlength="100"
              ?disabled=${this.busy}
              .value=${this.user.timezone}
            />
          </label>
        </section>
        <div class="settings-actions">
          <p>Gespeicherte Trainingswerte bleiben erhalten.</p>
          <button class="primary" ?disabled=${this.busy}>
            ${this.busy ? 'Wird gespeichert …' : 'Einstellungen speichern'}
          </button>
        </div>
      </form>
    </div>`;
  }
}
customElements.define('account-view', AccountView);
