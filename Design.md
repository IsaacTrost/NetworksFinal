# DESIGN.md – Distributed‑Voting Blockchain

https://arxiv.org/pdf/1702.02566

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [System Components](#2-system-components)
3. [Data Structures](#3-data-structures)
4. [Cryptography & Hashing](#4-cryptography--hashing)
5. [Consensus & Mining](#5-consensus--mining)
6. [Peer‑to‑Peer Protocol](#6-peer-to-peer-protocol)
7. [Node Lifecycle & Fork Resolution](#7-node-lifecycle--fork-resolution)
8. [Demo Application — Distributed Voting](#8-demo-application--distributed-voting)
9. [Security Model & Threat Analysis](#9-security-model--threat-analysis)
10. [Performance & Scalability](#10-performance--scalability)
11. [Extensibility & Extra‑Credit Features](#11-extensibility--extra-credit-features)

---

## 1  Project Overview
The goal is to implement a minimal yet *fully functional* blockchain network that anyone can audit and that **records votes for campus‑wide student elections**.  The network consists of **one tracker** (for peer discovery) and **three or more full‑node peers** (miners) hosted on Google Compute Engine VMs.  Each peer maintains the same append‑only ledger; the longest valid chain is considered canonical.

Key success criteria:
* All nodes converge on the same chain even adversarial traffic (assuming less than 51% of adversaries are coordinating).
* A vote can be cast exactly once and becomes practically immutable after *k* confirmations.
* Anyone (even a disconnected laptop) can recompute the tally from the publicly available chain.

---

## 2  System Components
| Component | Responsibility | Implementation |
|-----------|---------------|---------------|
|**Tracker**|Maintains the set of active peer addresses; relays incremental updates.|`tracker.py`, 0 persistent state.|
|**Peer Node**|Holds full chain, validates blocks/txs, mines, relays messages.|`node/` package, one process per VM.|
|**Voter**|Signs VoteTx and broadcasts to peers via HTTP API. Needs a valid key to sign votes, and can only sign once.|`voter.py`.|
|**Web UI**|Single‑page React app served from each node: cast vote, view live tally, block explorer.|`ui/` directory.|
|**Test Harness**|Automates failure injection and log capture for TESTING.md.|`tests/`|


---

## 3  Data Structures
### 3.1  VoteTx (transaction)
```text
struct VoteTx {
    bytes32 election_id;     // UUIDv4
    bytes32 voter_pk_hash;   // SHA‑256 of voter public key
    uint8   candidate_id;    // index in candidates[]
    uint64  timestamp;       // unix seconds
    bytes   signature;       // ECDSA over tx_hash
}
```
*Uniqueness rule*: only one VoteTx with the same `voter_pk_hash` **per election_id** is permitted.

### 3.2  BlockHeader
```text
index | prev_hash | merkle_root | timestamp | difficulty | nonce
```

### 3.3  BlockBody
`Vec<VoteTx>` (0 ≤ len ≤ MAX_TX_PER_BLOCK).

### 3.4  Merkle Tree
We store only the **root** in `BlockHeader`.  Leaf = `SHA‑256(tx_bytes)`.  Provides *O(log n)* inclusion proofs for lightweight clients, where n is the number of transactions in the block.

---

## 4  Cryptography & Hashing
* **Hash function:** SHA‑256 (stdlib `hashlib`).
* **Digital signature:** ECDSA over curve secp256k1 (same as Bitcoin).  Signatures verified with `cryptography` library.
* **Proof‑of‑Work target:** `SHA‑256(BlockHeader) < 2^(256‑difficulty)`.

---

## 5  Consensus & Mining
1. **Mining loop**
   ```python
   while True:
       header.nonce = random64()
       h = sha256(header_bytes)
       if h < target(difficulty):
           broadcast(NewBlock)
   ```
2. **Difficulty retarget** every 10 blocks to target 30 sec average block time:
   `new_diff = old_diff * (elapsed / (30 * 10))` (clamped). Elapsed is time for the last 10 blocks, based on reported timestamps in the mined blocks. Other nodes will not accept the block if the reported timestamp is more than 1 hour in the future, or before the 5th most recent block.
3. **Chain selection**: longest total difficulty; tie ⇒ lower block hash.

---

## 6  Peer‑to‑Peer Protocol
All messages are JSON over TCP + length‑prefix framing.

| Type | Payload | Purpose |
|------|---------|---------|
|`JOIN`|`{addr}`|Sent by peer to tracker at startup.|
|`PEERLIST`|`[addr]`|Tracker → peer (full list).|
|`PING/PONG`|`{ts}`|Liveness; RTT measuring.|
|`VOTE_TX`|`VoteTx`|Relay new transaction.|
|`NEW_BLOCK`|`Block`|Relay freshly mined block.|
|`GET_CHAIN`|`{from_index}`|Request missing blocks.|

Messages > 1 MB rejected.

---

 7  Node Lifecycle & Fork Resolution
1. **Startup**: node contacts tracker → receives peer list → opens outbound connections.
2. **Sync**: requests missing blocks until local tip matches network height.
3. **Normal operation**: validate → store → relay inbound TX or Block.
4. **Fork handling**:
   * If new block’s `prev_hash` matches local tip ⇒ append.
   * Else if block builds a branch with higher cumulative difficulty ⇒ *reorg*:
     
     ```text
     save orphan chain
     revert state → common_ancestor
     fast‑apply blocks of stronger branch
     ``
Orphaned branches are stored until their difficulty falls behind by some threshold from the leading branch.

---

8  Demo Application — Distributed Voting
Authentication/Registration
Setting up the Voting
Voting Process
Verifiability

8.1  Actors
| Role | Credential | Capability 
|Admin | Ed25519 keypair in `config/admin.pem`| Create election, close election |
|Voter | Keypair generated by wallet CLI| Cast exactly one VoteTx |
|Auditor| None | Read‑only; verify chain & tally |

### 8.2  Election Lifecycle
1. **Create** – Admin sends `ADMIN_TX {type:"CREATE", election_id, candidates[], voter_pks[],  close_time}`, 
2. **Cast vote** – Voter signs and POSTs `VoteTx` via `/api/vote` (HTTP) → node emits `VOTE_TX`.
3. **Close** – After `close_time`, miners refuse VoteTx for that election.
4. **Tally** – Deterministic `tally(chain, election_id)` runs in browser & CLI; returns `{candidate_id: count}`.
5. **UI** – React + recharts bar chart updates WebSocket `/ws/tally` every block.

### 8.3  Invalid‑Vote Scenarios to be Tested
* Double‑vote attempt
* Wrong signature
* Late vote after close
* Malformed tx structure

---

## 9  Security Model & Threat Analysis
Inclusion of the control node can be used 
| Threat | Mitigation |
|--------|-----------|
|Block tampering|SHA‑256 links; PoW cost makes deep rewrite infeasible.|
|51 % attack|On private net we simulate but document that public net would need > 50 % hash power.|

---

## 10  Performance 
* **Block size** 256 KB → ≈2 000 votes per block.
* **Throughput** @30 s block time ≈ 4 000 votes/min.
* **Disk usage** linear in blocks; with pruning mode a node may discard old blocks > k confirmations.

---

## 11  Extra‑Credit Features
* **Dynamic difficulty** implemented in §5.
* **Merkle proofs** enable light clients (extra credit).
* **Graphical dashboard** both for voting and for tracking live tallys  (React)