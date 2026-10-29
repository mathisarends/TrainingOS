import { LitElement, html, nothing, type PropertyValues } from 'lit';
import { keyed } from 'lit/directives/keyed.js';
import { plans as api } from '../../api/generated';
import type {
  Exercise,
  Plan,
  PlanSlot,
  ProgressionPreview,
  TrainingDay,
  Transport,
  User,
} from '../../shared/types';
import { categories, empty, formValues, icon, statuses, today, weekdays } from '../../shared/ui';

export class PlansView extends LitElement {
  static properties = {
    api: { attribute: false },
    plans: { attribute: false },
    exercises: { attribute: false },
    user: { attribute: false },
    selected: { attribute: false },
    createNew: { attribute: false },
    createDays: { state: true },
    createStep: { state: true },
    week: { state: true },
    dayIndex: { state: true },
    creating: { state: true },
    editing: { state: true },
    adding: { state: true },
    progressing: { state: true },
    sharing: { state: true },
    busy: { state: true },
    error: { state: true },
    preview: { state: true },
    message: { state: true },
    shareToken: { state: true },
  };
  api!: Transport;
  plans: Plan[] = [];
  exercises: Exercise[] = [];
  user!: User;
  selected = '';
  createNew = false;
  private createDays = new Set([0, 2, 4]);
  private createStep = 0;
  private week = 1;
  private dayIndex = 0;
  private creating = false;
  private editing = false;
  private adding = false;
  private progressing = false;
  private sharing = false;
  private busy = false;
  private error = '';
  private message = '';
  private shareToken = '';
  private preview: ProgressionPreview | null = null;
  private progression = { increment: '0.5', deload: true };
  createRenderRoot() {
    return this;
  }
  private get plan() {
    return (
      this.plans.find((p) => p.id === this.selected) ??
      this.plans.find((p) => p.status === 'active') ??
      this.plans[0]
    );
  }
  protected willUpdate(changes: PropertyValues) {
    if (changes.has('createNew') && this.createNew) this.creating = true;
    if (!this.selected && this.plans.length) this.selected = this.plan.id;
  }
  protected updated(changes: PropertyValues) {
    if (changes.has('selected')) {
      this.week = 1;
      this.dayIndex = 0;
      this.preview = null;
    }
    const dialog = this.querySelector<HTMLDialogElement>('dialog');
    if (dialog && !dialog.open) dialog.showModal();
  }
  private close() {
    if (this.busy) return;
    this.createStep = 0;
    this.createDays = new Set([0, 2, 4]);
    this.creating = false;
    this.editing = false;
    this.progressing = false;
    this.sharing = false;
    this.error = '';
  }
  private accept(plan: Plan) {
    const changed = this.selected !== plan.id;
    this.plans = this.plans.some((p) => p.id === plan.id)
      ? this.plans.map((p) => (p.id === plan.id ? plan : p))
      : [...this.plans, plan];
    if (this.selected !== plan.id) this.selected = plan.id;
    this.dispatchEvent(new CustomEvent('plans-changed', { bubbles: true }));
    if (changed)
      this.dispatchEvent(new CustomEvent('plan-selected', { detail: plan.id, bubbles: true }));
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
  private mutate(action: () => Promise<Plan>) {
    return this.act(async () => {
      this.accept(await action());
      this.message = 'Gespeichert.';
    });
  }
  private create(e: Event) {
    e.preventDefault();
    if (this.createStep === 0) {
      this.createStep = 1;
      return;
    }
    const data = new FormData(e.currentTarget as HTMLFormElement);
    const days = data.getAll('weekday').map((day) => ({
      name: String(data.get(`day-${day}`) || weekdays[Number(day)]),
      weekday: Number(day),
    }));
    if (!days.length) {
      this.error = 'Wähle mindestens einen Trainingstag.';
      return;
    }
    void this.act(async () => {
      this.accept(
        await api.createPlan(
          {
            title: String(data.get('title')),
            start_date: String(data.get('start_date')),
            weeks: Number(data.get('weeks')),
            days,
          },
          { transport: this.api },
        ),
      );
      this.creating = false;
      this.createStep = 0;
      this.createDays = new Set([0, 2, 4]);
      this.week = 1;
      this.dayIndex = 0;
    });
  }
  private move(day: TrainingDay, index: number, delta: number) {
    const ids = day.slots.map((s) => s.id);
    const target = index + delta;
    if (target < 0 || target >= ids.length) return;
    [ids[index], ids[target]] = [ids[target], ids[index]];
    void this.mutate(() =>
      api.reorderExerciseSlots(this.plan.id, day.id, { slot_ids: ids }, { transport: this.api }),
    );
  }
  private prescription(e: Event, day: TrainingDay, slot: PlanSlot) {
    const v = formValues(e);
    void this.act(async () => {
      if (Number(v.rest_seconds) !== slot.rest_seconds)
        this.accept(
          await api.editExerciseSlot(
            this.plan.id,
            day.id,
            slot.id,
            { rest_seconds: Number(v.rest_seconds) },
            { transport: this.api },
          ),
        );
      this.accept(
        await api.setWeekPrescription(
          this.plan.id,
          slot.id,
          this.week,
          {
            sets: Number(v.sets),
            reps: Number(v.reps),
            target_effort: String(v.target_effort),
            note: String(v.note),
          },
          { transport: this.api },
        ),
      );
      this.message = 'Vorgabe gespeichert.';
    });
  }
  private errorNotice() {
    return this.error ? html`<div class="notice error" role="alert">${this.error}</div>` : nothing;
  }
  private creationDialog() {
    return html`<dialog
      class="modal create-plan-modal"
      aria-labelledby="plan-title"
      @cancel=${(e: Event) => {
        e.preventDefault();
        this.close();
      }}
    >
      <div class="plan-dialog-heading">
        <h2 id="plan-title">${this.createStep === 0 ? 'Allgemein' : 'Kalender'}</h2>
        <button
          type="button"
          class="bare-icon"
          aria-label="Schließen"
          ?disabled=${this.busy}
          @click=${this.close}
        >
          ${icon('close')}
        </button>
      </div>
      <form class="plan-create-form" @submit=${this.create}>
        <div class="plan-wizard-body">
          ${this.errorNotice()}
          <section aria-label="Allgemein" ?hidden=${this.createStep !== 0}>
            <label
              >Titel<input
                name="title"
                required
                maxlength="200"
                placeholder="Name des Trainingsplans"
                autofocus
            /></label>
            <label
              >Blocklänge (Wochen)<input
                name="weeks"
                type="number"
                min="1"
                max="104"
                value="6"
                required
            /></label>
          </section>
          <section aria-label="Kalender" ?hidden=${this.createStep !== 1}>
            <div class="plan-wizard-info">
              ${icon('info')}
              <p>
                Die ausgewählten Trainingstage bestimmen deine Trainingsfrequenz und werden
                automatisch in deinen Trainingskalender eingetragen.
              </p>
            </div>
            <fieldset class="plan-weekdays">
              <legend>Trainingstage auswählen</legend>
              <div class="weekday-options">
                ${weekdays.map(
                  (day, i) =>
                    html` <label class="weekday-option"
                      ><input
                        type="checkbox"
                        name="weekday"
                        value=${i}
                        aria-label=${day}
                        .checked=${this.createDays.has(i)}
                        @change=${(e: Event) => {
                          const days = new Set(this.createDays);
                          if ((e.target as HTMLInputElement).checked) days.add(i);
                          else days.delete(i);
                          this.createDays = days;
                        }}
                      /><span class="weekday-name">${day.slice(0, 2)}</span
                      ><span class="weekday-cell"
                        ><span class="weekday-number">${i + 1}</span></span
                      ></label
                    >`,
                )}
              </div>
            </fieldset>
            <label
              >Startdatum<input type="date" name="start_date" required .value=${today()}
            /></label>
            <details>
              <summary>Trainingstage benennen</summary>
              <div class="selected-day-names">
                ${weekdays.map((day, i) => html`<label class="training-day-name" ?hidden=${!this.createDays.has(i)}><span>${day}</span><input name=${`day-${i}`} aria-label=${`Name für ${day}`} .value=${day} maxlength="200" ?disabled=${!this.createDays.has(i)} /></label>`)}
              </div>
            </details>
          </section>
        </div>
        <div class="plan-dialog-footer">
          <nav class="plan-wizard-pagination" aria-label="Schritte">
            <button
              type="button"
              aria-current=${this.createStep === 0 ? 'step' : 'false'}
              ?disabled=${this.busy}
              @click=${() => (this.createStep = 0)}
            >
              Allgemein</button
            >${icon('arrow')}<button
              type="button"
              aria-current=${this.createStep === 1 ? 'step' : 'false'}
              ?disabled=${this.busy}
              @click=${() => {
                if (this.querySelector<HTMLFormElement>('.plan-create-form')!.reportValidity())
                  this.createStep = 1;
              }}
            >
              Kalender
            </button>
          </nav>
          <button class="primary" ?disabled=${this.busy}>
            ${this.busy ? 'Wird erstellt …' : this.createStep === 0 ? 'Weiter' : 'Erstellen'}
          </button>
        </div>
      </form>
    </dialog>`;
  }
  private metadata() {
    if (this.creating) return this.creationDialog();
    const plan = this.plan;
    return html`<dialog class="modal wide-modal" aria-labelledby="plan-title" @cancel=${this.close}>
      <div class="panel-heading">
        <h2 id="plan-title">Planeinstellungen</h2>
        <button class="bare-icon" aria-label="Schließen" @click=${this.close}>
          ${icon('close')}
        </button>
      </div>
      ${this.errorNotice()}
      <form
        class="stack"
        @submit=${(e: Event) => {
          const v = formValues(e);
          void this.act(async () => {
            this.accept(
              await api.configurePlan(
                plan.id,
                {
                  title: String(v.title),
                  start_date: String(v.start_date),
                  recommendations: v.recommendations === 'on',
                },
                { transport: this.api },
              ),
            );
            this.editing = false;
            this.message = 'Plan gespeichert.';
          });
        }}
      >
        <label
          >Titel<input name="title" required maxlength="200" .value=${plan.title} autofocus
        /></label>
        <div class="input-grid">
          <label
            >Startdatum<input
              type="date"
              name="start_date"
              required
              .value=${plan.start_date} /></label
          ><label
            >Wochen<input name="weeks" type="number" disabled .value=${String(plan.weeks)}
          /></label>
        </div>
        <label class="check-label"
          ><input
            type="checkbox"
            name="recommendations"
            .checked=${plan.recommendations}
          />Gewichtsempfehlungen aktivieren</label
        >
        <div class="actions modal-actions">
          <button class="secondary" type="button" @click=${this.close}>Abbrechen</button
          ><button class="primary" ?disabled=${this.busy}>Speichern</button>
        </div>
      </form>
      <details>
        <summary>Trainingstage bearbeiten</summary>
        ${plan.days.map(
          (day) =>
            html`<form
              class="edit-day-form"
              @submit=${(e: Event) => {
                const v = formValues(e);
                void this.mutate(() =>
                  api.editTrainingDay(
                    plan.id,
                    day.id,
                    { name: String(v.name), weekday: Number(v.weekday) },
                    { transport: this.api },
                  ),
                );
              }}
            >
              <label>Name<input name="name" required maxlength="200" .value=${day.name} /></label
              ><label
                >Wochentag<select name="weekday">
                  ${weekdays.map((name, i) => html`<option value=${i} ?selected=${day.weekday === i}>${name}</option>`)}
                </select></label
              ><button
                class="bare-icon"
                ?disabled=${this.busy}
                aria-label=${`${day.name} speichern`}
              >
                ${icon('save')}
              </button>
            </form>`,
        )}
      </details>
    </dialog>`;
  }
  private progressionDialog() {
    const plan = this.plan;
    return html`<dialog
      class="modal wide-modal"
      aria-labelledby="progression-title"
      @cancel=${this.close}
    >
      <div class="panel-heading">
        <h2 id="progression-title">Auto-Progression</h2>
        <button class="bare-icon" aria-label="Schließen" @click=${this.close}>
          ${icon('close')}
        </button>
      </div>
      ${this.errorNotice()}
      <p class="muted">
        Erzeuge die Folgewochen aus Woche 1 und prüfe die Vorgaben vor der Übernahme.
      </p>
      <form
        class="progression-form"
        @submit=${(e: Event) => {
          const v = formValues(e);
          this.progression = { increment: String(v.increment), deload: v.deload === 'on' };
          void this.act(async () => {
            this.preview = await api.previewProgression(plan.id, this.progression, {
              transport: this.api,
            });
          });
        }}
      >
        <label
          >RPE-Steigerung<select name="increment">
            <option value="0.5">+0,5 pro Woche</option>
            <option value="1">+1 pro Woche</option>
          </select></label
        ><label class="check-label"
          ><input type="checkbox" name="deload" checked />Letzte Woche als Deload</label
        ><button class="secondary" ?disabled=${this.busy}>Vorschau erstellen</button>
      </form>
      ${
        this.preview
          ? html`<div class="progression-preview">
              ${this.preview.plan.days.map(
                (day) =>
                  html`<h3>${day.name}</h3>
                    ${day.slots.map(
                      (slot) =>
                        html`<p>${slot.exercise_name}</p>
                          <div class="week-chips">
                            ${slot.prescriptions.map((rx) => html`<span>W${rx.week}<strong>${rx.sets} × ${rx.reps}</strong>${this.user.effort_scale.toUpperCase()} ${rx.target_effort}</span>`)}
                          </div>`,
                    )}`,
              )}
              <p class="muted">Ersetzt auch manuell gepflegte Vorgaben der Folgewochen.</p>
              <div class="actions modal-actions">
                <button
                  class="secondary"
                  @click=${() => {
                    this.preview = null;
                  }}
                >
                  Verwerfen</button
                ><button
                  class="primary"
                  ?disabled=${this.busy}
                  @click=${() =>
                    this.act(async () => {
                      this.accept(
                        await api.applyProgression(
                          plan.id,
                          { ...this.progression, expected_revision: this.preview!.base_revision },
                          { transport: this.api },
                        ),
                      );
                      this.preview = null;
                      this.progressing = false;
                      this.message = 'Progression übernommen.';
                    })}
                >
                  Folgewochen ersetzen
                </button>
              </div>
            </div>`
          : nothing
      }
      <details>
        <summary>Woche ${this.week} unverändert in Folgewochen kopieren</summary>
        <p class="muted">Überschreibt die vorhandenen Vorgaben der Folgewochen.</p>
        <button
          class="secondary"
          ?disabled=${this.busy}
          @click=${() => this.mutate(() => api.copyWeekForward(plan.id, this.week, { transport: this.api }))}
        >
          Vorgaben übernehmen
        </button>
      </details>
    </dialog>`;
  }
  render() {
    const plan = this.plan,
      day = plan?.days[this.dayIndex] ?? plan?.days[0];
    return html`<div class="plan-editor-toolbar">
        <div class="actions">
          ${
            plan
              ? html`<select
                    aria-label="Trainingsplan auswählen"
                    .value=${plan.id}
                    @change=${(e: Event) => {
                      this.selected = (e.target as HTMLSelectElement).value;
                      this.dispatchEvent(
                        new CustomEvent('plan-selected', { detail: this.selected, bubbles: true }),
                      );
                    }}
                  >
                    ${this.plans.map((p) => html`<option value=${p.id} ?selected=${p.id === plan.id}>${p.title}</option>`)}</select
                  ><span class="badge">${statuses[plan.status]}</span>`
              : nothing
          }
        </div>
        <button
          class="secondary"
          @click=${() => {
            this.creating = true;
          }}
        >
          ${icon('plus')} Neuer Plan
        </button>
      </div>
      ${!(this.creating || this.editing || this.progressing || this.sharing) ? this.errorNotice() : nothing}${this.message ? html`<div class="notice success" role="status">${this.message}</div>` : nothing}
      ${
        plan && day
          ? html`<div class="plan-editor-actions">
                <div class="actions">
                  <button
                    class="text-button"
                    @click=${() => {
                      this.editing = true;
                    }}
                  >
                    ${icon('settings')} Einstellungen</button
                  ><button
                    class="text-button"
                    @click=${() => {
                      this.progressing = true;
                      this.preview = null;
                    }}
                  >
                    ${icon('activity')} Auto-Progression</button
                  ><button
                    class="text-button"
                    ?disabled=${this.busy}
                    @click=${() => this.mutate(() => api.duplicatePlan(plan.id, { title: `${plan.title} · Kopie`, start_date: today() }, { transport: this.api }))}
                  >
                    ${icon('copy')} Duplizieren</button
                  ><button
                    class="text-button"
                    ?disabled=${this.busy}
                    @click=${() =>
                      this.act(async () => {
                        const share = await api.sharePlanTemplate(plan.id, { transport: this.api });
                        this.shareToken = share.token;
                        this.sharing = true;
                      })}
                  >
                    ${icon('share')} Teilen
                  </button>
                </div>
                <button
                  class="secondary"
                  ?disabled=${this.busy}
                  @click=${() => this.mutate(() => api.setPlanStatus(plan.id, { status: plan.status === 'active' ? 'archived' : 'active' }, { transport: this.api }))}
                >
                  ${plan.status === 'active' ? 'Archivieren' : 'Aktivieren'}
                </button>
              </div>
              <div class="training-context">
                <span>${weekdays[day.weekday]} · ${day.name} · Woche ${this.week}</span
                ><button
                  class="text-button"
                  ?disabled=${this.busy || !day.slots.length || day.slots.some((s) => !s.prescriptions.some((p) => p.week === this.week))}
                  @click=${() => this.dispatchEvent(new CustomEvent('start-training', { detail: { plan_id: plan.id, day_id: day.id, week: this.week }, bubbles: true }))}
                >
                  ${icon('play')} Trainieren
                </button>
              </div>
              <div class="training-pagination overview-pagination">
                <div class="day-pagination" role="group" aria-label="Trainingstag auswählen">
                  ${plan.days.map(
                    (d, i) =>
                      html`<button
                        class=${d.id === day.id ? 'selected' : ''}
                        aria-label=${d.name}
                        aria-pressed=${d.id === day.id}
                        @click=${() => {
                          this.dayIndex = i;
                          this.adding = false;
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
                    ?disabled=${this.week <= 1}
                    @click=${() => {
                      this.week--;
                    }}
                  >
                    ${icon('chevron-left')}</button
                  ><span>W${this.week} / ${plan.weeks}</span
                  ><button
                    class="bare-icon"
                    aria-label="Nächste Woche"
                    ?disabled=${this.week >= plan.weeks}
                    @click=${() => {
                      this.week++;
                    }}
                  >
                    ${icon('chevron-right')}
                  </button>
                </div>
              </div>
              ${keyed(
                `${plan.id}-${day.id}-${this.week}`,
                html`<div class="plan-sheet">
                  <div class="plan-column-headings">
                    <span>Kategorie</span><span>Übung</span><span>Sätze</span><span>Wdh.</span
                    ><span>${this.user.effort_scale.toUpperCase()}</span><span>Pause (s)</span
                    ><span>Notiz</span><span></span>
                  </div>
                  ${day.slots.map((slot, i) => {
                    const rx = slot.prescriptions.find((p) => p.week === this.week);
                    return html`<form
                      class="plan-sheet-row"
                      aria-label=${`Vorgabe für ${slot.exercise_name}`}
                      @submit=${(e: Event) => this.prescription(e, day, slot)}
                    >
                      <div class="sheet-exercise-heading">
                        <span class="row-number">${String(i + 1).padStart(2, '0')}</span>
                        <h2>${slot.exercise_name}</h2>
                        <span>${categories[slot.category]}</span>
                      </div>
                      <div class="plan-field plan-category">
                        <span class="field-label">Kategorie</span
                        ><span>${categories[slot.category]}</span>
                      </div>
                      <div class="plan-field plan-exercise-name">
                        <span class="field-label">Übung</span
                        ><span
                          >${slot.exercise_name}${!rx ? html`<small class="missing-prescription">Vorgabe fehlt</small>` : nothing}</span
                        >
                      </div>
                      <label class="plan-field"
                        ><span class="field-label">Sätze</span
                        ><input
                          name="sets"
                          type="number"
                          inputmode="numeric"
                          min="1"
                          max="100"
                          required
                          .value=${String(rx?.sets ?? 3)} /></label
                      ><label class="plan-field"
                        ><span class="field-label">Wdh.</span
                        ><input
                          name="reps"
                          type="number"
                          inputmode="numeric"
                          min="1"
                          max="100"
                          required
                          .value=${String(rx?.reps ?? 8)}
                      /></label>
                      <label class="plan-field"
                        ><span class="field-label">${this.user.effort_scale.toUpperCase()}</span
                        ><input
                          name="target_effort"
                          type="number"
                          inputmode="decimal"
                          min=${this.user.effort_scale === 'rpe' ? 1 : 0}
                          max=${this.user.effort_scale === 'rpe' ? 10 : 9}
                          step="0.5"
                          required
                          .value=${rx?.target_effort ?? (this.user.effort_scale === 'rpe' ? '8' : '2')}
                      /></label>
                      <label class="plan-field"
                        ><span class="field-label">Pause (s)</span
                        ><input
                          name="rest_seconds"
                          type="number"
                          min="0"
                          max="3600"
                          required
                          .value=${String(slot.rest_seconds)} /></label
                      ><label class="plan-field plan-note"
                        ><span class="field-label">Notiz</span
                        ><input
                          name="note"
                          maxlength="2000"
                          placeholder="–"
                          .value=${rx?.note ?? ''}
                      /></label>
                      <div class="plan-row-actions">
                        <button
                          class="bare-icon"
                          ?disabled=${this.busy}
                          aria-label=${`Vorgabe für ${slot.exercise_name} speichern`}
                        >
                          ${icon('save')}</button
                        ><button
                          type="button"
                          class="bare-icon"
                          ?disabled=${this.busy || i === 0}
                          aria-label=${`${slot.exercise_name} nach oben`}
                          @click=${() => this.move(day, i, -1)}
                        >
                          ${icon('chevron-left')}</button
                        ><button
                          type="button"
                          class="bare-icon"
                          ?disabled=${this.busy || i === day.slots.length - 1}
                          aria-label=${`${slot.exercise_name} nach unten`}
                          @click=${() => this.move(day, i, 1)}
                        >
                          ${icon('chevron-right')}</button
                        ><button
                          type="button"
                          class="bare-icon"
                          ?disabled=${this.busy}
                          aria-label=${`${slot.exercise_name} entfernen`}
                          @click=${() => this.mutate(() => api.removeExerciseSlot(plan.id, day.id, slot.id, { transport: this.api }))}
                        >
                          ${icon('close')}
                        </button>
                      </div>
                    </form>`;
                  })}
                </div>`,
              )}
              <button
                class="add-row"
                aria-label="Übung hinzufügen"
                @click=${() => {
                  this.adding = !this.adding;
                }}
              >
                ${icon(this.adding ? 'close' : 'plus')}
              </button>
              ${
                this.adding
                  ? html`<form
                      class="add-slot-form"
                      @submit=${(e: Event) => {
                        const v = formValues(e);
                        void this.act(async () => {
                          this.accept(
                            await api.addExerciseSlot(
                              plan.id,
                              day.id,
                              {
                                exercise_id: String(v.exercise_id),
                                rest_seconds: v.rest_seconds === '' ? null : Number(v.rest_seconds),
                              },
                              { transport: this.api },
                            ),
                          );
                          this.adding = false;
                        });
                      }}
                    >
                      <label
                        >Übung<select name="exercise_id" required>
                          <option value="">Übung wählen …</option>
                          ${this.exercises.filter((e) => !e.archived).map((e) => html`<option value=${e.id}>${e.name}</option>`)}
                        </select></label
                      ><label
                        >Pause (s)<input
                          type="number"
                          name="rest_seconds"
                          min="0"
                          max="3600"
                          placeholder="Kategorie-Standard" /></label
                      ><button class="secondary" ?disabled=${this.busy}>
                        ${icon('plus')} Hinzufügen
                      </button>
                    </form>`
                  : nothing
              } `
          : empty(
              'Dein erster Trainingsplan',
              'Lege einen Plan mit Trainingstagen und Wochenvorgaben an.',
            )
      }
      ${this.creating || this.editing ? this.metadata() : this.progressing ? this.progressionDialog() : nothing}
      ${
        this.sharing
          ? html`<dialog class="modal" aria-labelledby="share-title" @cancel=${this.close}>
              <div class="panel-heading">
                <h2 id="share-title">Plan als Vorlage teilen</h2>
                <button class="bare-icon" aria-label="Schließen" @click=${this.close}>
                  ${icon('close')}
                </button>
              </div>
              ${this.errorNotice()}
              <p>Die Vorlage enthält deinen Plan und keine erfassten Trainings.</p>
              <label>Vorlagen-Token<input readonly .value=${this.shareToken} /></label>
              <p class="muted">Der Token kann über „Vorlage importieren“ übernommen werden.</p>
              <div class="actions modal-actions">
                <button
                  class="secondary"
                  ?disabled=${this.busy}
                  @click=${() =>
                    this.act(async () => {
                      await api.revokePlanTemplate(this.shareToken, { transport: this.api });
                      this.sharing = false;
                      this.shareToken = '';
                      this.message = 'Freigabe widerrufen.';
                    })}
                >
                  Freigabe widerrufen</button
                ><button class="primary" @click=${this.close}>Fertig</button>
              </div>
            </dialog>`
          : nothing
      }
      <details class="template-import">
        <summary>Vorlage importieren</summary>
        <form
          class="stack"
          @submit=${(e: Event) => {
            const v = formValues(e);
            void this.act(async () => {
              this.accept(
                await api.importPlanTemplate(
                  String(v.token),
                  { title: String(v.title), start_date: String(v.start_date) },
                  { transport: this.api },
                ),
              );
              this.message = 'Vorlage importiert.';
            });
          }}
        >
          <label>Vorlagen-Token<input name="token" required /></label>
          <div class="input-grid">
            <label>Titel<input name="title" required maxlength="200" /></label
            ><label
              >Startdatum<input name="start_date" type="date" required .value=${today()}
            /></label>
          </div>
          <button class="secondary" ?disabled=${this.busy}>Vorlage importieren</button>
        </form>
      </details>`;
  }
}
customElements.define('plans-view', PlansView);
