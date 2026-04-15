import axios from 'axios'
import { logger } from '../lib/logger'
import { cache } from '../lib/cache'

const api = axios.create({
    // Use relative path in production; 
    // Vite handles proxy in dev
    baseURL: import.meta.env.VITE_API_URL || '',
    withCredentials: true
})

api.interceptors.request.use((config) => {
    logger.info(`Request: ${config.method?.toUpperCase()} ${config.url}`)
    return config
})

api.interceptors.response.use(
    (response) => {
        logger.info(`Response: ${response.status} ${response.config.url}`)
        cache.set(response.config.url!, response.data)
        return response
    },
    (error) => {
        logger.error(`Error: ${error.response?.status} ${error.config?.url}`, error)
        return Promise.reject(error)
    }
)

export default api