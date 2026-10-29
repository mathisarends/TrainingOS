/** RFC 9457 problem details returned by an API. */
export interface ApiProblem {
    type: string;
    title: string;
    status: number;
    detail?: string | null;
    instance?: string | null;
    [key: string]: unknown;
}
export declare class ApiError<P extends Partial<Pick<ApiProblem, "type" | "title" | "status" | "detail" | "instance">> = ApiProblem> extends Error {
    readonly status: number;
    readonly problem: P | null;
    constructor(status: number, problem: P | null);
}
export type ApiRequestOptions = Omit<RequestInit, "body"> & {
    body?: unknown;
    query?: object;
};
export interface ApiFetchConfig {
    baseUrl?: string;
    credentials?: RequestCredentials;
    /**
     * Static headers, or a function called before every request with the path from the
     * generated client (before `baseUrl` and the query string) and the upper-case method.
     * Per-request headers override these.
     */
    headers?: HeadersInit | ((request: {
        url: string;
        method: string;
    }) => HeadersInit | Promise<HeadersInit>);
    fetch?: typeof globalThis.fetch;
}
export declare function createApiFetch(config?: ApiFetchConfig): <T>(url: string, options?: ApiRequestOptions) => Promise<T>;
/** Set defaults for generated clients; call once during application startup. */
export declare function configureApiFetch(config: ApiFetchConfig): void;
export declare function apiFetch<T>(url: string, options?: ApiRequestOptions): Promise<T>;
