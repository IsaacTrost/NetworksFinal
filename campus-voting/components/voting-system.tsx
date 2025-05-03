"use client"

import { useState, useEffect } from "react"
import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import * as z from "zod"
import { Check, ChevronsUpDown } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command"
import { cn } from "@/lib/utils"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { BarChart } from "@/components/ui/chart"

// Define the form schema
const formSchema = z.object({
  electionId: z.string().min(6, {
    message: "Election ID must be at least 6 characters.",
  }),
  candidateId: z.string({
    required_error: "Please select a candidate.",
  }),
})

// Mock candidates data
const candidates = [
  { id: "1", name: "Alex Johnson", party: "Student Progress Party" },
  { id: "2", name: "Taylor Smith", party: "Campus Reform Coalition" },
  { id: "3", name: "Jordan Lee", party: "University Voice Alliance" },
  { id: "4", name: "Morgan Rivera", party: "Independent" },
]

export default function VotingSystem() {
  const [submitted, setSubmitted] = useState(false)
  const [votingData, setVotingData] = useState([
    { name: "Alex Johnson", votes: 145 },
    { name: "Taylor Smith", votes: 132 },
    { name: "Jordan Lee", votes: 118 },
    { name: "Morgan Rivera", votes: 97 },
  ])

  // Initialize the form
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      electionId: "",
      candidateId: "",
    },
  })

  // Handle form submission
  function onSubmit(values: z.infer<typeof formSchema>) {
    // In a real app, this would send the vote to a server
    console.log(values)

    // Update the voting data to simulate real-time updates
    setVotingData((prevData) => {
      return prevData.map((candidate) => {
        const selectedCandidate = candidates.find((c) => c.id === values.candidateId)
        if (selectedCandidate && candidate.name === selectedCandidate.name) {
          return { ...candidate, votes: candidate.votes + 1 }
        }
        return candidate
      })
    })

    setSubmitted(true)
  }

  // Simulate real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      if (!submitted) {
        setVotingData((prevData) => {
          return prevData.map((candidate) => {
            // Randomly update votes to simulate real-time changes
            const change = Math.random() > 0.7 ? Math.floor(Math.random() * 3) + 1 : 0
            return { ...candidate, votes: candidate.votes + change }
          })
        })
      }
    }, 3000)

    return () => clearInterval(interval)
  }, [submitted])

  return (
    <div className="grid gap-8 md:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Cast Your Vote</CardTitle>
          <CardDescription>Enter your election ID and select your preferred candidate.</CardDescription>
        </CardHeader>
        <CardContent>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
              <FormField
                control={form.control}
                name="electionId"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Election ID</FormLabel>
                    <FormControl>
                      <Input placeholder="Enter your election ID" {...field} />
                    </FormControl>
                    <FormDescription>This is the unique ID provided to you by the election committee.</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

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
                              ? candidates.find((candidate) => candidate.id === field.value)?.name
                              : "Select candidate"}
                            <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                          </Button>
                        </FormControl>
                      </PopoverTrigger>
                      <PopoverContent className="p-0">
                        <Command>
                          <CommandInput placeholder="Search candidate..." />
                          <CommandList>
                            <CommandEmpty>No candidate found.</CommandEmpty>
                            <CommandGroup>
                              {candidates.map((candidate) => (
                                <CommandItem
                                  value={candidate.name}
                                  key={candidate.id}
                                  onSelect={() => {
                                    form.setValue("candidateId", candidate.id)
                                  }}
                                >
                                  <Check
                                    className={cn(
                                      "mr-2 h-4 w-4",
                                      candidate.id === field.value ? "opacity-100" : "opacity-0",
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

              <Button type="submit" className="w-full">
                Submit Vote
              </Button>
            </form>
          </Form>
        </CardContent>
        <CardFooter className="flex justify-center">
          {submitted && (
            <Alert className="border-green-500">
              <AlertTitle>Vote Submitted!</AlertTitle>
              <AlertDescription>
                Your vote has been successfully recorded. Thank you for participating.
              </AlertDescription>
            </Alert>
          )}
        </CardFooter>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Real-time Results</CardTitle>
          <CardDescription>Live vote count for each candidate. Updates every few seconds.</CardDescription>
        </CardHeader>
        <CardContent className="h-80">
          <BarChart
            data={votingData}
            index="name"
            categories={["votes"]}
            colors={["#3b82f6"]}
            valueFormatter={(value) => `${value} votes`}
            yAxisWidth={48}
          />
        </CardContent>
        <CardFooter>
          <p className="text-sm text-muted-foreground">
            Total votes: {votingData.reduce((sum, candidate) => sum + candidate.votes, 0)}
          </p>
        </CardFooter>
      </Card>
    </div>
  )
}
