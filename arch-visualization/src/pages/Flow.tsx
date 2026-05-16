import { motion } from 'framer-motion'
import { ArrowRight, Database, Brain, Layers, Zap } from 'lucide-react'
import { layers, cn } from '../utils/constants'

export function Flow() {
  return (
    <div className="min-h-screen pb-20">
      <div className="max-w-7xl mx-auto px-6 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-3xl font-bold text-white mb-2">Data Flow</h1>
          <p className="text-slate-400">Visualize the complete data processing pipeline</p>
        </motion.div>

        <div className="space-y-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-slate-900/50 rounded-2xl border border-slate-700/50 p-6"
          >
            <h3 className="text-white font-semibold text-lg mb-6 flex items-center gap-2">
              <Zap className="w-5 h-5 text-yellow-400" />
              Input Processing Pipeline
            </h3>
            
            <div className="flex flex-col items-center space-y-4">
              {layers.slice(0, 6).map((layer, index) => (
                <motion.div
                  key={layer.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.2 + index * 0.05 }}
                  className="flex items-center w-full"
                >
                  <div className="flex-1">
                    <div className="group relative">
                      <div className={cn('px-4 py-3 rounded-xl border bg-gradient-to-r', layer.color, 'border-opacity-30')}>
                        <span className="text-white font-medium">{layer.name}</span>
                        <p className="text-xs text-white/70 mt-1">{layer.desc}</p>
                      </div>
                    </div>
                  </div>
                  {index < 5 && (
                    <div className="mx-4">
                      <ArrowRight className="w-5 h-5 text-slate-500" />
                    </div>
                  )}
                </motion.div>
              ))}
            </div>
          </motion.div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.5 }}
              className="bg-slate-900/50 rounded-2xl border border-slate-700/50 p-6"
            >
              <h3 className="text-white font-semibold text-lg mb-6 flex items-center gap-2">
                <Brain className="w-5 h-5 text-violet-400" />
                Neural Processing
              </h3>
              <div className="space-y-3">
                {layers.slice(6, 10).map((layer, index) => (
                  <motion.div
                    key={layer.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.6 + index * 0.1 }}
                    className="flex items-center gap-3 p-3 rounded-lg bg-slate-800/50 border border-slate-700/50"
                  >
                    <Layers className="w-5 h-5 text-violet-400" />
                    <div>
                      <p className="text-white text-sm font-medium">{layer.name}</p>
                      <p className="text-xs text-slate-400">{layer.desc}</p>
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.6 }}
              className="bg-slate-900/50 rounded-2xl border border-slate-700/50 p-6"
            >
              <h3 className="text-white font-semibold text-lg mb-6 flex items-center gap-2">
                <Database className="w-5 h-5 text-cyan-400" />
                Output & Execution
              </h3>
              <div className="space-y-3">
                {layers.slice(10).map((layer, index) => (
                  <motion.div
                    key={layer.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.8 + index * 0.1 }}
                    className="flex items-center gap-3 p-3 rounded-lg bg-slate-800/50 border border-slate-700/50"
                  >
                    <Database className="w-5 h-5 text-cyan-400" />
                    <div>
                      <p className="text-white text-sm font-medium">{layer.name}</p>
                      <p className="text-xs text-slate-400">{layer.desc}</p>
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          </div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1 }}
            className="bg-gradient-to-br from-violet-600/20 to-purple-600/20 rounded-2xl border border-violet-500/30 p-8 text-center"
          >
            <Zap className="w-12 h-12 text-violet-400 mx-auto mb-4" />
            <h3 className="text-white text-xl font-bold mb-2">Complete Agent Workflow</h3>
            <p className="text-slate-300 max-w-2xl mx-auto">
              From raw input through 18 processing layers to final execution and feedback loop
            </p>
          </motion.div>
        </div>
      </div>
    </div>
  )
}
