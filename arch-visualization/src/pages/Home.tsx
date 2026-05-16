import { motion } from 'framer-motion'
import { Layers, Zap, GitBranch, ArrowRight, Clock } from 'lucide-react'
import { useAppStore } from '../store/useAppStore'
import { modules } from '../utils/constants'
import { cn } from '../utils/constants'

const stats = [
  { label: '总文件数', value: '145', color: 'text-cyan-400', bg: 'from-cyan-500/20 to-transparent' },
  { label: '代码行数', value: '39,663', color: 'text-violet-400', bg: 'from-violet-500/20 to-transparent' },
  { label: '核心模块', value: '31', color: 'text-purple-400', bg: 'from-purple-500/20 to-transparent' },
]

export function Home() {
  const { setRoute } = useAppStore()

  return (
    <div className="min-h-screen pb-20">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="relative mb-12 pt-8"
      >
        <div className="absolute inset-0 bg-gradient-to-b from-violet-600/20 via-transparent to-transparent pointer-events-none" />
        <div className="relative max-w-5xl mx-auto px-6">
          <div className="text-center mb-12">
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: 0.1 }}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-violet-500/10 border border-violet-500/30 mb-6"
            >
              <Zap className="w-4 h-4 text-yellow-400" />
              <span className="text-sm text-violet-300">v2.0 架构统一版</span>
            </motion.div>
            <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold text-white mb-6 tracking-tight">
              NeuralAgent
              <span className="block bg-gradient-to-r from-cyan-400 via-violet-400 to-purple-400 bg-clip-text text-transparent">
                架构可视化
              </span>
            </h1>
            <p className="text-xl text-slate-300 max-w-2xl mx-auto">
              探索18层神经网络架构、模块关系和系统工作流程
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-12">
            {stats.map((stat, index) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 + index * 0.1 }}
                className="relative overflow-hidden rounded-2xl bg-gradient-to-br bg-slate-800/50 border border-slate-700/50 p-6"
              >
                <div className={cn('absolute inset-0 bg-gradient-to-r', stat.bg)} />
                <div className="relative">
                  <p className="text-sm text-slate-400 mb-1">{stat.label}</p>
                  <p className={cn('text-3xl font-bold', stat.color)}>{stat.value}</p>
                </div>
              </motion.div>
            ))}
          </div>

          <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
            {modules.map((module, index) => (
              <motion.button
                key={module.name}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 + index * 0.05 }}
                onClick={() => setRoute('/architecture')}
                className={cn(
                  'group relative overflow-hidden rounded-2xl p-6 text-left transition-all duration-300',
                  module.bg,
                  'border',
                  module.border,
                  'hover:scale-105 hover:shadow-2xl'
                )}
              >
                <div className="flex items-center gap-3 mb-3">
                  <div className={module.color}>
                    <Layers className="w-6 h-6" />
                  </div>
                  <h3 className="font-semibold text-white">{module.name}</h3>
                </div>
                <div className="flex items-center gap-2 text-sm text-slate-400">
                  <span>查看架构</span>
                  <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
                </div>
              </motion.button>
            ))}
          </div>
        </div>
      </motion.div>

      <div className="max-w-5xl mx-auto px-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <motion.button
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.6 }}
            onClick={() => setRoute('/flow')}
            className="group relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700 p-8 text-left hover:border-cyan-500/50 transition-all"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
            <div className="relative">
              <GitBranch className="w-8 h-8 text-cyan-400 mb-3" />
              <h3 className="text-xl font-bold text-white mb-2">数据流</h3>
              <p className="text-slate-400">查看数据如何通过神经层流动</p>
            </div>
          </motion.button>

          <motion.button
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.7 }}
            onClick={() => setRoute('/sequence')}
            className="group relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700 p-8 text-left hover:border-violet-500/50 transition-all"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-violet-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
            <div className="relative">
              <Clock className="w-8 h-8 text-violet-400 mb-3" />
              <h3 className="text-xl font-bold text-white mb-2">时序图</h3>
              <p className="text-slate-400">查看模块的交互序列</p>
            </div>
          </motion.button>
        </div>
      </div>
    </div>
  )
}
