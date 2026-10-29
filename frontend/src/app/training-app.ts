import { LitElement, html, nothing, type PropertyValues } from 'lit';
import { ContextConsumer } from '@lit/context';
import { auth, plans as planApi, trainingSessions } from '../api/generated';
import { ApiError } from '../shared/api';
import type { Exercise, NextTraining, Plan, TrainingSession, User } from '../shared/types';
import {
  categories,
  dateLabel,
  empty,
  formatNumber,
  icon,
  statuses,
  today,
  weekdays,
} from '../shared/ui';
import { transportContext, storeContext, navigationContext } from './context';
import { paths, titles, trainingOverviewHref, type Page, type TrainingSelection } from './routing';
import '../features/training/rest-timer';
import '../features/auth/auth-view';
import type { RestTimer } from '../features/training/rest-timer';

export class TrainingApp extends LitElement {
  static properties = {
    page: { attribute: false },
    routeId: { attribute: false },
    trainingSelection: { attribute: false },
    user: { state: true },
    plans: { state: true },
    exercises: { state: true },
    sessions: { state: true },
    next: { state: true },
    session: { state: true },
    loading: { state: true },
    busy: { state: true },
    error: { state: true },
    online: { state: true },
    historyMore: { state: true },
    homeDay: { state: true },
    homeWeek: { state: true },
    selectedPlan: { state: true },
    deleting: { state: true },
    signingOut: { state: true },
  };
  page: Page = 'home';
  routeId = '';
  trainingSelection: TrainingSelection | null = null;
  private user: User | null = null;
  private plans: Plan[] = [];
  private exercises: Exercise[] = [];
  private sessions: TrainingSession[] = [];
  private next: NextTraining | null = null;
  private session: TrainingSession | null = null;
  private loading = true;
  private busy = false;
  private error = '';
  private online = navigator.onLine;
  private historyMore = false;
  private homeDay = '';
  private homeWeek = 0;
  private selectedPlan = '';
  private deleting: Plan | null = null;
  private signingOut = false;
  private sessionRequest = 0;
  private userRevision = 0;
  private refreshPending = false;
  private refreshing?: Promise<void>;
  private readonly demo = new URLSearchParams(location.search).get('demo') === '1';
  private readonly transport = new ContextConsumer(this, { context: transportContext });
  private readonly store = new ContextConsumer(this, { context: storeContext });
  private readonly navigation = new ContextConsumer(this, { context: navigationContext });
  private get api() {
    return this.transport.value!;
  }
  private readonly onNetwork = () => {
    this.online = navigator.onLine;
  };
  private get runningSession() {
    return this.session && !this.session.ended_at
      ? this.session
      : this.sessions.find((s) => !s.ended_at);
  }
  private get plan() {
    if (this.trainingSelection) return this.plans.find((p) => p.id === this.selectedPlan);
    return (
      this.plans.find((p) => p.id === this.selectedPlan) ??
      this.plans.find((p) => p.id === this.next?.plan_id) ??
      this.plans.find((p) => p.status === 'active') ??
      this.plans[0]
    );
  }

