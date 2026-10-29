import type { CodegenConfig } from "./config.js";
export type { CodegenConfig, GenerateOptions, GenerateResult } from "./config.js";
export { generate } from "./generate.js";
export declare function defineConfig<T extends CodegenConfig>(config: T): T;
