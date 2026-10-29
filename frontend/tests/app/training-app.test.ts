// @vitest-environment happy-dom
import { afterEach, expect, it, vi } from 'vitest';
import { ContextProvider } from '@lit/context';
import { TrainingApp } from '../../src/app/training-app';
import '../../src/features/account/profile-view';
import type { ProfileView } from '../../src/features/account/profile-view';
import '../../src/features/account/account-view';
import { transportContext, storeContext, navigationContext } from '../../src/app/context';
import type { TrainingStore } from '../../src/app/store';
import type { Transport, User } from '../../src/shared/types';
import { ApiError } from '../../src/shared/api';

afterEach(() => {
  document.body.replaceChildren();
  vi.restoreAllMocks();
  history.replaceState(null, '', '/');
});

async function account(demo = false) {
  history.replaceState(null, '', demo ? '/profile?demo=1' : '/profile');
  const user: User = {
    id: 'user-a',
    unit: 'kg',
    rounding_step: '2.5',
    effort_scale: 'rpe',
    timezone: 'Europe/Berlin',
  };
  const state = {
    plans: [],
    exercises: [],
    sessions: [],
    next: {
      plan_id: null,
      day_id: null,
      week: null,
      scheduled_date: null,
      running_training_session_id: null,
    },
  };
  const store = {
    user: vi.fn().mockResolvedValue(user),
    dashboard: vi.fn().mockResolvedValue(state),
    clear: vi.fn(),
  };
  const request = vi.fn().mockResolvedValue(undefined);
  const navigate = vi.fn();
  const host = document.createElement('div');
  const providers = [
    new ContextProvider(host, {
      context: storeContext,
      initialValue: store as unknown as TrainingStore,
    }),
    new ContextProvider(host, {
      context: transportContext,
      initialValue: { request } as Transport,
    }),
    new ContextProvider(host, { context: navigationContext, initialValue: { navigate } }),
  ];
  document.body.append(host);
  providers.forEach((provider) => provider.hostConnected());
  const app = new TrainingApp();
  app.page = 'account';
  host.append(app);
  await vi.waitFor(() => expect(app.querySelector('.profile-logout')).not.toBeNull());
  await app.updateComplete;
  return { app, request, navigate, store, user, state };
}

it('waits for confirmed logout, blocks duplicate clicks, clears cached user state and opens login', async () => {
  const { app, request, navigate, store } = await account();
  let finish!: () => void;
  request.mockImplementation(
    () =>
      new Promise<void>((resolve) => {
        finish = resolve;
      }),
  );
  const button = app.querySelector<HTMLButtonElement>('.profile-logout')!;
  button.click();
  // Also guard repeated events before the pending state has rendered.
  app.querySelector('profile-view')!.dispatchEvent(new CustomEvent('logout', { bubbles: true }));
  await app.updateComplete;
  await app.querySelector<ProfileView>('profile-view')!.updateComplete;
  expect(button.disabled).toBe(true);
  expect(button.textContent).toContain('Wird abgemeldet');
  expect(request).toHaveBeenCalledExactlyOnceWith('/auth/logout', 'POST', undefined);
  expect(navigate).not.toHaveBeenCalled();
  expect(store.clear).not.toHaveBeenCalled();
  finish();
  await vi.waitFor(() => expect(navigate).toHaveBeenCalledWith('/login'));
  expect(store.clear).toHaveBeenCalledOnce();
  expect(app.querySelector('profile-view')).toBeNull();
  expect(app.querySelector('auth-view')).not.toBeNull();
});

it('keeps the account visible after a failed logout and only retries on a new click', async () => {
  const { app, request, navigate, store } = await account();
  request.mockRejectedValueOnce(new ApiError(0, 'Offline'));
  app.querySelector<HTMLButtonElement>('.profile-logout')!.click();
  await vi.waitFor(() =>
    expect(app.querySelector('[role=alert]')?.textContent).toContain('Abmelden fehlgeschlagen'),
  );
  expect(request).toHaveBeenCalledOnce();
  expect(store.clear).not.toHaveBeenCalled();
  expect(navigate).not.toHaveBeenCalled();
  const button = app.querySelector<HTMLButtonElement>('.profile-logout')!;
  expect(button.disabled).toBe(false);
  button.click();
  await vi.waitFor(() => expect(navigate).toHaveBeenCalledWith('/login'));
  expect(request).toHaveBeenCalledTimes(2);
  expect(store.clear).toHaveBeenCalledOnce();
});

it('treats an expired session as signed out', async () => {
  const { app, request, navigate, store } = await account();
  request.mockRejectedValueOnce(new ApiError(401, 'Expired'));
  app.querySelector<HTMLButtonElement>('.profile-logout')!.click();
  await vi.waitFor(() => expect(navigate).toHaveBeenCalledWith('/login'));
  expect(store.clear).toHaveBeenCalledOnce();
  expect(app.querySelector('[role=alert]')).toBeNull();
});

it('leaves the preview at the real login without calling real authentication', async () => {
  const replace = vi.spyOn(location, 'replace').mockImplementation(() => {});
  const { app, request, store } = await account(true);
  const button = app.querySelector<HTMLButtonElement>('.profile-logout')!;
  expect(button.textContent).toContain('Vorschau verlassen');
  button.click();
  await vi.waitFor(() => expect(replace).toHaveBeenCalledWith('/login'));
  expect(request).not.toHaveBeenCalled();
  expect(store.clear).toHaveBeenCalledOnce();
});

it('can sign out while a dashboard refresh is still pending', async () => {
  const { app, request, navigate, store, user, state } = await account();
  let finishRefresh!: (value: typeof state) => void;
  store.dashboard.mockImplementationOnce(
    () =>
      new Promise((resolve) => {
        finishRefresh = resolve;
      }),
  );
  app.page = 'settings';
  await app.updateComplete;
  app
    .querySelector('account-view')!
    .dispatchEvent(new CustomEvent('user-changed', { detail: user, bubbles: true }));
  await vi.waitFor(() => expect(store.dashboard).toHaveBeenCalledTimes(2));
  app.page = 'account';
  await app.updateComplete;
  await app.querySelector<ProfileView>('profile-view')!.updateComplete;
  app.querySelector<HTMLButtonElement>('.profile-logout')!.click();
  await vi.waitFor(() => expect(navigate).toHaveBeenCalledWith('/login'));
  expect(request).toHaveBeenCalledExactlyOnceWith('/auth/logout', 'POST', undefined);
  finishRefresh(state);
  await app.updateComplete;
  expect(app.querySelector('profile-view')).toBeNull();
});
