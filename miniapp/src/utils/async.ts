export type SettledResult<T> =
  | { status: 'fulfilled'; value: T }
  | { status: 'rejected'; reason: unknown }

export function settle<T>(promise: Promise<T>): Promise<SettledResult<T>> {
  return promise.then(
    (value) => ({ status: 'fulfilled', value }),
    (reason) => ({ status: 'rejected', reason }),
  )
}

export function allSettled<T extends readonly unknown[]>(
  promises: { [K in keyof T]: Promise<T[K]> },
): Promise<{ [K in keyof T]: SettledResult<T[K]> }> {
  return Promise.all(promises.map((promise) => settle(promise))) as Promise<{
    [K in keyof T]: SettledResult<T[K]>
  }>
}
