import React, { useEffect, useState } from "react"
import { useApi } from "../hooks/useAPI"
import { Store } from "../store/Store"
import { v4 as uuidv4 } from 'uuid'

interface Algorithm {
    name: string
    description: string
    category: string
}

export const Algorithms: React.FC = () => {
    const { get } = useApi()
    const { isLoading, error, addStep } = Store()

    const [data, setData] = useState<Algorithm[]>([])
    const [search, setSearch] = useState("")

    useEffect(() => {
        const fetchData = async () => {
            const result = await get("/api/Meta/algorithms")
            if (result) {
                const flat = (result as any[]).flatMap(cat =>
                    cat.algorithms.map((a: any) => ({ ...a, category: cat.category }))
                )
                setData(flat)
            }
        }
        fetchData()
    }, [])

    const filtered = data.filter(a =>
        a.name.toLowerCase().includes(search.toLowerCase())
    )

    const handleAdd = (algorithm: Algorithm) => {
        addStep({
            id: uuidv4(),
            algorithmName: algorithm.name,
            category: algorithm.category,
            parametersJson: '{}',
        })
    }

    if (isLoading) return <div className="text-white p-4">Завантаження...</div>
    if (error) return <div className="text-red-400 p-4">Помилка: {error}</div>

    return (
        <div className="bg-[#3a3a3a] text-white border-t border-[#555] h-screen overflow-y-auto">
            <div className="flex flex-col p-2">
                <div className="text-1xl mb-2">Algorithms</div>
                <input
                    type="text"
                    placeholder="Search algorithm"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="bg-[#2c2c2c] h-10 w-[90%] px-3 rounded outline-none"
                />
            </div>

            {filtered.map(algorithm => (
                <div
                    key={algorithm.name}
                    className="flex justify-between items-center px-3 py-2 hover:bg-[#555] cursor-pointer"
                >
                    <div className="flex flex-col">
                        <span className="text-sm">{algorithm.name}</span>
                        {algorithm.description && (
                            <span className="text-xs text-[#888]">{algorithm.description}</span>
                        )}
                    </div>
                    <button
                        onClick={() => handleAdd(algorithm)}
                        className="text-lg px-2 hover:text-green-400"
                    >
                        +
                    </button>
                </div>
            ))}

            {filtered.length === 0 && (
                <div className="text-gray-400 text-center mt-4">
                    Нічого не знайдено
                </div>
            )}
        </div>
    )
}