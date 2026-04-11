import React, { useEffect, useState } from "react"
import { Store } from "../store/Store"
import { useApi } from "../hooks/useAPI"

export const Parameters: React.FC = () => {
    const { steps, selectedStepId, updateStepParams } = Store()
    const { get } = useApi()
    const [schema, setSchema] = useState<any>(null)
    const [form, setForm] = useState<Record<string, string>>({})

    const selected = steps.find(s => s.id === selectedStepId)

    useEffect(() => {
        if (!selected) { setSchema(null); setForm({}); return }

        get<any>(`/api/meta/input/${selected.category}/${selected.algorithmName}`)
            .then(s => {
                if (!s) return
                setSchema(s)
                // Prefill defaults
                const defaults: Record<string, string> = {}
                Object.entries(s.properties || {}).forEach(([key, val]: any) => {
                    defaults[key] = val.default !== undefined ? String(val.default) : ''
                })
                try {
                    const existing = JSON.parse(selected.parametersJson || '{}')
                    setForm({ ...defaults, ...existing })
                } catch {
                    setForm(defaults)
                }
            })
    }, [selectedStepId])

    const handleChange = (key: string, value: string) => {
        const updated = { ...form, [key]: value }
        setForm(updated)
        if (selected) updateStepParams(selected.id, JSON.stringify(updated))
    }

    return (
        <div className="flex flex-col h-full text-white bg-[#2c2c2c]">
            <div className="flex items-center px-4 h-[40px] border-t border-[#555]">
                Parameters
            </div>

            {!selected && (
                <div className="flex-1 flex items-center justify-center text-[#777] text-sm">
                    Select a node to edit parameters
                </div>
            )}

            {selected && !schema && (
                <div className="flex-1 flex items-center justify-center text-[#777] text-sm">
                    Loading schema...
                </div>
            )}

            {selected && schema && (
                <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-3">
                    <div className="text-[#f97316] text-sm font-semibold mb-1">
                        {selected.algorithmName}
                    </div>
                    {Object.entries(schema.properties || {}).map(([key, val]: any) => (
                        <div key={key} className="flex flex-col gap-1">
                            <label className="text-xs text-[#aaa]">
                                {val.title || key}
                                {(schema.required || []).includes(key) && (
                                    <span className="text-red-400 ml-1">*</span>
                                )}
                            </label>
                            <input
                                value={form[key] || ''}
                                onChange={(e) => handleChange(key, e.target.value)}
                                className="bg-[#3a3a3a] border border-[#555] rounded px-3 py-1.5 text-sm outline-none focus:border-[#f97316]"
                                placeholder={val.default !== undefined ? String(val.default) : ''}
                            />
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}