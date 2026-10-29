/** Human-readable name of a context key created with `createContext`. */
export declare const contextName: (context: unknown) => string;
export declare const duplicateFeature: (name: string) => Error;
export declare const duplicatePath: (path: string, first: string, second: string) => Error;
export declare const duplicateContext: (context: unknown, first: string, second: string) => Error;
export declare const tagTaken: (tagName: string) => Error;
export declare const missingContext: (context: unknown, requester?: string) => Error;
export declare const notStarted: () => Error;
export declare const redirectLoop: (to: string, max: number) => string;
export declare const guardFailed: (path: string) => string;
export declare const loadFailed: (path: string) => string;
//# sourceMappingURL=errors.d.ts.map