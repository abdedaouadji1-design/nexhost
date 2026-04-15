import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import App from './App'
import './index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
        <Toaster
          position="top-left"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#080e14',
              color: '#b8d4e8',
              border: '1px solid #1a3040',
              fontFamily: 'Cairo, sans-serif',
            },
            success: {
              iconTheme: {
                primary: '#00ff88',
                secondary: '#080e14',
              },
            },
            error: {
              iconTheme: {
                primary: '#ff2244',
                secondary: '#080e14',
              },
            },
          }}
        />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>,
)
