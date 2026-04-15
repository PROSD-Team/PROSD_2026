import { useEffect, useRef } from 'react'
import * as signalR from '@microsoft/signalr'
import { Store } from '../store/Store'
import { useApi } from './useAPI'

// Use relative path – works with Nginx proxy and Vite dev proxy
const HUB_URL = '/hubs/pipeline'

export const usePipeline = () => {
    const { steps, setJobResult, setJobStatus } = Store()
    const { post } = useApi()
    const connectionRef = useRef<signalR.HubConnection | null>(null)
    const startedRef = useRef(false)

    useEffect(() => {
        if (startedRef.current) return
        startedRef.current = true

        const connection = new signalR.HubConnectionBuilder()
            .withUrl(HUB_URL)
            .withAutomaticReconnect()
            .build()

        connection.on('JobCompleted', (data: { jobId: number, status: string, output: string }) => {
            setJobStatus(data.status)
            setJobResult(data.output)
        })

        connection.start()
            .then(() => {
                console.log('SignalR connected, connectionId:', connection.connectionId)
            })
            .catch(err => console.error('SignalR connection error:', err))

        connectionRef.current = connection

        return () => {
            startedRef.current = false
            connection.stop()
        }
    }, [])

    const run = async () => {
        if (steps.length === 0) {
            console.warn('No steps')
            return
        }

        const connection = connectionRef.current
        const connId = connection?.connectionId

        console.log('connection state:', connection?.state)
        console.log('connectionId at run time:', connId)

        if (!connId) {
            console.warn('No connectionId')
            return
        }

        const firstStep = steps[0]
        const pipelineSteps = steps.map(s => s.algorithmName).join(',')

        setJobStatus('running')
        setJobResult(null)

        await post('/api/jobs', {
            pipelineSteps,
            connectionId: connId,
            parametersJson: firstStep.parametersJson || '{}',
            targetWorker: firstStep.algorithmName,
        })
    }

    return { run }
}