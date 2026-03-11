import './App.css'
import RegistrationForm from './components/RegistrationForm';

function App() {


  return (
    <>
      <p className='text-red-500'> Start</p>


      <div className="min-h-screen bg-gray-50 py-10">
      {/* Викликаємо новий компонент форми */}
      <RegistrationForm />
      </div>
    </>
  )
}

export default App
