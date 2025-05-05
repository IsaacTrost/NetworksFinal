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
      option.value = election.id;
      option.textContent = election.title;
      electionSelect.appendChild(option);
    });
  
    electionSelect.addEventListener('change', () => updateCandidates(elections));
    updateCandidates(elections);
  }
  
  function updateCandidates(elections) {
    const electionId = document.getElementById('election').value;
    const selected = elections.find(e => e.id === electionId);
    const candidateSelect = document.getElementById('candidate');
    candidateSelect.innerHTML = '';
    selected.candidates.forEach(c => {
      const option = document.createElement('option');
      option.value = c.id;
      option.textContent = `${c.name} (${c.party})`;
      candidateSelect.appendChild(option);
    });
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
        candidate_id: parseInt(candidateId),
        private_key: privateKey,
        timestamp: Math.floor(Date.now() / 1000)
      })
    });
  
    const result = await res.json();
    document.getElementById('vote-result').innerText = result.message;
  });
  
  async function fetchResults() {
    const res = await fetch('/api/results');
    const data = await res.json();
    const resultsList = document.getElementById('results-list');
    resultsList.innerHTML = '';
    data.forEach(result => {
      const item = document.createElement('li');
      item.textContent = `${result.candidate}: ${result.votes} vote(s)`;
      resultsList.appendChild(item);
    });
  }
  
  // Initial load
  fetchNodeInfo();
  fetchElections();
  