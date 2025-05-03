export interface Candidate {
  id: number
  name: string
  party: string
}

export interface ElectionData {
  id: string
  title: string
  description?: string
  candidates: Candidate[]
  status: "active" | "closed"
  closeTime?: string
}

export interface BlockchainStatus {
  currentHeight: number
  peerCount: number
  difficulty: number
  lastBlockTime: string
  hashRate: number
}
