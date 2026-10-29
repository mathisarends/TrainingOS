import type { Container } from "./container.js";
import type { Params } from "./page.js";
declare const REDIRECT: unique symbol;
/** Opaque result of {@link redirect}. */
export interface Redirect {
    readonly [REDIRECT]: true;
    readonly to: string;
}
export type GuardResult = boolean | Redirect;
export type Guard = (ctx: {
    params: Params;
    /** The pathname being navigated to, e.g. `/browsers/42`. */
    path: string;
    container: Container;
}) => GuardResult | Promise<GuardResult>;
/** Guard result that cancels the navigation and replaces it with one to `to`. */
export declare const redirect: (to: string) => Redirect;
export declare const isRedirect: (value: unknown) => value is Redirect;
export {};
//# sourceMappingURL=guard.d.ts.map