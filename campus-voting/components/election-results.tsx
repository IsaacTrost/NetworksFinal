"use client"

import { useState, useEffect } from "react"
import { BarChart } from "@/components/ui/chart"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import type { ElectionData } from "@/lib/types"
import { formatDistanceToNow } from "date-fns"

interface ElectionResultsProps {
  elections: ElectionData[]
}

export default function ElectionResults({ elections }: ElectionResultsProps) {
  const [selectedElectionId, setSelectedElectionId] = useState<string>("")
  const [tallyData, setTallyData] = useState<{ name: string; votes: number; party: string }[]>([])
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [wsConnected, setWsConnected] = useState(false)

  // Get the selected election
  const selectedElection = selectedElectionId ? elections.find((e) => e.id === selectedElectionId) : null

  // Fetch tally data when election selection changes
  useEffect(() => {
    if (!selectedElectionId) {
      setTallyData([])
      return
    }

    const fetchTallyData = async () => {
      setIsLoading(true)
      setError(null)

      try {
        const response = await fetch(`/api/tally?election_id=${selectedElectionId}`)

        if (response.ok) {
          const data = await response.json()
          updateTallyData(data)
        } else {
          const errorData = await response.json()
          setError(errorData.error || "Failed to fetch tally data")
        }
      } catch (error) {
        console.error("Error fetching tally data:", error)
        setError("An error occurred while fetching tally data")
      } finally {
        setIsLoading(false)
      }
    }

    fetchTallyData()

    // Set up WebSocket for real-time tally updates
    const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:"
    const ws = new WebSocket(`${wsProtocol}//${window.location.host}/ws/tally?election_id=${selectedElectionId}`)

    ws.onopen = () => {
      console.log("Tally WebSocket connected")
      setWsConnected(true)
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        console.log("Tally update received:", data)
        updateTallyData(data)
      } catch (error) {
        console.error("Error processing tally update:", error)
      }
    }

    ws.onerror = (error) => {
      console.error("Tally WebSocket error:", error)
      setWsConnected(false)
    }

    ws.onclose = () => {
      console.log("Tally WebSocket closed")
      setWsConnected(false)
    }

    // Polling fallback if WebSocket fails
    let pollInterval: NodeJS.Timeout | null = null

    if (!wsConnected) {
      pollInterval = setInterval(fetchTallyData, 10000) // Poll every 10 seconds
    }

    return () => {
      ws.close()
      if (pollInterval) clearInterval(pollInterval)
    }
  }, [selectedElectionId, selectedElection, wsConnected])

  // Helper function to update tally data
  const updateTallyData = (data: Record<string, number>) => {
    // Transform the data for the chart
    const formattedData = Object.entries(data)
      .map(([candidateId, votes]) => {
        const candidate = selectedElection?.candidates.find((c) => c.id.toString() === candidateId)

        return {
          name: candidate?.name || `Unknown (${candidateId})`,
          party: candidate?.party || "Unknown",
          votes: votes as number,
        }
      })
      .sort((a, b) => b.votes - a.votes) // Sort by votes descending

    setTallyData(formattedData)
    setLastUpdated(new Date())
  }

  // Calculate total votes
  const totalVotes = tallyData.reduce((sum, candidate) => sum + candidate.votes, 0)

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Election Results</CardTitle>
        <CardDescription>Real-time voting results from the blockchain</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="mb-6">
          <Select value={selectedElectionId} onValueChange={setSelectedElectionId}>
            <SelectTrigger>
              <SelectValue placeholder="Select an election" />
            </SelectTrigger>
            <SelectContent>
              {elections.map((election) => (
                <SelectItem key={election.id} value={election.id}>
                  {election.title}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {selectedElection && (
          <div className="mb-4">
            <h3 className="text-lg font-semibold">{selectedElection.title}</h3>
            <div className="flex items-center gap-2 mt-1">
              <Badge variant={selectedElection.status === "active" ? "success" : "secondary"}>
                {selectedElection.status === "active" ? "Active" : "Closed"}
              </Badge>
              {selectedElection.closeTime && (
                <p className="text-sm text-muted-foreground">
                  {selectedElection.status === "active"
                    ? `Closes ${formatDistanceToNow(new Date(selectedElection.closeTime))}`
                    : `Closed ${formatDistanceToNow(new Date(selectedElection.closeTime))} ago`}
                </p>
              )}
            </div>
            <div className="mt-2">
              <Badge variant={wsConnected ? "outline" : "secondary"} className="text-xs">
                {wsConnected ? "Live Updates" : "Polling Updates"}
              </Badge>
            </div>
          </div>
        )}

        {isLoading ? (
          <div className="flex justify-center items-center h-80">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
          </div>
        ) : error ? (
          <Alert variant="destructive">
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        ) : tallyData.length > 0 ? (
          <div className="h-80">
            <BarChart
              data={tallyData}
              index="name"
              categories={["votes"]}
              colors={["#3b82f6"]}
              valueFormatter={(value) => `${value} vote${value !== 1 ? "s" : ""}`}
              yAxisWidth={48}
            />
          </div>
        ) : selectedElectionId ? (
          <div className="text-center py-12 text-muted-foreground">No votes have been cast yet for this election.</div>
        ) : (
          <div className="text-center py-12 text-muted-foreground">Select an election to view results.</div>
        )}

        {tallyData.length > 0 && (
          <div className="mt-6 space-y-4">
            <h4 className="font-medium">Detailed Results</h4>
            <div className="space-y-2">
              {tallyData.map((candidate, index) => (
                <div key={index} className="flex justify-between items-center">
                  <div>
                    <p className="font-medium">{candidate.name}</p>
                    <p className="text-sm text-muted-foreground">{candidate.party}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-bold">
                      {candidate.votes} vote{candidate.votes !== 1 ? "s" : ""}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {totalVotes > 0 ? Math.round((candidate.votes / totalVotes) * 100) : 0}%
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>

      {lastUpdated && (
        <CardFooter>
          <p className="text-sm text-muted-foreground">
            Last updated: {lastUpdated.toLocaleTimeString()}
            {totalVotes > 0 && ` • Total votes: ${totalVotes}`}
          </p>
        </CardFooter>
      )}
    </Card>
  )
}
