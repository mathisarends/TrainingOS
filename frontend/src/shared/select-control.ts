import { LitElement, css, html, nothing } from 'lit';

let nextId = 0;

/** Keeps the native form contract while presenting one consistent, keyboardable menu. */
export class SelectControl extends LitElement {
  static properties = {
    opened: { state: true },
    active: { state: true },
    invalidSelection: { state: true },
  };
  private invalidSelection = false;
  private opened = false;
  private active = 0;
  private source?: HTMLSelectElement;
  private observer?: MutationObserver;
  private readonly menuId = `select-menu-${++nextId}`;
  private search = '';
  private searchAt = 0;
  private readonly refresh = () => {
    if (this.source?.validity.valid) this.invalidSelection = false;
    this.requestUpdate();
  };
  private readonly invalid = (event: Event) => {
    event.preventDefault();
    this.invalidSelection = true;
    this.button?.focus();
  };
  private readonly reposition = (event: Event) => {
    if (this.opened && !event.composedPath().includes(this.menu!)) this.close();
  };
  private get button() {
    return this.renderRoot.querySelector<HTMLButtonElement>('.trigger');
  }
  private get menu() {
    return this.renderRoot.querySelector<HTMLElement>('.menu');
  }
  private get options() {
    return Array.from(this.source?.options ?? []);
  }
  connectedCallback() {
    super.connectedCallback();
    this.bind();
    window.addEventListener('resize', this.reposition);
    window.addEventListener('scroll', this.reposition, true);
  }
  disconnectedCallback() {
    this.unbind();
    this.source = undefined;
    window.removeEventListener('resize', this.reposition);
    window.removeEventListener('scroll', this.reposition, true);
    super.disconnectedCallback();
  }
  private unbind() {
    this.observer?.disconnect();
    this.source?.removeEventListener('change', this.refresh);
    this.source?.removeEventListener('invalid', this.invalid);
  }
  private bind() {
    const source = this.querySelector('select');
    if (source === this.source) return;
    this.unbind();
    this.source = source ?? undefined;
    if (source) {
      source.addEventListener('change', this.refresh);
      source.addEventListener('invalid', this.invalid);
      this.observer = new MutationObserver(this.refresh);
      this.observer.observe(source, {
        subtree: true,
        childList: true,
        attributes: true,
        characterData: true,
      });
    }
    this.requestUpdate();
  }
  private label() {
    return (
      this.source?.getAttribute('aria-label') ||
      Array.from(this.source?.labels ?? [])
        .map((label) =>
          Array.from(label.childNodes)
            .filter((node) => node.nodeType === Node.TEXT_NODE)
            .map((node) => node.textContent?.trim())
            .join(' '),
        )
        .join(' ') ||
      this.source?.name ||
      'Auswahl'
    );
  }
  private async open() {
    if (!this.source || this.source.disabled) return;
    this.active = Math.max(0, this.source.selectedIndex);
    this.opened = true;
    await this.updateComplete;
    const rect = this.button!.getBoundingClientRect();
    const menu = this.menu!;
    const below = window.innerHeight - rect.bottom - 12;
    const above = rect.top - 12;
    const upwards = below < Math.min(240, this.options.length * 40 + 10) && above > below;
    menu.style.width = `${Math.max(rect.width, 120)}px`;
    menu.style.maxHeight = `${Math.max(80, Math.min(264, upwards ? above - 6 : below - 6))}px`;
    menu.style.left = `${Math.max(8, Math.min(rect.left, window.innerWidth - Math.max(rect.width, 120) - 8))}px`;
    menu.style.top = upwards ? 'auto' : `${rect.bottom + 6}px`;
    menu.style.bottom = upwards ? `${window.innerHeight - rect.top + 6}px` : 'auto';
    menu.showPopover?.();
    this.scrollActive();
  }
  private close() {
    this.menu?.hidePopover?.();
    this.opened = false;
    this.search = '';
  }
  private choose(index: number) {
    const option = this.options[index];
    if (!this.source || this.source.disabled || !option || option.disabled) return;
    const changed = this.source.selectedIndex !== index;
    this.source.selectedIndex = index;
    this.close();
    this.button?.focus();
    if (changed) this.source.dispatchEvent(new Event('change', { bubbles: true }));
    this.requestUpdate();
  }
  private scrollActive() {
    this.renderRoot
      .querySelector(`#${this.menuId}-${this.active}`)
      ?.scrollIntoView?.({ block: 'nearest' });
  }
  private move(direction: number) {
    const options = this.options;
    let index = this.active;
    do {
      index += direction;
    } while (options[index]?.disabled);
    if (index >= 0 && index < options.length) this.active = index;
    void this.updateComplete.then(() => this.scrollActive());
  }
  private async keydown(event: KeyboardEvent) {
    if (['ArrowDown', 'ArrowUp', 'Home', 'End', 'Enter', ' '].includes(event.key)) {
      event.preventDefault();
      if (!this.opened) {
        await this.open();
        return;
      }
      if (event.key === 'ArrowDown' || event.key === 'ArrowUp')
        this.move(event.key === 'ArrowDown' ? 1 : -1);
      else if (event.key === 'Home' || event.key === 'End') {
        this.active = event.key === 'Home' ? -1 : this.options.length;
        this.move(event.key === 'Home' ? 1 : -1);
      } else this.choose(this.active);
    } else if (event.key === 'Escape') {
      event.preventDefault();
      this.close();
    } else if (event.key === 'Tab') this.close();
    else if (event.key.length === 1 && !event.ctrlKey && !event.metaKey && !event.altKey) {
      event.preventDefault();
      if (!this.opened) await this.open();
      this.search = Date.now() - this.searchAt < 700 ? this.search + event.key : event.key;
      this.searchAt = Date.now();
      const index = this.options.findIndex(
        (option) =>
          !option.disabled &&
          option.text.toLocaleLowerCase('de').startsWith(this.search.toLocaleLowerCase('de')),
      );
      if (index >= 0) {
        this.active = index;
        await this.updateComplete;
        this.scrollActive();
      }
    }
  }
  render() {
    return html`<slot @slotchange=${this.bind}></slot
      ><button
        type="button"
        class="trigger"
        role="combobox"
        aria-label=${this.label()}
        aria-haspopup="listbox"
        aria-expanded=${this.opened}
        aria-controls=${this.menuId}
        aria-activedescendant=${this.opened ? `${this.menuId}-${this.active}` : nothing}
        aria-required=${this.source?.required ? 'true' : nothing}
        aria-invalid=${this.invalidSelection ? 'true' : (this.source?.getAttribute('aria-invalid') ?? nothing)}
        aria-describedby=${this.invalidSelection ? `${this.menuId}-error` : nothing}
        ?disabled=${this.source?.disabled}
        @keydown=${this.keydown}
        @click=${(event: Event) => {
          event.preventDefault();
          this.opened ? this.close() : void this.open();
        }}
      >
        <span>${this.options[this.source?.selectedIndex ?? -1]?.text ?? 'Auswählen'}</span
        ><svg viewBox="0 0 20 20" aria-hidden="true"><path d="m6 8 4 4 4-4" /></svg>
      </button>
      <div
        class="menu"
        popover="auto"
        id=${this.menuId}
        role="listbox"
        aria-label=${this.label()}
        ?hidden=${!this.opened}
        @toggle=${(event: ToggleEvent) => {
          if (event.newState === 'closed') this.opened = false;
        }}
      >
        ${this.options.map(
          (option, index) =>
            html`<button
              type="button"
              role="option"
              id=${`${this.menuId}-${index}`}
              tabindex="-1"
              aria-selected=${option.selected}
              ?disabled=${option.disabled}
              class=${this.active === index ? 'active' : ''}
              @pointermove=${() => {
                if (!option.disabled) this.active = index;
              }}
              @mousedown=${(event: Event) => event.preventDefault()}
              @click=${(event: Event) => {
                event.preventDefault();
                this.choose(index);
              }}
            >
              <span>${option.text}</span
              >${option.selected ? html`<svg viewBox="0 0 20 20" aria-hidden="true"><path d="m5 10 3 3 7-7" /></svg>` : nothing}
            </button>`,
        )}
      </div>
      ${this.invalidSelection ? html`<span class="validation" id=${`${this.menuId}-error`} role="alert">Bitte wähle eine Option.</span>` : nothing}`;
  }
  static styles = css`
    :host {
      display: block;
      min-width: 0;
      width: 100%;
      font: inherit;
    }
    ::slotted(select) {
      display: none !important;
    }
    button {
      font: inherit;
      color: var(--color-text);
      cursor: pointer;
    }
    button:disabled {
      opacity: 0.45;
      cursor: default;
    }
    svg {
      width: 18px;
      height: 18px;
      flex-shrink: 0;
      fill: none;
      stroke: currentColor;
      stroke-width: 1.5;
      stroke-linecap: round;
      stroke-linejoin: round;
      color: var(--color-text-muted);
    }
    .trigger {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      width: 100%;
      min-height: var(--control-height, 44px);
      padding: 10px 12px;
      background: var(--color-background);
      border: 1px solid var(--color-border-strong);
      border-radius: var(--radius-sm, 12px);
      text-align: left;
      transition:
        background 120ms,
        border-color 120ms;
    }
    .trigger > span {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .trigger:hover {
      background: var(--color-surface-muted);
      border-color: var(--color-control-hover, #505050);
    }
    .trigger:focus-visible {
      outline: 2px solid var(--color-focus, #888);
      outline-offset: 2px;
    }
    .trigger[aria-expanded='true'] {
      border-color: var(--color-control-hover, #505050);
      background: var(--color-surface-muted);
    }
    .trigger[aria-invalid='true'] {
      border-color: var(--color-error);
    }
    .validation {
      display: block;
      font-size: var(--font-xs);
      color: var(--color-error);
      margin-top: 6px;
    }
    .menu {
      position: fixed;
      box-sizing: border-box;
      margin: 0;
      padding: 5px;
      overflow: auto;
      border: 1px solid var(--color-control-hover, #505050);
      border-radius: 12px;
      background: var(--color-popover, #292929);
      color: var(--color-text);
      box-shadow: 0 12px 32px #0005;
      scrollbar-width: thin;
      scrollbar-color: var(--color-accent-soft) transparent;
    }
    .menu[hidden] {
      display: none;
    }
    .menu::backdrop {
      background: transparent;
    }
    .menu button {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      width: 100%;
      border: 0;
      border-radius: 7px;
      background: transparent;
      min-height: 36px;
      padding: 8px 10px;
      text-align: left;
      font-size: var(--font-sm, 14px);
    }
    .menu button.active {
      background: var(--color-surface-hover, #373737);
    }
    .menu button[aria-selected='true'] {
      color: var(--color-text);
    }
    :host([variant='inline']) .trigger {
      min-height: 36px;
      padding: 6px 9px;
      border-color: transparent;
      background: transparent;
      border-radius: 8px;
      font-size: var(--font-sm, 14px);
    }
    :host([variant='inline']) .trigger:hover,
    :host([variant='inline']) .trigger[aria-expanded='true'] {
      background: var(--color-surface-hover);
    }
    :host([variant='pill']) .trigger {
      min-height: 36px;
      padding: 6px 12px;
      border-radius: 999px;
      font-size: var(--font-sm, 14px);
      color: var(--color-text-muted);
    }
  `;
}
if (globalThis.customElements && !customElements.get('training-select'))
  customElements.define('training-select', SelectControl);
