import type { OpenAPIV3 } from "@scalar/openapi-types";
import type { CodegenConfig } from "./config.js";
import type { Operations } from "./operation.js";
export declare function identifier(name: string, label: string): string;
export declare function operationName(id: string | undefined): string;
export declare function collectOperations(spec: OpenAPIV3.Document, config: CodegenConfig): {
    operationsByTag: Map<string, Operations>;
    mutationOperations: string[];
};
