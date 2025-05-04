"use client"

import type React from "react"
import { useState, useEffect, useRef } from "react"
import { Chart, registerables } from "chart.js"

// Register Chart.js components
Chart.register(...registerables)

interface Candidate {
  id: number
  name: string
  party: string
}

interface Election {
  id: string
  title: string
  description?: string
  candidates: Candidate[]
  status: "active" | "closed"
  closeTime?: string
}

interface TallyData {
  [candidateId: string]: number
}

const ElectionResults: React.FC = () => {
  const [elections, setElections] = useState<Election[]>([])
  const [selectedElection, setSelectedElection] = useState<string>("")
  const [tallyData, setTallyData] = useState<TallyData>({})
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  const [wsConnected, setWsConnected] = useState<boolean>(false)

  const chartRef = useRef<HTMLCanvasElement>(null)
  const chartInstance = useRef<Chart | null>(null)

  useEffect(() => {
    // Fetch available elections
    fetch("/api/elections")
      .then((response) => response.json())
      .then((data) => {
        setElections(data)
      })
      .catch((err) => {
        console.error("Failed to fetch elections:", err)
        setError("Failed to load elections. Please try again later.")
      })
  }, [])

  useEffect(() => {
    // Clean up chart when component unmounts
    return () => {
      if (chartInstance.current) {
        chartInstance.current.destroy()
        chartInstance.current = null
      }
    }
  }, [])

  useEffect(() => {
    if (!selectedElection) {
      setTallyData({})
      return
    }

    // Fetch initial tally data
    fetchTallyData()

    // Set up WebSocket for real-time updates
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:"
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/tally?election_id=${selectedElection}`)

    ws.onopen = () => {
      console.log("Tally WebSocket connected")
      setWsConnected(true)
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        setTallyData(data)
        setLastUpdated(new Date())
      } catch (error) {
        console.error("Error processing tally update:", error)
      }
    }

    ws.onerror = () => {
      console.error("Tally WebSocket error")
      setWsConnected(false)
    }

    ws.onclose = () => {
      console.log("Tally WebSocket closed")
      setWsConnected(false)
    }

    // Polling fallback if WebSocket fails
    const interval = setInterval(() => {
      if (!wsConnected) {
        fetchTallyData()
      }
    }, 10000)

    return () => {
      ws.close()
      clearInterval(interval)
    }
  }, [selectedElection, wsConnected])

  useEffect(() => {
    if (Object.keys(tallyData).length > 0 && selectedElection) {
      updateChart()
    }
  }, [tallyData, selectedElection])

  const fetchTallyData = async () => {
    if (!selectedElection) return

    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch(`/api/tally?election_id=${selectedElection}`)

      if (response.ok) {
        const data = await response.json()
        setTallyData(data)
        setLastUpdated(new Date())
      } else {
        const errorData = await response.json()
        setError(errorData.error || "Failed to fetch tally data")
      }
    } catch (err) {
      console.error("Error fetching tally data:", err)
      setError("An error occurred while fetching tally data")
    } finally {
      setIsLoading(false)
    }
  }

  const updateChart = () => {
    if (!chartRef.current) return

    const election = elections.find((e) => e.id === selectedElection)
    if (!election) return

    // Prepare data for chart
    const labels: string[] = []
    const data: number[] = []
    const backgroundColor: string[] = []
    const borderColor: string[] = []

    // Default colors for candidates
    const colors = [
      "rgba(54, 162, 235, 0.8)",
      "rgba(255, 99, 132, 0.8)",
      "rgba(75, 192, 192, 0.8)",
      "rgba(255, 206, 86, 0.8)",
      "rgba(153, 102, 255, 0.8)",
      "rgba(255, 159, 64, 0.8)",
      "rgba(199, 199, 199, 0.8)",
    ]

    Object.entries(tallyData).forEach(([candidateId, votes], index) => {
      const candidate = election.candidates.find((c) => c.id.toString() === candidateId)
      labels.push(candidate ? candidate.name : `Unknown (${candidateId})`)
      data.push(votes)
      backgroundColor.push(colors[index % colors.length])
      borderColor.push(colors[index % colors.length].replace("0.8", "1"))
    })

    // If chart already exists, update it
    if (chartInstance.current) {
      chartInstance.current.data.labels = labels
      chartInstance.current.data.datasets[0].data = data
      chartInstance.current.data.datasets[0].backgroundColor = backgroundColor
      chartInstance.current.data.datasets[0].borderColor = borderColor
      chartInstance.current.update()
    } else {
      // Create new chart
      chartInstance.current = new Chart(chartRef.current, {
        type: "bar",
        data: {
          labels: labels,
          datasets: [
            {
              label: "Votes",
              data: data,
              backgroundColor: backgroundColor,
              borderColor: borderColor,
              borderWidth: 1,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: {
              beginAtZero: true,
              ticks: {
                precision: 0,
              },
            },
          },
          plugins: {
            legend: {
              display: false,
            },
            tooltip: {
              callbacks: {
                label: (context) => {
                  const votes = context.raw as number
                  return `${votes} vote${votes !== 1 ? "s" : ""}`
                },
              },
            },
          },
        },
      })
    }
  }

  // Calculate total votes
  const totalVotes = Object.values(tallyData).reduce((sum, votes) => sum + votes, 0)

  // Get the selected election object
  const election = elections.find((e) => e.id === selectedElection)

  return (
    <div className="card">
      <div className="card-header">
        <h2 className="card-title">Election Results</h2>
        <p className="card-description">Real-time voting results from the blockchain</p>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      <div className="form-group">
        <label htmlFor="election-select" className="form-label">
          Select Election
        </label>
        <select
          id="election-select"
          className="form-select"
          value={selectedElection}
          onChange={(e) => setSelectedElection(e.target.value)}
        >
          <option value="">Select an election</option>
          {elections.map((election) => (
            <option key={election.id} value={election.id}>
              {election.title}
            </option>
          ))}
        </select>
      </div>

      {election && (
        <div className="mb-4">
          <h3 className="text-lg font-semibold">{election.title}</h3>
          <div className="flex items-center gap-2 mt-2">
            <span className={`badge ${election.status === "active" ? "badge-success" : "badge-warning"}`}>
              {election.status === "active" ? "Active" : "Closed"}
            </span>
            {wsConnected && <span className="badge badge-success">Live Updates</span>}
          </div>
        </div>
      )}

      {isLoading ? (
        <div className="text-center p-4">
          <div className="spinner"></div>
          <p className="mt-2 text-muted">Loading results...</p>
        </div>
      ) : selectedElection ? (
        Object.keys(tallyData).length > 0 ? (
          <>
            <div className="chart-container">
              <canvas ref={chartRef}></canvas>
            </div>

            <div className="mt-4">
              <h4 className="mb-2 font-semibold">Detailed Results</h4>
              <div className="space-y-2">
                {Object.entries(tallyData)
                  .sort(([, a], [, b]) => b - a) // Sort by votes (descending)
                  .map(([candidateId, votes]) => {
                    const candidate = election?.candidates.find((c) => c.id.toString() === candidateId)
                    return (
                      <div key={candidateId} className="flex justify-between items-center p-2 border-b">
                        <div>
                          <p className="font-medium">{candidate?.name || `Unknown (${candidateId})`}</p>
                          {candidate && <p className="text-sm text-muted">{candidate.party}</p>}
                        </div>
                        <div className="text-right">
                          <p className="font-bold">
                            {votes} vote{votes !== 1 ? "s" : ""}
                          </p>
                          <p className="text-sm text-muted">
                            {totalVotes > 0 ? Math.round((votes / totalVotes) * 100) : 0}%
                          </p>
                        </div>
                      </div>
                    )
                  })}
              </div>

              <div className="mt-4 text-right text-muted">
                <p>Total votes: {totalVotes}</p>
                {lastUpdated && <p>Last updated: {lastUpdated.toLocaleTimeString()}</p>}
              </div>
            </div>
          </>
        ) : (
          <div className="text-center p-4 text-muted">No votes have been cast yet for this election.</div>
        )
      ) : (
        <div className="text-center p-4 text-muted">Select an election to view results.</div>
      )}
    </div>
  )
}

export default ElectionResults
