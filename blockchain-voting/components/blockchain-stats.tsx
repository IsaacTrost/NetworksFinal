"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ChartContainer, ChartTooltip, ChartLegend } from "@/components/ui/chart"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer } from "recharts"
import { Clock, Database, Cpu, Activity } from "lucide-react"
import { fetchBlockchainStats } from "@/lib/api"

// Mock data - would be replaced with real API calls
const blockTimeData = Array.from({ length: 20 }, (_, i) => ({
  time: `${i + 1}h ago`,
  blockTime: 25 + Math.random() * 10,
})).reverse()

const difficultyData = Array.from({ length: 20 }, (_, i) => ({
  time: `${i + 1}h ago`,
  difficulty: 10 + Math.sin(i / 3) * 2 + Math.random(),
})).reverse()

export function BlockchainStats() {
  const [stats, setStats] = useState({
    latestBlock: 1024,
    averageBlockTime: "30.2s",
    currentDifficulty: "12.4",
    activeNodes: 5,
    pendingTransactions: 12,
  })

  // Simulate fetching updated stats
  useEffect(() => {
    // Initial fetch
    fetchBlockchainStats()
      .then((data) => {
        // Make sure data exists before setting state
        if (data && typeof data === "object") {
          setStats(data)
        }
      })
      .catch((error) => {
        console.error("Error fetching blockchain stats:", error)
        // Keep using the default stats on error
      })

    // Set up polling
    const interval = setInterval(() => {
      fetchBlockchainStats()
        .then((data) => {
          if (data && typeof data === "object") {
            setStats(data)
          }
        })
        .catch((error) => {
          console.error("Error fetching blockchain stats:", error)
        })
    }, 30000)

    return () => clearInterval(interval)
  }, [])

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Latest Block</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">#{stats.latestBlock}</div>
            <p className="text-xs text-muted-foreground">Updated just now</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Block Time</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.averageBlockTime}</div>
            <p className="text-xs text-muted-foreground">30s target</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Difficulty</CardTitle>
            <Cpu className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.currentDifficulty}</div>
            <p className="text-xs text-muted-foreground">Adjusts every 10 blocks</p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="blockTime">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="blockTime">Block Time</TabsTrigger>
          <TabsTrigger value="difficulty">Difficulty</TabsTrigger>
        </TabsList>
        <TabsContent value="blockTime" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Block Time (seconds)</CardTitle>
              <CardDescription>Average time between blocks over the last 20 hours</CardDescription>
            </CardHeader>
            <CardContent className="h-[300px]">
              <ChartContainer>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={blockTimeData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis domain={[20, 40]} />
                    <ChartTooltip />
                    <Line
                      type="monotone"
                      dataKey="blockTime"
                      stroke="#2563eb"
                      strokeWidth={2}
                      dot={{ r: 4 }}
                      activeDot={{ r: 6 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
                <ChartLegend>
                  <div className="flex items-center gap-2">
                    <div className="h-3 w-3 rounded-full bg-blue-500" />
                    <span>Block Time</span>
                  </div>
                </ChartLegend>
              </ChartContainer>
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="difficulty" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Mining Difficulty</CardTitle>
              <CardDescription>Network difficulty adjustments over the last 20 hours</CardDescription>
            </CardHeader>
            <CardContent className="h-[300px]">
              <ChartContainer>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={difficultyData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis domain={[8, 14]} />
                    <ChartTooltip />
                    <Line
                      type="monotone"
                      dataKey="difficulty"
                      stroke="#10b981"
                      strokeWidth={2}
                      dot={{ r: 4 }}
                      activeDot={{ r: 6 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
                <ChartLegend>
                  <div className="flex items-center gap-2">
                    <div className="h-3 w-3 rounded-full bg-emerald-500" />
                    <span>Difficulty</span>
                  </div>
                </ChartLegend>
              </ChartContainer>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <div className="grid gap-4 grid-cols-2">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Nodes</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.activeNodes}</div>
            <p className="text-xs text-muted-foreground">Full nodes in the network</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Votes</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.pendingTransactions}</div>
            <p className="text-xs text-muted-foreground">Waiting to be mined</p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
