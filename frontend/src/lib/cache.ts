const store = new Map<string, { value: unknown; expires: number }>()

export const cache = {
    set: (key: string, value: unknown, ttlMs = 5 * 60 * 1000) => {
        store.set(key, { value, expires: Date.now() + ttlMs })
    },
    get: <T>(key: string): T | null => {
        const item = store.get(key)
        if (!item) return null
        if (Date.now() > item.expires) { store.delete(key); return null }
        return item.value as T
    },
    clear: (key: string) => store.delete(key),
}   