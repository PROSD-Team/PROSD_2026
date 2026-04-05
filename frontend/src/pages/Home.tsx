import { useEffect, useState } from 'react'
import { useApi } from '../hooks/useAPI'
import { Store } from '../store/Store'
import "../App.css";
import { Header } from '../components/Header';

const Home = () => {
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

  return (

    <div className='bg-[#2c2c2c] h-screen'>
      <Header />
      <pre className='text-[#FFFFFF]'>{JSON.stringify(data, null, 2)}</pre>
    </div>
  )

}

export default Home;