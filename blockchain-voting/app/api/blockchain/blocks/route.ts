import { NextResponse } from "next/server"

/**
 * TEMPORARY PLACEHOLDER API ROUTE
 *
 * This file contains a mock implementation of the blockchain blocks API route
 * that will be replaced with actual API calls once the backend integration is complete.
 *
 * TODO: Replace this mock implementation with actual API calls to your
 * blockchain backend (tracker.py and peer.py) when they're ready.
 */

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const page = Number.parseInt(searchParams.get("page") || "1")
  const limit = Number.parseInt(searchParams.get("limit") || "10")

  // Mock data for blockchain blocks
  const mockBlocks = Array.from({ length: 10 }, (_, i) => ({
    index: 1024 - i,
    hash: `0x${Array.from({ length: 64 }, () => Math.floor(Math.random() * 16).toString(16)).join("")}`,
    prevHash: `0x${Array.from({ length: 64 }, () => Math.floor(Math.random() * 16).toString(16)).join("")}`,
    timestamp: new Date(Date.now() - i * 30000).toISOString(),
    difficulty: 12.4,
    nonce: Math.floor(Math.random() * 1000000),
    transactions: Array.from({ length: Math.floor(Math.random() * 5) + 1 }, (_, j) => ({
      id: `tx-${i}-${j}`,
      electionId: `e${Math.floor(Math.random() * 2) + 1}`,
      voterPkHash: `0x${Array.from({ length: 40 }, () => Math.floor(Math.random() * 16).toString(16)).join("")}`,
      candidateId: Math.floor(Math.random() * 4),
      timestamp: new Date(Date.now() - i * 30000 - j * 1000).toISOString(),
    })),
  }))

  // Paginate the blocks
  const paginatedBlocks = mockBlocks.slice((page - 1) * limit, page * limit)

  // Return mock data
  return NextResponse.json(paginatedBlocks)
}
