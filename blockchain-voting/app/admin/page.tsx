"use client"

import { useState } from "react"
import Link from "next/link"
import { ArrowLeft, Calendar, Plus, Save, Trash, Users } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"

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
  {
    id: "e3",
    title: "Academic Calendar Reform",
    description: "Vote on proposed changes to the academic calendar for next year.",
    candidates: ["Current Schedule", "4-day Week Proposal", "Early Summer Break"],
    startDate: "2023-03-20",
    endDate: "2023-04-05",
    status: "completed",
  },
]

export default function AdminPage() {
  const [elections, setElections] = useState(mockElections)
  const [newElection, setNewElection] = useState({
    title: "",
    description: "",
    startDate: "",
    endDate: "",
    candidates: ["", ""],
  })

  const addCandidate = () => {
    setNewElection({
      ...newElection,
      candidates: [...newElection.candidates, ""],
    })
  }

  const removeCandidate = (index: number) => {
    setNewElection({
      ...newElection,
      candidates: newElection.candidates.filter((_, i) => i !== index),
    })
  }

  const updateCandidate = (index: number, value: string) => {
    const updatedCandidates = [...newElection.candidates]
    updatedCandidates[index] = value
    setNewElection({
      ...newElection,
      candidates: updatedCandidates,
    })
  }

  const handleCreateElection = () => {
    // In a real implementation, this would create a new election on the blockchain
    alert("Election creation would be implemented here")
  }

  return (
    <div className="container max-w-6xl py-12">
      <Link href="/" className="flex items-center text-sm font-medium text-muted-foreground hover:text-foreground mb-8">
        <ArrowLeft className="mr-2 h-4 w-4" />
        Back to Dashboard
      </Link>

      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Admin Dashboard</h1>
          <p className="text-muted-foreground mt-2">Create and manage elections on the blockchain</p>
        </div>

        <Tabs defaultValue="elections">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="elections">Manage Elections</TabsTrigger>
            <TabsTrigger value="create">Create Election</TabsTrigger>
          </TabsList>

          <TabsContent value="elections" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Active Elections</CardTitle>
                <CardDescription>View and manage currently active elections</CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Title</TableHead>
                      <TableHead>Start Date</TableHead>
                      <TableHead>End Date</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {(elections || []).map((election) => (
                      <TableRow key={election.id || "unknown"}>
                        <TableCell className="font-medium">{election.title}</TableCell>
                        <TableCell>{election.startDate}</TableCell>
                        <TableCell>{election.endDate}</TableCell>
                        <TableCell>
                          <Badge variant={election.status === "active" ? "default" : "secondary"}>
                            {election.status === "active" ? "Active" : "Completed"}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex gap-2">
                            <Button variant="outline" size="sm" asChild>
                              <Link href={`/admin/elections/${election.id}`}>View</Link>
                            </Button>
                            {election.status === "active" && (
                              <Button variant="destructive" size="sm">
                                Close
                              </Button>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="create" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Create New Election</CardTitle>
                <CardDescription>Set up a new election to be deployed on the blockchain</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4">
                  <div className="grid gap-2">
                    <Label htmlFor="title">Election Title</Label>
                    <Input
                      id="title"
                      placeholder="Enter election title"
                      value={newElection.title}
                      onChange={(e) => setNewElection({ ...newElection, title: e.target.value })}
                    />
                  </div>

                  <div className="grid gap-2">
                    <Label htmlFor="description">Description</Label>
                    <Textarea
                      id="description"
                      placeholder="Describe the purpose of this election"
                      value={newElection.description}
                      onChange={(e) => setNewElection({ ...newElection, description: e.target.value })}
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="grid gap-2">
                      <Label htmlFor="start-date">Start Date</Label>
                      <div className="flex items-center">
                        <Calendar className="mr-2 h-4 w-4 text-muted-foreground" />
                        <Input
                          id="start-date"
                          type="date"
                          value={newElection.startDate}
                          onChange={(e) => setNewElection({ ...newElection, startDate: e.target.value })}
                        />
                      </div>
                    </div>

                    <div className="grid gap-2">
                      <Label htmlFor="end-date">End Date</Label>
                      <div className="flex items-center">
                        <Calendar className="mr-2 h-4 w-4 text-muted-foreground" />
                        <Input
                          id="end-date"
                          type="date"
                          value={newElection.endDate}
                          onChange={(e) => setNewElection({ ...newElection, endDate: e.target.value })}
                        />
                      </div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label>Candidates</Label>
                      <Button variant="outline" size="sm" onClick={addCandidate}>
                        <Plus className="mr-2 h-4 w-4" />
                        Add Candidate
                      </Button>
                    </div>

                    <div className="space-y-2">
                      {(newElection.candidates || []).map((candidate, index) => (
                        <div key={index} className="flex items-center gap-2">
                          <Input
                            placeholder={`Candidate ${index + 1}`}
                            value={candidate}
                            onChange={(e) => updateCandidate(index, e.target.value)}
                          />
                          {newElection.candidates.length > 2 && (
                            <Button variant="ghost" size="icon" onClick={() => removeCandidate(index)}>
                              <Trash className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="grid gap-2">
                    <Label htmlFor="voters">Eligible Voters</Label>
                    <div className="flex items-center">
                      <Users className="mr-2 h-4 w-4 text-muted-foreground" />
                      <Input id="voters" placeholder="Upload CSV file with voter public keys" disabled />
                      <Button variant="outline" className="ml-2">
                        Upload
                      </Button>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Upload a CSV file containing the public keys of all eligible voters.
                    </p>
                  </div>
                </div>
              </CardContent>
              <CardFooter>
                <Button onClick={handleCreateElection} className="w-full">
                  <Save className="mr-2 h-4 w-4" />
                  Create Election
                </Button>
              </CardFooter>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
