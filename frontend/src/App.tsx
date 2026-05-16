import { Routes, Route } from 'react-router-dom'
import { Toaster } from '@/components/ui/toaster'
import Layout from '@/components/layout/Layout'
import Dashboard from '@/pages/Dashboard'
import Agents from '@/pages/Agents'
import Workflows from '@/pages/Workflows'
import Settings from '@/pages/Settings'
import Monitoring from '@/pages/Monitoring'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/agents" element={<Agents />} />
        <Route path="/workflows" element={<Workflows />} />
        <Route path="/monitoring" element={<Monitoring />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
      <Toaster />
    </Layout>
  )
}

export default App
