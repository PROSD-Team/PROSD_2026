import './App.css'
import { Store } from "./store/Store.ts"

function App() {
  const { count, increment, decrement, reset } = Store()


  return (
    <div>
      <span>{count}</span>
      <button onClick={decrement}>-</button>d
      <button onClick={increment}>+</button>
      <button onClick={reset}>reset</button>
    </div>
  )

}

export default App
