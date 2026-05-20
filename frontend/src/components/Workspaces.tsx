import React from "react"
import { Store } from "../store/Store"
import { usePipeline } from "../hooks/usePipeline"
import { useApi } from "../hooks/useAPI"
import { getStoredUser } from "../lib/session"
import type { PipelineSummary } from "../types/api"

export const Workspace: React.FC = () => {
    const {
        steps,
        selectedStepId,
        selectStep,
        removeStep,
        moveStep,
        jobResult,
        jobStatus,
        activePipelineId,
        activePipelineName,
        setPipelineName,
        setPipeline,
        clearPipeline
    } = Store()
    const { run } = usePipeline()
    const { post, put } = useApi()
    const user = getStoredUser()

    const handleSave = async () => {
        if (!user) return
        if (steps.length === 0) return

        const name = activePipelineName.trim()
        if (!name) {
            alert("Вкажіть назву пайплайна перед збереженням.")
            return
        }

        const payload = {
            userId: user.id,
            name,
            definitionJson: JSON.stringify({ steps }),
        }

        let result: PipelineSummary | null = null
        if (activePipelineId) {
            result = await put<PipelineSummary>(`/api/pipelines/${activePipelineId}`, payload)
        } else {
            result = await post<PipelineSummary>("/api/pipelines", payload)
        }

        if (result) {
            setPipeline(steps, result.name, result.id)
        }
    }

    return (
        <div className="flex flex-col h-full w-full relative">

            {/* Tabs bar */}
            <div className="flex bg-[#2c2c2c] h-[48px] items-center gap-3 px-4 border-b border-[#555]">
                <input
                    value={activePipelineName}
                    onChange={(e) => setPipelineName(e.target.value)}
                    placeholder="Pipeline name"
                    className="h-8 w-52 rounded-md bg-[#3a3a3a] px-3 text-sm text-white outline-none focus:border-[#f97316] border border-transparent"
                />
                <span className="text-[#777] text-sm">
                    {steps.length === 0 ? 'Pipeline empty' : `${steps.length} step(s)`}
                </span>
                <div className="ml-auto flex items-center gap-2">
                    <button
                        onClick={handleSave}
                        disabled={!user || steps.length === 0}
                        className="rounded-md bg-[#3a3a3a] px-3 py-1.5 text-xs text-white hover:bg-[#4a4a4a] disabled:opacity-40"
                    >
                        {activePipelineId ? "Update" : "Save"}
                    </button>
                    <button
                        onClick={clearPipeline}
                        className="rounded-md bg-[#2c2c2c] px-3 py-1.5 text-xs text-[#aaa] hover:text-white"
                    >
                        New
                    </button>
                </div>
            </div>

            {/* Pipeline steps list */}
            <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-2">
                {steps.length === 0 && (
                    <div className="flex items-center justify-center h-full text-[#666] text-sm">
                        Add algorithms from the left panel
                    </div>
                )}
                {steps.map((step, index) => (
                    <div
                        key={step.id}
                        onClick={() => selectStep(step.id)}
                        className={`flex items-center justify-between px-4 py-3 rounded-lg border cursor-pointer transition-colors ${selectedStepId === step.id
                            ? 'bg-[#3a3a3a] border-[#f97316]'
                            : 'bg-[#3a3a3a] border-[#555] hover:border-[#777]'
                            }`}
                    >
                        <div className="flex items-center gap-3">
                            <span className="text-[#f97316] text-xs font-mono w-5">{index + 1}</span>
                            <span className="text-white text-sm">{step.algorithmName}</span>
                        </div>
                        <div className="flex items-center gap-1">
                            <button
                                onClick={(e) => { e.stopPropagation(); moveStep(index, index - 1) }}
                                disabled={index === 0}
                                className="text-[#777] hover:text-white px-1 disabled:opacity-30"
                            >↑</button>
                            <button
                                onClick={(e) => { e.stopPropagation(); moveStep(index, index + 1) }}
                                disabled={index === steps.length - 1}
                                className="text-[#777] hover:text-white px-1 disabled:opacity-30"
                            >↓</button>
                            <button
                                onClick={(e) => { e.stopPropagation(); removeStep(step.id) }}
                                className="text-[#777] hover:text-red-400 px-1 ml-1"
                            >✕</button>
                        </div>
                    </div>
                ))}
            </div>

            {/* Run button */}
            <button
                onClick={run}
                disabled={steps.length === 0 || jobStatus === 'running'}
                className="absolute bottom-[216px] right-6 bg-[#f97316] hover:bg-[#ea580c] disabled:opacity-40 text-white px-6 py-2 rounded-md font-semibold transition-colors"
            >
                {jobStatus === 'running' ? 'Running...' : 'Run'}
            </button>

            {/* Result panel */}
            <div className="h-[200px] border-t border-[#555] bg-[#2c2c2c] flex flex-col">
                <div className="px-4 py-2 border-b border-[#333] text-sm text-[#aaa] flex items-center gap-2">
                    Result
                    {jobStatus && (
                        <span className={`text-xs px-2 py-0.5 rounded-full ${jobStatus === 'completed' ? 'bg-green-900 text-green-300' :
                            jobStatus === 'running' ? 'bg-yellow-900 text-yellow-300' :
                                'bg-red-900 text-red-300'
                            }`}>{jobStatus}</span>
                    )}
                </div>
                <div className="flex-1 p-4 text-[#aaa] text-sm font-mono overflow-y-auto">
                    {jobResult
                        ? <pre>{JSON.stringify(JSON.parse(jobResult), null, 2)}</pre>
                        : <span className="text-[#666]">No output yet</span>
                    }
                </div>
            </div>
        </div>
    )
}
