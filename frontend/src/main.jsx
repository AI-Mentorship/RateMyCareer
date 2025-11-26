import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
// install global fetch wrapper to emit loading events for API calls
import './utils/fetchWrapper'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
