import { html, type TemplateResult } from 'lit';
import { icons } from './icons';
import './select-control';
export const categories: Record<string, string> = {
  squat: 'Kniebeuge',
  bench_press: 'Bankdrücken',
  deadlift: 'Kreuzheben',
  overhead_press: 'Überkopfdrücken',
  back: 'Rücken',
  chest: 'Brust',
  shoulders: 'Schultern',
  legs: 'Beine',
  biceps: 'Bizeps',
  triceps: 'Trizeps',
};
export const weekdays = [
  'Montag',
  'Dienstag',
  'Mittwoch',
  'Donnerstag',
  'Freitag',
  'Samstag',
  'Sonntag',
];
export const statuses = {
  draft: 'Entwurf',
  active: 'Aktiv',
  ended: 'Beendet',
  archived: 'Archiviert',
};
export const formatNumber = (n: string | number) =>
  Number(n).toLocaleString('de-DE', { maximumFractionDigits: 2 });
export const dateLabel = (date: string) =>
  new Date(date.length === 10 ? `${date}T12:00:00` : date).toLocaleDateString('de-DE', {
    day: 'numeric',
    month: 'short',
  });
export function today() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}
export function formValues(event: Event) {
  event.preventDefault();
  return Object.fromEntries(new FormData(event.currentTarget as HTMLFormElement));
}
export function icon(name: string): TemplateResult {
  return html`<svg
    class="icon"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="2"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    ${icons[name] || icons.activity}
  </svg>`;
}
export function empty(title: string, detail: string) {
  return html`<div class="empty">
    <span class="empty-icon">${icon('dumbbell')}</span>
    <h3>${title}</h3>
    <p>${detail}</p>
  </div>`;
}
