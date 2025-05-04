"use client"

import type React from "react"
import { useState, useEffect } from "react"

interface Transaction {
  election_id: string
  voter_pk_hash: string
  candidate_id: number
  timestamp: number
  signature: string
}

interface Block {
  index: number
  hash: string
  prev_hash: string
  merkle_root: string
  timestamp: number
  difficulty: number
  nonce: number
  transactions: Transaction[]
}

const BlockExplorer: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState<string>("")
  const [blocks, setBlocks] = useState<Block[]>([])
  const [selectedBlock, setSelectedBlock] = useState<Block | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [currentPage, setCurrentPage] = useState<number>(1)
  const [totalBlocks, setTotalBlocks] = useState<number>(0)
  const blocksPerPage = 10

  useEffect(() => {
    fetchBlocks()
  }, [currentPage])

  const fetchBlocks = async () => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch(`/api/blocks?page=${currentPage}&limit=${blocksPerPage}`)

      if (response.ok) {
        const data = await response.json()
        setBlocks(data.blocks)
        setTotalBlocks(data.total)
      } else {
        const errorData = await response.json()
        setError(errorData.error || "Failed to fetch blocks")
      }
    } catch (err) {
      console.error("Error fetching blocks:", err)
      setError("An error occurred while fetching blocks")
    } finally {
      setIsLoading(false)
    }
  }

  const handleSearch = async () => {
    if (!searchQuery.trim()) return

    setIsLoading(true)
    setError(null)

    try {
      // Determine if searching by block hash, block height, or transaction hash
      let endpoint = ""

      if (/^\d+$/.test(searchQuery)) {
        // Search by block height
        endpoint = `/api/blocks/${searchQuery}`
      } else if (searchQuery.length === 64) {
        // Search by hash (block or transaction)
        endpoint = `/api/search?hash=${searchQuery}`
      } else {
        throw new Error("Invalid search query. Please enter a block height or hash.")
      }

      const response = await fetch(endpoint)

      if (response.ok) {
        const data = await response.json()

        if (data.type === "block") {
          setSelectedBlock(data.block)
          setBlocks([])
        } else if (data.type === "transaction") {
          // Fetch the block containing this transaction
          const blockResponse = await fetch(`/api/blocks/${data.block_index}`)
          if (blockResponse.ok) {
            const blockData = await blockResponse.json()
            setSelectedBlock(blockData.block)
          }
        }
      } else {
        const errorData = await response.json()
        setError(errorData.error || "No results found for your search query")
      }
    } catch (err: any) {
      setError(err.message || "An error occurred during search")
    } finally {
      setIsLoading(false)
    }
  }

  const selectBlock = async (index: number) => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch(`/api/blocks/${index}`)

      if (response.ok) {
        const data = await response.json()
        setSelectedBlock(data.block)
      } else {
        const errorData = await response.json()
        setError(errorData.error || "Failed to fetch block details")
      }
    } catch (err) {
      console.error("Error fetching block details:", err)
      setError("An error occurred while fetching block details")
    } finally {
      setIsLoading(false)
    }
  }

  const backToBlockList = () => {
    setSelectedBlock(null)
    setSearchQuery("")
  }

  const goToNextPage = () => {
    if (currentPage < Math.ceil(totalBlocks / blocksPerPage)) {
      setCurrentPage(currentPage + 1)
    }
  }

  const goToPrevPage = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1)
    }
  }

  const formatTimeAgo = (timestamp: number) => {
    const date = new Date(timestamp * 1000)
    const now = new Date()
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000)

    if (seconds < 60) return `${seconds} seconds ago`
    if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes ago`
    if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours ago`
    return `${Math.floor(seconds / 86400)} days ago`
  }

  // Check if a hash is valid proof of work based on difficulty
  const isValidProofOfWork = (hash: string, difficulty: number) => {
    // Simple check: first few characters should be zeros
    const requiredZeros = Math.floor(difficulty / 4) // Each hex digit represents 4 bits
    const leadingZeros = hash.match(/^0*/)?.[0].length || 0
    return leadingZeros >= requiredZeros
  }

  return (
    <div className="card">
      <div className="card-header">
        <h2 className="card-title">Block Explorer</h2>
        <p className="card-description">Explore the blockchain and verify transactions</p>
      </div>

      <div className="flex mb-4">
        <input
          type="text"
          className="form-control"
          placeholder="Search by block height, block hash, or tx hash"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
        <button className="btn btn-primary ml-2" onClick={handleSearch}>
          Search
        </button>
        {selectedBlock && (
          <button className="btn btn-outline ml-2" onClick={backToBlockList}>
            Back to List
          </button>
        )}
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      {isLoading ? (
        <div className="text-center p-4">
          <div className="spinner"></div>
          <p className="mt-2 text-muted">Loading...</p>
        </div>
      ) : selectedBlock ? (
        <div>
          <div className="card mb-4">
            <h3 className="mb-2 font-semibold">Block #{selectedBlock.index}</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-muted">Hash</p>
                <p className="font-mono text-sm truncate">{selectedBlock.hash}</p>
              </div>
              <div>
                <p className="text-sm text-muted">Previous Hash</p>
                <p className="font-mono text-sm truncate">{selectedBlock.prev_hash}</p>
              </div>
              <div>
                <p className="text-sm text-muted">Merkle Root</p>
                <p className="font-mono text-sm truncate">{selectedBlock.merkle_root}</p>
              </div>
              <div>
                <p className="text-sm text-muted">Timestamp</p>
                <p title={new Date(selectedBlock.timestamp * 1000).toLocaleString()}>
                  {formatTimeAgo(selectedBlock.timestamp)}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted">Difficulty</p>
                <p>{selectedBlock.difficulty}</p>
              </div>
              <div>
                <p className="text-sm text-muted">Nonce</p>
                <p>{selectedBlock.nonce}</p>
              </div>
              <div>
                <p className="text-sm text-muted">Proof of Work</p>
                <p
                  className={
                    isValidProofOfWork(selectedBlock.hash, selectedBlock.difficulty) ? "text-success" : "text-danger"
                  }
                >
                  {isValidProofOfWork(selectedBlock.hash, selectedBlock.difficulty) ? "Valid" : "Invalid"}
                </p>
              </div>
            </div>
          </div>

          <h3 className="mb-2 font-semibold">Transactions ({selectedBlock.transactions.length})</h3>
          {selectedBlock.transactions.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="table">
                <thead>
                  <tr>
                    <th>Election ID</th>
                    <th>Candidate ID</th>
                    <th>Timestamp</th>
                    <th className="hidden md:table-cell">Voter (hashed)</th>
                  </tr>
                </thead>
                <tbody>
                  {selectedBlock.transactions.map((tx, index) => (
                    <tr key={index}>
                      <td className="font-mono text-sm truncate" title={tx.election_id}>
                        {tx.election_id.substring(0, 8)}...{tx.election_id.substring(tx.election_id.length - 8)}
                      </td>
                      <td>{tx.candidate_id}</td>
                      <td title={new Date(tx.timestamp * 1000).toLocaleString()}>{formatTimeAgo(tx.timestamp)}</td>
                      <td className="hidden md:table-cell font-mono text-sm truncate" title={tx.voter_pk_hash}>
                        {tx.voter_pk_hash.substring(0, 8)}...{tx.voter_pk_hash.substring(tx.voter_pk_hash.length - 8)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center p-4 text-muted">No transactions in this block (genesis block)</div>
          )}
        </div>
      ) : (
        <>
          <div className="overflow-x-auto">
            <table className="table">
              <thead>
                <tr>
                  <th>Height</th>
                  <th>Hash (first 8 bytes)</th>
                  <th>Time</th>
                  <th className="hidden md:table-cell">Transactions</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {blocks.map((block) => (
                  <tr key={block.index}>
                    <td>{block.index}</td>
                    <td className="font-mono">{block.hash.substring(0, 16)}...</td>
                    <td>{formatTimeAgo(block.timestamp)}</td>
                    <td className="hidden md:table-cell">{block.transactions?.length || 0}</td>
                    <td>
                      <button className="btn btn-outline btn-sm" onClick={() => selectBlock(block.index)}>
                        View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {blocks.length > 0 && (
            <div className="flex justify-between items-center mt-4">
              <button className="btn btn-outline btn-sm" onClick={goToPrevPage} disabled={currentPage === 1}>
                Previous
              </button>
              <span className="text-muted">
                Page {currentPage} of {Math.ceil(totalBlocks / blocksPerPage)}
              </span>
              <button
                className="btn btn-outline btn-sm"
                onClick={goToNextPage}
                disabled={currentPage >= Math.ceil(totalBlocks / blocksPerPage)}
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default BlockExplorer
