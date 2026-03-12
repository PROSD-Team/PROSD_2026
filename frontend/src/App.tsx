import './App.css'
import RegistrationForm from './components/RegistrationForm';

function App() {
  const { count, increment, decrement, reset } = Store()


  return (


      <div className="min-h-screen bg-gray-50 py-10">
      {/* Викликаємо новий компонент форми */}
      <RegistrationForm />
      </div>
    </>
  )

}

export default App
