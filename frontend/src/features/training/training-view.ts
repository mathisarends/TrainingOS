import { trainingSessions } from '../../api/generated';
import { LitElement, html, nothing } from 'lit';
import { repeat } from 'lit/directives/repeat.js';
import { live } from 'lit/directives/live.js';
import type {
  Guidance,
  SetFeedback,
  TrainingSession,
  TrainingSlot,
  Transport,
  WorkSet,
} from '../../shared/types';
import { categories, dateLabel, formatNumber, formValues, icon } from '../../shared/ui';

interface SetDraft {
  weight: string;
  reps: string;
  effort: string;
  editing: WorkSet | null;
}

export class TrainingView extends LitElement {
  static properties = {
    api: { attribute: false },
    session: { attribute: false },
    busy: { state: true },
    error: { state: true },
    confirmFinish: { state: true },
    feedback: { state: true },
    guidance: { state: true },
    drafts: { state: true },
    deleteSet: { state: true },
  };
  api!: Transport;
  session!: TrainingSession;
  private busy = false;
  private error = '';
  private confirmFinish = false;
  private feedback: Record<string, string> = {};
  private guidance: Record<string, Guidance> = {};
  private drafts: Record<string, SetDraft> = {};
  private generation = 0;
  private deleteSet: { slot: TrainingSlot; set: WorkSet } | null = null;
  createRenderRoot() {
    return this;
  }
  disconnectedCallback() {
    super.disconnectedCallback();
    this.generation++;
  }
  protected willUpdate(changes: Map<string, unknown>) {
    if (
      changes.has('session') &&
      this.session &&
      (changes.get('session') as TrainingSession | undefined)?.id !== this.session.id
    ) {
      this.drafts = {};
      this.feedback = {};
      this.guidance = {};
      const version = ++this.generation;
      for (const slot of this.session.slots) {
        this.drafts[slot.id] = {
          weight: '',
          reps: String(slot.prescription.reps),
          effort: slot.prescription.target_effort,
          editing: null,
        };
        void this.loadGuidance(slot, version);
      }
    }
  }
  protected updated() {
    const dialog = this.querySelector<HTMLDialogElement>('dialog');
    if ((this.confirmFinish || this.deleteSet) && dialog && !dialog.open) dialog.showModal();
  }
  private async loadGuidance(slot: TrainingSlot, version: number) {
    try {
      const result = await trainingSessions.getSlotGuidance(this.session.id, slot.id, {
        transport: this.api,
      });
      if (version !== this.generation) return;
      this.guidance = { ...this.guidance, [slot.id]: result };
      const draft = this.drafts[slot.id];
      if (draft && !draft.weight)
        this.drafts = {
          ...this.drafts,
          [slot.id]: { ...draft, weight: result.backoff_weight ?? result.recommended_weight ?? '' },
        };
    } catch (e) {
      if (version === this.generation) this.error = (e as Error).message;
    }
  }
  private accept(session: TrainingSession) {
    this.session = session;
    this.dispatchEvent(new CustomEvent('session-changed', { detail: session, bubbles: true }));
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
  private async refresh() {
    if (!this.session || this.busy) return;
    await this.act(async () =>
      this.accept(
        await trainingSessions.getTrainingSession(this.session.id, { transport: this.api }),
      ),
    );
  }
  private draftInput(slot: TrainingSlot, field: 'weight' | 'reps' | 'effort', event: Event) {
    this.drafts = {
      ...this.drafts,
      [slot.id]: { ...this.drafts[slot.id], [field]: (event.target as HTMLInputElement).value },
    };
  }
  private save(event: Event, slot: TrainingSlot) {
    const values = formValues(event);
    this.dispatchEvent(new CustomEvent('training-interaction', { bubbles: true }));
    void this.act(async () => {
      const draft = this.drafts[slot.id];
      const request = {
        weight: String(values.weight),
        reps: Number(values.reps),
        effort: String(values.effort),
      };
      const feedback = draft.editing
        ? await trainingSessions.correctWorkSet(
            this.session.id,
            slot.id,
            draft.editing.id,
            request,
            { transport: this.api },
          )
        : await trainingSessions.recordWorkSet(this.session.id, slot.id, request, {
            transport: this.api,
          });
      this.accept(feedback.training_session);
      this.drafts = {
        ...this.drafts,
        [slot.id]: { ...draft, editing: null, weight: feedback.backoff_weight },
      };
      this.feedback = {
        ...this.feedback,
        [slot.id]: `${feedback.new_personal_record ? 'Neue Bestleistung! ' : 'Satz gespeichert. '}e1RM ${formatNumber(feedback.work_set.e1rm)} ${this.session.unit} · Backoff ${formatNumber(feedback.backoff_weight)} ${this.session.unit}`,
      };
    });
  }
  private edit(slot: TrainingSlot, set: WorkSet) {
    this.drafts = {
      ...this.drafts,
      [slot.id]: { weight: set.weight, reps: String(set.reps), effort: set.effort, editing: set },
    };
    this.updateComplete.then(() =>
      this.querySelector<HTMLInputElement>(`[id="weight-${slot.id}"]`)?.focus(),
    );
  }
  private cancelEdit(slot: TrainingSlot) {
    this.drafts = {
      ...this.drafts,
      [slot.id]: {
        weight: this.guidance[slot.id]?.backoff_weight ?? '',
        reps: String(slot.prescription.reps),
        effort: slot.prescription.target_effort,
        editing: null,
      },
    };
  }
  private exercise(slot: TrainingSlot, index: number) {
    const session = this.session;
    const draft = this.drafts[slot.id];
    if (!draft) return nothing;
    const editable = (!session.ended_at && !slot.skipped) || draft.editing;
    const best = slot.sets.length ? Math.max(...slot.sets.map((s) => Number(s.e1rm))) : null;
    const last = this.guidance[slot.id]?.last_sets;
    return html`<section
      class="training-sheet-exercise ${slot.skipped ? 'is-skipped' : ''}"
      aria-label=${slot.exercise_name}
    >
      <div class="sheet-exercise-heading">
        <span class="row-number">${String(index + 1).padStart(2, '0')}</span>
        <h2>${slot.exercise_name}</h2>
        <span>${categories[slot.category]}</span>
      </div>
      <form
        class="training-sheet-form"
        aria-label=${`Satz für ${slot.exercise_name}`}
        @submit=${(e: Event) => this.save(e, slot)}
      >
        <div class="sheet-field sheet-category">
          <span class="field-label">Kategorie</span><span>${categories[slot.category]}</span>
        </div>
        <div class="sheet-field sheet-name">
          <span class="field-label">Übung</span
          ><strong
            ><span class="row-number">${String(index + 1).padStart(2, '0')}</span
            >${slot.exercise_name}</strong
          >
        </div>
        <div class="sheet-field">
          <span class="field-label">Sätze</span
          ><span class="sets-value"
            >${slot.sets.length}
            <span>/ ${slot.prescription.sets}</span
            >${slot.sets.length >= slot.prescription.sets ? icon('check') : nothing}</span
          >
        </div>
        <label class="sheet-field"
          ><span class="field-label">Wdh.</span
          >${editable ? html`<input name="reps" type="number" inputmode="numeric" min="1" max="100" required .value=${live(draft.reps)} @input=${(e: Event) => this.draftInput(slot, 'reps', e)} />` : html`<span>${slot.prescription.reps}</span>`}</label
        >
        <label class="sheet-field"
          ><span class="field-label">Gewicht (${session.unit})</span
          >${editable ? html`<input id=${`weight-${slot.id}`} name="weight" type="number" inputmode="decimal" min="0" max="10000" step="0.0001" placeholder="–" required .value=${live(draft.weight)} @input=${(e: Event) => this.draftInput(slot, 'weight', e)} />` : html`<span>${slot.sets.length ? formatNumber(slot.sets.at(-1)!.weight) : '–'}</span>`}</label
        >
        <div class="sheet-field">
          <span class="field-label">${session.effort_scale.toUpperCase()}</span
          ><span>${formatNumber(slot.prescription.target_effort)}</span>
        </div>
        <label class="sheet-field"
          ><span class="field-label">@${session.effort_scale.toUpperCase()}</span
          >${editable ? html`<input name="effort" type="number" inputmode="decimal" min=${session.effort_scale === 'rpe' ? 1 : 0} max=${session.effort_scale === 'rpe' ? 10 : 9} step="0.5" required .value=${live(draft.effort)} @input=${(e: Event) => this.draftInput(slot, 'effort', e)} />` : html`<span>${slot.sets.length ? formatNumber(slot.sets.at(-1)!.effort) : '–'}</span>`}</label
        >
        <div class="sheet-field">
          <span class="field-label">e1RM (${session.unit})</span
          ><span>${best === null ? '–' : formatNumber(best)}</span>
        </div>
        <div class="sheet-field sheet-note">
          <span class="field-label">Notiz</span><span>${slot.prescription.note || '–'}</span>
          ${editable ? html`<button class="bare-icon desktop-set-save" ?disabled=${this.busy} aria-label=${`Satz für ${slot.exercise_name} speichern`}>${icon('save')}</button>` : nothing}
        </div>
        <div class="sheet-exercise-footer">
          <div class="previous-performance">
            ${icon('history')}<span
              >${last?.length ? `Zuletzt: ${last.map((s) => `${formatNumber(s.weight)} × ${s.reps} @ ${formatNumber(s.effort)}`).join(' · ')}` : 'Noch keine passende Vorleistung'}<span
                class="rest-label"
              >
                · Pause ${formatNumber(slot.rest_seconds / 60)} min</span
              ></span
            >
          </div>
          <div class="sheet-actions">
            ${draft.editing ? html`<button type="button" class="text-button" @click=${() => this.cancelEdit(slot)}>Abbrechen</button>` : !session.ended_at ? html`<button type="button" class="text-button" ?disabled=${this.busy || slot.sets.length > 0} @click=${() => this.act(async () => this.accept(await trainingSessions.skipTrainingSessionSlot(session.id, slot.id, { skipped: !slot.skipped }, { transport: this.api })))}>${slot.skipped ? 'Wieder aufnehmen' : 'Überspringen'}</button>` : nothing}
            ${editable ? html`<button class="primary" ?disabled=${this.busy}>${icon('check')}${this.busy ? 'Wird gespeichert …' : draft.editing ? 'Korrektur speichern' : 'Satz speichern'}</button>` : html`<span class="badge">${slot.skipped ? 'Übersprungen' : `${slot.sets.length} Sätze erfasst`}</span>`}
          </div>
        </div>
      </form>
      ${
        slot.sets.length
          ? html`<details class="recorded-sets">
              <summary>
                ${`${slot.sets.length} ${slot.sets.length === 1 ? 'gespeicherter Satz' : 'gespeicherte Sätze'}`}<span
                  >${slot.sets.map((s) => `${formatNumber(s.weight)} × ${s.reps}`).join(' / ')}</span
                >
              </summary>
              <div>
                ${repeat(
                  slot.sets,
                  (s) => s.id,
                  (s, i) =>
                    html`<div class="recorded-set">
                      <span>Satz ${i + 1}</span
                      ><strong>${formatNumber(s.weight)} ${session.unit} × ${s.reps}</strong
                      ><span>@ ${formatNumber(s.effort)}</span
                      ><span>e1RM ${formatNumber(s.e1rm)}</span
                      ><button
                        class="text-button"
                        aria-label=${`Satz ${i + 1} korrigieren`}
                        ?disabled=${this.busy}
                        @click=${() => this.edit(slot, s)}
                      >
                        Ändern
                      </button>
                      <button
                        class="bare-icon"
                        aria-label=${`Satz ${i + 1} löschen`}
                        ?disabled=${this.busy}
                        @click=${() => {
                          this.deleteSet = { slot, set: s };
                        }}
                      >
                        ${icon('trash')}
                      </button>
                    </div>`,
                )}
              </div>
            </details>`
          : nothing
      }
      ${this.feedback[slot.id] ? html`<p class="notice success sheet-feedback" role="status">${this.feedback[slot.id]}</p>` : nothing}
    </section>`;
  }
  render() {
    if (!this.session) return nothing;
    const session = this.session;
    const done = session.slots.reduce((n, s) => n + s.sets.length, 0);
    const target = session.slots.reduce((n, s) => n + s.prescription.sets, 0);
    return html`<div class="page-heading training-page-heading">
        <div>
          <div class="eyebrow">${session.plan_title} · WOCHE ${session.week}</div>
          <h1>${session.day_name}</h1>
          <p>
            ${dateLabel(session.started_at)} · ${done} / ${target} Sätze
            erfasst${session.ended_at ? ` · ${Math.round((session.duration_seconds || 0) / 60)} Minuten` : ''}
          </p>
        </div>
        ${!session.ended_at ? html`<button class="secondary" ?disabled=${this.busy} @click=${() => (this.confirmFinish = true)}>${icon('check')} Training beenden</button>` : html`<span class="badge accent">Abgeschlossen</span>`}
      </div>
      ${this.error ? html`<div class="notice error" role="alert">${this.error}<button class="text-button" @click=${this.refresh} ?disabled=${this.busy}>Stand neu laden</button></div>` : nothing}
      <div class="training-sheet">
        <div class="sheet-column-headings" aria-hidden="true">
          <span>Kategorie</span><span>Übung</span><span>Sätze</span><span>Wdh.</span
          ><span>Gewicht (${session.unit})</span><span>${session.effort_scale.toUpperCase()}</span
          ><span>@${session.effort_scale.toUpperCase()}</span><span>e1RM</span><span>Notiz</span>
        </div>
        ${repeat(
          session.slots,
          (s) => s.id,
          (slot, i) => this.exercise(slot, i),
        )}
      </div>
      <p class="training-save-note">
        ${icon('check')} Ein Satz wird erst mit „Satz speichern“ als Leistung erfasst.
      </p>
      ${
        session.ended_at
          ? html`<details class="session-times">
              <summary>Trainingszeiten korrigieren</summary>
              <form
                class="stack"
                @submit=${(e: Event) => {
                  const values = formValues(e);
                  void this.act(async () => {
                    const started_at = new Date(String(values.started_at)).toISOString();
                    const ended_at = new Date(String(values.ended_at)).toISOString();
                    this.accept(
                      await trainingSessions.correctTrainingSessionTimes(
                        session.id,
                        { started_at, ended_at },
                        { transport: this.api },
                      ),
                    );
                  });
                }}
              >
                <div class="input-grid">
                  <label
                    >Beginn<input
                      type="datetime-local"
                      name="started_at"
                      required
                      .value=${this.localTime(session.started_at)} /></label
                  ><label
                    >Ende<input
                      type="datetime-local"
                      name="ended_at"
                      required
                      .value=${this.localTime(session.ended_at)}
                  /></label>
                </div>
                <button class="secondary" ?disabled=${this.busy}>Zeiten speichern</button>
              </form>
            </details>`
          : nothing
      }
      ${
        this.deleteSet
          ? html`<dialog
              class="modal"
              aria-labelledby="delete-set-title"
              @cancel=${() => {
                this.deleteSet = null;
              }}
            >
              <h2 id="delete-set-title">Satz löschen?</h2>
              <p>
                ${this.deleteSet.slot.exercise_name}: ${formatNumber(this.deleteSet.set.weight)}
                ${session.unit} × ${this.deleteSet.set.reps}. Die Bestleistungen werden neu
                ausgewertet.
              </p>
              <div class="actions">
                <button
                  class="secondary"
                  autofocus
                  @click=${() => {
                    this.deleteSet = null;
                  }}
                >
                  Abbrechen</button
                ><button
                  class="primary"
                  ?disabled=${this.busy}
                  @click=${() =>
                    this.act(async () => {
                      const entry = this.deleteSet!;
                      this.accept(
                        await trainingSessions.deleteWorkSet(
                          session.id,
                          entry.slot.id,
                          entry.set.id,
                          { transport: this.api },
                        ),
                      );
                      if (this.drafts[entry.slot.id]?.editing?.id === entry.set.id)
                        this.cancelEdit(entry.slot);
                      this.deleteSet = null;
                    })}
                >
                  Satz löschen
                </button>
              </div>
            </dialog>`
          : nothing
      }
      ${
        this.confirmFinish
          ? html`<dialog
              class="modal"
              aria-labelledby="finish-title"
              @cancel=${() => (this.confirmFinish = false)}
            >
              <h2 id="finish-title">Training abschließen?</h2>
              <p>${done} Sätze erfasst. Du kannst die Werte später im Verlauf korrigieren.</p>
              <div class="actions">
                <button class="secondary" autofocus @click=${() => (this.confirmFinish = false)}>
                  Weitertrainieren</button
                ><button
                  class="primary"
                  ?disabled=${this.busy}
                  @click=${() =>
                    this.act(async () => {
                      this.accept(
                        await trainingSessions.finishTrainingSession(session.id, {
                          transport: this.api,
                        }),
                      );
                      this.confirmFinish = false;
                    })}
                >
                  Training abschließen
                </button>
              </div>
            </dialog>`
          : nothing
      }`;
  }
  private localTime(value: string) {
    const date = new Date(value);
    return new Date(date.getTime() - date.getTimezoneOffset() * 60_000).toISOString().slice(0, 16);
  }
}
customElements.define('training-view', TrainingView);
