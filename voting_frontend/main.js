let electionsCache = [];
let chart;

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
      updateChart();
    });

    updateCandidates(elections);
    updateChart();
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

async function updateChart() {
  const electionId = document.getElementById('election')?.value;
  if (!electionId) return;

  try {
    const res = await fetch('/api/results');
    if (!res.ok) throw new Error(`Failed to fetch results: ${res.status}`);
    const results = await res.json();

    const selectedElection = electionsCache.find(e => e.hash === electionId);
    if (!selectedElection) return;

    const candidateData = selectedElection.choices.reduce((acc, c) => {
      acc[c] = 0;
      return acc;
    }, {});

    const electionResult = results[selectedElection.name];
    if (electionResult?.per_candidate) {
      for (const [candidate, count] of Object.entries(electionResult.per_candidate)) {
        candidateData[candidate] = count;
      }
    }

    const ctx = document.getElementById('voteChart');
    if (!ctx) return;

    if (chart) chart.destroy();

    chart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: Object.keys(candidateData),
        datasets: [{
          label: 'Votes',
          data: Object.values(candidateData),
          backgroundColor: 'rgba(75, 192, 192, 0.6)'
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } }
      }
    });
  } catch (err) {
    console.error('Failed to update chart:', err);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('vote-form')) {
    document.getElementById('vote-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const electionId = document.getElementById('election').value;
      const candidateId = document.getElementById('candidate').value;
      const privateKey = document.getElementById('privateKey').value;

      const res = await fetch('/api/vote', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          election_id: electionId,
          candidate_id: candidateId,
          private_key: privateKey,
          timestamp: Math.floor(Date.now() / 1000)
        })
      });

      const result = await res.json();
      const resultDiv = document.getElementById('vote-result');
      if (resultDiv) {
        resultDiv.classList.remove('d-none');
        resultDiv.textContent = result.message || result.error || 'Vote submitted.';
      }

      updateChart();
    });
  }

  fetchNodeInfo();
  fetchElections();
  fetchResults();
  loadAllBlockchainElections();
});

async function fetchResults() {
  const resultsList = document.getElementById('results-list');
  if (!resultsList) return;
  const res = await fetch('/api/results');
  if (!res.ok) throw new Error(`Failed to fetch results: ${res.status}`);
  const data = await res.json();
  resultsList.innerHTML = '';
  for (const name in data) {
    const item = document.createElement('li');
    item.className = 'list-group-item';
    item.textContent = `${name}: ${data[name].winner} (${data[name].total_votes} votes)`;
    resultsList.appendChild(item);
  }
}

async function loadAllBlockchainElections() {
  const list = document.getElementById('all-elections-list');
  if (!list) return;
  try {
    const res = await fetch('/api/elections');
    if (!res.ok) throw new Error(`Failed to load elections list: ${res.status}`);
    const elections = await res.json();
    list.innerHTML = '';
    elections.forEach(e => {
      const li = document.createElement('li');
      li.className = 'list-group-item';
      const endDate = new Date(e.end_time * 1000);
      const now = new Date();
      const status = now < endDate ? 'Open' : 'Ended';
      li.innerHTML = `
        <strong>${e.name}</strong><br>
        <small>Hash: ${e.hash}</small><br>
        <small>Candidates: ${e.choices.join(', ')}</small><br>
        <small>Total Votes: ${e.total_votes}</small><br>
        <small>Status: ${status}</small><br>
        ${status === 'Ended' && e.winner ? `<small>Winner: ${e.winner}</small><br>` : ''}
      `;
      list.appendChild(li);
    });
  } catch (err) {
    console.error('Error loading blockchain elections:', err);
  }
}
