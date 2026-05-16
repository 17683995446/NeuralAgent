import { motion } from 'framer-motion'
import { Home, Layers, GitBranch, Clock, Activity } from 'lucide-react'
import { useAppStore } from '../store/useAppStore'
import { cn } from '../utils/constants'

const navItems = [
  { path: '/', icon: Home, label: 'Home' },
  { path: '/architecture', icon: Layers, label: 'Architecture' },
  { path: '/flow', icon: GitBranch, label: 'Flow' },
  { path: '/sequence', icon: Clock, label: 'Sequence' },
  { path: '/monitor', icon: Activity, label: 'Monitor' },
]

export function Navigation() {
  const { currentRoute, setRoute } = useAppStore()

  return (
    <nav className="fixed left-0 top-0 h-screen w-16 sm:w-64 bg-slate-900/80 backdrop-blur-xl border-r border-slate-700/50 z-50">
      <div className="flex flex-col h-full">
        <div className="p-4 sm:p-6 border-b border-slate-700/50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-purple-700 flex items-center justify-center">
              <Layers className="w-5 h-5 text-white" />
            </div>
            <div className="hidden sm:block">
              <h1 className="font-bold text-white text-lg">NeuralAgent</h1>
              <p className="text-xs text-slate-400">Architecture View</p>
            </div>
          </div>
        </div>

        <div className="flex-1 p-2 sm:p-4 space-y-1">
          {navItems.map((item, index) => {
            const Icon = item.icon
            const isActive = currentRoute === item.path

            return (
              <motion.button
                key={item.path}
                initial={{ x: -20, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                transition={{ delay: index * 0.05 }}
                onClick={() => setRoute(item.path)}
                className={cn(
                  'w-full flex items-center gap-3 px-3 sm:px-4 py-3 rounded-xl transition-all duration-200',
                  isActive
                    ? 'bg-gradient-to-r from-violet-600/20 to-purple-600/20 border border-violet-500/50 text-violet-300'
                    : 'text-slate-400 hover:bg-slate-800/50 hover:text-white'
                )}
              >
                <Icon className="w-5 h-5" />
                <span className="hidden sm:block font-medium">{item.label}</span>
              </motion.button>
            )
          })}
        </div>

        <div className="p-4 border-t border-slate-700/50">
          <div className="hidden sm:block">
            <p className="text-xs text-slate-500 mb-2">Status</p>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-sm text-emerald-400">System Active</span>
            </div>
          </div>
        </div>
      </div>
    </nav>
  )
}
