import type { OpenAPIV3 } from "@scalar/openapi-types";
import type { Operations } from "./operation.js";
export interface ProblemType {
    name: string;
    hasCode: boolean;
}
export declare function operationProblems(operation: OpenAPIV3.OperationObject, spec: OpenAPIV3.Document): ProblemType[];
export declare function renderProblems(tag: string, operations: Operations, header: string, requestImport: string, includeEmpty?: boolean): string | null;
