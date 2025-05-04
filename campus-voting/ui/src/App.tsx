"use client"

import React, { useState } from "react"
import { ChevronDown } from "lucide-react"
import VoteForm from "./components/VoteForm"
import ElectionResults from "./components/ElectionResults"
import BlockExplorer from "./components/BlockExplorer"
import NetworkStatus from "./components/NetworkStatus"
import "./App.css"

function App() {
  const [activeTab, setActiveTab] = useState("vote")
  const [nodeInfo, setNodeInfo] = useState({
    name: "",
    address: "",
    port: 0,
  })

  // Fetch node info on component mount
  React.useEffect(() => {
    fetch("/api/node-info")
      .then((res) => res.json())
      .then((data) => {
        setNodeInfo(data)
      })
      .catch((err) => {
        console.error("Failed to fetch node info:", err)
      })
  }, [])

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>Blockchain Voting System</h1>
        <div className="node-info">
          <div className="dropdown">
            <button className="dropdown-toggle">
              Node: {nodeInfo.name || "Loading..."} <ChevronDown size={16} />
            </button>
            <div className="dropdown-content">
              <p>
                <strong>Address:</strong> {nodeInfo.address}
              </p>
              <p>
                <strong>Port:</strong> {nodeInfo.port}
              </p>
            </div>
          </div>
        </div>
      </header>

      <NetworkStatus />

      <div className="tabs">
        <button className={activeTab === "vote" ? "active" : ""} onClick={() => setActiveTab("vote")}>
          Cast Vote
        </button>
        <button className={activeTab === "results" ? "active" : ""} onClick={() => setActiveTab("results")}>
          Election Results
        </button>
        <button className={activeTab === "explorer" ? "active" : ""} onClick={() => setActiveTab("explorer")}>
          Block Explorer
        </button>
      </div>

      <main className="content">
        {activeTab === "vote" && <VoteForm />}
        {activeTab === "results" && <ElectionResults />}
        {activeTab === "explorer" && <BlockExplorer />}
      </main>

      <footer className="app-footer">
        <p>Blockchain Voting System - {new Date().getFullYear()}</p>
      </footer>
    </div>
  )
}

export default App
