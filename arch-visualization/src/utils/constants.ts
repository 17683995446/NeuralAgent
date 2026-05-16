import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export const layers = [
  { id: 1, name: '嵌入层', color: 'from-cyan-500 to-cyan-700', desc: '输入嵌入和转换' },
  { id: 2, name: '输入层', color: 'from-cyan-400 to-cyan-600', desc: '数据归一化和预处理' },
  { id: 3, name: '归一化层', color: 'from-blue-500 to-blue-700', desc: '层归一化和缩放' },
  { id: 4, name: '卷积层', color: 'from-blue-400 to-blue-600', desc: '模式提取和特征学习' },
  { id: 5, name: '池化层', color: 'from-indigo-500 to-indigo-700', desc: '特征压缩和下采样' },
  { id: 6, name: '注意力层', color: 'from-indigo-400 to-indigo-600', desc: '自注意力和聚焦机制' },
  { id: 7, name: '残差层', color: 'from-violet-500 to-violet-700', desc: '残差连接和梯度流动' },
  { id: 8, name: 'Dropout层', color: 'from-violet-400 to-violet-600', desc: '正则化和防止过拟合' },
  { id: 9, name: '全连接层', color: 'from-purple-500 to-purple-700', desc: '全连接密集层' },
  { id: 10, name: '记忆层', color: 'from-purple-400 to-purple-600', desc: '记忆集成和检索' },
  { id: 11, name: '推理层', color: 'from-pink-500 to-pink-700', desc: '逻辑推理和演绎' },
  { id: 12, name: '规划层', color: 'from-pink-400 to-pink-600', desc: '任务规划和步骤生成' },
  { id: 13, name: '输出层', color: 'from-rose-500 to-rose-700', desc: '结果生成和格式化' },
  { id: 14, name: '执行层', color: 'from-rose-400 to-rose-600', desc: '动作执行和编排' },
  { id: 15, name: '反向传播', color: 'from-red-500 to-red-700', desc: '梯度计算和权重更新' },
]

export const modules = [
  { name: '记忆系统', icon: 'Brain', color: 'text-purple-400', bg: 'bg-purple-500/10', border: 'border-purple-500/30' },
  { name: '神经网络层', icon: 'Network', color: 'text-cyan-400', bg: 'bg-cyan-500/10', border: 'border-cyan-500/30' },
  { name: 'LLM集成', icon: 'MessageSquare', color: 'text-green-400', bg: 'bg-green-500/10', border: 'border-green-500/30' },
  { name: 'Agent协调', icon: 'Users', color: 'text-yellow-400', bg: 'bg-yellow-500/10', border: 'border-yellow-500/30' },
  { name: '任务管理', icon: 'ListTodo', color: 'text-orange-400', bg: 'bg-orange-500/10', border: 'border-orange-500/30' },
  { name: '质量保证', icon: 'CheckCircle', color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/30' },
]
