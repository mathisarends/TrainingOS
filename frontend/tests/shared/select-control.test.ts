// @vitest-environment happy-dom
import { afterEach, expect, it, vi } from 'vitest';
import { html, render } from 'lit';
import type { SelectControl } from '../../src/shared/select-control';
import '../../src/shared/select-control';

afterEach(() => document.body.replaceChildren());

async function control() {
  const container = document.createElement('div');
  document.body.append(container);
  render(
    html`<form>
      <label
        >Gewichtseinheit<training-select
          ><select name="unit">
            <option value="kg">Kilogramm</option>
            <option value="disabled" disabled>Unavailable</option>
            <option value="lb">Pfund</option>
          </select></training-select
        ></label
      >
    </form>`,
    container,
  );
  const element = document.querySelector('training-select') as SelectControl;
  const source = element.querySelector('select')!;
  source.selectedIndex = 0;
  source.dispatchEvent(new Event('change', { bubbles: true }));
  await element.updateComplete;
  await element.updateComplete;
  const button = element.shadowRoot!.querySelector<HTMLButtonElement>('[role=combobox]')!;
  return { element, source, button };
}

it('commits a keyboard choice once, skips disabled options and preserves FormData', async () => {
  const { element, source, button } = await control();
  const change = vi.fn();
  source.addEventListener('change', change);
  expect(button.getAttribute('aria-label')).toBe('Gewichtseinheit');
  button.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowDown', cancelable: true }));
  await element.updateComplete;
  button.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowDown', cancelable: true }));
  await element.updateComplete;
  button.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', cancelable: true }));
  await element.updateComplete;
  expect(source.value).toBe('lb');
  expect(new FormData(document.querySelector('form')!).get('unit')).toBe('lb');
  expect(change).toHaveBeenCalledOnce();
  expect(button.getAttribute('aria-expanded')).toBe('false');
});

it('Escape discards navigation and a disabled control cannot open', async () => {
  const { element, source, button } = await control();
  const change = vi.fn();
  source.addEventListener('change', change);
  button.click();
  await element.updateComplete;
  button.dispatchEvent(new KeyboardEvent('keydown', { key: 'End', cancelable: true }));
  button.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', cancelable: true }));
  await element.updateComplete;
  expect(source.value).toBe('kg');
  expect(change).not.toHaveBeenCalled();
  source.disabled = true;
  await vi.waitFor(() => expect(button.disabled).toBe(true));
  button.click();
  await element.updateComplete;
  expect(button.getAttribute('aria-expanded')).toBe('false');
});

it('reflects native changes and an option click without duplicate writes', async () => {
  const { element, source, button } = await control();
  source.value = 'lb';
  source.dispatchEvent(new Event('change', { bubbles: true }));
  await element.updateComplete;
  expect(button.textContent).toContain('Pfund');
  const change = vi.fn();
  source.addEventListener('change', change);
  button.click();
  await element.updateComplete;
  element.shadowRoot!.querySelector<HTMLButtonElement>('[role=option]')!.click();
  await element.updateComplete;
  expect(source.value).toBe('kg');
  expect(change).toHaveBeenCalledOnce();
});

it('exposes required validation at the visible control and clears it after a valid choice', async () => {
  const { element, source, button } = await control();
  source.options[0].value = '';
  source.required = true;
  await element.updateComplete;
  expect(document.querySelector('form')!.reportValidity()).toBe(false);
  await element.updateComplete;
  expect(button.getAttribute('aria-invalid')).toBe('true');
  expect(element.shadowRoot!.activeElement).toBe(button);
  expect(element.shadowRoot!.querySelector('[role=alert]')?.textContent).toContain('Bitte wähle');
  button.click();
  await element.updateComplete;
  element.shadowRoot!.querySelectorAll<HTMLButtonElement>('[role=option]')[2].click();
  await element.updateComplete;
  expect(document.querySelector('form')!.checkValidity()).toBe(true);
  expect(button.getAttribute('aria-invalid')).not.toBe('true');
});
