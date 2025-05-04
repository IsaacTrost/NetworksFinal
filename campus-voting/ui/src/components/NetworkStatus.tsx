"use client"

import type React from "react"
import { useState, useEffect } from "react"

interface BlockchainStatus {
  currentHeight: number
  peerCount: number
  difficulty: number
  lastBlockTime: string
  hashRate: number
  isConnected: boolean
}

const NetworkStatus: React.FC = () => {
  const [status, setStatus] = useState<BlockchainStatus>({
    currentHeight: 0,
    peerCount: 0,
    difficulty: 16,
    lastBlockTime: "",
    hashRate: 0,
    isConnected: false,
  })

  useEffect(() => {
    // Initial fetch
    fetchStatus()

    // Set up WebSocket connection
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:"
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/blockchain`)

    ws.onopen = () => {
      setStatus((prev) => ({ ...prev, isConnected: true }))
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === "BLOCKCHAIN_STATUS") {
          setStatus((prev) => ({ ...prev, ...data.payload, isConnected: true }))
        } else if (data.type === "NEW_BLOCK") {
          setStatus((prev) => ({
            ...prev,
            currentHeight: data.payload.index,
            lastBlockTime: new Date(data.payload.timestamp * 1000).toLocaleString(),
            difficulty: data.payload.difficulty,
            isConnected: true,
          }))
        }
      } catch (error) {
        console.error("Error parsing WebSocket message:", error)
      }
    }

    ws.onerror = () => {
      setStatus((prev) => ({ ...prev, isConnected: false }))
    }

    ws.onclose = () => {
      setStatus((prev) => ({ ...prev, isConnected: false }))
    }

    // Polling fallback
    const interval = setInterval(() => {
      if (!status.isConnected) {
        fetchStatus()
      }
    }, 10000)

    return () => {
      ws.close()
      clearInterval(interval)
    }
  }, [status.isConnected])

  const fetchStatus = async () => {
    try {
      const response = await fetch("/api/status")
      if (response.ok) {
        const data = await response.json()
        setStatus((prev) => ({ ...prev, ...data, isConnected: true }))
      }
    } catch (error) {
      console.error("Failed to fetch blockchain status:", error)
      setStatus((prev) => ({ ...prev, isConnected: false }))
    }
  }

  const formatTimeAgo = (timestamp: string) => {
    if (!timestamp) return "N/A"

    const date = new Date(timestamp)
    const now = new Date()
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000)

    if (seconds < 60) return `${seconds} seconds ago`
    if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes ago`
    if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours ago`
    return `${Math.floor(seconds / 86400)} days ago`
  }

  return (
    <div className="network-status">
      <div className="network-status-item">
        <span>Status:</span>
        <span className={`badge ${status.isConnected ? "badge-success" : "badge-danger"}`}>
          {status.isConnected ? "Connected" : "Disconnected"}
        </span>
      </div>

      <div className="network-status-item">
        <span>Block Height:</span>
        <span>{status.currentHeight}</span>
      </div>

      <div className="network-status-item">
        <span>Peers:</span>
        <span>{status.peerCount}</span>
      </div>

      <div className="network-status-item">
        <span>Difficulty:</span>
        <span>{status.difficulty}</span>
      </div>

      {status.lastBlockTime && (
        <div className="network-status-item">
          <span>Last Block:</span>
          <span title={new Date(status.lastBlockTime).toLocaleString()}>{formatTimeAgo(status.lastBlockTime)}</span>
        </div>
      )}

      {status.hashRate > 0 && (
        <div className="network-status-item">
          <span>Hash Rate:</span>
          <span>{status.hashRate.toFixed(1)} H/s</span>
        </div>
      )}
    </div>
  )
}

export default NetworkStatus
