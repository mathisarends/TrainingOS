import type { ApiRequestOptions as CanonOptions } from 'lit-canon-fetch';
import { ApiError, HttpTransport } from '../shared/api';
import type { Transport } from '../shared/types';

export { ApiError };
export type ApiRequestOptions = CanonOptions & { transport?: Transport };
let defaultTransport: Transport = new HttpTransport();
export const configurePreviewTransport = (transport?: Transport) => {
  defaultTransport = transport ?? new HttpTransport();
};

/** One request boundary shared by generated APIs, production, preview and tests. */
export function apiFetch<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  const { transport = defaultTransport, ...request } = options;
  const url = new URL(path, 'http://trainingos.local');
  for (const [key, value] of Object.entries(request.query ?? {})) {
    if (value != null) url.searchParams.set(key, String(value));
  }
  const target = url.pathname.replace(/^\/api\/v1/, '') + url.search;
  const { method, body, query: _query, ...init } = request;
  return Object.keys(init).length
    ? transport.request<T>(target, method, body, init)
    : transport.request<T>(target, method, body);
}
