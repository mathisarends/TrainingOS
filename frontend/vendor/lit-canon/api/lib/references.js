export function resolveReference(value, spec, label, seen = new Set()) {
    if (!("$ref" in value)) {
        return value;
    }
    const ref = value.$ref;
    if (typeof ref !== "string" || !ref.startsWith("#/") || seen.has(ref)) {
        throw new Error(`${label} require non-circular local references: ${ref}`);
    }
    seen.add(ref);
    let target = spec;
    for (const key of ref.slice(2).split("/")) {
        if (target === null || typeof target !== "object") {
            throw new Error(`Missing ${label.toLowerCase()} reference: ${ref}`);
        }
        target = target[key.replace(/~1/g, "/").replace(/~0/g, "~")];
    }
    if (target === null || typeof target !== "object") {
        throw new Error(`Missing ${label.toLowerCase()} reference: ${ref}`);
    }
    return resolveReference(target, spec, label, seen);
}
