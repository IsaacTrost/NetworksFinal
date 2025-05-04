"use client"

import { useState } from "react"
import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import * as z from "zod"
import { Check, ChevronsUpDown, KeyRound, Vote } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command"
import { cn } from "@/lib/utils"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import type { ElectionData } from "@/lib/types"

// Define the form schema
const formSchema = z.object({
  electionId: z.string().uuid({
    message: "Please select a valid election.",
  }),
  privateKey: z.string().min(64, {
    message: "Private key must be at least 64 characters.",
  }),
  candidateId: z.string({
    required_error: "Please select a candidate.",
  }),
})

interface VoteFormProps {
  elections: ElectionData[]
}

export default function VoteForm({ elections }: VoteFormProps) {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [voteResult, setVoteResult] = useState<{
    success: boolean
    message: string
    txHash?: string
  } | null>(null)

  // Initialize the form
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      electionId: "",
      privateKey: "",
      candidateId: "",
    },
  })

  // Handle form submission
  async function onSubmit(values: z.infer<typeof formSchema>) {
    setIsSubmitting(true)
    setVoteResult(null)

    try {
      // Format the vote transaction according to your blockchain's expected format
      const voteTransaction = {
        election_id: values.electionId,
        private_key: values.privateKey,
        candidate_id: Number.parseInt(values.candidateId),
        timestamp: Math.floor(Date.now() / 1000), // Unix timestamp in seconds
      }

      const response = await fetch("/api/vote", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(voteTransaction),
      })

      const data = await response.json()

      if (response.ok) {
        setVoteResult({
          success: true,
          message: "Your vote has been submitted to the blockchain network!",
          txHash: data.tx_hash,
        })
        form.reset()
      } else {
        setVoteResult({
          success: false,
          message: data.error || "Failed to submit vote. Please try again.",
        })
      }
    } catch (error) {
      console.error("Error submitting vote:", error)
      setVoteResult({
        success: false,
        message: "An error occurred while submitting your vote. Please check your connection and try again.",
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  // Get the selected election
  const selectedElection = form.watch("electionId") ? elections.find((e) => e.id === form.watch("electionId")) : null

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Cast Your Vote</CardTitle>
        <CardDescription>
          Submit your vote to the blockchain. Once submitted, your vote cannot be changed.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            <FormField
              control={form.control}
              name="electionId"
              render={({ field }) => (
                <FormItem className="flex flex-col">
                  <FormLabel>Election</FormLabel>
                  <Popover>
                    <PopoverTrigger asChild>
                      <FormControl>
                        <Button
                          variant="outline"
                          role="combobox"
                          className={cn("justify-between", !field.value && "text-muted-foreground")}
                        >
                          {field.value
                            ? elections.find((election) => election.id === field.value)?.title
                            : "Select election"}
                          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                        </Button>
                      </FormControl>
                    </PopoverTrigger>
                    <PopoverContent className="p-0">
                      <Command>
                        <CommandInput placeholder="Search elections..." />
                        <CommandList>
                          <CommandEmpty>No elections found.</CommandEmpty>
                          <CommandGroup>
                            {elections.map((election) => (
                              <CommandItem
                                value={election.title}
                                key={election.id}
                                onSelect={() => {
                                  form.setValue("electionId", election.id)
                                }}
                              >
                                <Check
                                  className={cn(
                                    "mr-2 h-4 w-4",
                                    election.id === field.value ? "opacity-100" : "opacity-0",
                                  )}
                                />
                                {election.title}
                              </CommandItem>
                            ))}
                          </CommandGroup>
                        </CommandList>
                      </Command>
                    </PopoverContent>
                  </Popover>
                  <FormDescription>Select the election you want to participate in.</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            {selectedElection && (
              <FormField
                control={form.control}
                name="candidateId"
                render={({ field }) => (
                  <FormItem className="flex flex-col">
                    <FormLabel>Candidate</FormLabel>
                    <Popover>
                      <PopoverTrigger asChild>
                        <FormControl>
                          <Button
                            variant="outline"
                            role="combobox"
                            className={cn("justify-between", !field.value && "text-muted-foreground")}
                          >
                            {field.value
                              ? selectedElection.candidates.find((candidate) => candidate.id.toString() === field.value)
                                  ?.name
                              : "Select candidate"}
                            <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                          </Button>
                        </FormControl>
                      </PopoverTrigger>
                      <PopoverContent className="p-0">
                        <Command>
                          <CommandInput placeholder="Search candidates..." />
                          <CommandList>
                            <CommandEmpty>No candidates found.</CommandEmpty>
                            <CommandGroup>
                              {selectedElection.candidates.map((candidate) => (
                                <CommandItem
                                  value={candidate.name}
                                  key={candidate.id}
                                  onSelect={() => {
                                    form.setValue("candidateId", candidate.id.toString())
                                  }}
                                >
                                  <Check
                                    className={cn(
                                      "mr-2 h-4 w-4",
                                      candidate.id.toString() === field.value ? "opacity-100" : "opacity-0",
                                    )}
                                  />
                                  <div className="flex flex-col">
                                    <span>{candidate.name}</span>
                                    <span className="text-xs text-muted-foreground">{candidate.party}</span>
                                  </div>
                                </CommandItem>
                              ))}
                            </CommandGroup>
                          </CommandList>
                        </Command>
                      </PopoverContent>
                    </Popover>
                    <FormDescription>Select the candidate you wish to vote for.</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            )}

            <FormField
              control={form.control}
              name="privateKey"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Your Private Key</FormLabel>
                  <FormControl>
                    <div className="flex">
                      <KeyRound className="mr-2 h-4 w-4 mt-3" />
                      <Input type="password" placeholder="Enter your private key" {...field} />
                    </div>
                  </FormControl>
                  <FormDescription>
                    This is the private key provided to you by the election committee. Your vote will be signed with
                    this key.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <Button type="submit" className="w-full" disabled={isSubmitting}>
              {isSubmitting ? (
                <>
                  <span className="mr-2">Submitting...</span>
                  <span className="animate-spin">⏳</span>
                </>
              ) : (
                <>
                  <Vote className="mr-2 h-4 w-4" />
                  Submit Vote
                </>
              )}
            </Button>
          </form>
        </Form>
      </CardContent>

      {voteResult && (
        <CardFooter>
          <Alert className={cn("w-full", voteResult.success ? "border-green-500" : "border-red-500")}>
            <AlertTitle>{voteResult.success ? "Vote Submitted!" : "Error"}</AlertTitle>
            <AlertDescription>
              {voteResult.message}
              {voteResult.txHash && (
                <div className="mt-2">
                  <p className="font-semibold">Transaction Hash:</p>
                  <code className="bg-muted p-1 rounded text-xs block overflow-x-auto">{voteResult.txHash}</code>
                  <p className="text-xs mt-2">
                    Your vote will be included in the blockchain once miners confirm it. This usually takes a few
                    minutes.
                  </p>
                </div>
              )}
            </AlertDescription>
          </Alert>
        </CardFooter>
      )}
    </Card>
  )
}
