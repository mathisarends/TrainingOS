import { html } from 'lit';

export type Page =
  | 'login'
  | 'register'
  | 'home'
  | 'plans'
  | 'training'
  | 'history'
  | 'catalog'
  | 'account'
  | 'records'
  | 'settings'
  | 'data';

export const paths: Record<Page, string> = {
  login: '/login',
  register: '/register',
  home: '/',
  plans: '/plans',
  training: '/training',
  history: '/logs',
  catalog: '/profile/exercises',
  account: '/profile',
  records: '/profile/best-performance',
  settings: '/profile/settings',
  data: '/profile', // Legacy data hash links open the integrated account page.
};

export const titles: Record<Page, string> = {
  login: 'Anmelden',
  register: 'Registrieren',
  home: 'Training',
  plans: 'Bearbeiten',
  training: 'Training',
  history: 'Logs',
  catalog: 'Übungen',
  account: 'Konto',
  records: 'Bestleistungen',
  settings: 'Einstellungen',
  data: 'Konto',
};

export interface TrainingSelection {
  planId: string;
  dayId: string;
  week: number;
}

export function trainingOverviewHref(selection: TrainingSelection, demo = false) {
  const query = new URLSearchParams({
    plan: selection.planId,
    day: selection.dayId,
    week: String(selection.week),
  });
  if (demo) query.set('demo', '1');
  return `${paths.training}?${query}`;
}

export function trainingSelectionFromSearch(search: string): TrainingSelection | null {
  const query = new URLSearchParams(search);
  if (!['plan', 'day', 'week'].some((key) => query.has(key))) return null;
  return {
    planId: query.get('plan') ?? '',
    dayId: query.get('day') ?? '',
    week: Number(query.get('week') ?? Number.NaN),
  };
}

export const shell = (page: Page, id = '', selection: TrainingSelection | null = null) =>
  html`<training-app .page=${page} .routeId=${id} .trainingSelection=${selection}></training-app>`;

/** Keep existing shared session links usable after switching to Canon pathname routing. */
export function migrateHashRoute() {
  const [page, id] = location.hash.slice(1).split('/');
  if (!(page in paths)) return;
  const path =
    paths[page as Page] + (page === 'training' && id ? `/${encodeURIComponent(id)}` : '');
  history.replaceState(null, '', path + location.search);
}
