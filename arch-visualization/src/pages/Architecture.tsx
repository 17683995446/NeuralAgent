import { motion } from 'framer-motion'
import { Folder, FileText, ChevronRight, ChevronDown, Layers } from 'lucide-react'
import { useState } from 'react'
import { layers, cn } from '../utils/constants'

const directories = [
  { name: 'backend', type: 'folder', children: [
    { name: 'core', type: 'folder', children: [
      { name: 'neural_layers', type: 'folder', children: [
        { name: 'neural_embedding_layer.py', type: 'file' },
        { name: 'neural_input_layer.py', type: 'file' },
        { name: 'neural_convolution_layer.py', type: 'file' },
        { name: 'neural_fully_connected_layers.py', type: 'file' },
      ]},
      { name: 'memory', type: 'folder', children: [
        { name: 'enhanced_memory_system.py', type: 'file' },
        { name: 'short_term_memory.py', type: 'file' },
      ]},
      { name: 'agents', type: 'folder' },
    ]},
    { name: 'api', type: 'folder' },
    { name: 'processing', type: 'folder' },
  ]},
  { name: 'docs', type: 'folder' },
  { name: 'tests', type: 'folder' },
  { name: 'scripts', type: 'folder' },
]

function DirectoryItem({ item, depth = 0 }: { item: any; depth?: number }) {
  const [isExpanded, setIsExpanded] = useState(true)
  const Icon = item.type === 'folder' ? (isExpanded ? ChevronDown : ChevronRight) : FileText
  const FolderIcon = item.type === 'folder' ? Folder : FileText

  return (
    <div>
      <button
        onClick={() => item.type === 'folder' && setIsExpanded(!isExpanded)}
        className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-slate-800/50 w-full text-left transition-colors"
        style={{ paddingLeft: `${depth * 16 + 12}px` }}
      >
        {item.type === 'folder' && <Icon className="w-4 h-4 text-slate-500" />}
        <FolderIcon className={item.type === 'folder' ? 'w-4 h-4 text-yellow-400' : 'w-4 h-4 text-blue-400'} />
        <span className="text-sm text-slate-300">{item.name}</span>
      </button>
      {item.children && isExpanded && (
        <div>
          {item.children.map((child: any, idx: number) => (
            <DirectoryItem key={idx} item={child} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  )
}

export function Architecture() {
  return (
    <div className="min-h-screen pb-20">
      <div className="max-w-7xl mx-auto px-6 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-3xl font-bold text-white mb-2">System Architecture</h1>
          <p className="text-slate-400">Explore the 18-layer neural network and directory structure</p>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
            className="lg:col-span-1"
          >
            <div className="bg-slate-900/50 rounded-2xl border border-slate-700/50 overflow-hidden">
              <div className="p-4 border-b border-slate-700/50">
                <h3 className="text-white font-semibold">Directory Structure</h3>
              </div>
              <div className="p-4 max-h-[600px] overflow-y-auto">
                {directories.map((dir, idx) => (
                  <DirectoryItem key={idx} item={dir} />
                ))}
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="lg:col-span-2"
          >
            <div className="bg-slate-900/50 rounded-2xl border border-slate-700/50 p-6">
              <div className="flex items-center gap-3 mb-6">
                <Layers className="w-6 h-6 text-violet-400" />
                <h3 className="text-white font-semibold text-lg">18-Layer Neural Network</h3>
              </div>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {layers.map((layer, index) => (
                  <motion.div
                    key={layer.id}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.3 + index * 0.03 }}
                    className="group relative overflow-hidden rounded-xl border border-slate-700/50 bg-slate-800/30 hover:border-violet-500/50 transition-all"
                  >
                    <div className={cn('absolute inset-0 bg-gradient-to-br opacity-20 group-hover:opacity-30', layer.color)} />
                    <div className="relative p-4">
                      <div className="flex items-start justify-between mb-2">
                        <span className="text-xs text-slate-500 font-mono">Layer {layer.id}</span>
                      </div>
                      <h4 className="text-white font-medium mb-1">{layer.name}</h4>
                      <p className="text-xs text-slate-400">{layer.desc}</p>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  )
}
