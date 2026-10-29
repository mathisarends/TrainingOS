import { type TemplateResult } from "lit";
import { type Container, type ProviderDef } from "./container.js";
import type { FeatureDef } from "./feature.js";
export interface AppOptions {
    /** Element the root element is appended to. */
    root: Element;
    features: FeatureDef[];
    /** App-wide providers, created before any feature provider. */
    providers?: ProviderDef[];
    notFound?: () => TemplateResult;
    /** Default: `'lit-canon-root'`. */
    rootTagName?: string;
    /** E.g. `'Vizro'` turns a page title `'Browser 42'` into `'Browser 42 · Vizro'`. */
    baseTitle?: string;
}
export interface App {
    start(): void;
    /** `history.pushState` + routing. Resolves once the navigation (and any redirects) settled. */
    navigate(path: string): Promise<void>;
    container: Container;
}
export declare function createApp(options: AppOptions): App;
//# sourceMappingURL=app.d.ts.map