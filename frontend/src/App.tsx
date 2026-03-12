import './App.css'
import RegistrationForm from './pages/RegistrationForm.tsx';
import Test from "./components/Test.tsx"
import { BrowserRouter, Routes, Route } from 'react-router-dom';

function App() {



  return (

    <BrowserRouter>
      <Routes>
        <Route path="/" element={<RegistrationForm />} />
        <Route path="/test" element={<Test />} />
      </Routes>
    </BrowserRouter>

  )

}

export default App
