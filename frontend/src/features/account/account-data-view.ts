import { LitElement, html, nothing } from 'lit';
import { users } from '../../api/generated';
import type { Transport } from '../../shared/types';
import { icon, today } from '../../shared/ui';

export class AccountDataView extends LitElement {
  static properties = {
    api: { attribute: false },
    busy: { state: true },
    error: { state: true },
    deleting: { state: true },
    confirmed: { state: true },
  };
  api!: Transport;
  private busy = false;
  private error = '';
  private deleting = false;
  private confirmed = false;
  createRenderRoot() {
    return this;
  }
  protected updated() {
    const dialog = this.querySelector<HTMLDialogElement>('dialog');
    if (this.deleting && dialog && !dialog.open) dialog.showModal();
  }
  private async act(action: () => Promise<void>) {
    if (this.busy) return;
    this.busy = true;
    this.error = '';
    try {
      await action();
    } catch (e) {
      this.error = (e as Error).message;
    } finally {
      this.busy = false;
    }
  }
  private download() {
    void this.act(async () => {
      const data = await users.exportUserData({ transport: this.api });
      const url = URL.createObjectURL(
        new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }),
      );
      const link = document.createElement('a');
      link.href = url;
      link.download = `trainingos-${today()}.json`;
      link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    });
  }
  render() {
    return html`<div class="account-data-sections">
        ${this.error ? html`<div class="notice error" role="alert">${this.error}</div>` : nothing}
        <section class="settings-section" aria-labelledby="account-export-title">
          <div class="settings-section-heading"><h2 id="account-export-title">Daten</h2></div>
          <div class="settings-row">
            <div class="settings-row-copy">
              <strong>Daten exportieren</strong>
              <small>Deine Pläne, erfassten Trainings und Einstellungen als JSON-Datei.</small>
            </div>
            <button class="secondary" ?disabled=${this.busy} @click=${this.download}>
              ${icon('download')} Herunterladen
            </button>
          </div>
        </section>
        <section class="settings-section danger-section" aria-labelledby="account-manage-title">
          <div class="settings-section-heading"><h2 id="account-manage-title">Konto</h2></div>
          <div class="settings-row">
            <div class="settings-row-copy">
              <strong>Konto löschen</strong>
              <small>Dein Konto und alle zugehörigen Daten werden dauerhaft gelöscht.</small>
            </div>
            <button
              class="text-button danger-text"
              @click=${() => {
                this.deleting = true;
                this.confirmed = false;
              }}
            >
              Konto löschen
            </button>
          </div>
        </section>
      </div>
      ${
        this.deleting
          ? html`<dialog
              class="modal"
              aria-labelledby="delete-account-title"
              @cancel=${() => {
                this.deleting = false;
              }}
            >
              <h2 id="delete-account-title">Konto endgültig löschen?</h2>
              <p>
                Alle Pläne, Trainings und Einstellungen werden entfernt. Das lässt sich nicht
                rückgängig machen.
              </p>
              <label class="check-label"
                ><input
                  type="checkbox"
                  .checked=${this.confirmed}
                  @change=${(e: Event) => {
                    this.confirmed = (e.target as HTMLInputElement).checked;
                  }}
                />Ich möchte alle meine Daten endgültig löschen.</label
              >
              <div class="actions">
                <button
                  class="secondary"
                  autofocus
                  @click=${() => {
                    this.deleting = false;
                  }}
                >
                  Abbrechen</button
                ><button
                  class="primary danger-button"
                  ?disabled=${this.busy || !this.confirmed}
                  @click=${() =>
                    this.act(async () => {
                      await users.deleteUserAccount({ transport: this.api });
                      this.dispatchEvent(new CustomEvent('account-deleted', { bubbles: true }));
                    })}
                >
                  Endgültig löschen
                </button>
              </div>
            </dialog>`
          : nothing
      }`;
  }
}
customElements.define('account-data-view', AccountDataView);
