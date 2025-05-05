async function fetchNodeInfo() {
  const res = await fetch('/api/node-info');
  const data = await res.json();
  document.getElementById('node-info').innerText =
    `Node: ${data.name} (${data.address}:${data.port})`;
}

async function fetchElections() {
  const res = await fetch('/api/elections');
  const elections = await res.json();

  const electionSelect = document.getElementById('election');
  electionSelect.innerHTML = '';
  elections.forEach(election => {
    const option = document.createElement('option');
    option.value = election.hash;
    option.textContent = election.name;
    electionSelect.appendChild(option);
  });

  electionSelect.addEventListener('change', () => updateCandidates(elections));
  updateCandidates(elections);
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
  resultDiv.classList.remove('d-none');
  resultDiv.textContent = result.message || result.error;
});

async function fetchResults() {
  const res = await fetch('/api/results');
  const data = await res.json();
  const resultsList = document.getElementById('results-list');
  resultsList.innerHTML = '';
  for (const name in data) {
    const item = document.createElement('li');
    item.className = 'list-group-item';
    item.textContent = `${name}: ${data[name].winner} (${data[name].total_votes} votes)`;
    resultsList.appendChild(item);
  }
}

async function loadAllBlockchainElections() {
  try {
    const res = await fetch('/api/elections');
    const elections = await res.json();

    const list = document.getElementById('all-elections-list');
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

// Initial load
fetchNodeInfo();
fetchElections();
fetchResults();
loadAllBlockchainElections();