  createRenderRoot() {
    return this;
  }
  connectedCallback() {
    super.connectedCallback();
    window.addEventListener('online', this.onNetwork);
    window.addEventListener('offline', this.onNetwork);
    void this.load();
  }
  disconnectedCallback() {
    super.disconnectedCallback();
    window.removeEventListener('online', this.onNetwork);
    window.removeEventListener('offline', this.onNetwork);
  }
  protected willUpdate(changes: PropertyValues) {
    if (!changes.has('trainingSelection')) return;
    if (this.trainingSelection) {
      this.selectedPlan = this.trainingSelection.planId;
      this.homeDay = this.trainingSelection.dayId;
      this.homeWeek = this.trainingSelection.week;
    } else if (changes.get('trainingSelection')) {
      this.selectedPlan = '';
      this.homeDay = '';
      this.homeWeek = 0;
    }
  }
  protected updated(changes: PropertyValues) {
    if (changes.has('page')) this.error = '';
    if ((changes.has('routeId') || changes.has('page')) && this.user && !this.loading)
      void this.restoreSessionRoute();
    const dialog = this.querySelector<HTMLDialogElement>('#delete-plan');
    if (this.deleting && dialog && !dialog.open) dialog.showModal();
  }
  private href(page: Page, id = '') {
    return paths[page] + (id ? `/${encodeURIComponent(id)}` : '') + (this.demo ? '?demo=1' : '');
  }
  private navigate(page: Page, id = '') {
    void this.navigation.value!.navigate(paths[page] + (id ? `/${encodeURIComponent(id)}` : ''));
  }
  private async load() {
    this.loading = true;
    this.error = '';
    try {
      this.user = await this.store.value!.user();
      await this.refresh();
      await this.restoreSessionRoute();
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) {
        this.user = null;
        this.store.value!.clear();
        if (this.page !== 'login' && this.page !== 'register') this.navigate('login');
      } else this.error = (e as Error).message;
    } finally {
      this.loading = false;
    }
  }
  private async refresh() {
    if (this.refreshing) {
      this.refreshPending = true;
      return this.refreshing;
    }
    this.refreshing = (async () => {
      do {
        this.refreshPending = false;
        await this.loadDashboard();
      } while (this.refreshPending);
    })();
    try {
      await this.refreshing;
    } finally {
      this.refreshing = undefined;
    }
  }
  private async loadDashboard() {
    const revision = this.userRevision;
    const userId = this.user?.id;
    const state = await this.store.value!.dashboard();
    if (!this.user || this.user.id !== userId || revision !== this.userRevision) return;
    this.plans = state.plans;
    this.exercises = state.exercises;
    this.sessions = state.sessions;
    this.next = state.next;
    this.historyMore = false;
    if (
      state.next.running_training_session_id &&
      (!this.routeId || this.routeId === state.next.running_training_session_id)
    ) {
      const session = await trainingSessions.getTrainingSession(
        state.next.running_training_session_id,
        { transport: this.api },
      );
      if (this.user && revision === this.userRevision) this.session = session;
    }
  }
  private async restoreSessionRoute() {
    if (this.page === 'training' && this.routeId && this.session?.id !== this.routeId) {
      const requestedId = this.routeId,
        request = ++this.sessionRequest;
      try {
        const session = await trainingSessions.getTrainingSession(requestedId, {
          transport: this.api,
        });
        if (
          this.page === 'training' &&
          this.routeId === requestedId &&
          request === this.sessionRequest
        )
          this.session = session;
      } catch (e) {
        if (request !== this.sessionRequest || this.routeId !== requestedId) return;
        if (this.demo && e instanceof ApiError && e.status === 404) this.navigate('training');
        else this.error = (e as Error).message;
      }
    }
  }
  private async act(action: () => Promise<void>) {
    if (this.busy) return;
    this.busy = true;
    this.error = '';
    try {
      await action();
    } catch (e) {
      this.error = (e as Error).message;
      if (e instanceof ApiError && e.status === 401) {
        this.user = null;
        this.session = null;
        this.plans = [];
        this.sessions = [];
        this.exercises = [];
        this.next = null;
        this.store.value!.clear();
      }
    } finally {
      this.busy = false;
    }
  }
  private start(body?: { plan_id: string; day_id: string; week: number }) {
    void this.act(async () => {
      if (this.next?.running_training_session_id)
        this.session = await trainingSessions.getTrainingSession(
          this.next.running_training_session_id,
          { transport: this.api },
        );
      else if (body)
        this.session = await trainingSessions.startTrainingSession(body, { transport: this.api });
      else return;
      await this.refresh();
      this.navigate('training', this.session.id);
    });
  }
  private onSession(event: CustomEvent<TrainingSession>) {
    this.session = event.detail;
    this.sessions = [event.detail, ...this.sessions.filter((s) => s.id !== event.detail.id)];
    void this.act(async () => {
      this.next = await planApi.getNextTraining({ transport: this.api });
    });
  }
  private onTimerSession(event: CustomEvent<TrainingSession>) {
    this.sessions = this.sessions.map((s) => (s.id === event.detail.id ? event.detail : s));
    if (this.session?.id === event.detail.id) this.session = event.detail;
  }
  private clearUserState() {
    ++this.userRevision;
    ++this.sessionRequest;
    this.refreshPending = false;
    this.store.value!.clear();
    this.user = null;
    this.session = null;
    this.plans = [];
    this.sessions = [];
    this.exercises = [];
    this.next = null;
    this.deleting = null;
    this.selectedPlan = '';
    this.homeDay = '';
    this.homeWeek = 0;
    this.historyMore = false;
  }
  private async logout() {
    if (this.signingOut) return;
    this.signingOut = true;
    this.error = '';
    try {
      if (this.demo) {
        this.clearUserState();
        location.replace('/login');
        return;
      }
      try {
        await auth.logoutUser({ transport: this.api });
      } catch (error) {
        // An expired session is already signed out; other failures need explicit retry.
        if (!(error instanceof ApiError && error.status === 401)) throw error;
      }
      this.clearUserState();
      this.navigate('login');
    } catch {
      this.error = 'Abmelden fehlgeschlagen. Bitte prüfe die Verbindung und versuche es erneut.';
    } finally {
      this.signingOut = false;
    }
  }
  private currentWeek(plan: Plan) {
    const days = (Date.parse(today()) - Date.parse(plan.start_date)) / 86400000;
    return Math.max(1, Math.min(plan.weeks, Math.floor(days / 7) + 1));
  }
  private planProgress(plan: Plan) {
    const completed = this.sessions.filter((s) => s.plan_id === plan.id && s.ended_at);
    const currentWeek = this.currentWeek(plan);
    const summary =
      plan.status === 'active'
        ? `Woche ${currentWeek} / ${plan.weeks}`
        : plan.status === 'draft'
          ? `Startet ${dateLabel(plan.start_date)}`
          : `${completed.length} / ${plan.weeks * plan.days.length} Einheiten`;
    return html`<a
      class="plan-progress-link"
      href=${this.href('training')}
      @click=${() => {
        this.selectedPlan = plan.id;
        this.homeDay = '';
        this.homeWeek = plan.status === 'active' ? currentWeek : 1;
      }}
      aria-label=${`${plan.title} ansehen · ${statuses[plan.status]} · ${summary}`}
    >
      <div class="plan-progress-heading">
        <span class="plan-status status-${plan.status}"
          ><span class="status-dot"></span>${statuses[plan.status]}</span
        >
        <span class="plan-progress-summary">${summary}</span>
      </div>
      <div class="plan-progress-scroll">
        <div
          class="plan-progress-grid"
          style=${`grid-template-columns: repeat(${plan.weeks}, minmax(1.5rem, 1fr))`}
        >
          ${Array.from(
            { length: plan.weeks },
            (_, i) =>
              html`<div
                class="plan-progress-week ${plan.status === 'active' && i + 1 === currentWeek ? 'current' : ''}"
              >
                <div class="plan-progress-days">
                  ${plan.days.map((day) => html`<span class="progress-segment ${completed.some((s) => s.week === i + 1 && s.day_id === day.id) ? 'completed' : ''}"></span>`)}
                </div>
                <span>W${i + 1}</span>
              </div>`,
          )}
        </div>
      </div>
    </a>`;
  }
  private home() {
    return html`<div class="training-plan-grid">
        ${this.plans.map(
          (plan) =>
            html`<article class="training-plan-card plan-${plan.status}">
              ${this.planProgress(plan)}
              <div class="card-body">
                <h2>
                  <a
                    href=${this.href('training')}
                    @click=${() => {
                      this.selectedPlan = plan.id;
                      this.homeDay = '';
                      this.homeWeek = plan.status === 'active' ? this.currentWeek(plan) : 1;
                    }}
                    >${plan.title}</a
                  >
                </h2>
                <p>
                  ${plan.days.length} Trainings / Woche · ${dateLabel(plan.start_date)} ·
                  ${plan.weeks} Wochen
                </p>
                <details class="plan-card-menu">
                  <summary class="bare-icon" aria-label=${`Aktionen für ${plan.title}`}>
                    ${icon('more-horizontal')}
                  </summary>
                  <div class="plan-card-menu-items">
                    <a href=${this.href('plans', plan.id)}>${icon('edit')} Bearbeiten</a>
                    <button
                      @click=${(e: Event) => {
                        (e.currentTarget as HTMLElement).closest('details')!.open = false;
                        this.deleting = plan;
                      }}
                    >
                      ${icon('trash')} Löschen
                    </button>
                  </div>
                </details>
              </div>
            </article>`,
        )}
        ${
          !this.plans.length
            ? html`<section class="empty-plan" aria-labelledby="first-plan-title">
                <div class="empty-plan-copy">
                  <span class="eyebrow">Dein erster Schritt</span>
                  <h2 id="first-plan-title">Dein Training.<br />Mit einem Plan.</h2>
                  <p>
                    Lege deine Trainingstage und Übungen fest. Deine Vorgaben und Fortschritte
                    bleiben an einem Ort.
                  </p>
                  <a class="primary" href=${this.href('plans', 'new')}
                    >${icon('plus')} Ersten Plan erstellen</a
                  >
                </div>
                <div class="empty-plan-preview" aria-hidden="true">
                  <div class="empty-preview-heading">
                    ${icon('dumbbell')}<span>Dein Trainingsplan</span><span>6 Wochen</span>
                  </div>
                  <div class="empty-preview-weeks">
                    ${Array.from({ length: 6 }, (_, week) => html`<div><span>W${week + 1}</span>${Array.from({ length: 3 }, () => html`<i></i>`)}</div>`)}
                  </div>
                  <div class="empty-preview-day">
                    <span>A</span>
                    <div>
                      <strong>Trainingstag</strong><small>Deine Übungen und Vorgaben</small>
                    </div>
                    ${icon('chevron-right')}
                  </div>
                </div>
              </section>`
            : nothing
        }
      </div>
      ${
        this.deleting
          ? html`<dialog
              class="modal"
              id="delete-plan"
              aria-labelledby="delete-title"
              @cancel=${() => {
                this.deleting = null;
              }}
            >
              <h2 id="delete-title">Plan löschen?</h2>
              <p>
                „${this.deleting.title}“ wird gelöscht. Bereits erfasste Trainings bleiben im
                Verlauf erhalten.
              </p>
              <div class="actions">
                <button
                  class="secondary"
                  autofocus
                  @click=${() => {
                    this.deleting = null;
                  }}
                >
                  Abbrechen</button
                ><button
                  class="primary"
                  ?disabled=${this.busy}
                  @click=${() =>
                    this.act(async () => {
                      await planApi.deletePlan(this.deleting!.id, { transport: this.api });
                      this.deleting = null;
                      await this.refresh();
                    })}
                >
                  Plan löschen
                </button>
              </div>
            </dialog>`
          : nothing
      }`;
  }
  private selectTrainingOverview(planId: string, dayId: string, week: number) {
    void this.navigation.value!.navigate(trainingOverviewHref({ planId, dayId, week }));
  }
  private trainingOverview() {
    const plan = this.plan;
    const explicit = this.trainingSelection !== null;
    const day = explicit
      ? plan?.days.find((d) => d.id === this.homeDay)
      : (plan?.days.find((d) => d.id === (this.homeDay || this.next?.day_id)) ?? plan?.days[0]);
    const week = explicit
      ? this.homeWeek
      : Math.min(this.homeWeek || this.next?.week || 1, plan?.weeks ?? 1);
    const running = !!this.runningSession;
    if (explicit && (!plan || !day || !Number.isInteger(week) || week < 1 || week > plan.weeks)) {
      const recorded = this.sessions.find(
        (s) =>
          s.plan_id === this.selectedPlan && s.day_id === this.homeDay && s.week === this.homeWeek,
      );
      return html`${empty('Trainingstag nicht verfügbar', 'Der verlinkte Trainingstag ist in diesem Plan nicht mehr verfügbar.')}
        <div class="actions">
          <a class="secondary" href=${this.href('history')}>Zurück zu den Logs</a>
          ${recorded ? html`<a class="secondary" href=${this.href('training', recorded.id)}>Gespeichertes Training ansehen</a>` : nothing}
        </div>`;
    }
    if (!plan || !day)
      return html`${empty('Noch kein Trainingsplan', 'Erstelle zuerst deinen Trainingsplan.')}<a
          class="secondary"
          href=${this.href('plans')}
          >Plan erstellen</a
        >`;
    const valid =
      day.slots.length > 0 && day.slots.every((s) => s.prescriptions.some((p) => p.week === week));
    const recorded = this.sessions.find(
      (s) => s.plan_id === plan.id && s.day_id === day.id && s.week === week,
    );
    return html`<div class="training-context">
        <div class="training-context-title">
          <p class="eyebrow">${plan.title}</p>
          <h1>${day.name}<span> · Woche ${week} von ${plan.weeks}</span></h1>
        </div>
        <div class="actions">
          <a
            class="secondary overview-edit"
            href=${this.href('plans', plan.id)}
            aria-label="Plan bearbeiten"
            >${icon('edit')}<span>Bearbeiten</span></a
          ><button
            class="primary overview-start"
            ?disabled=${this.busy || (!recorded && !valid && !running)}
            @click=${() => (recorded ? this.navigate('training', recorded.id) : this.start({ plan_id: plan.id, day_id: day.id, week }))}
          >
            ${icon('play')}${recorded ? 'Training ansehen' : running ? 'Training fortsetzen' : 'Training starten'}
          </button>
        </div>
      </div>
      <div class="training-pagination overview-pagination">
        <div class="day-pagination" role="group" aria-label="Trainingstag auswählen">
          ${plan.days.map(
            (d, i) =>
              html`<button
                class=${d.id === day.id ? 'selected' : ''}
                aria-label=${`${weekdays[d.weekday]} · ${d.name}`}
                aria-pressed=${d.id === day.id}
                @click=${() => {
                  this.selectTrainingOverview(plan.id, d.id, week);
                }}
              >
                ${String.fromCharCode(65 + i)}
              </button>`,
          )}
        </div>
        <div class="week-navigation">
          <button
            class="bare-icon"
            aria-label="Vorherige Woche"
            ?disabled=${week <= 1}
            @click=${() => {
              this.selectTrainingOverview(plan.id, day.id, week - 1);
            }}
          >
            ${icon('chevron-left')}
          </button>
          <span><strong>W${week}</strong> / ${plan.weeks}</span>
          <button
            class="bare-icon"
            aria-label="Nächste Woche"
            ?disabled=${week >= plan.weeks}
            @click=${() => {
              this.selectTrainingOverview(plan.id, day.id, week + 1);
            }}
          >
            ${icon('chevron-right')}
          </button>
        </div>
      </div>
      <div class="training-sheet preview-sheet">
        <div class="sheet-column-headings">
          <span>Kategorie</span><span>Übung</span><span>Sätze</span><span>Wdh.</span
          ><span>Gewicht</span><span>${this.user!.effort_scale.toUpperCase()}</span
          ><span>@${this.user!.effort_scale.toUpperCase()}</span><span>e1RM</span><span>Notiz</span>
        </div>
        ${day.slots.map((slot, index) => {
          const rx = slot.prescriptions.find((p) => p.week === week);
          return html`<section class="training-sheet-exercise">
            <div class="sheet-exercise-heading">
              <span class="row-number">${String(index + 1).padStart(2, '0')}</span>
              <h2>${slot.exercise_name}</h2>
              <span>${categories[slot.category]}</span>
            </div>
            <div class="training-sheet-form">
              ${[categories[slot.category], slot.exercise_name, rx?.sets ?? '–', rx?.reps ?? '–', '–', rx ? formatNumber(rx.target_effort) : '–', '–', '–', rx?.note || '–'].map((value, i) => html`<div class="sheet-field ${i === 0 ? 'sheet-category' : i === 1 ? 'sheet-name' : i === 8 ? 'sheet-note' : ''} ${value === '–' ? 'empty-value' : ''}"><span class="field-label">${['Kategorie', 'Übung', 'Sätze', 'Wdh.', `Gewicht (${this.user!.unit})`, this.user!.effort_scale.toUpperCase(), `@${this.user!.effort_scale.toUpperCase()}`, 'e1RM', 'Notiz'][i]}</span><span>${value}</span></div>`)}
              <div class="sheet-field preview-rest">
                <span class="field-label">Pause</span
                ><span
                  >${Math.floor(slot.rest_seconds / 60)}:${String(slot.rest_seconds % 60).padStart(2, '0')}</span
                >
              </div>
            </div>
          </section>`;
        })}
      </div>
      ${!valid ? html`<p class="muted training-save-note">Ergänze die Wochenvorgaben im Plan, bevor du das Training startest.</p>` : nothing} `;
  }
  private login() {
    return html`<auth-view
      .api=${this.api}
      .mode=${this.page === 'register' ? 'register' : 'login'}
      .demo=${this.demo}
      .connectionError=${this.error}
      @authenticated=${(event: CustomEvent<User>) => {
        this.store.value!.clear();
        this.user = event.detail;
        this.navigate('home');
        void this.act(() => this.refresh());
      }}
    ></auth-view>`;
  }
  private content() {
    if (this.loading)
      return html`<div class="empty loading" role="status">
        <span class="loader"></span>
        <p>Wird geladen …</p>
      </div>`;
    if (!this.user || this.page === 'login' || this.page === 'register') return this.login();
    switch (this.page) {
      case 'home':
        return this.home();
      case 'plans':
        if (
          this.routeId &&
          this.routeId !== 'new' &&
          !this.plans.some((p) => p.id === this.routeId)
        )
          return empty('Plan nicht gefunden', 'Öffne einen vorhandenen Trainingsplan über Home.');
        return html`<plans-view
          .api=${this.api}
          .plans=${this.plans}
          .exercises=${this.exercises}
          .user=${this.user}
          .selected=${this.routeId}
          .createNew=${this.routeId === 'new'}
          @plan-selected=${(e: CustomEvent<string>) => this.navigate('plans', e.detail)}
          @plans-changed=${() => {
            void this.refresh().catch((e: Error) => {
              this.error = e.message;
            });
          }}
          @start-training=${(e: CustomEvent<{ plan_id: string; day_id: string; week: number }>) => this.start(e.detail)}
        ></plans-view>`;
      case 'catalog':
        return html`<catalog-view
          .user=${this.user}
          .api=${this.api}
          .exercises=${this.exercises}
          @catalog-changed=${() => {
            void this.refresh().catch((e: Error) => {
              this.error = e.message;
            });
          }}
        ></catalog-view>`;
      case 'account':
      case 'data':
        return html`<profile-view
          .user=${this.user}
          .api=${this.api}
          .demo=${this.demo}
          .signingOut=${this.signingOut}
          @logout=${this.logout}
          @account-deleted=${() => {
            this.clearUserState();
            location.replace('/login');
          }}
        ></profile-view>`;
      case 'settings':
        return html`<account-view
          .api=${this.api}
          .user=${this.user}
          .demo=${this.demo}
          @user-changed=${(e: CustomEvent<User>) => {
            this.user = e.detail;
            this.store.value!.clear();
            void this.act(() => this.refresh());
          }}
        ></account-view>`;
      case 'records':
        return html`<records-view .api=${this.api} .user=${this.user}></records-view>`;
      case 'history':
        return html`<history-view
          .api=${this.api}
          .sessions=${this.sessions}
          .more=${this.historyMore}
          .demo=${this.demo}
        ></history-view>`;
      case 'training':
        return this.routeId && this.session?.id === this.routeId
          ? html`<training-view
              .api=${this.api}
              .session=${this.session}
              @session-changed=${this.onSession}
              @training-interaction=${() => {
                void this.querySelector<RestTimer>('rest-timer')?.enable();
              }}
            ></training-view>`
          : this.trainingOverview();
    }
  }
  render() {
    if (this.loading && !this.user)
      return html`<div class="auth-layout">
        <main class="auth-main">
          <div class="empty loading" role="status">
            <span class="loader"></span>
            <p>Wird geladen …</p>
          </div>
        </main>
      </div>`;
    if (!this.loading && (!this.user || this.page === 'login' || this.page === 'register'))
      return this.login();
    const training = this.page === 'training';
    const context = this.page === 'plans' ? 'Plan' : '';
    const accountSection = ['account', 'settings', 'data'].includes(this.page);
    const heading = accountSection ? 'Konto' : training ? 'Training' : titles[this.page];
    const nav = [
      { page: 'home' as Page, label: 'Home', icon: 'home' },
      { page: 'training' as Page, label: 'Training', icon: 'activity' },
      { page: 'history' as Page, label: 'Logs', icon: 'plans' },
      { page: 'account' as Page, label: 'Konto', icon: 'user' },
    ];
    return html`<a class="skip-link" href="#main-content">Zum Inhalt springen</a>
      <div
        class="app-shell page-${this.page} ${this.user && this.runningSession ? 'has-rest-dock' : ''}"
      >
        <header class="topbar">
          <div class="header-title">
            ${['catalog', 'records', 'plans'].includes(this.page) ? html`<a class="bare-icon back-link" href=${this.href(['catalog', 'records'].includes(this.page) ? 'account' : 'home')} aria-label="Zurück">${icon('arrow-left')}</a>` : nothing}${context ? html`<span class="context">${context}</span>` : nothing}<span
              class="current"
              role=${this.page === 'history' ? 'heading' : nothing}
              aria-level=${this.page === 'history' ? '1' : nothing}
              >${heading}</span
            >
          </div>
          <div class="header-actions">
            ${this.page === 'home' && this.user ? html`<a class="bare-icon header-add" href=${this.href('plans', 'new')} aria-label="Neuen Plan erstellen">${icon('plus')}</a>` : accountSection ? nothing : html`<a class="bare-icon header-account" href=${this.href('account')} aria-label="Konto öffnen">${icon('user')}</a>`}
          </div>
        </header>
        <main id="main-content" tabindex="-1">
          ${!this.online ? html`<div class="notice error" role="alert">Du bist offline. Zum Speichern brauchst du eine Verbindung.</div>` : nothing}${this.error ? html`<div class="notice error" role="alert">${this.error}<button class="text-button" @click=${this.load}>Erneut laden</button></div>` : nothing}${this.content()}
        </main>
        <nav class="mobile-nav" aria-label="Hauptnavigation">
          ${nav.map((n) => {
            const active =
              n.page === this.page ||
              (n.page === 'account' &&
                ['catalog', 'records', 'settings', 'data'].includes(this.page)) ||
              (n.page === 'home' && this.page === 'plans');
            return html`<a
              href=${this.href(n.page, n.page === 'training' ? this.runningSession?.id : '')}
              class=${active ? 'active' : ''}
              aria-current=${active ? 'page' : nothing}
              >${icon(n.icon)}<span>${n.label}</span></a
            >`;
          })}
        </nav>
        ${this.user && this.runningSession ? html`<rest-timer .api=${this.api} .session=${this.runningSession} @timer-session-changed=${this.onTimerSession}></rest-timer>` : nothing}
      </div>`;
  }
}
customElements.define('training-app', TrainingApp);
