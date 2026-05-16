import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export const layers = [
  { id: 1, name: 'Embedding Layer', color: 'from-cyan-500 to-cyan-700', desc: 'Input embedding and transformation' },
  { id: 2, name: 'Input Layer', color: 'from-cyan-400 to-cyan-600', desc: 'Data normalization and preprocessing' },
  { id: 3, name: 'Normalization Layer', color: 'from-blue-500 to-blue-700', desc: 'Layer normalization and scaling' },
  { id: 4, name: 'Convolution Layer', color: 'from-blue-400 to-blue-600', desc: 'Pattern extraction and feature learning' },
  { id: 5, name: 'Pooling Layer', color: 'from-indigo-500 to-indigo-700', desc: 'Feature compression and downsampling' },
  { id: 6, name: 'Attention Layer', color: 'from-indigo-400 to-indigo-600', desc: 'Self-attention and focus mechanism' },
  { id: 7, name: 'Residual Layer', color: 'from-violet-500 to-violet-700', desc: 'Residual connections and gradient flow' },
  { id: 8, name: 'Dropout Layer', color: 'from-violet-400 to-violet-600', desc: 'Regularization and overfitting prevention' },
  { id: 9, name: 'FC Layer', color: 'from-purple-500 to-purple-700', desc: 'Fully connected dense layers' },
  { id: 10, name: 'Memory Layer', color: 'from-purple-400 to-purple-600', desc: 'Memory integration and retrieval' },
  { id: 11, name: 'Reasoning Layer', color: 'from-pink-500 to-pink-700', desc: 'Logical reasoning and deduction' },
  { id: 12, name: 'Planning Layer', color: 'from-pink-400 to-pink-600', desc: 'Task planning and step generation' },
  { id: 13, name: 'Output Layer', color: 'from-rose-500 to-rose-700', desc: 'Result generation and formatting' },
  { id: 14, name: 'Execution Layer', color: 'from-rose-400 to-rose-600', desc: 'Action execution and orchestration' },
  { id: 15, name: 'Backward Propagation', color: 'from-red-500 to-red-700', desc: 'Gradient computation and weight update' },
]

export const modules = [
  { name: 'Memory System', icon: 'Brain', color: 'text-purple-400', bg: 'bg-purple-500/10', border: 'border-purple-500/30' },
  { name: 'Neural Layers', icon: 'Network', color: 'text-cyan-400', bg: 'bg-cyan-500/10', border: 'border-cyan-500/30' },
  { name: 'LLM Integration', icon: 'MessageSquare', color: 'text-green-400', bg: 'bg-green-500/10', border: 'border-green-500/30' },
  { name: 'Agent Coordination', icon: 'Users', color: 'text-yellow-400', bg: 'bg-yellow-500/10', border: 'border-yellow-500/30' },
  { name: 'Task Management', icon: 'ListTodo', color: 'text-orange-400', bg: 'bg-orange-500/10', border: 'border-orange-500/30' },
  { name: 'Quality Assurance', icon: 'CheckCircle', color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/30' },
]
