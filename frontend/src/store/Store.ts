import { create } from 'zustand'

export interface PipelineStep {
    id: string
    algorithmName: string
    category: string
    parametersJson: string
}

interface AppState {
    isLoading: boolean
    error: string | null
    setLoading: (loading: boolean) => void
    setError: (error: string | null) => void

    // Pipeline
    steps: PipelineStep[]
    selectedStepId: string | null
    jobResult: string | null
    jobStatus: string | null
    activePipelineId: number | null
    activePipelineName: string

    addStep: (step: PipelineStep) => void
    removeStep: (id: string) => void
    moveStep: (from: number, to: number) => void
    selectStep: (id: string | null) => void
    updateStepParams: (id: string, parametersJson: string) => void
    setJobResult: (result: string | null) => void
    setJobStatus: (status: string | null) => void
    setPipelineName: (name: string) => void
    setPipeline: (steps: PipelineStep[], name: string, id: number | null) => void
    clearPipeline: () => void
}

export const Store = create<AppState>((set) => ({
    isLoading: false,
    error: null,
    setLoading: (loading) => set({ isLoading: loading }),
    setError: (error) => set({ error }),

    steps: [],
    selectedStepId: null,
    jobResult: null,
    jobStatus: null,
    activePipelineId: null,
    activePipelineName: '',

    addStep: (step) => set((s) => ({ steps: [...s.steps, step] })),
    removeStep: (id) => set((s) => ({ steps: s.steps.filter(x => x.id !== id) })),
    moveStep: (from, to) => set((s) => {
        const steps = [...s.steps]
        const [item] = steps.splice(from, 1)
        steps.splice(to, 0, item)
        return { steps }
    }),
    selectStep: (id) => set({ selectedStepId: id }),
    updateStepParams: (id, parametersJson) => set((s) => ({
        steps: s.steps.map(x => x.id === id ? { ...x, parametersJson } : x)
    })),
    setJobResult: (result) => set({ jobResult: result }),
    setJobStatus: (status) => set({ jobStatus: status }),
    setPipelineName: (name) => set({ activePipelineName: name }),
    setPipeline: (steps, name, id) => set({
        steps,
        selectedStepId: null,
        activePipelineId: id,
        activePipelineName: name,
        jobResult: null,
        jobStatus: null
    }),
    clearPipeline: () => set({
        steps: [],
        selectedStepId: null,
        jobResult: null,
        jobStatus: null,
        activePipelineId: null,
        activePipelineName: ''
    }),
}))
