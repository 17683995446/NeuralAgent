import { useState } from 'react'
import { Plus, MoreVertical, Pencil, Trash2, Play, Square, Bot, Activity, Zap } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

const sampleAgents = [
  {
    id: 'agent-1',
    name: 'Researcher',
    type: 'Research',
    status: 'running',
    tasksCompleted: 42,
    avgResponseTime: '1.2s',
    lastActive: 'Just now',
    description: 'Research and gather information from various sources',
  },
  {
    id: 'agent-2',
    name: 'Writer',
    type: 'Creative',
    status: 'idle',
    tasksCompleted: 28,
    avgResponseTime: '0.8s',
    lastActive: '5 minutes ago',
    description: 'Write creative content and stories',
  },
  {
    id: 'agent-3',
    name: 'Analyzer',
    type: 'Analysis',
    status: 'error',
    tasksCompleted: 15,
    avgResponseTime: '0.5s',
    lastActive: '12 minutes ago',
    description: 'Analyze data and generate insights',
  },
  {
    id: 'agent-4',
    name: 'Coder',
    type: 'Development',
    status: 'running',
    tasksCompleted: 34,
    avgResponseTime: '1.5s',
    lastActive: '2 minutes ago',
    description: 'Generate and review code',
  },
]

const agentTypes = [
  { label: 'Research', value: 'research' },
  { label: 'Creative', value: 'creative' },
  { label: 'Analysis', value: 'analysis' },
  { label: 'Development', value: 'development' },
  { label: 'Support', value: 'support' },
]

export default function Agents() {
  const [agents, setAgents] = useState(sampleAgents)
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')

  const filteredAgents = agents.filter(agent =>
    agent.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    agent.type.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const toggleAgentStatus = (agentId: string) => {
    setAgents(agents.map(agent =>
      agent.id === agentId
        ? { ...agent, status: agent.status === 'running' ? 'idle' : 'running' }
        : agent
    ))
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'bg-green-500'
      case 'idle':
        return 'bg-gray-400'
      case 'error':
        return 'bg-red-500'
      default:
        return 'bg-gray-400'
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Agents</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Manage and monitor your AI agents
          </p>
        </div>
        <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              Create Agent
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create New Agent</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Agent Name</label>
                <Input placeholder="e.g. Researcher" />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Agent Type</label>
                <Select>
                  <SelectTrigger>
                    <SelectValue placeholder="Select type" />
                  </SelectTrigger>
                  <SelectContent>
                    {agentTypes.map(type => (
                      <SelectItem key={type.value} value={type.value}>
                        {type.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Description</label>
                <Input placeholder="Describe what this agent does" />
              </div>
              <div className="flex justify-end gap-3 pt-4">
                <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={() => setIsCreateDialogOpen(false)}>
                  Create Agent
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <div className="flex gap-4">
        <Input
          placeholder="Search agents..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="max-w-sm"
        />
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-2">
        {filteredAgents.map((agent) => (
          <Card key={agent.id}>
            <CardHeader className="pb-4">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center">
                    <Bot className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div>
                    <CardTitle className="text-lg">{agent.name}</CardTitle>
                    <p className="text-sm text-gray-500">{agent.type}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <div className="flex items-center gap-1.5">
                    <div className={cn("w-2 h-2 rounded-full", getStatusColor(agent.status))} />
                    <span className="text-sm capitalize">{agent.status}</span>
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                {agent.description}
              </p>
              
              <div className="grid grid-cols-3 gap-4 mb-4">
                <div>
                  <p className="text-sm text-gray-500">Tasks</p>
                  <p className="text-lg font-semibold">{agent.tasksCompleted}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Avg Time</p>
                  <p className="text-lg font-semibold">{agent.avgResponseTime}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Last Active</p>
                  <p className="text-lg font-semibold text-xs">{agent.lastActive}</p>
                </div>
              </div>

              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  className="flex-1"
                  onClick={() => toggleAgentStatus(agent.id)}
                >
                  {agent.status === 'running' ? (
                    <><Square className="w-4 h-4 mr-2" /> Stop</>
                  ) : (
                    <><Play className="w-4 h-4 mr-2" /> Start</>
                  )}
                </Button>
                <Button variant="ghost" size="icon">
                  <Pencil className="w-4 h-4" />
                </Button>
                <Button variant="ghost" size="icon">
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}

function cn(...classes: (string | undefined)[]) {
  return classes.filter(Boolean).join(' ')
}
