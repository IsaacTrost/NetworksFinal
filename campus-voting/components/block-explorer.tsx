"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Search, ChevronRight, ChevronLeft, Hash, Clock } from "lucide-react"
import { formatDistanceToNow } from "date-fns"

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

interface Transaction {
  election_id: string
  voter_pk_hash: string
  candidate_id: number
  timestamp: number
  signature: string
}

export default function BlockExplorer() {
  const [searchQuery, setSearchQuery] = useState("")
  const [currentPage, setCurrentPage] = useState(1)
  const [blocks, setBlocks] = useState<Block[]>([])
  const [selectedBlock, setSelectedBlock] = useState<Block | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [totalBlocks, setTotalBlocks] = useState(0)
  const blocksPerPage = 10

  // Fetch blocks on initial load and page change
  useEffect(() => {
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
      } catch (error) {
        console.error("Error fetching blocks:", error)
        setError("An error occurred while fetching blocks")
      } finally {
        setIsLoading(false)
      }
    }

    fetchBlocks()
  }, [currentPage])

  // Handle search
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
    } catch (error: any) {
      setError(error.message || "An error occurred during search")
    } finally {
      setIsLoading(false)
    }
  }

  // Handle block selection
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
    } catch (error) {
      console.error("Error fetching block details:", error)
      setError("An error occurred while fetching block details")
    } finally {
      setIsLoading(false)
    }
  }

  // Handle pagination
  const totalPages = Math.ceil(totalBlocks / blocksPerPage)

  const goToNextPage = () => {
    if (currentPage < totalPages) {
      setCurrentPage(currentPage + 1)
    }
  }

  const goToPrevPage = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1)
    }
  }

  // Reset to block list view
  const backToBlockList = () => {
    setSelectedBlock(null)
    setSearchQuery("")
  }

  // Check if a hash is valid proof of work based on difficulty
  const isValidProofOfWork = (hash: string, difficulty: number) => {
    // Convert the first few bytes of the hash to a number
    const hashStart = Number.parseInt(hash.substring(0, 8), 16)
    // Check if it's below the target based on difficulty
    return hashStart < 2 ** 32 - difficulty
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Block Explorer</CardTitle>
        <CardDescription>Explore the blockchain and verify transactions</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex mb-6">
          <div className="relative flex-1">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              type="text"
              placeholder="Search by block height, block hash, or tx hash"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>
          <Button onClick={handleSearch} className="ml-2">
            Search
          </Button>
          {selectedBlock && (
            <Button variant="outline" onClick={backToBlockList} className="ml-2">
              Back to List
            </Button>
          )}
        </div>

        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {isLoading ? (
          <div className="flex justify-center items-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
          </div>
        ) : selectedBlock ? (
          <div className="space-y-6">
            <div className="bg-muted p-4 rounded-lg">
              <h3 className="text-lg font-semibold mb-2">Block #{selectedBlock.index}</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">Hash</p>
                  <div className="flex items-center">
                    <Hash className="h-4 w-4 mr-2 text-muted-foreground" />
                    <p className="font-mono text-xs break-all">{selectedBlock.hash}</p>
                  </div>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Previous Hash</p>
                  <p className="font-mono text-xs break-all">{selectedBlock.prev_hash}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Merkle Root</p>
                  <p className="font-mono text-xs break-all">{selectedBlock.merkle_root}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Timestamp</p>
                  <div className="flex items-center">
                    <Clock className="h-4 w-4 mr-2 text-muted-foreground" />
                    <p>
                      {new Date(selectedBlock.timestamp * 1000).toLocaleString()} (
                      {formatDistanceToNow(new Date(selectedBlock.timestamp * 1000))} ago)
                    </p>
                  </div>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Difficulty</p>
                  <p>{selectedBlock.difficulty}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Nonce</p>
                  <p>{selectedBlock.nonce}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Proof of Work</p>
                  <p
                    className={
                      isValidProofOfWork(selectedBlock.hash, selectedBlock.difficulty)
                        ? "text-green-500"
                        : "text-red-500"
                    }
                  >
                    {isValidProofOfWork(selectedBlock.hash, selectedBlock.difficulty) ? "Valid" : "Invalid"}
                  </p>
                </div>
              </div>
            </div>

            <div>
              <h3 className="text-lg font-semibold mb-2">Transactions ({selectedBlock.transactions.length})</h3>
              {selectedBlock.transactions.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Election ID</TableHead>
                      <TableHead>Candidate ID</TableHead>
                      <TableHead>Timestamp</TableHead>
                      <TableHead className="hidden md:table-cell">Voter (hashed)</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {selectedBlock.transactions.map((tx, index) => (
                      <TableRow key={index}>
                        <TableCell className="font-mono text-xs">
                          {tx.election_id.substring(0, 8)}...{tx.election_id.substring(tx.election_id.length - 8)}
                        </TableCell>
                        <TableCell>{tx.candidate_id}</TableCell>
                        <TableCell>{new Date(tx.timestamp * 1000).toLocaleString()}</TableCell>
                        <TableCell className="hidden md:table-cell font-mono text-xs">
                          {tx.voter_pk_hash.substring(0, 8)}...{tx.voter_pk_hash.substring(tx.voter_pk_hash.length - 8)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="text-center py-4 text-muted-foreground">
                  No transactions in this block (genesis block)
                </div>
              )}
            </div>
          </div>
        ) : (
          <>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Height</TableHead>
                  <TableHead>Hash (first 8 bytes)</TableHead>
                  <TableHead>Time</TableHead>
                  <TableHead className="hidden md:table-cell">Transactions</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {blocks.map((block) => (
                  <TableRow key={block.index}>
                    <TableCell className="font-medium">{block.index}</TableCell>
                    <TableCell className="font-mono">{block.hash.substring(0, 16)}...</TableCell>
                    <TableCell>{formatDistanceToNow(new Date(block.timestamp * 1000))} ago</TableCell>
                    <TableCell className="hidden md:table-cell">{block.transactions?.length || 0}</TableCell>
                    <TableCell>
                      <Button variant="ghost" size="sm" onClick={() => selectBlock(block.index)}>
                        View
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>

            {blocks.length > 0 && (
              <div className="flex items-center justify-between mt-4">
                <Button variant="outline" size="sm" onClick={goToPrevPage} disabled={currentPage === 1}>
                  <ChevronLeft className="h-4 w-4 mr-1" />
                  Previous
                </Button>
                <span className="text-sm text-muted-foreground">
                  Page {currentPage} of {totalPages}
                </span>
                <Button variant="outline" size="sm" onClick={goToNextPage} disabled={currentPage === totalPages}>
                  Next
                  <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  )
}
