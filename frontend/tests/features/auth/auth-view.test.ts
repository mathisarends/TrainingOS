// @vitest-environment happy-dom
import { afterEach, expect, it, vi } from 'vitest';
import { AuthView } from '../../../src/features/auth/auth-view';
import { ApiError } from '../../../src/shared/api';
import type { Transport } from '../../../src/shared/types';

afterEach(() => document.body.replaceChildren());

async function setup(mode: 'login' | 'register' = 'login') {
  const view = new AuthView();
  const request = vi.fn();
  view.api = { request } as Transport;
  view.mode = mode;
  document.body.append(view);
  await view.updateComplete;
  view.querySelector<HTMLInputElement>('[name=email]')!.value = ' training@example.com ';
  view.querySelector<HTMLInputElement>('[name=password]')!.value = '  My training password 2026!  ';
  if (mode === 'register')
    view.querySelector<HTMLInputElement>('[name=confirmation]')!.value =
      '  My training password 2026!  ';
  return { view, request };
}

function submit(view: AuthView) {
  view
    .querySelector('form')!
    .dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
}

it('submits real credentials without trimming the password and clears them after success', async () => {
  const { view, request } = await setup();
  const signedIn = vi.fn();
  view.addEventListener('authenticated', signedIn);
  request.mockResolvedValue({ id: 'user-a' });
  submit(view);
  await vi.waitFor(() => expect(signedIn).toHaveBeenCalledOnce());
  expect(request).toHaveBeenCalledWith('/auth/login', 'POST', {
    email: 'training@example.com',
    password: '  My training password 2026!  ',
  });
  expect(view.querySelector<HTMLInputElement>('[name=password]')!.value).toBe('');
});

it('requires matching registration passwords before sending a request', async () => {
  const { view, request } = await setup('register');
  view.querySelector<HTMLInputElement>('[name=confirmation]')!.value = 'Another long password';
  submit(view);
  await view.updateComplete;
  expect(request).not.toHaveBeenCalled();
  expect(view.querySelector('[role=alert]')?.textContent).toContain('stimmen nicht überein');
  view.querySelector<HTMLInputElement>('[name=confirmation]')!.value =
    '  My training password 2026!  ';
  request.mockResolvedValue({ id: 'created' });
  submit(view);
  await vi.waitFor(() => expect(request).toHaveBeenCalledOnce());
  expect(request.mock.calls[0][0]).toBe('/auth/register');
});

it('retains entries after a rejected login and never retries automatically', async () => {
  const { view, request } = await setup();
  request.mockRejectedValue(new ApiError(401, 'Wrong credentials'));
  submit(view);
  await vi.waitFor(() =>
    expect(view.querySelector('[role=alert]')?.textContent).toContain('E-Mail oder das Passwort'),
  );
  expect(request).toHaveBeenCalledOnce();
  expect(view.querySelector<HTMLInputElement>('[name=password]')!.value).toBe(
    '  My training password 2026!  ',
  );
});

it('blocks duplicate submissions while a login is pending', async () => {
  const { view, request } = await setup();
  request.mockImplementation(() => new Promise(() => {}));
  submit(view);
  submit(view);
  expect(request).toHaveBeenCalledOnce();
  await view.updateComplete;
  expect(view.querySelector<HTMLButtonElement>('.auth-submit')!.disabled).toBe(true);
});

it('never creates a real account in the isolated preview', async () => {
  const { view, request } = await setup('register');
  view.demo = true;
  await view.updateComplete;
  submit(view);
  expect(request).not.toHaveBeenCalled();
  expect(view.querySelector('.auth-preview a')?.getAttribute('href')).toBe('/register');
});
