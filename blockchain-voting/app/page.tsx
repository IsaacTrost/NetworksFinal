import Link from "next/link"
import { ArrowRight, BarChart3, CheckCircle, FileText, Shield } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { BlockchainStats } from "@/components/blockchain-stats"
import { ActiveElections } from "@/components/active-elections"

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-16 items-center">
          <Link href="/" className="flex items-center gap-2 font-bold">
            <Shield className="h-6 w-6" />
            <span>BlockVote</span>
          </Link>
          <nav className="ml-auto flex gap-4 sm:gap-6">
            <Link href="/" className="text-sm font-medium text-foreground">
              Dashboard
            </Link>
            <Link href="/vote" className="text-sm font-medium text-muted-foreground hover:text-foreground">
              Vote
            </Link>
            <Link href="/explorer" className="text-sm font-medium text-muted-foreground hover:text-foreground">
              Explorer
            </Link>
            <Link href="/admin" className="text-sm font-medium text-muted-foreground hover:text-foreground">
              Admin
            </Link>
          </nav>
        </div>
      </header>
      <main className="flex-1">
        <section className="w-full py-12 md:py-24 lg:py-32 bg-gradient-to-b from-muted/50 to-background">
          <div className="container px-4 md:px-6">
            <div className="flex flex-col items-center justify-center space-y-4 text-center">
              <div className="space-y-2">
                <h1 className="text-3xl font-bold tracking-tighter sm:text-4xl md:text-5xl">
                  Secure Distributed Voting on Blockchain
                </h1>
                <p className="mx-auto max-w-[700px] text-muted-foreground md:text-xl">
                  A transparent, immutable, and verifiable voting system built on blockchain technology
                </p>
              </div>
              <div className="flex flex-col gap-2 min-[400px]:flex-row">
                <Button asChild>
                  <Link href="/vote">
                    Cast Your Vote
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Link>
                </Button>
                <Button variant="outline" asChild>
                  <Link href="/explorer">View Blockchain</Link>
                </Button>
              </div>
            </div>
          </div>
        </section>

        <section className="container px-4 py-12 md:px-6">
          <div className="grid gap-6 lg:grid-cols-2 lg:gap-12">
            <div className="space-y-4">
              <h2 className="text-3xl font-bold tracking-tight">Active Elections</h2>
              <p className="text-muted-foreground">
                Current elections open for voting. Cast your vote securely using your wallet.
              </p>
              <ActiveElections />
            </div>
            <div className="space-y-4">
              <h2 className="text-3xl font-bold tracking-tight">Blockchain Status</h2>
              <p className="text-muted-foreground">Real-time statistics about the blockchain network.</p>
              <BlockchainStats />
            </div>
          </div>
        </section>

        <section className="container px-4 py-12 md:px-6">
          <h2 className="mb-8 text-3xl font-bold tracking-tight">How It Works</h2>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader>
                <CheckCircle className="h-10 w-10 text-primary mb-2" />
                <CardTitle>Secure Authentication</CardTitle>
              </CardHeader>
              <CardContent>
                <p>
                  Each voter has a unique cryptographic key pair that ensures only authorized voters can participate.
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <Shield className="h-10 w-10 text-primary mb-2" />
                <CardTitle>Immutable Records</CardTitle>
              </CardHeader>
              <CardContent>
                <p>Once cast, votes are permanently recorded on the blockchain and cannot be altered or deleted.</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <FileText className="h-10 w-10 text-primary mb-2" />
                <CardTitle>Transparent Verification</CardTitle>
              </CardHeader>
              <CardContent>
                <p>Anyone can verify the integrity of the election by auditing the public blockchain ledger.</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <BarChart3 className="h-10 w-10 text-primary mb-2" />
                <CardTitle>Real-time Results</CardTitle>
              </CardHeader>
              <CardContent>
                <p>View election results as they happen with live updates from the blockchain network.</p>
              </CardContent>
            </Card>
          </div>
        </section>
      </main>
      <footer className="border-t py-6 md:py-0">
        <div className="container flex flex-col items-center justify-between gap-4 md:h-16 md:flex-row">
          <p className="text-sm text-muted-foreground">
            &copy; {new Date().getFullYear()} BlockVote. All rights reserved.
          </p>
          <div className="flex gap-4 text-sm text-muted-foreground">
            <Link href="/about" className="hover:underline">
              About
            </Link>
            <Link href="/privacy" className="hover:underline">
              Privacy
            </Link>
            <Link href="/terms" className="hover:underline">
              Terms
            </Link>
          </div>
        </div>
      </footer>
    </div>
  )
}
