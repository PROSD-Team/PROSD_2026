import React from "react"
import { useEffect, useState } from 'react'
import { useApi } from '../hooks/useAPI'
import { Store } from '../store/Store'

interface Algorithm {
    name: string
    description: string
}

interface AlgorithmCategory {
    category: string
    algorithms: Algorithm[]
}

export const Algorithms: React.FC = () => {
    const { get } = useApi()
    const { isLoading, error } = Store()
    const [data, setData] = useState<AlgorithmCategory[]>([])

    useEffect(() => {
        const fetchData = async () => {
            const result = await get('/api/Meta/algorithms')
            if (result) setData(result as AlgorithmCategory[])
        }
        fetchData()
    }, [])

    if (isLoading) return <div>Завантаження...</div>
    if (error) return <div>Помилка: {error}</div>


    return (
        <div className="bg-[#494949] text-white ">
            <div className="flex flex-col  items-center">
                <div className="text-2xl text-center m-2">Algorithms</div>
                <input type="text" placeholder="Search algorithm" className="bg-[#2c2c2c] h-10  w-60 px-15" />
            </div>

            {data.flatMap(category => category.algorithms).map(algorithm => (
                <div key={algorithm.name} className="px-3 py-2 hover:bg-[#555] cursor-pointer">
                    {algorithm.name}
                </div>
            ))}
        </div>
    )
}