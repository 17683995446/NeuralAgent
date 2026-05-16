import { useEffect } from 'react'
import { Navigation } from './components/Navigation'
import { Home } from './pages/Home'
import { Architecture } from './pages/Architecture'
import { Flow } from './pages/Flow'
import { Sequence } from './pages/Sequence'
import { Monitor } from './pages/Monitor'
import { useAppStore } from './store/useAppStore'

function App() {
  const { currentRoute } = useAppStore()

  useEffect(() => {
    document.title = 'NeuralAgent - Architecture Visualization'
  }, [])

  const renderPage = () => {
    switch (currentRoute) {
      case '/architecture':
        return <Architecture />
      case '/flow':
        return <Flow />
      case '/sequence':
        return <Sequence />
      case '/monitor':
        return <Monitor />
      default:
        return <Home />
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200">
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-violet-600/20 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-cyan-600/20 rounded-full blur-3xl" />
      </div>
      
      <Navigation />
      
      <main className="pl-16 sm:pl-64 pt-0">
        {renderPage()}
      </main>
    </div>
  )
}

export default App
