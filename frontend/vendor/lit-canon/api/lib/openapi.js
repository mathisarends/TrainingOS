import ts from "typescript";
import { resolveReference } from "./references.js";
import { operationProblems } from "./render-problems.js";
const methods = new Set(["get", "put", "post", "delete", "options", "head", "patch", "trace"]);
function validateParameterSchema(value, spec, context, allowArray, seen = new Set()) {
    const schema = resolveReference(value, spec, "Schemas");
    if (seen.has(schema)) {
        return;
    }
    const visited = new Set(seen).add(schema);
    const types = Array.isArray(schema.type) ? schema.type : [schema.type ?? ""];
    if (types.includes("object") || schema.properties || (!allowArray && types.includes("array"))) {
        throw new Error(`Unsupported object or array parameter in ${context}`);
    }
    if ("items" in schema && schema.items) {
        validateParameterSchema(schema.items, spec, context, false, visited);
    }
    for (const variant of [
        ...(schema.allOf ?? []),
        ...(schema.oneOf ?? []),
        ...(schema.anyOf ?? []),
    ]) {
        validateParameterSchema(variant, spec, context, allowArray, visited);
    }
}
function validateParameter(parameter, spec, context) {
    if (parameter.in !== "path" && parameter.in !== "query") {
        throw new Error(`Unsupported ${parameter.in} parameter ${parameter.name} in ${context}`);
    }
    const style = parameter.in === "query" ? "form" : "simple";
    const explode = parameter.in === "query";
    if (parameter.content ||
        (parameter.style && parameter.style !== style) ||
        (parameter.explode !== undefined && parameter.explode !== explode) ||
        parameter.allowReserved) {
        throw new Error(`Unsupported serialization for parameter ${parameter.name} in ${context}`);
    }
    if (parameter.schema) {
        validateParameterSchema(parameter.schema, spec, `${context} (${parameter.name})`, parameter.in === "query");
    }
}
export function identifier(name, label) {
    if (typeof name !== "string" || !/^[A-Za-z_$][\w$]*$/.test(name)) {
        throw new Error(`Invalid ${label}: ${name}`);
    }
    const token = ts
        .createScanner(ts.ScriptTarget.Latest, false, ts.LanguageVariant.Standard, name)
        .scan();
    if (token >= ts.SyntaxKind.FirstKeyword && token <= ts.SyntaxKind.LastReservedWord) {
        throw new Error(`Reserved ${label}: ${name}`);
    }
    return name;
}
export function operationName(id) {
    if (typeof id !== "string" || !/^[A-Za-z_][A-Za-z0-9_]*$/.test(id)) {
        throw new Error(`Operation IDs must be explicit snake_case or camelCase identifiers: ${id}`);
    }
    const name = id.replace(/_([a-z0-9])/g, (_, character) => character.toUpperCase());
    return identifier(name, "operation name");
}
export function collectOperations(spec, config) {
    const operationsByTag = new Map();
    const names = new Set();
    const excluded = new Set(config.excludeTags ?? []);
    for (const [path, pathItem] of Object.entries(spec.paths ?? {})) {
        if (!pathItem) {
            continue;
        }
        if (pathItem.$ref) {
            throw new Error(`Path item references must be bundled before generation: ${path}`);
        }
        for (const [method, value] of Object.entries(pathItem)) {
            if (!methods.has(method)) {
                continue;
            }
            const operation = value;
            if (operation.tags?.length !== 1) {
                throw new Error(`${method.toUpperCase()} ${path} needs exactly one OpenAPI tag`);
            }
            const [tag] = operation.tags;
            if (!/^[a-z][a-z0-9-]*$/.test(tag)) {
                throw new Error(`OpenAPI tag cannot be used as a resource directory: ${tag}`);
            }
            if (excluded.has(tag)) {
                continue;
            }
            const name = operationName(operation.operationId);
            if (["apiFetch", "ApiRequestOptions", "queryOptions", "mutationOptions"].includes(name)) {
                throw new Error(`Operation name conflicts with a generated import: ${name}`);
            }
            if (names.has(name)) {
                throw new Error(`Duplicate generated operation name: ${name}`);
            }
            names.add(name);
            const parameters = new Map([...(pathItem.parameters ?? []), ...(operation.parameters ?? [])].map((value) => {
                const parameter = resolveReference(value, spec, "Parameters");
                return [`${parameter.in}:${parameter.name}`, parameter];
            }));
            for (const parameter of parameters.values()) {
                validateParameter(parameter, spec, `${method.toUpperCase()} ${path}`);
            }
            const operations = operationsByTag.get(tag) ?? new Map();
            operations.set(name, {
                path,
                method,
                hasQuery: [...parameters.values()].some((parameter) => parameter.in === "query"),
                problems: config.problems === false ? [] : operationProblems(operation, spec),
            });
            operationsByTag.set(tag, operations);
        }
    }
    const mutationOperations = (config.mutationOperations ?? []).map(operationName);
    for (const name of mutationOperations) {
        if (!names.has(name)) {
            throw new Error(`Configured mutation has no included operation: ${name}`);
        }
    }
    return { operationsByTag, mutationOperations };
}
