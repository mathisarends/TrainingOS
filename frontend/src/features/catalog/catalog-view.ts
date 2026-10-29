import { LitElement, html, nothing } from 'lit';
import { repeat } from 'lit/directives/repeat.js';
import { live } from 'lit/directives/live.js';
import { exercises } from '../../api/generated';
import type { Category, CategoryDefaults, Exercise, Transport, User } from '../../shared/types';
import { categories, empty, formValues, icon } from '../../shared/ui';

type SaveState = { pending?: boolean; error?: string; saved?: boolean };
export class CatalogView extends LitElement {
  static properties = {
    api: { attribute: false },
    user: { attribute: false },
    exercises: { attribute: false },
    search: { state: true },
    category: { state: true },
    searching: { state: true },
    editing: { state: true },
    adding: { state: true },
    busy: { state: true },
    error: { state: true },
    defaults: { state: true },
    defaultsError: { state: true },
    loadingDefaults: { state: true },
  };
  api!: Transport;
  user?: User;
  exercises: Exercise[] = [];
  private search = '';
  private category = '';
  private searching = false;
  private editing: Exercise | null = null;
  private adding = false;
  private busy = false;
  private error = '';
  private defaults: CategoryDefaults[] = [];
  private defaultsError = '';
  private loadingDefaults = true;
  private names = new Map<string, string>();
  private nameStates = new Map<string, SaveState>();
  private defaultStates = new Map<Category, SaveState>();
  createRenderRoot() {
    return this;
  }
  connectedCallback() {
    super.connectedCallback();
    void this.loadDefaults();
  }
  private async loadDefaults() {
    this.loadingDefaults = true;
    this.defaultsError = '';
    try {
      this.defaults = (await exercises.listCategoryDefaults({ transport: this.api })).items;
    } catch (e) {
      this.defaultsError = (e as Error).message;
    } finally {
      this.loadingDefaults = false;
    }
  }
  protected updated() {
    const dialog = this.querySelector<HTMLDialogElement>('dialog');
    if (dialog && !dialog.open) dialog.showModal();
  }
  private close() {
    if (!this.busy) {
      this.adding = false;
      this.editing = null;
      this.error = '';
    }
  }
  private async rename(exercise: Exercise) {
    const name = this.names.get(exercise.id)?.trim();
    if (this.nameStates.get(exercise.id)?.pending || name === undefined || name === exercise.name)
      return;
    if (!name) {
      this.nameStates.set(exercise.id, { error: 'Der Name darf nicht leer sein.' });
      this.requestUpdate();
      return;
    }
    this.nameStates.set(exercise.id, { pending: true });
    this.requestUpdate();
    try {
      const updated = await exercises.reviseExercise(
        exercise.id,
        { name, category: exercise.category, main: exercise.main },
        { transport: this.api },
      );
      this.exercises = this.exercises.map((e) => (e.id === exercise.id ? updated : e));
      this.names.delete(exercise.id);
      this.nameStates.set(exercise.id, { saved: true });
      this.dispatchEvent(new CustomEvent('catalog-changed', { bubbles: true }));
    } catch (e) {
      this.nameStates.set(exercise.id, { error: (e as Error).message });
    } finally {
      this.requestUpdate();
    }
  }
  private async saveDefaults(value: CategoryDefaults) {
    const category = value.category;
    if (this.defaultStates.get(category)?.pending) return;
    this.defaultStates.set(category, { pending: true });
    this.requestUpdate();
    try {
      const saved = await exercises.configureCategoryDefaults(
        category,
        {
          rest_seconds: value.rest_seconds,
          sets: value.sets,
          reps: value.reps,
          target_effort: value.target_effort,
        },
        { transport: this.api },
      );
      this.defaults = this.defaults.map((d) => (d.category === category ? saved : d));
      this.defaultStates.set(category, { saved: true });
    } catch (e) {
      this.defaultStates.set(category, { error: (e as Error).message });
    } finally {
      this.requestUpdate();
    }
  }
  private defaultRows(category: Category) {
    const value = this.defaults.find((d) => d.category === category);
    if (!value) return nothing;
    const state = this.defaultStates.get(category);
    const scale = this.user?.effort_scale === 'rir' ? 'RIR' : 'RPE';
    const rows = [
      {
        key: 'rest_seconds' as const,
        label: 'Pause',
        options: Array.from(
          new Set([value.rest_seconds, ...Array.from({ length: 9 }, (_, i) => 60 + i * 30)]),
        ).sort((a, b) => a - b),
        text: (n: number) =>
          n === 0 ? 'Keine Pause' : `${n / 60} ${n === 60 ? 'Minute' : 'Minuten'}`,
      },
      {
        key: 'sets' as const,
        label: 'Sätze',
        options: Array.from(
          new Set([value.sets, ...Array.from({ length: 8 }, (_, i) => i + 1)]),
        ).sort((a, b) => a - b),
        text: (n: number) => `${n} ${n === 1 ? 'Satz' : 'Sätze'}`,
      },
      {
        key: 'reps' as const,
        label: 'Wiederholungen',
        options: Array.from(
          new Set([value.reps, ...Array.from({ length: 13 }, (_, i) => i + 3)]),
        ).sort((a, b) => a - b),
        text: (n: number) => `${n} Wdh.`,
      },
      {
        key: 'target_effort' as const,
        label: scale,
        options: Array.from(
          new Set([
            Number(value.target_effort),
            ...Array.from({ length: 9 }, (_, i) => (scale === 'RIR' ? i / 2 : 6 + i / 2)),
          ]),
        ).sort((a, b) => a - b),
        text: (n: number) => `${scale} ${n}`,
      },
    ];
    return html`${rows.map(
      (row, i) =>
        html`<tr class=${i === 0 ? 'catalog-default-first' : ''}>
          <td>
            <label class="catalog-default-control"
              ><select
                aria-label=${`${categories[category]} ${row.label}`}
                ?disabled=${state?.pending}
                @change=${(e: Event) => {
                  const raw = (e.target as HTMLSelectElement).value;
                  const next = {
                    ...value,
                    [row.key]: row.key === 'target_effort' ? raw : Number(raw),
                  };
                  this.defaults = this.defaults.map((d) => (d.category === category ? next : d));
                  void this.saveDefaults(next);
                }}
              >
                ${row.options.map((n) => html`<option value=${n} ?selected=${Number(value[row.key]) === n}>${row.text(n)}</option>`)}
              </select></label
            >
          </td>
        </tr>`,
    )}
    ${
      state
        ? html`<tr>
            <td>
              <div class="catalog-status" role=${state.error ? 'alert' : 'status'}>
                ${state.pending ? 'Wird gespeichert …' : state.error ? `Nicht gespeichert: ${state.error}` : 'Gespeichert'}${state.error ? html`<button class="text-button" @click=${() => void this.saveDefaults(value)}>Erneut speichern</button>` : nothing}
              </div>
            </td>
          </tr>`
        : nothing
    }`;
  }
  private async archiveExercise() {
    if (!this.editing || this.busy) return;
    this.busy = true;
    this.error = '';
    try {
      await exercises.removeExercise(this.editing.id, { transport: this.api });
      this.exercises = this.exercises.map((e) =>
        e.id === this.editing!.id ? { ...e, archived: true } : e,
      );
      this.close();
      this.dispatchEvent(new CustomEvent('catalog-changed', { bubbles: true }));
    } catch (e) {
      this.error = (e as Error).message;
    } finally {
      this.busy = false;
    }
  }
  private async save(e: Event) {
    const v = formValues(e);
    if (this.busy) return;
    this.busy = true;
    this.error = '';
    try {
      const request = {
        name: String(v.name),
        category: v.category as Category,
        main: v.main === 'on',
      };
      const saved = this.editing
        ? await exercises.reviseExercise(this.editing.id, request, { transport: this.api })
        : await exercises.createExercise(request, { transport: this.api });
      this.exercises = this.exercises.some((e) => e.id === saved.id)
        ? this.exercises.map((e) => (e.id === saved.id ? saved : e))
        : [...this.exercises, saved];
      this.names.delete(saved.id);
      this.adding = false;
      this.editing = null;
      this.dispatchEvent(new CustomEvent('catalog-changed', { bubbles: true }));
    } catch (e) {
      this.error = (e as Error).message;
    } finally {
      this.busy = false;
    }
  }
  render() {
    const items = this.exercises.filter(
      (e) =>
        !e.archived &&
        e.name.toLocaleLowerCase('de').includes(this.search.toLocaleLowerCase('de')) &&
        (!this.category || e.category === this.category),
    );
    return html`<div class="catalog-tools">
        <span>${items.length} Übungen</span
        ><button
          class="bare-icon"
          aria-label="Suche und Filter"
          aria-expanded=${this.searching}
          @click=${() => {
            this.searching = !this.searching;
            if (!this.searching) {
              this.search = '';
              this.category = '';
            }
          }}
        >
          ${icon('search')}</button
        ><button
          class="bare-icon"
          aria-label="Eigene Übung"
          @click=${() => {
            this.adding = true;
            this.editing = null;
            this.error = '';
          }}
        >
          ${icon('plus')}
        </button>
      </div>
      ${this.error && !this.adding && !this.editing ? html`<div class="notice error" role="alert">${this.error}</div>` : nothing}
      ${
        this.adding || this.editing
          ? html`<dialog class="modal" aria-labelledby="exercise-title" @cancel=${this.close}>
              <div class="panel-heading">
                <h2 id="exercise-title">
                  ${this.editing ? 'Übung bearbeiten' : 'Eigene Übung anlegen'}
                </h2>
                <button class="bare-icon" aria-label="Schließen" @click=${this.close}>
                  ${icon('close')}
                </button>
              </div>
              ${this.error ? html`<div class="notice error" role="alert">${this.error}</div>` : nothing}
              <form @submit=${this.save}>
                <div class="input-grid">
                  <label
                    >Name<input
                      name="name"
                      required
                      maxlength="200"
                      .value=${this.editing?.name ?? ''} /></label
                  ><label
                    >Kategorie<select name="category">
                      ${Object.entries(categories).map(([value, label]) => html`<option value=${value} ?selected=${this.editing?.category === value}>${label}</option>`)}
                    </select></label
                  >
                </div>
                <label class="check-label"
                  ><input name="main" type="checkbox" .checked=${this.editing?.main ?? false} />
                  Hauptübung</label
                >
                <div class="actions">
                  <button
                    class="secondary"
                    type="button"
                    @click=${() => {
                      this.adding = false;
                      this.editing = null;
                    }}
                  >
                    Abbrechen</button
                  ><button class="primary" ?disabled=${this.busy}>Speichern</button>
                </div>
              </form>
              ${
                this.editing
                  ? html`<details>
                      <summary>Übung entfernen</summary>
                      <p class="muted">
                        Übungen mit erfasster Historie werden archiviert. Gespeicherte Trainings
                        bleiben erhalten.
                      </p>
                      <button
                        class="text-button danger-text"
                        ?disabled=${this.busy}
                        @click=${this.archiveExercise}
                      >
                        ${icon('trash')} Übung entfernen
                      </button>
                    </details>`
                  : nothing
              }
            </dialog>`
          : nothing
      }
      ${
        this.searching
          ? html`<div class="catalog-filters">
              <label class="search-input"
                >${icon('search')}<input
                  aria-label="Übung suchen"
                  placeholder="Übung suchen …"
                  .value=${this.search}
                  @input=${(e: Event) => (this.search = (e.target as HTMLInputElement).value)} /></label
              ><select
                aria-label="Kategorie filtern"
                .value=${this.category}
                @change=${(e: Event) => (this.category = (e.target as HTMLSelectElement).value)}
              >
                <option value="">Alle Kategorien</option>
                ${Object.entries(categories).map(([value, label]) => html`<option value=${value}>${label}</option>`)}
              </select>
            </div>`
          : nothing
      }
      ${this.loadingDefaults ? html`<p class="muted" role="status">Standardwerte werden geladen …</p>` : nothing}
      ${this.defaultsError ? html`<div class="notice error" role="alert">Standardwerte konnten nicht geladen werden: ${this.defaultsError} <button class="text-button" @click=${this.loadDefaults}>Erneut laden</button></div>` : nothing}
      <div class="catalog-grid">
        ${Object.entries(categories)
          .filter(
            ([category]) =>
              (!this.category || this.category === category) &&
              (!this.search || items.some((e) => e.category === category)),
          )
          .map(
            ([category, label]) =>
              html`<section class="catalog-category" aria-label=${label}>
                <table class="catalog-table">
                  <thead>
                    <tr>
                      <th scope="col">${label}</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${repeat(
                      items.filter((e) => e.category === category),
                      (e) => e.id,
                      (e) => {
                        const state = this.nameStates.get(e.id);
                        return html`<tr>
                          <td>
                            <div class="catalog-name-cell">
                              <input
                                aria-label=${`${e.name} Name`}
                                maxlength="200"
                                required
                                .value=${live(this.names.get(e.id) ?? e.name)}
                                ?disabled=${state?.pending}
                                @input=${(event: Event) => {
                                  this.names.set(e.id, (event.target as HTMLInputElement).value);
                                  this.nameStates.delete(e.id);
                                  this.requestUpdate();
                                }}
                                @change=${() => void this.rename(e)}
                                @blur=${() => void this.rename(e)}
                                @keydown=${(event: KeyboardEvent) => {
                                  if (event.key === 'Enter') {
                                    event.preventDefault();
                                    void this.rename(e);
                                  }
                                }}
                              />${e.main ? html`<span class="small-dot" title="Hauptübung"></span>` : nothing}<button
                                class="bare-icon catalog-row-menu"
                                ?disabled=${state?.pending}
                                aria-label=${`${e.name} Einstellungen`}
                                @click=${() => {
                                  this.editing = e;
                                  this.error = '';
                                }}
                              >
                                ${icon('more')}
                              </button>
                            </div>
                            ${state ? html`<div class="catalog-status" role=${state.error ? 'alert' : 'status'}>${state.pending ? 'Wird gespeichert …' : state.error ? `Nicht gespeichert: ${state.error}` : 'Gespeichert'}${state.error ? html`<button class="text-button" @click=${() => void this.rename(e)}>Erneut speichern</button>` : nothing}</div>` : nothing}
                          </td>
                        </tr>`;
                      },
                    )}${this.defaultRows(category as Category)}
                  </tbody>
                </table>
              </section>`,
          )}
      </div>
      ${!items.length ? empty('Keine Übung gefunden', 'Passe deinen Filter an oder lege eine eigene Übung an.') : nothing}`;
  }
}
customElements.define('catalog-view', CatalogView);
