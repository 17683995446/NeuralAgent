import { useState, useCallback, useRef } from 'react'
import ReactFlow, {
  ReactFlowProvider,
  addEdge,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  Handle,
  Position,
  Node,
  Edge,
  Connection,
  MarkerType,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { Plus, Play, Save, Trash2, Workflow } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'

const CustomNode = ({ data, selected }: { data: any; selected: boolean }) => {
  return (
    <div
      className={cn(
        "px-4 py-3 rounded-lg border-2 shadow-sm min-w-[150px]",
        selected
          ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
          : "border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800"
      )}
    >
      <Handle type="target" position={Position.Top} />
      <div className="flex items-center gap-2">
        <div className={cn(
          "w-8 h-8 rounded-full flex items-center justify-center",
          data.type === 'agent' && "bg-blue-100 text-blue-600",
          data.type === 'condition' && "bg-yellow-100 text-yellow-600",
          data.type === 'action' && "bg-green-100 text-green-600",
          data.type === 'start' && "bg-purple-100 text-purple-600",
          data.type === 'end' && "bg-red-100 text-red-600"
        )}>
          {data.icon || '📦'}
        </div>
        <div>
          <p className="font-medium text-sm">{data.label}</p>
          <p className="text-xs text-gray-500">{data.type}</p>
        </div>
      </div>
      <Handle type="source" position={Position.Bottom} />
    </div>
  )
}

const nodeTypes = {
  custom: CustomNode,
}

const initialNodes: Node[] = [
  {
    id: '1',
    type: 'custom',
    position: { x: 250, y: 50 },
    data: { label: 'Start', type: 'start', icon: '🚀' },
  },
  {
    id: '2',
    type: 'custom',
    position: { x: 250, y: 150 },
    data: { label: 'Research', type: 'agent', icon: '🔍' },
  },
  {
    id: '3',
    type: 'custom',
    position: { x: 250, y: 250 },
    data: { label: 'Analyze', type: 'condition', icon: '⚡' },
  },
  {
    id: '4',
    type: 'custom',
    position: { x: 250, y: 350 },
    data: { label: 'End', type: 'end', icon: '✅' },
  },
]

const initialEdges: Edge[] = [
  { id: 'e1-2', source: '1', target: '2', animated: true, markerEnd: { type: MarkerType.ArrowClosed } },
  { id: 'e2-3', source: '2', target: '3', animated: true, markerEnd: { type: MarkerType.ArrowClosed } },
  { id: 'e3-4', source: '3', target: '4', animated: true, markerEnd: { type: MarkerType.ArrowClosed } },
]

const nodeTemplates = [
  { type: 'agent', label: 'Agent', icon: '🤖' },
  { type: 'condition', label: 'Condition', icon: '❓' },
  { type: 'action', label: 'Action', icon: '⚡' },
]

function WorkflowEditor() {
  const reactFlowWrapper = useRef<HTMLDivElement>(null)
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)
  const [reactFlowInstance, setReactFlowInstance] = useState<any>(null)
  const [workflowName, setWorkflowName] = useState('My Workflow')

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge({ ...params, animated: true, markerEnd: { type: MarkerType.ArrowClosed } }, eds)),
    [setEdges]
  )

  const addNode = (type: string, label: string, icon: string) => {
    const newNode: Node = {
      id: `node-${Date.now()}`,
      type: 'custom',
      position: { x: 250, y: 200 + nodes.length * 100 },
      data: { label, type, icon },
    }
    setNodes((nds) => nds.concat(newNode))
  }

  const onDragStart = (event: React.DragEvent, nodeType: string, label: string, icon: string) => {
    event.dataTransfer.setData('application/reactflow/type', nodeType)
    event.dataTransfer.setData('application/reactflow/label', label)
    event.dataTransfer.setData('application/reactflow/icon', icon)
    event.dataTransfer.effectAllowed = 'move'
  }

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault()
    event.dataTransfer.dropEffect = 'move'
  }, [])

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault()
      const type = event.dataTransfer.getData('application/reactflow/type')
      const label = event.dataTransfer.getData('application/reactflow/label')
      const icon = event.dataTransfer.getData('application/reactflow/icon')

      if (typeof type === 'undefined' || !type) {
        return
      }

      const position = reactFlowInstance.screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      })

      const newNode: Node = {
        id: `node-${Date.now()}`,
        type: 'custom',
        position,
        data: { label, type, icon },
      }

      setNodes((nds) => nds.concat(newNode))
    },
    [reactFlowInstance, setNodes]
  )

  return (
    <div className="h-[calc(100vh-200px)] flex gap-6">
      <div className="w-64 space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Properties</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Workflow Name</label>
                <Input
                  value={workflowName}
                  onChange={(e) => setWorkflowName(e.target.value)}
                />
              </div>
              <div className="flex gap-2">
                <Button className="flex-1">
                  <Save className="w-4 h-4 mr-2" />
                  Save
                </Button>
              </div>
              <Button variant="outline" className="w-full">
                <Play className="w-4 h-4 mr-2" />
                Run
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Add Nodes</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {nodeTemplates.map((template) => (
                <div
                  key={template.type}
                  className="flex items-center gap-2 p-3 border rounded-lg cursor-grab hover:bg-gray-50 dark:hover:bg-gray-700"
                  draggable
                  onDragStart={(event) => onDragStart(event, template.type, template.label, template.icon)}
                >
                  <span className="text-xl">{template.icon}</span>
                  <span className="text-sm font-medium">{template.label}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="flex-1" ref={reactFlowWrapper}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onInit={setReactFlowInstance}
          onDrop={onDrop}
          onDragOver={onDragOver}
          nodeTypes={nodeTypes}
          fitView
        >
          <Background />
          <Controls />
        </ReactFlow>
      </div>
    </div>
  )
}

export default function Workflows() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Workflows</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Create and manage automated workflows
          </p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline">Load Workflow</Button>
          <Button>
            <Plus className="w-4 h-4 mr-2" />
            New Workflow
          </Button>
        </div>
      </div>

      <ReactFlowProvider>
        <WorkflowEditor />
      </ReactFlowProvider>
    </div>
  )
}

function cn(...classes: (string | undefined)[]) {
  return classes.filter(Boolean).join(' ')
}
