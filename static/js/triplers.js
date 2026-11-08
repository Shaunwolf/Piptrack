/* Tripler Lab: historical overlay, analog match, 3D views and the readings heatmap (Plotly) */
(function () {
  "use strict";
  const root = document.getElementById("tl");
  if (!root || !window.Plotly) return;
  const $ = (s) => root.querySelector(s);
  const INK = "#e8e6df", INK2 = "#a9a79f", INK3 = "#6e6c66", GRID = "#1f252d";
  const AMBER = "#c98500", BLUE = "#3987e5", GREY = "#8a8780";
  const cfg = { responsive: true, displaylogo: false };
  const base = {
    paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)", font: { family: "JetBrains Mono, monospace", size: 11, color: INK2 },
    margin: { l: 56, r: 16, t: 16, b: 44 }, hovermode: "closest", showlegend: true,
    legend: { orientation: "h", y: 1.08, x: 0, font: { size: 11 } },
  };
  const axis = (o) => Object.assign({ gridcolor: GRID, zeroline: false, linecolor: GRID, tickfont: { color: INK3 } }, o);
  const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const state = { tf: "1d", data: {}, match: null, view: "landscape" };
  const cache = {};

  async function load(tf) {
    if (cache[tf]) return cache[tf];
    const r = await fetch(`/api/pump-research/triplers/overlay?tf=${tf}`, { credentials: "same-origin" });
    cache[tf] = r.ok ? await r.json() : { error: (await r.json().catch(() => ({}))).error || r.statusText };
    return cache[tf];
  }

  function sample(arr, n) {
    if (arr.length <= n) return arr;
    const step = arr.length / n;
    return Array.from({ length: n }, (_, i) => arr[Math.floor(i * step)]);
  }

  function band(b, color, fill, name, dash) {
    if (!b || !b.offset || !b.offset.length) return [];
    return [
      { x: b.offset, y: b.q3, mode: "lines", line: { width: 0 }, hoverinfo: "skip", showlegend: false, type: "scatter" },
      { x: b.offset, y: b.q1, mode: "lines", line: { width: 0 }, fill: "tonexty", fillcolor: fill, hoverinfo: "skip",
        name: `${name} (middle half)`, type: "scatter" },
      { x: b.offset, y: b.median, mode: "lines", line: { color, width: 2.5, dash: dash || "solid" }, name: `${name} median`,
        hovertemplate: `${name} median %{y:.2f}× at bar %{x}<extra></extra>`, type: "scatter" },
    ];
  }

  function drawOverlay() {
    const d = state.data[state.tf];
    const el = $("#overlay");
    if (!d || d.error) { el.innerHTML = `<p class="obs-empty">${esc((d && d.error) || "Loading…")}</p>`; return; }
    const traces = [];
    if ($("#show-lines").checked) {
      sample(d.triplers, 160).forEach((t, i) => traces.push({
        type: "scatter", mode: "lines", x: t.offset, y: t.close, line: { color: AMBER, width: 1 }, opacity: 0.16,
        name: "Each tripler", legendgroup: "lines", showlegend: i === 0,
        hovertemplate: `${esc(t.ticker)} ${t.date} · %{y:.2f}× at bar %{x}<extra></extra>` }));
    }
    if ($("#show-ordinary").checked) traces.push(...band(d.bands.ordinary, GREY, "rgba(138,135,128,0.16)", "Ordinary", "dash"));
    traces.push(...band(d.bands.triplers, AMBER, "rgba(201,133,0,0.22)", "Triplers"));
    const m = state.match;
    if (m && m.timeframe === state.tf && m.live) {
      (m.matches || []).filter((x) => x.tripler).slice(0, 5).forEach((x, i) => traces.push({
        type: "scatter", mode: "lines", x: x.offset, y: x.close, line: { color: AMBER, width: 1.5, dash: "dot" },
        name: "Nearest tripler analogs", legendgroup: "analogs", showlegend: i === 0,
        hovertemplate: `${esc(x.ticker)} ${x.date} · %{y:.2f}×<extra>analog</extra>` }));
      traces.push({ type: "scatter", mode: "lines", x: m.live.offset, y: m.live.close, line: { color: BLUE, width: 3 },
        name: `${m.ticker} now`, hovertemplate: `${esc(m.ticker)} %{y:.2f}× of today's close, bar %{x}<extra></extra>` });
    }
    const layout = Object.assign({}, base, {
      xaxis: axis({ title: { text: `Bars from launch (${{ "1d": "days", "4h": "4-hour bars", "1h": "hours" }[state.tf]})` } }),
      yaxis: axis({ type: "log", title: { text: "Price vs launch close" }, tickformat: ".2~f", ticksuffix: "×" }),
      shapes: [{ type: "line", x0: 0, x1: 0, yref: "paper", y0: 0, y1: 1, line: { color: INK3, dash: "dot", width: 1 } },
               { type: "line", xref: "paper", x0: 0, x1: 1, y0: 3, y1: 3, line: { color: "rgba(201,133,0,0.4)", dash: "dot", width: 1 } }],
      annotations: [{ xref: "paper", x: 0, y: Math.log10(3), text: "3×", showarrow: false, xanchor: "left", yanchor: "bottom",
        font: { color: AMBER, size: 10 } }],
    });
    Plotly.react(el, traces, layout, cfg);
    $("#overlay-count").textContent = `${d.triplers.length} triplers · ${d.bands.ordinary.n} ordinary windows on this chart`;
  }

  function drawMatchPanel() {
    const p = $("#match-panel"), m = state.match;
    if (!m) return;
    if (m.error) { p.innerHTML = `<h3 class="tl-h3">Analog match</h3><p class="obs-note">${esc(m.error)}</p>`; return; }
    const items = (m.matches || []).map((x) => `<li><a href="/pump-research/triplers/event/${encodeURIComponent(x.id)}"
      ${x.tripler ? "" : 'tabindex="-1" aria-disabled="true" onclick="return false"'}>${esc(x.ticker)}</a> ${esc(x.date)}
      · <span class="${x.tripler ? "yes" : "muted"}">${x.tripler ? `tripled (peak ${Number(x.peak).toFixed(1)}×)` : "ordinary"}</span></li>`).join("");
    p.innerHTML = `<h3 class="tl-h3">${esc(m.ticker)} · last ${m.bars_compared} bars</h3>
      <div class="odds">${(m.tripler_share * 100).toFixed(0)}%</div>
      <p class="obs-note">of the ${m.k} most similar historical run-ups went on to triple, against ${(m.base_share * 100).toFixed(0)}%
        of all windows${m.lift ? ` (${m.lift}×)` : ""}. Data as of ${esc(m.as_of)}. A similar shape is a clue, not a forecast.</p>
      <ol>${items}</ol>`;
  }

  async function runMatch(ticker) {
    $("#match-panel").innerHTML = `<h3 class="tl-h3">Analog match</h3><p class="obs-note">Matching ${esc(ticker)}…</p>`;
    const r = await fetch(`/api/pump-research/triplers/match/${encodeURIComponent(ticker)}?tf=${state.tf}`, { credentials: "same-origin" });
    state.match = await r.json().catch(() => ({ error: "could not read the response" }));
    if (!state.match.ticker) state.match.ticker = ticker;
    drawMatchPanel(); drawOverlay();
  }

  // --- 3D -------------------------------------------------------------------------------------------
  function landscape(d) {
    const rows = sample(d.triplers, 120);
    const offs = [...new Set(rows.flatMap((t) => t.offset))].sort((a, b) => a - b);
    const z = rows.map((t) => { const m = new Map(t.offset.map((o, i) => [o, t.close[i]]));
      return offs.map((o) => (m.get(o) > 0 ? Math.log10(m.get(o)) : null)); });
    const text = rows.map((t) => offs.map(() => `${t.ticker} ${t.date}`));
    return { traces: [{ type: "surface", x: offs, y: rows.map((_, i) => i), z, text, hovertemplate:
      "%{text}<br>bar %{x}: %{customdata:.2f}×<extra></extra>", customdata: z.map((r) => r.map((v) => (v == null ? null : 10 ** v))),
      colorscale: [[0, "#1a1408"], [0.35, "#5c3d00"], [0.6, "#c98500"], [0.85, "#f5c460"], [1, "#fff1cc"]],
      cmin: -0.3, cmax: 0.8, showscale: false, contours: { z: { show: true, usecolormap: true, project: { z: true } } } }],
      scene: { xaxis: axis({ title: { text: "Bars from launch" }, backgroundcolor: "rgba(0,0,0,0)" }),
               yaxis: axis({ title: { text: "Tripler (biggest first)" }, showticklabels: false }),
               zaxis: axis({ title: { text: "Price vs launch (log10)" } }), camera: { eye: { x: -1.6, y: -1.5, z: 0.9 } },
               aspectratio: { x: 1.6, y: 1.2, z: 0.7 } },
      caption: "Each ridge is one tripler: flat ground before launch (bar 0), then the climb. Valleys after the peak show how fast the moves gave back." };
  }

  function phasePoints(t, n) {
    const z0 = t.offset.indexOf(0);
    if (z0 < 0) return null;
    const xs = [], ys = [], zs = [];
    for (let i = Math.max(20, z0 - n + 1); i <= z0; i++) {
      const hi = Math.max(...t.close.slice(i - 19, i + 1));
      const v = t.volume[i];
      if (!(hi > 0) || v == null || !(v > 0) || i < 5) continue;
      xs.push(t.close[i] / hi - 1); ys.push(Math.log2(v)); zs.push(t.close[i] / t.close[i - 5] - 1);
    }
    return xs.length > 2 ? { xs, ys, zs } : null;
  }

  function phase(d) {
    const n = { "1d": 15, "4h": 20, "1h": 35 }[state.tf];
    const traces = [];
    const add = (list, color, opacity, name) => sample(list, 140).forEach((t, i) => {
      const p = phasePoints(t, n); if (!p) return;
      traces.push({ type: "scatter3d", mode: "lines", x: p.xs, y: p.ys, z: p.zs, line: { color, width: 2 }, opacity,
        name, legendgroup: name, showlegend: !traces.some((x) => x.legendgroup === name), hovertemplate: `${esc(t.ticker)} ${t.date}<extra></extra>` });
      traces.push({ type: "scatter3d", mode: "markers", x: [p.xs.at(-1)], y: [p.ys.at(-1)], z: [p.zs.at(-1)], showlegend: false,
        marker: { size: 3, color }, opacity: Math.min(1, opacity + 0.3), hovertemplate: `${esc(t.ticker)} at launch<extra></extra>` });
    });
    add(d.ordinary, GREY, 0.18, "Ordinary windows");
    add(d.triplers, AMBER, 0.5, "Triplers");
    return { traces, scene: {
      xaxis: axis({ title: { text: "Below 20-bar high" }, tickformat: ".0%" }), yaxis: axis({ title: { text: "Volume vs normal (log2)" } }),
      zaxis: axis({ title: { text: "5-bar momentum" }, tickformat: ".0%" }), camera: { eye: { x: 1.5, y: -1.6, z: 0.8 } } },
      caption: `Each line is a stock's path through three readings over the last ${n} bars before launch (dot = launch bar): how far below its recent high it sat, how heavy volume was, and its short-term momentum. Where amber paths bunch away from grey is where triplers behaved differently.` };
  }

  function draw3d() {
    const d = state.data[state.tf];
    const el = $("#three");
    if (!d || d.error) { el.innerHTML = `<p class="obs-empty">${esc((d && d.error) || "Loading…")}</p>`; return; }
    const v = state.view === "landscape" ? landscape(d) : phase(d);
    Plotly.react(el, v.traces, Object.assign({}, base, { margin: { l: 0, r: 0, t: 10, b: 0 }, scene: v.scene }), cfg);
    $("#three-caption").textContent = v.caption;
    $("#view3d-note").textContent = "drag to rotate · scroll to zoom";
  }

  function drawMatrix() {
    const src = document.getElementById("matrix-data");
    if (!src) return;
    const mx = JSON.parse(src.textContent);
    const text = mx.rows.map((r, i) => mx.cols.map((c, j) => mx.lift_raw[i][j] == null ? "not tested" :
      `${r} · ${c}<br>${(mx.rate[i][j] * 100).toFixed(0)}% of triplers · lift ${mx.lift_raw[i][j]}× · q ${mx.q[i][j]}`));
    Plotly.newPlot(document.getElementById("matrix"), [{ type: "heatmap", z: mx.lift, x: mx.cols.map((c) => ({ "1h": "1-hour", "4h": "4-hour", "1d": "Daily" }[c])),
      y: mx.rows, text, hovertemplate: "%{text}<extra></extra>", zmid: 0, zmin: -2, zmax: 2, xgap: 2, ygap: 2,
      colorscale: [[0, "#3987e5"], [0.5, "#2a2f36"], [1, "#c98500"]],
      colorbar: { title: { text: "lift", side: "right" }, tickvals: [-2, -1, 0, 1, 2], ticktext: ["¼×", "½×", "1×", "2×", "4×"], thickness: 10 } }],
      Object.assign({}, base, { showlegend: false, margin: { l: 220, r: 30, t: 10, b: 40 }, yaxis: axis({ autorange: "reversed" }), xaxis: axis({ side: "top" }) }), cfg);
  }

  async function setTf(tf) {
    state.tf = tf;
    root.querySelectorAll("#tf button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.tf === tf)));
    state.data[tf] = await load(tf);
    drawOverlay(); draw3d();
    if (state.match && state.match.ticker && state.match.timeframe !== tf) runMatch(state.match.ticker);
  }

  $("#tf").addEventListener("click", (e) => { const b = e.target.closest("button[data-tf]"); if (b) setTf(b.dataset.tf); });
  $("#view3d").addEventListener("click", (e) => {
    const b = e.target.closest("button[data-view]"); if (!b) return;
    state.view = b.dataset.view;
    root.querySelectorAll("#view3d button").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
    draw3d();
  });
  ["#show-lines", "#show-ordinary"].forEach((s) => $(s).addEventListener("change", drawOverlay));
  $("#match-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const t = $("#match-ticker").value.trim().toUpperCase();
    if (/^[A-Z0-9.\-]{1,10}$/.test(t)) runMatch(t);
  });
  drawMatrix();
  setTf("1d");
})();
