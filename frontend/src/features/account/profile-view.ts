import { LitElement, html } from 'lit';
import type { Transport, User } from '../../shared/types';
import { icon } from '../../shared/ui';
import { accountNavigation } from './account-navigation';
import './account-data-view';

export class ProfileView extends LitElement {
  static properties = {
    user: { attribute: false },
    api: { attribute: false },
    demo: { type: Boolean },
  };
  user!: User;
  api!: Transport;
  demo = false;
  createRenderRoot() {
    return this;
  }
  render() {
    const suffix = this.demo ? '?demo=1' : '';
    const entries = [
      {
        label: 'Übungen',
        description: 'Übungen verwalten und Kategorie-Vorgaben festlegen.',
        icon: 'dumbbell',
        path: '/profile/exercises',
      },
      {
        label: 'Bestleistungen',
        description: 'Deine Bestwerte und erfassten Trainings ansehen.',
        icon: 'award',
        path: '/profile/best-performance',
      },
    ];
    return html`<div class="profile-wrapper">
      ${accountNavigation('account', this.demo)}
      <div class="profile-identity">
        <div class="profile-avatar">${icon('user')}</div>
        <div class="profile-identity-copy">
          <h1>${this.demo ? 'Vorschau' : 'Dein Trainingskonto'}</h1>
          <p
            title=${this.demo ? 'Isolierte Vorschau. Änderungen werden beim Neuladen zurückgesetzt.' : ''}
          >
            ${this.demo ? 'Beispieldaten' : 'Angemeldet'} · ${this.user.unit} ·
            ${this.user.effort_scale.toUpperCase()}
          </p>
        </div>
        <button
          class="secondary profile-logout"
          @click=${() => this.dispatchEvent(new CustomEvent('logout', { bubbles: true }))}
        >
          ${icon('logout')} Abmelden
        </button>
      </div>
      <section class="settings-section" aria-labelledby="account-training-title">
        <div class="settings-section-heading"><h2 id="account-training-title">Training</h2></div>
        ${entries.map(
          (entry) =>
            html`<a class="settings-link" href=${entry.path + suffix}
              ><span class="profile-link-icon">${icon(entry.icon)}</span
              ><span class="settings-row-copy"
                ><strong>${entry.label}</strong><small>${entry.description}</small></span
              >${icon('chevron-right')}</a
            >`,
        )}
      </section>
      <account-data-view .api=${this.api}></account-data-view>
    </div>`;
  }
}
customElements.define('profile-view', ProfileView);
