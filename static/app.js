const standingsBody = document.getElementById("standings-body");
const standingsEmpty = document.getElementById("standings-empty");
const standingsTable = document.getElementById("standings");
const historyList = document.getElementById("history");
const historyEmpty = document.getElementById("history-empty");
const errorBox = document.getElementById("error");
const matchA = document.getElementById("match-a");
const matchB = document.getElementById("match-b");
const matchFeedback = document.getElementById("match-feedback");

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || "Er ging iets mis");
  return data;
}

function showError(message) {
  errorBox.textContent = message;
  errorBox.hidden = false;
  setTimeout(() => (errorBox.hidden = true), 5000);
}

function fmtDelta(after, before) {
  const d = after - before;
  const cls = d > 0 ? "up" : d < 0 ? "down" : "";
  const sign = d > 0 ? "+" : "";
  return `<span class="delta ${cls}">${sign}${d.toFixed(1)}</span>`;
}

async function loadStandings() {
  try {
    const { players } = await api("/api/standings");
    standingsBody.innerHTML = "";
    standingsEmpty.style.display = players.length ? "none" : "";
    standingsTable.style.display = players.length ? "" : "none";
    for (const p of players) {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td class="rank">${p.rank}</td>
        <td></td>
        <td class="rating">${p.rating.toFixed(1)}</td>
        <td>${p.wins}</td>
        <td>${p.losses}</td>
        <td>${p.draws}</td>
        <td></td>`;
      tr.children[1].textContent = p.name;
      const del = document.createElement("button");
      del.className = "delete-btn";
      del.title = "Speler verwijderen";
      del.textContent = "✕";
      del.addEventListener("click", () => deletePlayer(p.id, p.name));
      tr.lastElementChild.appendChild(del);
      standingsBody.appendChild(tr);
    }
    fillSelects(players);
  } catch (e) {
    showError(e.message);
  }
}

function fillSelects(players) {
  for (const sel of [matchA, matchB]) {
    const current = sel.value;
    sel.innerHTML = '<option value="">-- kies speler --</option>';
    for (const p of players) {
      const opt = document.createElement("option");
      opt.value = p.id;
      opt.textContent = `${p.name} (${p.rating.toFixed(0)})`;
      sel.appendChild(opt);
    }
    sel.value = current;
  }
}

async function loadHistory() {
  try {
    const { matches } = await api("/api/matches?limit=50");
    historyList.innerHTML = "";
    historyEmpty.style.display = matches.length ? "none" : "";
    for (const m of matches) {
      const li = document.createElement("li");
      let text;
      if (m.result === "draw") {
        text = `${m.name_a} — ${m.name_b} (gelijkspel)`;
      } else {
        const winner = m.result === "A" ? m.name_a : m.name_b;
        const loser = m.result === "A" ? m.name_b : m.name_a;
        text = `${winner} wint van ${loser}`;
      }
      const deltaA = m.result === "A" ? fmtDelta(m.rating_a_after, m.rating_a_before) : "";
      const deltaB = m.result === "B" ? fmtDelta(m.rating_b_after, m.rating_b_before) : "";
      li.innerHTML = `<span></span><span>${deltaA} ${deltaB}<span class="date">${m.created_at}</span></span>`;
      li.firstElementChild.textContent = text;
      historyList.appendChild(li);
    }
  } catch (e) {
    showError(e.message);
  }
}

document.getElementById("add-player-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const input = document.getElementById("player-name");
  try {
    await api("/api/players", { method: "POST", body: JSON.stringify({ name: input.value }) });
    input.value = "";
    await loadStandings();
  } catch (err) {
    showError(err.message);
  }
});

document.getElementById("match-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  matchFeedback.textContent = "";
  const result = new FormData(e.target).get("result");
  try {
    const res = await api("/api/matches", {
      method: "POST",
      body: JSON.stringify({ a: Number(matchA.value), b: Number(matchB.value), result }),
    });
    const m = res.match;
    const outcome =
      m.result === "draw"
        ? "Gelijkspel recorded"
        : `${m.a} wint van ${m.b}`;
    matchFeedback.textContent = `${outcome} — rating ${m.rating_a.after.toFixed(1)} / ${m.rating_b.after.toFixed(1)}`;
    e.target.reset();
    await loadStandings();
    await loadHistory();
  } catch (err) {
    showError(err.message);
  }
});

async function deletePlayer(id, name) {
  if (!confirm(`Weet je zeker dat je ${name} wilt verwijderen?`)) return;
  try {
    await api(`/api/players/${id}`, { method: "DELETE" });
    await loadStandings();
  } catch (err) {
    showError(err.message);
  }
}

loadStandings();
loadHistory();
