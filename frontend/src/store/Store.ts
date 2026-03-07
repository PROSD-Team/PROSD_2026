import { create } from 'zustand'

interface CounterState {
    count: number
    isLoading: boolean
    error: string | null
    increment: () => void
    decrement: () => void
    reset: () => void
    setLoading: (loading: boolean) => void
    setError: (error: string | null) => void
}

export const Store = create<CounterState>((set) => ({
    count: 0,
    isLoading: false,
    error: null,
    increment: () => set((state) => ({ count: state.count + 1 })),
    decrement: () => set((state) => ({ count: state.count - 1 })),
    reset: () => set({ count: 0 }),
    setLoading: (loading) => set({ isLoading: loading }),
    setError: (error) => set({ error }),
}))