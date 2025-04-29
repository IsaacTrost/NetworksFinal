"use client"

import { useState } from "react"
import { useSearchParams } from "next/navigation"
import Link from "next/link"
import { ArrowLeft, CheckCircle, Info, Key, Shield } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Label } from "@/components/ui/label"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Input } from "@/components/ui/input"

// Mock data - would be replaced with real API calls
const mockElections = [
  {
    id: "e1",
    title: "Student Council President",
    description: "Vote for the next student council president for the 2023-2024 academic year.",
    candidates: ["Alice Johnson", "Bob Smith", "Carol Williams"],
    startDate: "2023-04-15",
    endDate: "2023-04-29",
    status: "active",
  },
  {
    id: "e2",
    title: "Campus Improvement Initiative",
    description: "Choose which campus improvement project should receive funding this semester.",
    candidates: ["New Library Resources", "Cafeteria Renovation", "Outdoor Study Spaces", "Gym Equipment"],
    startDate: "2023-04-10",
    endDate: "2023-04-25",
    status: "active",
  },
]

export default function VotePage() {
  const searchParams = useSearchParams()
  const electionId = searchParams.get("election") || "e1"
  const election = mockElections.find((e) => e.id === electionId) || mockElections[0]

  const [selectedCandidate, setSelectedCandidate] = useState<string | null>(null)
  const [walletConnected, setWalletConnected] = useState(false)
  const [votingStep, setVotingStep] = useState<"select" | "confirm" | "success">("select")
  const [privateKey, setPrivateKey] = useState("")

  const handleConnectWallet = () => {
    // In a real implementation, this would connect to a wallet
    setWalletConnected(true)
  }

  const handleVote = () => {
    if (selectedCandidate === null) return
    setVotingStep("confirm")
  }

  const handleConfirmVote = () => {
    // In a real implementation, this would sign and submit the vote transaction
    setTimeout(() => {
      setVotingStep("success")
    }, 1500)
  }

  return (
    <div className="container max-w-4xl py-12">
      <Link href="/" className="flex items-center text-sm font-medium text-muted-foreground hover:text-foreground mb-8">
        <ArrowLeft className="mr-2 h-4 w-4" />
        Back to Dashboard
      </Link>

      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{election.title}</h1>
          <p className="text-muted-foreground mt-2">{election.description}</p>
        </div>

        <Alert>
          <Info className="h-4 w-4" />
          <AlertTitle>Important information</AlertTitle>
          <AlertDescription>
            Your vote will be recorded on the blockchain and cannot be changed once submitted. Make sure you review your
            selection carefully before confirming.
          </AlertDescription>
        </Alert>

        <Tabs defaultValue="vote" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="vote">Vote</TabsTrigger>
            <TabsTrigger value="wallet">Wallet</TabsTrigger>
          </TabsList>
          <TabsContent value="vote">
            {votingStep === "select" && (
              <Card>
                <CardHeader>
                  <CardTitle>Select a candidate</CardTitle>
                  <CardDescription>Choose one candidate from the list below</CardDescription>
                </CardHeader>
                <CardContent>
                  <RadioGroup value={selectedCandidate || ""} onValueChange={setSelectedCandidate}>
                    {(election.candidates || []).map((candidate, index) => (
                      <div key={index} className="flex items-center space-x-2 py-2">
                        <RadioGroupItem value={index.toString()} id={`candidate-${index}`} />
                        <Label htmlFor={`candidate-${index}`} className="flex-1 cursor-pointer">
                          {candidate}
                        </Label>
                      </div>
                    ))}
                  </RadioGroup>
                </CardContent>
                <CardFooter className="flex justify-between">
                  {!walletConnected ? (
                    <Button onClick={handleConnectWallet} className="w-full">
                      <Key className="mr-2 h-4 w-4" />
                      Connect Wallet to Vote
                    </Button>
                  ) : (
                    <Button onClick={handleVote} disabled={selectedCandidate === null} className="w-full">
                      Continue to Confirm
                    </Button>
                  )}
                </CardFooter>
              </Card>
            )}

            {votingStep === "confirm" && (
              <Card>
                <CardHeader>
                  <CardTitle>Confirm your vote</CardTitle>
                  <CardDescription>Please review your selection before submitting your vote</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="rounded-lg border p-4">
                    <div className="text-sm font-medium text-muted-foreground mb-2">Your selection:</div>
                    <div className="text-lg font-semibold">
                      {selectedCandidate !== null &&
                      election.candidates &&
                      election.candidates[Number.parseInt(selectedCandidate)]
                        ? election.candidates[Number.parseInt(selectedCandidate)]
                        : "No candidate selected"}
                    </div>
                  </div>

                  <div className="rounded-lg border p-4 space-y-2">
                    <div className="text-sm font-medium text-muted-foreground">Transaction details:</div>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div className="text-muted-foreground">Election ID:</div>
                      <div className="font-mono">{election.id}</div>
                      <div className="text-muted-foreground">Candidate ID:</div>
                      <div className="font-mono">{selectedCandidate}</div>
                      <div className="text-muted-foreground">Timestamp:</div>
                      <div className="font-mono">{new Date().toISOString()}</div>
                    </div>
                  </div>

                  <Alert variant="warning">
                    <Info className="h-4 w-4" />
                    <AlertTitle>Important</AlertTitle>
                    <AlertDescription>
                      This action cannot be undone. Your vote will be permanently recorded on the blockchain.
                    </AlertDescription>
                  </Alert>
                </CardContent>
                <CardFooter className="flex justify-between gap-2">
                  <Button variant="outline" onClick={() => setVotingStep("select")}>
                    Back
                  </Button>
                  <Button onClick={handleConfirmVote}>
                    <Shield className="mr-2 h-4 w-4" />
                    Sign and Submit Vote
                  </Button>
                </CardFooter>
              </Card>
            )}

            {votingStep === "success" && (
              <Card>
                <CardHeader>
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-6 w-6 text-green-500" />
                    <CardTitle>Vote Successfully Cast!</CardTitle>
                  </div>
                  <CardDescription>Your vote has been recorded on the blockchain</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="rounded-lg border p-4">
                    <div className="text-sm font-medium text-muted-foreground mb-2">Your selection:</div>
                    <div className="text-lg font-semibold">
                      {election.candidates[Number.parseInt(selectedCandidate || "0")]}
                    </div>
                  </div>

                  <div className="rounded-lg border p-4 space-y-2">
                    <div className="text-sm font-medium text-muted-foreground">Transaction details:</div>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div className="text-muted-foreground">Transaction Hash:</div>
                      <div className="font-mono truncate">
                        0x7f9e4e574ae8e1fc93c7f396711f064f3d1b3f6c2a0f9b4d5e6c7d8e9f0a1b2c
                      </div>
                      <div className="text-muted-foreground">Block Number:</div>
                      <div className="font-mono">1024</div>
                      <div className="text-muted-foreground">Timestamp:</div>
                      <div className="font-mono">{new Date().toISOString()}</div>
                    </div>
                  </div>
                </CardContent>
                <CardFooter>
                  <Button asChild className="w-full">
                    <Link href="/">Return to Dashboard</Link>
                  </Button>
                </CardFooter>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="wallet">
            <Card>
              <CardHeader>
                <CardTitle>Wallet Management</CardTitle>
                <CardDescription>
                  Connect your wallet or generate a new key pair to participate in blockchain voting.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {!walletConnected ? (
                  <>
                    <div className="space-y-2">
                      <Label htmlFor="private-key">Private Key</Label>
                      <Input
                        id="private-key"
                        type="password"
                        placeholder="Enter your private key"
                        value={privateKey}
                        onChange={(e) => setPrivateKey(e.target.value)}
                      />
                      <p className="text-xs text-muted-foreground">
                        Never share your private key with anyone. It gives full control over your votes.
                      </p>
                    </div>

                    <div className="flex flex-col gap-2">
                      <Button onClick={handleConnectWallet} disabled={!privateKey}>
                        <Key className="mr-2 h-4 w-4" />
                        Connect Wallet
                      </Button>
                      <Button variant="outline">Generate New Key Pair</Button>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="rounded-lg border p-4 space-y-2">
                      <div className="text-sm font-medium text-muted-foreground">Wallet Status:</div>
                      <div className="flex items-center gap-2">
                        <div className="h-3 w-3 rounded-full bg-green-500" />
                        <span className="font-medium">Connected</span>
                      </div>
                      <div className="text-sm font-medium text-muted-foreground mt-2">Public Key:</div>
                      <div className="font-mono text-xs truncate">
                        0x3f8e4a5b7c9d1e2f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f
                      </div>
                    </div>

                    <Alert>
                      <Info className="h-4 w-4" />
                      <AlertTitle>Wallet Connected</AlertTitle>
                      <AlertDescription>
                        Your wallet is connected and ready to sign vote transactions. You can now return to the Vote tab
                        to cast your vote.
                      </AlertDescription>
                    </Alert>

                    <Button variant="outline" onClick={() => setWalletConnected(false)}>
                      Disconnect Wallet
                    </Button>
                  </>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
