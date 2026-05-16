import { useState, useEffect } from 'react'
import { Activity, AlertTriangle, CheckCircle, Server, Zap, Clock, Bell } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
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
  BarChart,
  Bar,
} from 'recharts'

const systemMetrics = [
  { time: '09:00', cpu: 45, memory: 62, disk: 38 },
  { time: '10:00', cpu: 52, memory: 58, disk: 38 },
  { time: '11:00', cpu: 48, memory: 65, disk: 39 },
  { time: '12:00', cpu: 58, memory: 70, disk: 39 },
  { time: '13:00', cpu: 42, memory: 63, disk: 39 },
  { time: '14:00', cpu: 65, memory: 72, disk: 40 },
  { time: '15:00', cpu: 55, memory: 68, disk: 40 },
]

const requestMetrics = [
  { time: '09:00', requests: 120, errors: 2 },
  { time: '10:00', requests: 230, errors: 5 },
  { time: '11:00', requests: 180, errors: 1 },
  { time: '12:00', requests: 290, errors: 3 },
  { time: '13:00', requests: 245, errors: 0 },
  { time: '14:00', requests: 310, errors: 4 },
  { time: '15:00', requests: 275, errors: 1 },
]

const alerts = [
  { id: 1, level: 'critical', message: 'High CPU usage detected', time: '5 minutes ago', resolved: false },
  { id: 2, level: 'warning', message: 'Memory usage above threshold', time: '12 minutes ago', resolved: false },
  { id: 3, level: 'info', message: 'New agent created successfully', time: '25 minutes ago', resolved: true },
  { id: 4, level: 'warning', message: 'Database query slow', time: '45 minutes ago', resolved: true },
  { id: 5, level: 'critical', message: 'API rate limit exceeded', time: '1 hour ago', resolved: true },
]

export default function Monitoring() {
  const [currentTime, setCurrentTime] = useState(new Date())

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Monitoring</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Monitor system health and performance
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-500">
            Last updated: {currentTime.toLocaleTimeString()}
          </span>
          <Button>
            <Bell className="w-4 h-4 mr-2" />
            Alerts
          </Button>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">CPU Usage</CardTitle>
            <Server className="w-4 h-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">58%</div>
            <div className="h-2 bg-gray-200 rounded-full mt-2">
              <div className="h-2 bg-blue-500 rounded-full" style={{ width: '58%' }} />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Memory</CardTitle>
            <Zap className="w-4 h-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">68%</div>
            <div className="h-2 bg-gray-200 rounded-full mt-2">
              <div className="h-2 bg-purple-500 rounded-full" style={{ width: '68%' }} />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Active Requests</CardTitle>
            <Activity className="w-4 h-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">142</div>
            <p className="text-xs text-gray-500 mt-1">+12 from last minute</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Avg Latency</CardTitle>
            <Clock className="w-4 h-4 text-yellow-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">85ms</div>
            <p className="text-xs text-gray-500 mt-1">-5ms from last hour</p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="system">
        <TabsList>
          <TabsTrigger value="system">System</TabsTrigger>
          <TabsTrigger value="requests">Requests</TabsTrigger>
          <TabsTrigger value="alerts">Alerts</TabsTrigger>
        </TabsList>

        <TabsContent value="system" className="mt-6">
          <div className="grid gap-6 md:grid-cols-2">
            <Card className="col-span-1 md:col-span-2">
              <CardHeader>
                <CardTitle>System Metrics</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={systemMetrics}>
                      <defs>
                        <linearGradient id="colorCpu" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8} />
                          <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                        </linearGradient>
                        <linearGradient id="colorMemory" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.8} />
                          <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis dataKey="time" />
                      <YAxis />
                      <Tooltip />
                      <Area
                        type="monotone"
                        dataKey="cpu"
                        stroke="#3b82f6"
                        fillOpacity={1}
                        fill="url(#colorCpu)"
                      />
                      <Area
                        type="monotone"
                        dataKey="memory"
                        stroke="#8b5cf6"
                        fillOpacity={0.5}
                        fill="url(#colorMemory)"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="requests" className="mt-6">
          <Card className="col-span-1 md:col-span-2">
            <CardHeader>
              <CardTitle>Request Metrics</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={requestMetrics}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis dataKey="time" />
                    <YAxis yAxisId="left" />
                    <YAxis yAxisId="right" orientation="right" />
                    <Tooltip />
                    <Bar yAxisId="left" dataKey="requests" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                    <Bar yAxisId="right" dataKey="errors" fill="#ef4444" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="alerts" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Recent Alerts</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {alerts.map((alert) => (
                  <div key={alert.id} className="flex items-start gap-4 p-4 border rounded-lg">
                    <div className={cn(
                      "mt-1 w-3 h-3 rounded-full",
                      alert.level === 'critical' && "bg-red-500",
                      alert.level === 'warning' && "bg-yellow-500",
                      alert.level === 'info' && "bg-blue-500"
                    )} />
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <p className="font-medium">{alert.message}</p>
                        {alert.resolved ? (
                          <CheckCircle className="w-4 h-4 text-green-500" />
                        ) : (
                          <AlertTriangle className="w-4 h-4 text-yellow-500" />
                        )}
                      </div>
                      <p className="text-sm text-gray-500">{alert.time}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

function cn(...classes: (string | undefined)[]) {
  return classes.filter(Boolean).join(' ')
}
