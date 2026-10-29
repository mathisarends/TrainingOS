import { contextName, missingContext } from "./errors.js";
export const provide = (context, factory) => ({ context, factory });
/**
 * Eagerly instantiates `providers` in order. Each factory only sees the
 * values created before it. Every value is a singleton.
 */
export function resolveProviders(providers) {
    const values = new Map();
    let requester;
    const container = {
        get(context) {
            if (!values.has(context))
                throw missingContext(context, requester);
            return values.get(context);
        },
    };
    for (const { def, owner } of providers) {
        requester = `The provider for ${contextName(def.context)} (${owner})`;
        try {
            values.set(def.context, def.factory(container));
        }
        finally {
            requester = undefined;
        }
    }
    return { container, values };
}
//# sourceMappingURL=container.js.map