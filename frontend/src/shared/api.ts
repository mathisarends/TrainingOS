import { ApiError as CanonApiError, createApiFetch, type ApiProblem } from 'lit-canon-fetch';
import type { Transport } from './types';
import { timestampResponse } from './response-time';

export class ApiError<P extends ApiProblem = ApiProblem> extends CanonApiError<P> {
  constructor(status: number, problem: P | string | null) {
    super(
      status,
      typeof problem === 'string'
        ? ({ type: 'about:blank', title: problem, status, detail: problem } as P)
        : problem,
    );
  }
}

const fetchApi = createApiFetch({ baseUrl: '/api/v1', credentials: 'include' });

export class HttpTransport implements Transport {
  async request<T>(
    path: string,
    method = 'GET',
    body?: unknown,
    options: Omit<RequestInit, 'method' | 'body'> = {},
  ): Promise<T> {
    try {
      return timestampResponse(
        await fetchApi<T>(path, {
          method,
          body,
          cache: 'no-store',
          signal: AbortSignal.timeout(20_000),
          ...options,
        }),
      );
    } catch (error) {
      if (error instanceof CanonApiError) {
        const result = new ApiError(error.status, error.problem);
        if (error.status === 401) result.message = 'Bitte melde dich an, um weiterzumachen.';
        throw result;
      }
      if (options.signal?.aborted) throw error;
      throw new ApiError(
        0,
        'Keine Verbindung. Bitte prüfe dein Netzwerk. Die Eingabe bleibt erhalten; prüfe vor erneutem Speichern, ob der Satz angekommen ist.',
      );
    }
  }
}
