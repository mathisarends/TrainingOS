import { LitElement, html, type PropertyValues } from 'lit';
import type { User, TrainingSession } from '../../shared/types';
import { icon } from '../../shared/ui';

export class ProfileView extends LitElement {
  static properties = {
    user: { attribute: false },
    sessions: { attribute: false },
    demo: { attribute: false },
    year: { state: true },
  };
  user!: User;
  sessions: TrainingSession[] = [];
  demo = false;
  private year = new Date().getFullYear();
  createRenderRoot() {
    return this;
  }
  protected updated(changes: PropertyValues) {
    if (changes.has('year') || changes.has('sessions')) {
      const scroll = this.querySelector('.activity-scroll');
      if (scroll) scroll.scrollLeft = scroll.scrollWidth;
    }
  }
  render() {
    const suffix = this.demo ? '?demo=1' : '';
    const entries = [
      ['Übungen', 'dumbbell', '/profile/exercises'],
      ['Bestleistungen', 'award', '/profile/best-performance'],
      ['Körpergewicht', 'scale', '/profile/body-weight'],
      ['Trainingspläne', 'plans', '/plans'],
      ['Einstellungen', 'sliders', '/profile/settings'],
      ['Meine Daten', 'download', '/profile/data'],
    ];
    const since = new Date();
    since.setDate(since.getDate() - 29);
    since.setHours(0, 0, 0, 0);
    const recent = this.sessions.filter(
      (s) => s.ended_at && new Date(s.started_at) >= since,
    ).length;
    return html`<div class="profile-wrapper">
      <div class="profile-identity">
        <div class="profile-avatar">${icon('user')}</div>
        <div>
          <h1>${this.demo ? 'Vorschau' : 'Dein Trainingskonto'}</h1>
          <p
            title=${this.demo ? 'Isolierte Vorschau. Änderungen sind temporär und werden beim Neuladen zurückgesetzt.' : ''}
          >
            ${this.demo ? 'Beispieldaten' : 'Angemeldet'} · ${this.user.unit} ·
            ${this.user.effort_scale.toUpperCase()}
          </p>
        </div>
      </div>
      <div class="activity-card">
        <div class="activity-scroll">
          <div class="activity-months">
            ${['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez'].map((m) => html`<span>${m}</span>`)}
          </div>
          <div class="activity-grid">
            ${Array.from({ length: 371 }, (_, i) => {
              const date = new Date(
                this.year,
                0,
                1 + i - ((new Date(this.year, 0, 1).getDay() + 6) % 7),
              );
              const count = this.sessions.filter(
                (s) =>
                  !!s.ended_at && new Date(s.started_at).toDateString() === date.toDateString(),
              ).length;
              return html`<span
                class="activity-cell ${count ? 'trained' : ''}"
                title=${`${date.toLocaleDateString('de-DE')} · ${count} Trainings`}
              ></span>`;
            })}
          </div>
        </div>
        <div class="activity-footer">
          <div class="activity-summary">
            <span><strong>${recent} Trainings</strong> in den letzten 30 Tagen</span>
            <div class="activity-legend">
              <span>Weniger</span
              >${Array.from({ length: 5 }, (_, i) => html`<span class="activity-level level-${i}"></span>`)}<span
                >Mehr</span
              >
            </div>
          </div>
          <label
            ><select
              aria-label="Aktivitätsjahr"
              .value=${String(this.year)}
              @change=${(e: Event) => {
                this.year = Number((e.target as HTMLSelectElement).value);
              }}
            >
              ${Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - i).map((year) => html`<option value=${year}>${year}</option>`)}
            </select></label
          >
        </div>
      </div>
      <div class="profile-links">
        ${[entries.slice(0, 4), entries.slice(4)].map((group) => html`<div class="profile-link-group">${group.map(([label, name, path]) => html`<a class="profile-link" href=${path + suffix}><span class="profile-link-icon">${icon(name)}</span><span>${label}</span>${icon('chevron-right')}</a>`)}</div>`)}<button
          class="profile-link profile-logout"
          @click=${() => this.dispatchEvent(new CustomEvent('logout', { bubbles: true }))}
        >
          <span class="profile-link-icon">${icon('logout')}</span><span>Abmelden</span>
        </button>
      </div>
    </div>`;
  }
}
customElements.define('profile-view', ProfileView);
