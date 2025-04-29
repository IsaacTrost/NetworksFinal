"use client"

import { useState } from "react"
import Link from "next/link"
import { ArrowLeft, ArrowRight, ChevronDown, ChevronUp, Database, FileText, Search } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { Badge } from "@/components/ui/badge"

// Mock data - would be replaced with real API calls
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

export default function ExplorerPage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [expandedBlock, setExpandedBlock] = useState<number | null>(null)

  const toggleBlock = (index: number) => {
    setExpandedBlock(expandedBlock === index ? null : index)
  }

  return (
    <div className="container max-w-6xl py-12">
      <Link href="/" className="flex items-center text-sm font-medium text-muted-foreground hover:text-foreground mb-8">
        <ArrowLeft className="mr-2 h-4 w-4" />
        Back to Dashboard
      </Link>

      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Blockchain Explorer</h1>
          <p className="text-muted-foreground mt-2">Explore the blockchain, view blocks, and verify transactions</p>
        </div>

        <div className="flex gap-4">
          <div className="flex-1">
            <Input
              placeholder="Search by block hash, transaction ID, or voter public key..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full"
            />
          </div>
          <Button>
            <Search className="mr-2 h-4 w-4" />
            Search
          </Button>
        </div>

        <div className="space-y-4">
          <h2 className="text-xl font-semibold tracking-tight">Latest Blocks</h2>

          <div className="space-y-4">
            {(mockBlocks || []).map((block) => (
              <Collapsible
                key={block.index || "unknown"}
                open={expandedBlock === block.index}
                onOpenChange={() => toggleBlock(block.index)}
                className="border rounded-lg"
              >
                <div className="flex items-center p-4 cursor-pointer hover:bg-muted/50">
                  <CollapsibleTrigger asChild>
                    <div className="flex items-center justify-between w-full">
                      <div className="flex items-center gap-4">
                        <Database className="h-5 w-5 text-muted-foreground" />
                        <div>
                          <div className="font-medium">Block #{block.index}</div>
                          <div className="text-sm text-muted-foreground">
                            {new Date(block.timestamp).toLocaleString()}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <Badge variant="outline">{block.transactions.length} Transactions</Badge>
                        {expandedBlock === block.index ? (
                          <ChevronUp className="h-4 w-4" />
                        ) : (
                          <ChevronDown className="h-4 w-4" />
                        )}
                      </div>
                    </div>
                  </CollapsibleTrigger>
                </div>

                <CollapsibleContent>
                  <div className="border-t p-4 space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <Card>
                        <CardHeader className="pb-2">
                          <CardTitle className="text-sm">Block Details</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-2 text-sm">
                          <div className="grid grid-cols-3 gap-1">
                            <div className="text-muted-foreground">Index:</div>
                            <div className="col-span-2 font-medium">{block.index}</div>

                            <div className="text-muted-foreground">Hash:</div>
                            <div className="col-span-2 font-mono text-xs truncate">{block.hash}</div>

                            <div className="text-muted-foreground">Previous Hash:</div>
                            <div className="col-span-2 font-mono text-xs truncate">{block.prevHash}</div>

                            <div className="text-muted-foreground">Timestamp:</div>
                            <div className="col-span-2 font-medium">{new Date(block.timestamp).toLocaleString()}</div>

                            <div className="text-muted-foreground">Difficulty:</div>
                            <div className="col-span-2 font-medium">{block.difficulty}</div>

                            <div className="text-muted-foreground">Nonce:</div>
                            <div className="col-span-2 font-medium">{block.nonce}</div>
                          </div>
                        </CardContent>
                      </Card>

                      <Card>
                        <CardHeader className="pb-2">
                          <CardTitle className="text-sm">Merkle Tree</CardTitle>
                        </CardHeader>
                        <CardContent className="h-[200px] flex items-center justify-center">
                          <div className="text-center text-muted-foreground">
                            <FileText className="h-10 w-10 mx-auto mb-2 opacity-50" />
                            <p>Merkle tree visualization</p>
                          </div>
                        </CardContent>
                      </Card>
                    </div>

                    <div>
                      <h3 className="text-lg font-medium mb-2">Transactions</h3>
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Transaction ID</TableHead>
                            <TableHead>Election ID</TableHead>
                            <TableHead>Voter (hashed)</TableHead>
                            <TableHead>Candidate ID</TableHead>
                            <TableHead>Timestamp</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {(block.transactions || []).map((tx) => (
                            <TableRow key={tx.id || "unknown"}>
                              <TableCell className="font-mono text-xs">{tx.id}</TableCell>
                              <TableCell>{tx.electionId}</TableCell>
                              <TableCell className="font-mono text-xs truncate max-w-[150px]">
                                {tx.voterPkHash}
                              </TableCell>
                              <TableCell>{tx.candidateId}</TableCell>
                              <TableCell>{new Date(tx.timestamp).toLocaleString()}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  </div>
                </CollapsibleContent>
              </Collapsible>
            ))}
          </div>

          <div className="flex justify-center gap-2 pt-4">
            <Button variant="outline" size="sm">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Previous
            </Button>
            <Button variant="outline" size="sm">
              Next
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
