import type { OpenAPIV3 } from "@scalar/openapi-types";
export declare function resolveReference<T extends object>(value: T | OpenAPIV3.ReferenceObject, spec: OpenAPIV3.Document, label: string, seen?: Set<string>): T;
