import { NextResponse } from "next/server"

/**
 * TEMPORARY PLACEHOLDER API ROUTE
 *
 * This file contains a mock implementation of the elections API route
 * that will be replaced with actual API calls once the backend integration is complete.
 *
 * TODO: Replace this mock implementation with actual API calls to your
 * blockchain backend (tracker.py and peer.py) when they're ready.
 */

export async function GET() {
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

  // Return mock data
  return NextResponse.json(mockElections)
}
