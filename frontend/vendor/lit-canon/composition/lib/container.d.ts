import type { Context } from "@lit/context";
export interface Container {
    get<T>(context: Context<unknown, T>): T;
}
export interface ProviderDef<T = unknown> {
    context: Context<unknown, T>;
    factory: (c: Container) => T;
}
export declare const provide: <T>(context: Context<unknown, T>, factory: (c: Container) => T) => ProviderDef<T>;
/** A provider plus a description of where it was declared, for error messages. */
export interface OwnedProvider {
    def: ProviderDef;
    owner: string;
}
/**
 * Eagerly instantiates `providers` in order. Each factory only sees the
 * values created before it. Every value is a singleton.
 */
export declare function resolveProviders(providers: OwnedProvider[]): {
    container: Container;
    values: Map<{
        __context__: unknown;
    }, unknown>;
};
//# sourceMappingURL=container.d.ts.map