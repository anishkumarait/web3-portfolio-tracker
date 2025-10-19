// --------------------- Chart Logic ---------------------
let trendChart;

function drawChart(fiat) {
  if (!priceTrends[fiat] || priceTrends[fiat].length === 0) return;

  const ctx = document.getElementById('priceTrendChart').getContext('2d');
  const hourly = priceTrends[fiat];

  if (trendChart) trendChart.destroy();

  trendChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: hourly.map((_, i) => i),
      datasets: [{
        label: "ETH Price (" + fiat.toUpperCase() + ")",
        data: hourly,
        borderColor: '#36a2eb',
        fill: false
      }]
    },
    options: {
      scales: {
        x: { ticks: { color: 'white' } },
        y: { ticks: { color: 'white' } }
      },
      plugins: { legend: { labels: { color: 'white' } } }
    }
  });
}

// --------------------- Button Events ---------------------
document.querySelectorAll(".select-currency").forEach(btn => {
  btn.addEventListener("click", () => drawChart(btn.dataset.fiat));
});

// --------------------- Update Table ---------------------
function updateTable(values) {
  const tableBody = document.querySelector("table tbody");
  if (!tableBody) return;

  tableBody.innerHTML = "";  // clear existing rows
  for (const fiat in values) {
    const row = document.createElement("tr");
    const cellFiat = document.createElement("td");
    cellFiat.textContent = fiat.toUpperCase();
    const cellValue = document.createElement("td");
    cellValue.textContent = values[fiat];
    row.appendChild(cellFiat);
    row.appendChild(cellValue);
    tableBody.appendChild(row);
  }
}

// --------------------- Auto Refresh ---------------------
if (walletAddress) {
  setInterval(() => {
    fetch(`/refresh/${walletAddress}`)
      .then(res => res.json())
      .then(data => {
        if (data.balance) {
          // Update balance display
          const balanceElem = document.querySelector("h4");
          if (balanceElem) balanceElem.textContent = `💰 ETH Balance: ${data.balance} ETH`;

          // Update table
          updateTable(data.values);

          // Update chart for currently selected currency
          const activeBtn = document.querySelector(".select-currency.active") || document.querySelector(".select-currency");
          if (activeBtn) drawChart(activeBtn.dataset.fiat);

          // Update local priceTrends object
          window.priceTrends = data.price_trends;
        }
      });
  }, 60000);
}

// --------------------- Initial Setup ---------------------
if (fiats.length > 0) {
  drawChart(fiats[0]);
  // Mark first currency as active
  const firstBtn = document.querySelector(".select-currency");
  if (firstBtn) firstBtn.classList.add("active");
}

// Highlight selected currency
document.querySelectorAll(".select-currency").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".select-currency").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
  });
});
