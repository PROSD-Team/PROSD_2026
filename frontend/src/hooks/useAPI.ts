import { Store } from '../store/Store'
import api from '../api/axiosInstance'
import { cache } from '../lib/cache'

export const useApi = () => {
    const { setLoading, setError } = Store()

    const get = async <T>(url: string): Promise<T | null> => {
        const cached = cache.get<T>(url)
        if (cached) return cached

        setLoading(true)
        setError(null)
        try {
            const res = await api.get<T>(url)
            return res.data
        } catch (e) {
            const message = e instanceof Error ? e.message : 'Щось пішло не так'
            setError(message)
            return null
        } finally {
            setLoading(false)
        }
    }

    const post = async <T>(url: string, body: unknown): Promise<T | null> => {
        setLoading(true)
        setError(null)
        try {
            const res = await api.post<T>(url, body)
            return res.data
        } catch (e) {
            const message = e instanceof Error ? e.message : 'Щось пішло не так'
            setError(message)
            return null
        } finally {
            setLoading(false)
        }
    }

    return { get, post }
}