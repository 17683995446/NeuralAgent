import { useState, useEffect } from 'react'
import { LayoutDashboard, Activity, Bot, Zap, Clock, TrendingUp, AlertCircle, CheckCircle } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
} from 'recharts'

const sampleMetrics = [
  { time: '09:00', requests: 120, latency: 85 },
  { time: '10:00', requests: 230, latency: 92 },
  { time: '11:00', requests: 180, latency: 78 },
  { time: '12:00', requests: 290, latency: 105 },
  { time: '13:00', requests: 245, latency: 88 },
  { time: '14:00', requests: 310, latency: 95 },
  { time: '15:00', requests: 275, latency: 82 },
]

const recentActivities = [
  { id: 1, agent: 'Researcher', action: 'Completed task', time: '2 minutes ago', status: 'success' },
  { id: 2, agent: 'Writer', action: 'Started task', time: '5 minutes ago', status: 'active' },
  { id: 3, agent: 'Analyzer', action: 'Failed task', time: '12 minutes ago', status: 'error' },
  { id: 4, agent: 'Researcher', action: 'Completed task', time: '15 minutes ago', status: 'success' },
]

export default function Dashboard() {
  const [stats, setStats] = useState({
    totalAgents: 8,
    activeAgents: 5,
    totalTasks: 156,
    avgLatency: '85ms',
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Welcome back! Here's what's happening with your agents.
          </p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline">Export Data</Button>
          <Button>Create Agent</Button>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Agents</CardTitle>
            <Bot className="w-4 h-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalAgents}</div>
            <p className="text-xs text-gray-500 mt-1">+2 from last week</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Active Agents</CardTitle>
            <Activity className="w-4 h-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.activeAgents}</div>
            <p className="text-xs text-gray-500 mt-1">All healthy</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Tasks</CardTitle>
            <Zap className="w-4 h-4 text-yellow-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalTasks}</div>
            <p className="text-xs text-gray-500 mt-1">+42 from last week</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Avg Latency</CardTitle>
            <Clock className="w-4 h-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.avgLatency}</div>
            <p className="text-xs text-gray-500 mt-1">-5ms from last week</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card className="col-span-1 lg:col-span-2">
          <CardHeader>
            <CardTitle>Request Metrics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={sampleMetrics}>
                  <defs>
                    <linearGradient id="colorRequests" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8} />
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="time" />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip />
                  <Area
                    yAxisId="left"
                    type="monotone"
                    dataKey="requests"
                    stroke="#3b82f6"
                    fillOpacity={1}
                    fill="url(#colorRequests)"
                  />
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="latency"
                    stroke="#10b981"
                    strokeWidth={2}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentActivities.map((activity) => (
                <div key={activity.id} className="flex items-start gap-3">
                  <div className={cn(
                    "mt-1 w-2 h-2 rounded-full",
                    activity.status === 'success' && "bg-green-500",
                    activity.status === 'active' && "bg-blue-500",
                    activity.status === 'error' && "bg-red-500"
                  )} />
                  <div className="flex-1">
                    <p className="text-sm font-medium">
                      <span className="font-semibold">{activity.agent}</span> {activity.action}
                    </p>
                    <p className="text-xs text-gray-500">{activity.time}</p>
                  </div>
                  {activity.status === 'success' && <CheckCircle className="w-4 h-4 text-green-500" />}
                  {activity.status === 'error' && <AlertCircle className="w-4 h-4 text-red-500" />}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

function cn(...classes: (string | undefined)[]) {
  return classes.filter(Boolean).join(' ')
}
