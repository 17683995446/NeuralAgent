import { motion } from 'framer-motion'
import { Clock, MessageSquare, Brain, GitBranch, Database, Zap, ArrowRight } from 'lucide-react'
import { cn } from '../utils/constants'

const sequences = [
  {
    title: 'Memory Flow',
    steps: [
      { icon: Brain, color: 'text-violet-400', bg: 'bg-violet-500/20', border: 'border-violet-500/50', label: 'Input received', desc: 'New request arrives' },
      { icon: Database, color: 'text-cyan-400', bg: 'bg-cyan-500/20', border: 'border-cyan-500/50', label: 'Retrieve memory', desc: 'Check short-term & long-term' },
      { icon: MessageSquare, color: 'text-yellow-400', bg: 'bg-yellow-500/20', border: 'border-yellow-500/50', label: 'Context integration', desc: 'Combine with new info' },
      { icon: Brain, color: 'text-purple-400', bg: 'bg-purple-500/20', border: 'border-purple-500/50', label: 'Process & store', desc: 'Update memory system' },
    ]
  },
  {
    title: 'LLM Integration',
    steps: [
      { icon: Zap, color: 'text-yellow-400', bg: 'bg-yellow-500/20', border: 'border-yellow-500/50', label: 'API request', desc: 'Send prompt to LLM' },
      { icon: Brain, color: 'text-cyan-400', bg: 'bg-cyan-500/20', border: 'border-cyan-500/50', label: 'Generate response', desc: 'Model processes input' },
      { icon: GitBranch, color: 'text-violet-400', bg: 'bg-violet-500/20', border: 'border-violet-500/50', label: 'Parse output', desc: 'Extract structured data' },
      { icon: Database, color: 'text-emerald-400', bg: 'bg-emerald-500/20', border: 'border-emerald-500/50', label: 'Store result', desc: 'Save to memory' },
    ]
  },
  {
    title: 'Agent Coordination',
    steps: [
      { icon: Brain, color: 'text-orange-400', bg: 'bg-orange-500/20', border: 'border-orange-500/50', label: 'Task decomposition', desc: 'Break down request' },
      { icon: GitBranch, color: 'text-pink-400', bg: 'bg-pink-500/20', border: 'border-pink-500/50', label: 'Assign roles', desc: 'Distribute subtasks' },
      { icon: MessageSquare, color: 'text-blue-400', bg: 'bg-blue-500/20', border: 'border-blue-500/50', label: 'Sync communication', desc: 'Agents collaborate' },
      { icon: Zap, color: 'text-green-400', bg: 'bg-green-500/20', border: 'border-green-500/50', label: 'Consolidate', desc: 'Combine results' },
    ]
  },
]

export function Sequence() {
  return (
    <div className="min-h-screen pb-20">
      <div className="max-w-7xl mx-auto px-6 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-3xl font-bold text-white mb-2">Sequence Diagrams</h1>
          <p className="text-slate-400">Interactive timeline views of system operations</p>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {sequences.map((sequence, seqIndex) => (
            <motion.div
              key={sequence.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 + seqIndex * 0.1 }}
              className="bg-slate-900/50 rounded-2xl border border-slate-700/50 p-6"
            >
              <h3 className="text-white font-semibold text-lg mb-6 flex items-center gap-2">
                <Clock className="w-5 h-5 text-violet-400" />
                {sequence.title}
              </h3>
              
              <div className="relative">
                <div className="absolute left-4 top-8 bottom-8 w-0.5 bg-slate-700/50" />
                
                <div className="space-y-8">
                  {sequence.steps.map((step, stepIndex) => {
                    const Icon = step.icon
                    return (
                      <motion.div
                        key={stepIndex}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.2 + seqIndex * 0.1 + stepIndex * 0.1 }}
                        className="relative flex gap-4"
                      >
                        <div className={cn(
                          'w-8 h-8 rounded-full flex items-center justify-center shrink-0 z-10',
                          step.bg,
                          'border-2',
                          step.border
                        )}>
                          <Icon className="w-4 h-4" style={{ color: step.color }} />
                        </div>
                        <div className="flex-1">
                          <div className={cn(
                            'p-4 rounded-xl border',
                            step.bg,
                            step.border
                          )}>
                            <h4 className="text-white font-medium">{step.label}</h4>
                            <p className="text-sm text-slate-400">{step.desc}</p>
                          </div>
                        </div>
                      </motion.div>
                    )
                  })}
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="mt-8 bg-slate-900/50 rounded-2xl border border-slate-700/50 p-8"
        >
          <div className="text-center">
            <h3 className="text-xl font-bold text-white mb-4">Complete System Workflow</h3>
            <div className="flex items-center justify-center gap-4 flex-wrap">
              {['Input', 'Analyze', 'Process', 'Generate', 'Execute', 'Feedback'].map((step, idx) => (
                <motion.div
                  key={step}
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.7 + idx * 0.1 }}
                  className="flex items-center gap-2"
                >
                  <div className="px-4 py-2 rounded-full bg-gradient-to-r from-violet-600/20 to-purple-600/20 border border-violet-500/30">
                    <span className="text-sm font-medium text-white">{step}</span>
                  </div>
                  {idx < 5 && <ArrowRight className="w-4 h-4 text-slate-500" />}
                </motion.div>
              ))}
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  )
}
