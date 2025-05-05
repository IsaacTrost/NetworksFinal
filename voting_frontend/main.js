let electionsCache = [];

// Utility: Encode strings to Base64
function toBase64(str) {
  return btoa(unescape(encodeURIComponent(str)));
}

async function fetchNodeInfo() {
  const res = await fetch('/api/node-info');
  const data = await res.json();
  console.log("Node info:", data);
}

async function fetchElections() {
  const res = await fetch('/api/elections');
  if (!res.ok) throw new Error(`Failed to load elections: ${res.status}`);
  const elections = await res.json();
  electionsCache = elections;

  const electionSelect = document.getElementById('election');
  if (electionSelect) {
    electionSelect.innerHTML = '';
    elections.forEach(election => {
      const option = document.createElement('option');
      option.value = election.hash;
      option.textContent = election.name;
      electionSelect.appendChild(option);
    });

    electionSelect.addEventListener('change', () => {
      updateCandidates(elections);
    });

    updateCandidates(elections);
  }
}

function updateCandidates(elections) {
  const electionId = document.getElementById('election').value;
  const selected = elections.find(e => e.hash === electionId);
  const candidateSelect = document.getElementById('candidate');
  candidateSelect.innerHTML = '';
  if (selected && selected.choices) {
    selected.choices.forEach(c => {
      const option = document.createElement('option');
      option.value = c;
      option.textContent = c;
      candidateSelect.appendChild(option);
    });
  }
}

document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('vote-form')) {
    document.getElementById('vote-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const electionId = document.getElementById('election').value;
      const candidateId = document.getElementById('candidate').value;
      const privateKey = document.getElementById('privateKey').value;
      const publicKey = document.getElementById('publicKey').value;

      const res = await fetch('/api/vote', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          election_id: toBase64(electionId),
          candidate_id: toBase64(candidateId),
          private_key: toBase64(privateKey),
          public_key: publicKey,
          timestamp: Math.floor(Date.now() / 1000)
        })
      });

      const result = await res.json();
      const resultDiv = document.getElementById('vote-result');
      if (resultDiv) {
        resultDiv.classList.remove('d-none');
        resultDiv.textContent = result.message || result.error || 'Vote submitted.';
      }
    });
  }

  fetchNodeInfo();
  fetchElections();
});

