import { NextResponse } from "next/server"

/**
 * TEMPORARY PLACEHOLDER API ROUTE
 *
 * This file contains a mock implementation of the blockchain stats API route
 * that will be replaced with actual API calls once the backend integration is complete.
 *
 * TODO: Replace this mock implementation with actual API calls to your
 * blockchain backend (tracker.py and peer.py) when they're ready.
 */

export async function GET() {
  // Mock data for blockchain stats
  const mockStats = {
    latestBlock: 1024,
    averageBlockTime: "30.2s",
    currentDifficulty: "12.4",
    activeNodes: 5,
    pendingTransactions: 12,
  }

  // Return mock data
  return NextResponse.json(mockStats)
}
