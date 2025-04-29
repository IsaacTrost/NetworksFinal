/**
 * TEMPORARY PLACEHOLDER FILE
 *
 * This file contains mock implementations of API functions that will be
 * replaced with actual API calls once the backend integration is complete.
 *
 * TODO: Replace these mock implementations with actual API calls to your
 * blockchain backend (tracker.py and peer.py) when they're ready.
 */

// Add these helper functions at the top of the file to ensure safe data handling

/**
 * Safely handle API responses to prevent null/undefined errors
 */
function safeResponse(data, fallback) {
  return data !== null && data !== undefined ? data : fallback
}

/**
 * Safely handle array responses to prevent null/undefined errors with Object.entries
 */
function safeArrayResponse(data) {
  return Array.isArray(data) ? data : []
}

// Mock data for blockchain stats
const mockStats = {
  latestBlock: 1024,
  averageBlockTime: "30.2s",
  currentDifficulty: "12.4",
  activeNodes: 5,
  pendingTransactions: 12,
}

// Mock data for elections
const mockElections = [
  {
    id: "e1",
    title: "Student Council President",
    description: "Vote for the next student council president for the 2023-2024 academic year.",
    candidates: ["Alice Johnson", "Bob Smith", "Carol Williams"],
    votes: [423, 387, 291],
    totalVoters: 1500,
    startDate: "2023-04-15",
    endDate: "2023-04-29",
    status: "active",
  },
  {
    id: "e2",
    title: "Campus Improvement Initiative",
    description: "Choose which campus improvement project should receive funding this semester.",
    candidates: ["New Library Resources", "Cafeteria Renovation", "Outdoor Study Spaces", "Gym Equipment"],
    votes: [156, 210, 189, 102],
    totalVoters: 1500,
    startDate: "2023-04-10",
    endDate: "2023-04-25",
    status: "active",
  },
]

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

/**
 * Fetch blockchain statistics
 *
 * TODO: Replace with actual API call to your blockchain node
 * Example: const response = await fetch('http://localhost:5000/api/stats');
 */
export async function fetchBlockchainStats() {
  // Simulate network delay
  await new Promise((resolve) => setTimeout(resolve, 500))

  // Return mock data with safety check
  return safeResponse(
    { ...mockStats },
    {
      latestBlock: 0,
      averageBlockTime: "0s",
      currentDifficulty: "0",
      activeNodes: 0,
      pendingTransactions: 0,
    },
  )
}

/**
 * Fetch elections
 *
 * TODO: Replace with actual API call to your blockchain node
 * Example: const response = await fetch('http://localhost:5000/api/elections');
 */
export async function fetchElections() {
  // Simulate network delay
  await new Promise((resolve) => setTimeout(resolve, 500))

  // Return mock data with safety check
  return safeArrayResponse([...mockElections])
}

/**
 * Fetch blockchain blocks
 *
 * TODO: Replace with actual API call to your blockchain node
 * Example: const response = await fetch(`http://localhost:5000/api/blocks?page=${page}&limit=${limit}`);
 */
export async function fetchBlocks(page = 1, limit = 10) {
  // Simulate network delay
  await new Promise((resolve) => setTimeout(resolve, 500))

  // Return mock data with safety check
  return safeArrayResponse(mockBlocks.slice((page - 1) * limit, page * limit))
}

/**
 * Cast a vote
 *
 * TODO: Replace with actual API call to your blockchain node
 * Example: const response = await fetch('http://localhost:5000/api/vote', { method: 'POST', ... });
 */
export async function castVote(electionId, candidateId, signature, publicKey) {
  // Simulate network delay
  await new Promise((resolve) => setTimeout(resolve, 1000))

  // Simulate successful response
  return {
    success: true,
    transactionId: `tx-${Math.random().toString(36).substring(2, 15)}`,
    blockIndex: mockStats.latestBlock + 1,
    timestamp: new Date().toISOString(),
  }
}

/**
 * Create a new election
 *
 * TODO: Replace with actual API call to your blockchain node
 * Example: const response = await fetch('http://localhost:5000/api/elections', { method: 'POST', ... });
 */
export async function createElection(electionData) {
  // Simulate network delay
  await new Promise((resolve) => setTimeout(resolve, 1000))

  // Simulate successful response
  return {
    success: true,
    electionId: `e${Math.floor(Math.random() * 1000)}`,
    timestamp: new Date().toISOString(),
  }
}
