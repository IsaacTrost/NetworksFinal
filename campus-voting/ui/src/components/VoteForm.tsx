"use client"

import type React from "react"
import { useState, useEffect } from "react"

interface Candidate {
  id: number
  name: string
  party: string
}

interface Election {
  id: string
  title: string
  description?: string
  candidates: Candidate[]
  status: "active" | "closed"
  closeTime?: string
}

const VoteForm: React.FC = () => {
  const [elections, setElections] = useState<Election[]>([])
  const [selectedElection, setSelectedElection] = useState<string>("")
  const [selectedCandidate, setSelectedCandidate] = useState<string>("")
  const [privateKey, setPrivateKey] = useState<string>("")
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [txHash, setTxHash] = useState<string | null>(null)

  useEffect(() => {
    // Fetch available elections
    fetch("/api/elections")
      .then((response) => response.json())
      .then((data) => {
        setElections(data)
      })
      .catch((err) => {
        console.error("Failed to fetch elections:", err)
        setError("Failed to load elections. Please try again later.")
      })
  }, [])

  const handleElectionChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedElection(e.target.value)
    setSelectedCandidate("")
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    // Validate form
    if (!selectedElection) {
      setError("Please select an election.")
      return
    }

    if (!selectedCandidate) {
      setError("Please select a candidate.")
      return
    }

    if (!privateKey) {
      setError("Please enter your private key.")
      return
    }

    if (privateKey.length < 64) {
      setError("Private key must be at least 64 characters.")
      return
    }

    setIsSubmitting(true)
    setError(null)
    setSuccess(null)
    setTxHash(null)

    try {
      const response = await fetch("/api/vote", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          election_id: selectedElection,
          private_key: privateKey,
          candidate_id: Number.parseInt(selectedCandidate),
          timestamp: Math.floor(Date.now() / 1000), // Unix timestamp in seconds
        }),
      })

      const data = await response.json()

      if (response.ok) {
        setSuccess("Your vote has been submitted to the blockchain!")
        setTxHash(data.tx_hash)
        // Reset form
        setSelectedElection("")
        setSelectedCandidate("")
        setPrivateKey("")
      } else {
        setError(data.error || "Failed to submit vote. Please try again.")
      }
    } catch (err) {
      console.error("Error submitting vote:", err)
      setError("An error occurred while submitting your vote. Please try again.")
    } finally {
      setIsSubmitting(false)
    }
  }

  // Get the selected election object
  const election = elections.find((e) => e.id === selectedElection)

  return (
    <div className="card">
      <div className="card-header">
        <h2 className="card-title">Cast Your Vote</h2>
        <p className="card-description">
          Submit your vote to the blockchain. Once submitted, your vote cannot be changed.
        </p>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      {success && (
        <div className="alert alert-success">
          <p>{success}</p>
          {txHash && (
            <div className="mt-2">
              <p>
                <strong>Transaction Hash:</strong>
              </p>
              <code className="font-mono p-2 bg-gray-100 block overflow-x-auto text-sm">{txHash}</code>
              <p className="text-muted mt-2 text-sm">
                Your vote will be included in the blockchain once miners confirm it. This usually takes a few minutes.
              </p>
            </div>
          )}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="election" className="form-label">
            Election
          </label>
          <select
            id="election"
            className="form-select"
            value={selectedElection}
            onChange={handleElectionChange}
            disabled={isSubmitting}
          >
            <option value="">Select an election</option>
            {elections.map((election) => (
              <option key={election.id} value={election.id}>
                {election.title}
              </option>
            ))}
          </select>
          <div className="form-help">Select the election you want to participate in.</div>
        </div>

        {election && (
          <div className="form-group">
            <label htmlFor="candidate" className="form-label">
              Candidate
            </label>
            <select
              id="candidate"
              className="form-select"
              value={selectedCandidate}
              onChange={(e) => setSelectedCandidate(e.target.value)}
              disabled={isSubmitting}
            >
              <option value="">Select a candidate</option>
              {election.candidates.map((candidate) => (
                <option key={candidate.id} value={candidate.id.toString()}>
                  {candidate.name} ({candidate.party})
                </option>
              ))}
            </select>
            <div className="form-help">Select the candidate you wish to vote for.</div>
          </div>
        )}

        <div className="form-group">
          <label htmlFor="privateKey" className="form-label">
            Your Private Key
          </label>
          <input
            type="password"
            id="privateKey"
            className="form-control"
            value={privateKey}
            onChange={(e) => setPrivateKey(e.target.value)}
            placeholder="Enter your private key"
            disabled={isSubmitting}
          />
          <div className="form-help">
            This is the private key provided to you by the election committee. Your vote will be signed with this key.
          </div>
        </div>

        <button type="submit" className="btn btn-primary btn-block" disabled={isSubmitting}>
          {isSubmitting ? (
            <>
              <span className="spinner mr-2"></span>
              Submitting...
            </>
          ) : (
            "Submit Vote"
          )}
        </button>
      </form>
    </div>
  )
}

export default VoteForm
