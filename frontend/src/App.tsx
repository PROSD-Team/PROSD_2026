import './App.css'
import { Store } from "./store/Store.ts"
import Test from "./pages/Test.tsx"

function App() {
  const { count, increment, decrement, reset } = Store()


  return (

    <div>
      <span>{count}</span>
      <button onClick={decrement}>-</button>
      <button onClick={increment}>+</button>
      <button onClick={reset}>reset</button>
      <Test />
    </div>
  )

}

export default App
