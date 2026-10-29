const removedOptions = ["features", "queryAliases"];
export function validateConfig(config) {
    if (!config || typeof config.input !== "string" || typeof config.output !== "string") {
        throw new Error("Configuration requires input and output paths");
    }
    for (const option of removedOptions) {
        if (Object.hasOwn(config, option)) {
            throw new Error(`"${option}" was removed in lit-canon-api 1.0. See docs/migration.md.`);
        }
    }
}
