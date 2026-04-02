type LogLevel = 'info' | 'warn' | 'error'

const log = (level: LogLevel, message: string, data?: unknown) => {
    const timestamp = new Date().toISOString()
    const formatted = `[${timestamp}] [${level.toUpperCase()}] ${message}`

    if (level === 'error') console.error(formatted, data)
    else if (level === 'warn') console.warn(formatted, data)
    else console.log(formatted, data)
}

export const logger = {
    info: (msg: string, data?: unknown) => log('info', msg, data),
    warn: (msg: string, data?: unknown) => log('warn', msg, data),
    error: (msg: string, data?: unknown) => log('error', msg, data),
}