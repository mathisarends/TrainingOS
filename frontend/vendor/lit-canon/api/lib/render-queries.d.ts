import type { Operations } from "./operation.js";
interface RenderQueryOptions {
    /** camelCase resource name, e.g. "userSettings" for the tag "user-settings". */
    namespace: string;
    mutationOperations?: string[];
}
export declare function renderQueryFiles(tag: string, operations: Operations, apiSource: string, header: string, config: RenderQueryOptions): {
    queries: string | null;
    mutations: string | null;
};
export {};
