async function analyze() {

    const coins = document.getElementById("coinInput").value.trim().split(",");
    const output = document.getElementById("output");
    output.innerHTML = "<p>Loading analysis...</p>";

    try {
        const response = await fetch("http://localhost:8000/crypto/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ coins: coins.map(c => c.trim()) })
        });

        const data = await response.json();
        output.innerHTML = formatAnalysis(data.analysis);

    } catch (error) {
        output.innerHTML = "<p>Error fetching analysis.</p>";
    }
}

async function compare() {

    const coins = document.getElementById("coinInput").value.trim().split(",");
    const output = document.getElementById("output");
    output.innerHTML = "<p>Loading comparison...</p>";

    try {
        const response = await fetch("http://localhost:8000/crypto/compare", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ coins: coins.map(c => c.trim()) })
        });

        const data = await response.json();
        output.innerHTML = formatComparison(data.comparison);

    } catch (error) {
        output.innerHTML = "<p>Error fetching comparison.</p>";
    }
}

function formatAnalysis(analysisList) {
    let html = "";

    analysisList.forEach(item => {
        html += `
        <div class="coin-section">
            <h3>${item.coin.toUpperCase()}</h3>
            <p><strong>Summary:</strong> ${item.summary}</p>
            <p><strong>Sentiment:</strong> ${item.sentiment}</p>

            <h4>Key Factors:</h4>
            <ul>
                ${item.key_factors.map(k => `<li>${k.factor}: ${k.impact}</li>`).join("")}
            </ul>

            <h4>Insights:</h4>
            <ul>
                ${item.insights.map(i => `<li>${i.prediction} (Confidence: ${i.confidence}%)</li>`).join("")}
            </ul>

            <hr>
        </div>
        `;
    });

    return html;
}

function formatComparison(c) {
    return `
        <h3>Winner: ${c.winner.toUpperCase()}</h3>
        <p><strong>Summary:</strong> ${c.summary}</p>

        <h4>Reasons:</h4>
        <ul>
            ${c.reasons.map(r => `<li>${r}</li>`).join("")}
        </ul>
    `;
}
