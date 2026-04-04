import { useEffect, useState } from 'react'
import { useApi } from '../hooks/useAPI'
import { Store } from '../store/Store'

const TestPage = () => {
  const { get } = useApi()
  const { isLoading, error } = Store()
  const [data, setData] = useState<unknown>(null)

  useEffect(() => {
    const fetch = async () => {
      const result = await get('/api/Meta/algorithms')
      if (result) setData(result)
    }
    fetch()
  }, [])

  if (isLoading) return <div>Завантаження...</div>
  if (error) return <div>Помилка: {error}</div>

  return <pre>{JSON.stringify(data, null, 2)}</pre>
}

export default TestPage