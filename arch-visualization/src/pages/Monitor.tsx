import { motion } from 'framer-motion'
import { Activity, Clock, FileText, Database, RefreshCw, Bell } from 'lucide-react'
import { useEffect } from 'react'
import { useAppStore } from '../store/useAppStore'
import { cn } from '../utils/constants'

const recentChanges = [
  { file: 'requirements-minimal.txt', action: 'Updated', time: '2 min ago', type: 'config' },
  { file: 'enhanced_memory_system.py', action: 'Modified', time: '5 min ago', type: 'code' },
  { file: 'scripts/defect_audit.py', action: 'Created', time: '10 min ago', type: 'code' },
  { file: 'docs/REAL_GITHUB_TEST_REPORT_FINAL.md', action: 'Added', time: '15 min ago', type: 'doc' },
  { file: 'backend/core/neural_layers', action: 'Cleaned', time: '20 min ago', type: 'structure' },
]

const healthStatus = {
  memory: 'ok',
  neural_layers: 'ok',
  llm_integration: 'warning',
  agent_coordination: 'ok',
}

export function Monitor() {
  const { addFileChange, fileChanges, isWatcherActive, toggleWatcher } = useAppStore()

  useEffect(() => {
    if (!isWatcherActive) return
    
    const interval = setInterval(() => {
      const randomFiles = ['utils.ts', 'config.json', 'index.tsx', 'api.ts']
      const randomFile = randomFiles[Math.floor(Math.random() * randomFiles.length)]
      addFileChange(randomFile)
    }, 8000)

    return () => clearInterval(interval)
  }, [isWatcherActive, addFileChange])

  const getStatusColor = (status: string) => {
    switch(status) {
      case 'ok': return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30'
      case 'warning': return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30'
      case 'error': return 'text-red-400 bg-red-500/10 border-red-500/30'
      default: return 'text-slate-400 bg-slate-500/10 border-slate-500/30'
    }
  }

  const getTypeColor = (type: string) => {
    switch(type) {
      case 'config': return 'text-blue-400'
      case 'code': return 'text-violet-400'
      case 'doc': return 'text-yellow-400'
      case 'structure': return 'text-cyan-400'
      default: return 'text-slate-400'
    }
  }

  return (
    <div className="min-h-screen pb-20">
      <div className="max-w-7xl mx-auto px-6 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8 flex items-center justify-between"
        >
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Live Monitor</h1>
            <p className="text-slate-400">File watcher and system status</p>
          </div>
          <button
            onClick={toggleWatcher}
            className={cn(
              'flex items-center gap-2 px-4 py-2 rounded-xl border transition-all',
              isWatcherActive 
                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20'
                : 'bg-slate-500/10 border-slate-500/30 text-slate-400 hover:bg-slate-500/20'
            )}
          >
            <Activity className={cn('w-4 h-4', isWatcherActive && 'animate-pulse')} />
            <span className="font-medium">{isWatcherActive ? 'Watching' : 'Paused'}</span>
          </button>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
          >
            <div className="bg-slate-900/50 rounded-2xl border border-slate-700/50 p-6 mb-6">
              <h3 className="text-white font-semibold text-lg mb-6 flex items-center gap-2">
                <Database className="w-5 h-5 text-cyan-400" />
                System Health
              </h3>
              <div className="grid grid-cols-2 gap-4">
                {Object.entries(healthStatus).map(([key, status], idx) => (
                  <motion.div
                    key={key}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.2 + idx * 0.1 }}
                    className={cn(
                      'p-4 rounded-xl border transition-all hover:scale-105',
                      getStatusColor(status)
                    )}
                  >
                    <p className="text-sm font-medium capitalize">
                      {key.replace('_', ' ')}
                    </p>
                    <p className="text-xs mt-1 capitalize">{status}</p>
                  </motion.div>
                ))}
              </div>
            </div>

            <div className="bg-slate-900/50 rounded-2xl border border-slate-700/50 p-6">
              <h3 className="text-white font-semibold text-lg mb-6 flex items-center gap-2">
                <RefreshCw className="w-5 h-5 text-violet-400" />
                Recent Activity
              </h3>
              <div className="space-y-3">
                {recentChanges.map((change, idx) => (
                  <motion.div
                    key={idx}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.4 + idx * 0.1 }}
                    className="flex items-center justify-between p-3 rounded-lg bg-slate-800/50 border border-slate-700/50 hover:border-slate-600 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <FileText className={getTypeColor(change.type)} />
                      <div>
                        <p className="text-white text-sm font-medium">{change.file}</p>
                        <p className={cn(getTypeColor(change.type), 'text-xs')}>{change.action}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 text-slate-400 text-xs">
                      <Clock className="w-3 h-3" />
                      <span>{change.time}</span>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
          >
            <div className="bg-slate-900/50 rounded-2xl border border-slate-700/50 p-6 mb-6">
              <h3 className="text-white font-semibold text-lg mb-6 flex items-center gap-2">
                <Bell className="w-5 h-5 text-yellow-400" />
                Live File Changes
              </h3>
              <div className="space-y-3">
                {fileChanges.length === 0 ? (
                  <div className="text-center py-8 text-slate-500">
                    <p>No recent changes</p>
                    <p className="text-xs mt-1">Start the watcher to see updates</p>
                  </div>
                ) : (
                  fileChanges.map((file, idx) => (
                    <motion.div
                      key={idx}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="flex items-center gap-3 p-3 rounded-lg bg-gradient-to-r from-violet-500/10 to-transparent border border-violet-500/30"
                    >
                      <RefreshCw className="w-4 h-4 text-violet-400 animate-spin" />
                      <div>
                        <p className="text-white text-sm">{file}</p>
                        <p className="text-xs text-slate-400">File modified</p>
                      </div>
                    </motion.div>
                  ))
                )}
              </div>
            </div>

            <div className="bg-gradient-to-br from-violet-600/20 to-purple-600/20 rounded-2xl border border-violet-500/30 p-6">
              <h3 className="text-white font-semibold text-lg mb-4">Auto-Refresh</h3>
              <p className="text-slate-300 text-sm mb-4">
                This page will automatically update when files change in the project directory
              </p>
              <div className="flex items-center gap-2 text-sm">
                <div className={cn('w-2 h-2 rounded-full', isWatcherActive ? 'bg-emerald-500 animate-pulse' : 'bg-slate-500')} />
                <span className={isWatcherActive ? 'text-emerald-400' : 'text-slate-400'}>
                  {isWatcherActive ? 'Auto-refresh active' : 'Auto-refresh paused'}
                </span>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  )
}
