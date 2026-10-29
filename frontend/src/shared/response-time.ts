const received = new WeakMap<object, number>();

/** Keep receipt time outside the API DTO so cached timer snapshots keep aging. */
export function timestampResponse<T>(value: T, now = performance.now()): T {
  if (value && typeof value === 'object') {
    received.set(value, now);
    for (const child of Object.values(value)) timestampResponse(child, now);
  }
  return value;
}

export function responseTime(value: object) {
  return received.get(value);
}
