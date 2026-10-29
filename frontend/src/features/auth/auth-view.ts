import { LitElement, html, nothing } from 'lit';
import { auth } from '../../api/generated';
import { ApiError } from '../../shared/api';
import type { Transport } from '../../shared/types';
import { icon } from '../../shared/ui';
import './auth-training-illustration';

export class AuthView extends LitElement {
  static properties = {
    api: { attribute: false },
    mode: { attribute: false },
    demo: { attribute: false },
    connectionError: { attribute: false },
    busy: { state: true },
    error: { state: true },
    showPassword: { state: true },
  };
  api!: Transport;
  mode: 'login' | 'register' = 'login';
  demo = false;
  connectionError = '';
  private busy = false;
  private error = '';
  private showPassword = false;

  createRenderRoot() {
    return this;
  }

  private async submit(event: Event) {
    event.preventDefault();
    if (this.busy || this.demo) return;
    const form = event.currentTarget as HTMLFormElement;
    const values = new FormData(form);
    const password = String(values.get('password') ?? '');
    this.error = '';
    if (this.mode === 'register' && password !== values.get('confirmation')) {
      this.error = 'Die Passwörter stimmen nicht überein.';
      return;
    }
    this.busy = true;
    try {
      const request = { email: String(values.get('email') ?? '').trim(), password };
      const user =
        this.mode === 'register'
          ? await auth.registerUser(request, { transport: this.api })
          : await auth.loginUser(request, { transport: this.api });
      form.reset();
      this.dispatchEvent(
        new CustomEvent('authenticated', { detail: user, bubbles: true, composed: true }),
      );
    } catch (error) {
      const status = error instanceof ApiError ? error.status : 0;
      this.error =
        status === 401
          ? 'Die E-Mail oder das Passwort stimmt nicht.'
          : status === 409
            ? 'Registrierung nicht möglich. Melde dich an oder nutze eine andere E-Mail.'
            : status === 429
              ? 'Zu viele Versuche. Bitte warte fünf Minuten und versuche es erneut.'
              : status === 422
                ? 'Bitte prüfe deine Eingaben. Verwende zur Registrierung mindestens 15 Zeichen für dein Passwort.'
                : 'Die Anfrage konnte nicht abgeschlossen werden. Prüfe deine Verbindung und versuche die Anmeldung erneut.';
    } finally {
      this.busy = false;
    }
  }

  render() {
    const register = this.mode === 'register';
    const suffix = this.demo ? '?demo=1' : '';
    return html`<div class="auth-layout">
      <header class="auth-header">
        <a class="auth-brand" href=${'/login' + suffix} aria-label="TrainingOS Anmeldung"
          >${icon('dumbbell')}<span>Training<span>OS</span></span></a
        ><a class="text-button" href="/?demo=1">Vorschau ${icon('arrow')}</a>
      </header>
      <main class="auth-main">
        <section class="auth-form-panel">
          <div class="auth-card" aria-labelledby="auth-title">
            <div class="auth-intro">
              <h1 id="auth-title">
                ${register ? 'Dein Training beginnt hier.' : 'Willkommen zurück.'}
              </h1>
              <p>
                ${register ? 'Dein Konto für Plan, Training und Fortschritt.' : 'Melde dich an und setze dein Training fort.'}
              </p>
            </div>
            ${this.demo ? html`<div class="notice auth-preview">Du siehst die Vorschau. <a href=${register ? '/register' : '/login'}>Echte ${register ? 'Registrierung' : 'Anmeldung'} öffnen</a></div>` : nothing}
            ${this.error || this.connectionError ? html`<p class="notice error" role="alert">${this.error || this.connectionError}</p>` : nothing}
            <form
              class="auth-form"
              aria-label=${register ? 'Registrierung' : 'Anmeldung'}
              @submit=${this.submit}
            >
              <label
                >E-Mail<input
                  name="email"
                  type="email"
                  autocomplete="email"
                  autocapitalize="none"
                  spellcheck="false"
                  placeholder="du@beispiel.de"
                  maxlength="254"
                  required
                  ?disabled=${this.busy}
              /></label>
              <label
                >Passwort<span class="password-input"
                  ><input
                    aria-label="Passwort"
                    name="password"
                    type=${this.showPassword ? 'text' : 'password'}
                    autocomplete=${register ? 'new-password' : 'current-password'}
                    placeholder=${register ? 'Mindestens 15 Zeichen' : 'Dein Passwort'}
                    minlength=${register ? 15 : 1}
                    maxlength="128"
                    aria-describedby=${register ? 'password-hint' : nothing}
                    required
                    ?disabled=${this.busy}
                  /><button
                    type="button"
                    class="bare-icon"
                    aria-label=${this.showPassword ? 'Passwort verbergen' : 'Passwort anzeigen'}
                    aria-pressed=${this.showPassword}
                    @click=${() => {
                      this.showPassword = !this.showPassword;
                    }}
                  >
                    ${icon('eye')}
                  </button></span
                ></label
              >
              ${
                register
                  ? html`<p class="auth-hint" id="password-hint">
                        Mindestens 15 Zeichen. Eine längere Wortfolge funktioniert gut.
                      </p>
                      <label
                        >Passwort wiederholen<input
                          name="confirmation"
                          type=${this.showPassword ? 'text' : 'password'}
                          autocomplete="new-password"
                          minlength="15"
                          maxlength="128"
                          required
                          ?disabled=${this.busy}
                      /></label>`
                  : nothing
              }
              <button
                class="primary auth-submit"
                ?disabled=${this.busy || this.demo}
                aria-busy=${this.busy}
              >
                <span
                  >${this.busy ? 'Einen Moment …' : register ? 'Konto erstellen' : 'Anmelden'}</span
                >${!this.busy ? icon('arrow') : nothing}
              </button>
            </form>
            <p class="auth-switch">
              ${register ? 'Du hast bereits ein Konto?' : 'Noch kein Konto?'}
              <a href=${(register ? '/login' : '/register') + suffix}
                >${register ? 'Jetzt anmelden' : 'Jetzt registrieren'}</a
              >
            </p>
          </div>
        </section>
        <aside class="auth-story" aria-hidden="true">
          <auth-training-illustration></auth-training-illustration>
        </aside>
      </main>
    </div>`;
  }
}
customElements.define('auth-view', AuthView);
