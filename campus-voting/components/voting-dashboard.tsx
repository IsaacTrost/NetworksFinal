"use client"

import { useState, useEffect } from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import VoteForm from "@/components/vote-form"
import ElectionResults from "@/components/election-results"
import BlockExplorer from "@/components/block-explorer"
import NetworkStatus from "@/components/network-status"
import type { ElectionData, BlockchainStatus } from "@/lib/types"

export default function VotingDashboard() {
  // Constants from your blockchain implementation
  const DEFAULT_DIFFICULTY = 16
  const [elections, setElections] = useState<ElectionData[]>([])
  const [blockchainStatus, setBlockchainStatus] = useState<BlockchainStatus>({
    currentHeight: 0,
    peerCount: 0,
    difficulty: DEFAULT_DIFFICULTY,
    lastBlockTime: "",
    hashRate: 0,
  })
  const [isConnected, setIsConnected] = useState(false)
  const [wsError, setWsError] = useState<string | null>(null)

  useEffect(() => {
    // Fetch available elections
    const fetchElections = async () => {
      try {
        const response = await fetch("/api/elections")
        if (response.ok) {
          const data = await response.json()
          setElections(data)
        }
      } catch (error) {
        console.error("Failed to fetch elections:", error)
      }
    }

    fetchElections()

    // Set up WebSocket connection for real-time updates
    const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:"
    const ws = new WebSocket(`${wsProtocol}//${window.location.host}/ws/blockchain`)

    ws.onopen = () => {
      setIsConnected(true)
      setWsError(null)
      console.log("WebSocket connection established")
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        console.log("WebSocket message received:", data)

        if (data.type === "BLOCKCHAIN_STATUS") {
          setBlockchainStatus(data.payload)
        } else if (data.type === "NEW_BLOCK") {
          // Update blockchain status when a new block is mined
          setBlockchainStatus((prev) => ({
            ...prev,
            currentHeight: data.payload.index,
            lastBlockTime: new Date(data.payload.timestamp * 1000).toLocaleString(),
            difficulty: data.payload.difficulty,
          }))

          // Refresh elections data when a new block is mined
          fetchElections()
        }
      } catch (error) {
        console.error("Error processing WebSocket message:", error)
      }
    }

    ws.onerror = (error) => {
      console.error("WebSocket error:", error)
      setWsError("Failed to connect to blockchain node. Please refresh the page.")
      setIsConnected(false)
    }

    ws.onclose = (event) => {
      console.log("WebSocket connection closed:", event)
      setIsConnected(false)

      // Attempt to reconnect after a delay
      setTimeout(() => {
        console.log("Attempting to reconnect WebSocket...")
        // The effect cleanup will run and the effect will run again, creating a new connection
      }, 5000)
    }

    // Polling fallback for blockchain status if WebSocket fails
    let pollInterval: NodeJS.Timeout | null = null

    if (!isConnected) {
      pollInterval = setInterval(async () => {
        try {
          const response = await fetch("/api/status")
          if (response.ok) {
            const data = await response.json()
            setBlockchainStatus(data)
          }
        } catch (error) {
          console.error("Failed to poll blockchain status:", error)
        }
      }, 10000) // Poll every 10 seconds
    }

    return () => {
      ws.close()
      if (pollInterval) clearInterval(pollInterval)
    }
  }, [isConnected])

  return (
    <div className="container mx-auto py-6 px-4">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-center">Blockchain Voting System</h1>
        <p className="text-center text-muted-foreground mt-2">Secure, transparent, and verifiable campus elections</p>
      </header>

      <NetworkStatus status={blockchainStatus} isConnected={isConnected} />

      {wsError && <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">{wsError}</div>}

      <Tabs defaultValue="vote" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="vote">Cast Vote</TabsTrigger>
          <TabsTrigger value="results">Election Results</TabsTrigger>
          <TabsTrigger value="explorer">Block Explorer</TabsTrigger>
        </TabsList>

        <TabsContent value="vote">
          <VoteForm elections={elections} />
        </TabsContent>

        <TabsContent value="results">
          <ElectionResults elections={elections} />
        </TabsContent>

        <TabsContent value="explorer">
          <BlockExplorer />
        </TabsContent>
      </Tabs>
    </div>
  )
}
