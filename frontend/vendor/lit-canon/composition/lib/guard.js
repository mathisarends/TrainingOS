const REDIRECT = Symbol("lit-canon.redirect");
/** Guard result that cancels the navigation and replaces it with one to `to`. */
export const redirect = (to) => Object.freeze({ [REDIRECT]: true, to });
export const isRedirect = (value) => typeof value === "object" && value !== null && REDIRECT in value;
//# sourceMappingURL=guard.js.map