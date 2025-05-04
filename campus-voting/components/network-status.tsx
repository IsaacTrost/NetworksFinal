import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import type { BlockchainStatus } from "@/lib/types"
import { formatDistanceToNow } from "date-fns"
import { Activity, Clock, Database, Network, Shield } from "lucide-react"

interface NetworkStatusProps {
  status: BlockchainStatus
  isConnected: boolean
}

export default function NetworkStatus({ status, isConnected }: NetworkStatusProps) {
  return (
    <Card className="mb-6">
      <CardContent className="p-4">
        <div className="flex flex-wrap gap-4 justify-between">
          <div className="flex items-center">
            <Activity className="h-4 w-4 mr-2 text-muted-foreground" />
            <span className="text-sm mr-2">Network Status:</span>
            <Badge variant={isConnected ? "success" : "destructive"}>
              {isConnected ? "Connected" : "Disconnected"}
            </Badge>
          </div>

          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="flex items-center">
                  <Database className="h-4 w-4 mr-2 text-muted-foreground" />
                  <span className="text-sm">Block Height: {status.currentHeight}</span>
                </div>
              </TooltipTrigger>
              <TooltipContent>
                <p>Current blockchain height</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>

          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="flex items-center">
                  <Network className="h-4 w-4 mr-2 text-muted-foreground" />
                  <span className="text-sm">Peers: {status.peerCount}</span>
                </div>
              </TooltipTrigger>
              <TooltipContent>
                <p>Number of connected peers</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>

          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="flex items-center">
                  <Shield className="h-4 w-4 mr-2 text-muted-foreground" />
                  <span className="text-sm">Difficulty: {status.difficulty}</span>
                </div>
              </TooltipTrigger>
              <TooltipContent>
                <p>Current mining difficulty</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>

          {status.lastBlockTime && (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <div className="flex items-center">
                    <Clock className="h-4 w-4 mr-2 text-muted-foreground" />
                    <span className="text-sm">
                      Last Block: {formatDistanceToNow(new Date(status.lastBlockTime))} ago
                    </span>
                  </div>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Time since last block was mined</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
