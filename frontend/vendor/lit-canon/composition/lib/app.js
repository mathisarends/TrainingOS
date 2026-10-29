import { LitElement, html } from "lit";
import { Router } from "@lit-labs/router";
import { ContextProvider } from "@lit/context";
import { resolveProviders, } from "./container.js";
import * as errors from "./errors.js";
import { isRedirect } from "./guard.js";
const MAX_REDIRECTS = 10;
const DEFAULT_INTENT = { scroll: true, redirects: 0 };
const NO_SCROLL = { scroll: false, redirects: 0 };
export function createApp(options) {
    const { features, baseTitle, rootTagName = "lit-canon-root" } = options;
    const providers = collectProviders(options);
    validate(options, providers, rootTagName);
    const { container, values } = resolveProviders(providers);
    let root;
    // Set right before the router calls `enter`; link clicks leave it unset (= DEFAULT_INTENT).
    let intent;
    let navId = 0;
    let committedUrl;
    let scrollPending = false;
    let redirectTask;
    const currentUrl = () => location.pathname + location.search + location.hash;
    const pathnameOf = (path) => new URL(path, location.href).pathname;
    const setTitle = (title) => {
        const full = title !== undefined && baseTitle !== undefined
            ? `${title} · ${baseTitle}`
            : (title ?? baseTitle);
        if (full !== undefined)
            document.title = full;
    };
    /** Builds the router `enter` callback: guards → load → title → commit. */
    const enter = (page) => async (params) => {
        const id = ++navId;
        const nav = intent ?? DEFAULT_INTENT;
        intent = undefined;
        const path = location.pathname;
        const stale = () => id !== navId;
        // Keep the URL in sync with the page that stays visible (link clicks push before `enter`).
        const cancel = () => {
            if (committedUrl !== undefined && currentUrl() !== committedUrl) {
                history.replaceState(history.state, "", committedUrl);
            }
            return false;
        };
        if (page) {
            for (const guard of page.guards ?? []) {
                let result;
                try {
                    result = await guard({ params, path, container });
                }
                catch (err) {
                    if (stale())
                        return false;
                    console.error(errors.guardFailed(page.path), err);
                    return cancel();
                }
                if (stale())
                    return false;
                if (isRedirect(result)) {
                    if (nav.redirects >= MAX_REDIRECTS) {
                        console.error(errors.redirectLoop(result.to, MAX_REDIRECTS));
                        return cancel();
                    }
                    const to = result.to;
                    // Never start a navigation from inside `enter`; schedule it after this one is cancelled.
                    redirectTask = new Promise((resolve) => queueMicrotask(() => {
                        if (stale() || !root)
                            return resolve();
                        history.replaceState(null, "", to);
                        intent = { scroll: nav.scroll, redirects: nav.redirects + 1 };
                        resolve(root.router.goto(pathnameOf(to)));
                    }));
                    return false;
                }
                if (result !== true)
                    return cancel();
            }
            try {
                await page.load?.();
            }
            catch (err) {
                if (stale())
                    return false;
                console.error(errors.loadFailed(page.path), err);
                return cancel();
            }
            if (stale())
                return false;
        }
        const title = page?.title;
        setTitle(typeof title === "function" ? title({ params }) : title);
        committedUrl = currentUrl();
        scrollPending = nav.scroll;
        return true;
    };
    const routes = features.flatMap((feature) => feature.pages.map((page) => ({
        path: page.path,
        enter: enter(page),
        render: (params) => feature.layout ? feature.layout(page.render(params)) : page.render(params),
    })));
    const fallback = {
        enter: enter(undefined),
        render: options.notFound ?? (() => html ``),
    };
    const onPopState = () => {
        intent = NO_SCROLL;
    };
    class RootElement extends LitElement {
        constructor() {
            super();
            this.router = new Router(this, routes, { fallback });
            for (const [context, initialValue] of values) {
                new ContextProvider(this, { context: context, initialValue });
            }
        }
        // Light DOM, so the app's global styles reach pages and layouts.
        createRenderRoot() {
            return this;
        }
        connectedCallback() {
            // Registered before the router's own listener, so it runs first.
            window.addEventListener("popstate", onPopState);
            intent = NO_SCROLL; // initial navigation
            super.connectedCallback();
        }
        disconnectedCallback() {
            super.disconnectedCallback();
            window.removeEventListener("popstate", onPopState);
        }
        render() {
            return this.router.outlet();
        }
        updated() {
            if (scrollPending) {
                scrollPending = false;
                window.scrollTo(0, 0);
            }
        }
    }
    customElements.define(rootTagName, RootElement);
    return {
        container,
        start() {
            if (root)
                return;
            root = document.createElement(rootTagName);
            options.root.append(root);
        },
        async navigate(path) {
            if (!root)
                throw errors.notStarted();
            history.pushState({}, "", path);
            intent = DEFAULT_INTENT;
            await root.router.goto(pathnameOf(path));
            while (redirectTask) {
                const task = redirectTask;
                redirectTask = undefined;
                await task;
            }
            await root.updateComplete;
        },
    };
}
function collectProviders(options) {
    return [
        ...(options.providers ?? []).map((def) => ({ def, owner: "the app providers" })),
        ...options.features.flatMap((f) => (f.providers ?? []).map((def) => ({ def, owner: `feature "${f.name}"` }))),
    ];
}
function validate(options, providers, rootTagName) {
    const names = new Set();
    const paths = new Map();
    for (const feature of options.features) {
        if (names.has(feature.name))
            throw errors.duplicateFeature(feature.name);
        names.add(feature.name);
        for (const { path } of feature.pages) {
            const first = paths.get(path);
            if (first !== undefined)
                throw errors.duplicatePath(path, first, feature.name);
            paths.set(path, feature.name);
        }
    }
    const owners = new Map();
    for (const { def, owner } of providers) {
        const first = owners.get(def.context);
        if (first !== undefined)
            throw errors.duplicateContext(def.context, first, owner);
        owners.set(def.context, owner);
    }
    if (customElements.get(rootTagName))
        throw errors.tagTaken(rootTagName);
}
//# sourceMappingURL=app.js.map