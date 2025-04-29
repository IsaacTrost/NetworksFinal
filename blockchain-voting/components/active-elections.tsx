"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { ArrowRight, Calendar, Users } from "lucide-react"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { fetchElections } from "@/lib/api"

// Mock data - would be replaced with real API calls
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
  {
    id: "e3",
    title: "Academic Calendar Reform",
    description: "Vote on proposed changes to the academic calendar for next year.",
    candidates: ["Current Schedule", "4-day Week Proposal", "Early Summer Break"],
    votes: [521, 489, 312],
    totalVoters: 1500,
    startDate: "2023-03-20",
    endDate: "2023-04-05",
    status: "completed",
  },
]

export function ActiveElections() {
  const [elections, setElections] = useState(mockElections)

  useEffect(() => {
    fetchElections()
      .then((data) => {
        // Make sure data exists and is an array before setting state
        if (data && Array.isArray(data)) {
          setElections(data)
        }
      })
      .catch((error) => {
        console.error("Error fetching elections:", error)
        // Keep using the mock elections on error
      })
  }, [])

  const totalVotes = (votes: number[] | undefined) => {
    if (!votes || !Array.isArray(votes)) return 0
    return votes.reduce((sum, current) => sum + (current || 0), 0)
  }

  return (
    <div className="space-y-4">
      {(elections || [])
        .filter((e) => e && e.status === "active")
        .map((election) => (
          <Card key={election.id || "unknown"}>
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle>{election.title}</CardTitle>
                  <CardDescription>{election.description}</CardDescription>
                </div>
                <Badge variant={election.status === "active" ? "default" : "secondary"}>
                  {election.status === "active" ? "Active" : "Completed"}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center">
                    <Users className="mr-2 h-4 w-4 text-muted-foreground" />
                    <span>
                      {totalVotes(election.votes)} / {election.totalVoters} votes cast
                    </span>
                  </div>
                  <div className="flex items-center">
                    <Calendar className="mr-2 h-4 w-4 text-muted-foreground" />
                    <span>Ends {election.endDate}</span>
                  </div>
                </div>

                <Progress value={(totalVotes(election.votes) / election.totalVoters) * 100} className="h-2" />

                <div className="space-y-2">
                  {(election.candidates || []).map((candidate, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div
                          className="h-3 w-3 rounded-full"
                          style={{
                            backgroundColor:
                              index === 0 ? "#3b82f6" : index === 1 ? "#10b981" : index === 2 ? "#f59e0b" : "#ef4444",
                          }}
                        />
                        <span>{candidate}</span>
                      </div>
                      <div className="text-sm font-medium">
                        {election.votes[index]} votes (
                        {Math.round((election.votes[index] / totalVotes(election.votes)) * 100)}%)
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
            <CardFooter>
              <Button asChild className="w-full">
                <Link href={`/vote?election=${election.id}`}>
                  Cast Your Vote
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </CardFooter>
          </Card>
        ))}

      <div className="pt-2">
        <Link href="/elections" className="text-sm font-medium text-primary hover:underline flex items-center">
          View all elections
          <ArrowRight className="ml-1 h-4 w-4" />
        </Link>
      </div>
    </div>
  )
}
