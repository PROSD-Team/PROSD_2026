import './App.css'
import RegistrationForm from './pages/RegistrationForm.tsx';
import Home from "./pages/Home.tsx"
import { BrowserRouter, Routes, Route } from 'react-router-dom';

function App() {



  return (

    <BrowserRouter>
      <Routes>
        <Route path="/" element={<RegistrationForm />} />
        <Route path="/home" element={<Home />} />
      </Routes>
    </BrowserRouter>

  )

}

export default App
