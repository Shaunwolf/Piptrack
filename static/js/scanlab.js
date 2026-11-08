/* Scan Lab: drag-and-drop scanner builder. Vanilla JS, no build step. */
(function () {
  "use strict";

  const $ = (sel, root) => (root || document).querySelector(sel);
  const $$ = (sel, root) => Array.from((root || document).querySelectorAll(sel));
  const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const csrf = () => ($('meta[name="csrf-token"]') || {}).content || "";
  const DRAFT_KEY = "scanlab.draft.v1";
  const BATCH = 40;

  const GLYPHS = {
    squeeze: '<path d="M2 3h12M2 13h12" stroke="currentColor" stroke-width="1.4"/><path d="M8 4.5v7M5.5 6.5 8 4.5l2.5 2M5.5 9.5 8 11.5l2.5-2" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/>',
    candles: '<path d="M4 2v3M4 11v3M12 1v4M12 12v3" stroke="currentColor" stroke-width="1.4"/><rect x="2.5" y="5" width="3" height="6" fill="currentColor"/><rect x="10.5" y="5" width="3" height="7" fill="none" stroke="currentColor" stroke-width="1.4"/>',
    harmonics: '<path d="M1 12 L4.5 3 L8 9 L11.5 4 L15 13" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/><circle cx="15" cy="13" r="1.6" fill="currentColor"/>',
    chart: '<path d="M1 4 L4.5 12 L8 6 L11.5 12 L15 4" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/><path d="M1 6.5h14" stroke="currentColor" stroke-width="1" stroke-dasharray="2 2"/>',
    fibgann: '<path d="M8 8 m0 -1 a1 1 0 1 1 -1 1 a2.5 2.5 0 0 1 2.5 -2.5 a4 4 0 0 1 4 4 a6.5 6.5 0 0 1 -6.5 6.5" fill="none" stroke="currentColor" stroke-width="1.4"/><path d="M1 3h14M1 8h4" stroke="currentColor" stroke-width="1" opacity=".6"/>',
    trend: '<path d="M1 13 C5 12 7 6 15 3" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M1 11 L4 12 L7 8 L10 9 L15 2" fill="none" stroke="currentColor" stroke-width="1" opacity=".6"/>',
    momentum: '<path d="M1 8 C3 2 5 2 7 8 S11 14 13 8 15 5 15 5" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M1 4h14M1 12h14" stroke="currentColor" stroke-width="1" stroke-dasharray="1.5 2" opacity=".6"/>',
    volatility: '<path d="M1 4 C5 6 11 6 15 2M1 12 C5 10 11 10 15 14" fill="none" stroke="currentColor" stroke-width="1.4"/><path d="M1 8h14" stroke="currentColor" stroke-width="1" opacity=".6"/>',
    volume: '<path d="M2 15V10M5 15V8M8 15V11M11 15V5M14 15V2" stroke="currentColor" stroke-width="2"/>',
    structure: '<path d="M1 4h14M1 12h14" stroke="currentColor" stroke-width="1.5"/><path d="M2 11 L5 5 L8 11 L11 5 L14 2" fill="none" stroke="currentColor" stroke-width="1" opacity=".7"/>',
    filters: '<path d="M1 2h14L9.5 8.5V14l-3-1.5V8.5Z" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/>',
    composite: '<path d="M4 1 C12 5 4 11 12 15M12 1 C4 5 12 11 4 15" fill="none" stroke="currentColor" stroke-width="1.3"/><path d="M5 4.5h6M5 11.5h6M6.5 8h3" stroke="currentColor" stroke-width="1"/>',
  };
  const glyph = (fam) => `<span class="lab-glyph" style="--fam:var(--f-${esc(fam)})" aria-hidden="true"><svg viewBox="0 0 16 16">${GLYPHS[fam] || ""}</svg></span>`;
  const GRIP = '<svg viewBox="0 0 12 18" aria-hidden="true"><g fill="currentColor"><circle cx="3" cy="3" r="1.4"/><circle cx="9" cy="3" r="1.4"/><circle cx="3" cy="9" r="1.4"/><circle cx="9" cy="9" r="1.4"/><circle cx="3" cy="15" r="1.4"/><circle cx="9" cy="15" r="1.4"/></g></svg>';

  let catalog = null, blocks = {}, families = {};
  let state = null;              // {name, scanId, spec, universe, timeframe, activeGroup}
  let results = [], lastRun = null, running = null, filter = "matches", openRows = new Set();
  let uidSeq = 0;
  const uid = (p) => `${p}${Date.now().toString(36)}${(uidSeq++).toString(36)}`;

  // --- API ----------------------------------------------------------------------------------------
  async function api(path, opts) {
    opts = opts || {};
    const res = await fetch(path, {
      method: opts.method || "GET", credentials: "same-origin", signal: opts.signal,
      headers: Object.assign({ "Accept": "application/json" }, opts.body ? { "Content-Type": "application/json", "X-CSRFToken": csrf() } :
        (opts.method && opts.method !== "GET" ? { "X-CSRFToken": csrf() } : {})),
      body: opts.body ? JSON.stringify(opts.body) : undefined,
    });
    let data = null;
    try { data = await res.json(); } catch (e) { /* not JSON */ }
    if (!res.ok) throw new Error((data && (data.error || data.description)) || `Request failed (${res.status})`);
    return data;
  }

  function toast(msg) {
    let t = $(".lab-toast");
    if (!t) { t = document.createElement("div"); t.className = "lab-toast"; t.setAttribute("role", "status"); $("#lab").appendChild(t); }
    t.textContent = msg; t.hidden = false;
    clearTimeout(toast._t); toast._t = setTimeout(() => { t.hidden = true; }, 3200);
  }

  // --- State ----------------------------------------------------------------------------------------
  function defaults(type) {
    const b = blocks[type], p = {};
    b.params.forEach((x) => { p[x.key] = Array.isArray(x.default) ? x.default.slice() : x.default; });
    return p;
  }
  function makeBlock(type, params) {
    return { uid: uid("b"), type, params: Object.assign(defaults(type), params || {}), weight: 1, negate: false, enabled: true, open: false };
  }
  function makeGroup(name, logic) { return { id: uid("g"), name: name || "New group", logic: logic || "all", min: 1, weight: 1, blocks: [] }; }

  function fromPreset(p) {
    const spec = JSON.parse(JSON.stringify(p.spec));
    return {
      name: p.title, scanId: null, timeframe: "1d",
      universe: { sectors: (p.universe.sectors || []).slice(), lists: (p.universe.lists || []).slice(), tickers: [] },
      spec: {
        match: spec.match || "all", mode: spec.mode || "strict", min_score: spec.min_score || 0,
        groups: spec.groups.map((g) => Object.assign(makeGroup(g.name, g.logic), { min: g.min || 1, weight: g.weight || 1,
          blocks: g.blocks.filter((b) => blocks[b.type]).map((b) => Object.assign(makeBlock(b.type, b.params), { weight: b.weight == null ? 1 : b.weight, negate: !!b.negate, enabled: b.enabled !== false })) })),
      },
      activeGroup: null,
    };
  }

  function specForServer() {
    return {
      match: state.spec.match, mode: state.spec.mode, min_score: state.spec.min_score,
      groups: state.spec.groups.map((g) => ({ name: g.name, logic: g.logic, min: g.min, weight: g.weight,
        blocks: g.blocks.map((b) => ({ uid: b.uid, type: b.type, params: b.params, weight: b.weight, negate: b.negate, enabled: b.enabled })) })),
    };
  }

  function save() {
    try { localStorage.setItem(DRAFT_KEY, JSON.stringify(state)); } catch (e) { /* storage unavailable */ }
  }
  function loadDraft() {
    try {
      const d = JSON.parse(localStorage.getItem(DRAFT_KEY) || "null");
      if (d && d.spec && Array.isArray(d.spec.groups)) {
        d.spec.groups.forEach((g) => { g.blocks = g.blocks.filter((b) => blocks[b.type]); g.blocks.forEach((b) => { b.params = Object.assign(defaults(b.type), b.params); }); });
        return d;
      }
    } catch (e) { /* ignore */ }
    return null;
  }
  function changed(opts) {
    save();
    renderSentence();
    if (!opts || opts.canvas !== false) renderCanvas();
  }

  function findBlock(buid) {
    for (const g of state.spec.groups) {
      const i = g.blocks.findIndex((b) => b.uid === buid);
      if (i >= 0) return { group: g, index: i, block: g.blocks[i] };
    }
    return null;
  }
  function targetGroup() {
    return state.spec.groups.find((g) => g.id === state.activeGroup) || state.spec.groups[state.spec.groups.length - 1];
  }
  function addBlock(type, groupId, index) {
    if (!state.spec.groups.length) state.spec.groups.push(makeGroup("Group 1"));
    const g = state.spec.groups.find((x) => x.id === groupId) || targetGroup();
    const b = makeBlock(type);
    b.open = true;
    g.blocks.splice(index == null ? g.blocks.length : index, 0, b);
    state.activeGroup = g.id;
    changed();
    const card = document.querySelector(`[data-uid="${b.uid}"]`);
    if (card) { card.scrollIntoView({ block: "nearest", behavior: "smooth" }); }
    toast(`Added ${blocks[type].title} to “${g.name}”`);
  }

  // --- Describing blocks in words ----------------------------------------------------------------------
  function optLabel(param, value) {
    const o = (param.options || []).find((x) => String(x[0]) === String(value));
    return o ? o[1].replace(/^[▲▼◆]\s*/, "") : String(value);
  }
  function describe(b) {
    const def = blocks[b.type];
    const bits = [];
    def.params.forEach((p) => {
      const v = b.params[p.key];
      if (p.kind === "multi") {
        const names = v.map((x) => optLabel(p, x));
        bits.push(names.length > 3 ? `${names.slice(0, 3).join(", ")} +${names.length - 3}` : names.join(", "));
      } else if (p.kind === "select") {
        if (!(p.key === "swing" && v === "auto")) bits.push(optLabel(p, v));
      } else if (p.kind === "toggle") {
        if (v) bits.push(p.label.toLowerCase());
      } else if (p.kind === "number") {
        if (p.key === "volume" && !v) return;
        bits.push(`${p.label.toLowerCase()} ${v}${p.unit && !p.unit.startsWith("bar") ? (p.unit.startsWith("%") ? "%" : " " + p.unit) : p.unit ? " " + p.unit : ""}`);
      }
    });
    return bits.filter(Boolean).join(" · ");
  }

  function universeText() {
    const u = state.universe, parts = [];
    if (u.sectors.length) parts.push(u.sectors.length > 3 ? `${u.sectors.length} sectors` : u.sectors.join(", "));
    u.lists.forEach((k) => { const l = catalog.universe.lists.find((x) => x.key === k); if (l) parts.push(l.title); });
    if (u.tickers.length) parts.push(u.tickers.length > 4 ? `${u.tickers.length} tickers` : u.tickers.join(", "));
    return parts.length ? parts.join(" + ") : "nothing yet (pick a sector or list)";
  }

  function renderSentence() {
    const tf = { "1d": "daily", "1wk": "weekly", "1h": "hourly" }[state.timeframe] || "daily";
    const gs = state.spec.groups.filter((g) => g.blocks.some((b) => b.enabled));
    if (!gs.length) {
      $("#sentence").innerHTML = `Scan <b>${esc(universeText())}</b> on the ${tf} chart. Drag blocks from the left to say what you're looking for.`;
      return;
    }
    const groupText = gs.map((g) => {
      const items = g.blocks.filter((b) => b.enabled).map((b) => `${b.negate ? "<b>not</b> " : ""}<b>${esc(blocks[b.type].title)}</b>`);
      const head = g.logic === "all" ? "all of" : g.logic === "any" ? "any of" : `at least ${g.min} of`;
      return `<span class="op">${esc(g.name.toUpperCase())}</span> ${head} ${items.join(", ")}`;
    });
    const joiner = state.spec.match === "all" ? ' <span class="op">AND</span> ' : ' <span class="op">OR</span> ';
    const mode = state.spec.mode === "ranked" ? ` Rank everything by blend score${state.spec.min_score ? ` and keep ${state.spec.min_score}+` : ""}.`
      : state.spec.min_score ? ` Keep matches scoring ${state.spec.min_score}+.` : "";
    $("#sentence").innerHTML = `Scan <b>${esc(universeText())}</b> on the ${tf} chart for stocks with ${groupText.join(joiner)}.${mode}`;
  }

  // --- Universe bar ----------------------------------------------------------------------------------------
  function renderUniverse() {
    const u = state.universe;
    $("#sectors").innerHTML = catalog.universe.sectors.map((s) =>
      `<button type="button" class="lab-chip" data-sector="${esc(s.name)}" aria-pressed="${u.sectors.includes(s.name)}">${esc(s.name)} <span class="n">${s.count}</span></button>`).join("");
    $("#lists").innerHTML = catalog.universe.lists.map((l) =>
      `<button type="button" class="lab-chip" data-list="${esc(l.key)}" aria-pressed="${u.lists.includes(l.key)}">${esc(l.title)} <span class="n">${l.count}</span></button>`).join("");
    $("#tickers").value = u.tickers.join(", ");
    $("#timeframe").innerHTML = catalog.timeframes.map((t) =>
      `<button type="button" data-tf="${t.key}" aria-pressed="${state.timeframe === t.key}">${esc(t.title)}</button>`).join("");
    const n = u.sectors.reduce((a, s) => a + ((catalog.universe.sectors.find((x) => x.name === s) || {}).count || 0), 0)
      + u.lists.reduce((a, k) => a + (Number((catalog.universe.lists.find((x) => x.key === k) || {}).count) || 0), 0) + u.tickers.length;
    const live = u.lists.some((k) => (catalog.universe.lists.find((x) => x.key === k) || {}).count === "live");
    $("#universe-count").textContent = n || live ? `≈ ${n} stocks${live ? " + live lists" : ""} to scan` : "Pick at least one sector, list or ticker";
  }

  // --- Palette ------------------------------------------------------------------------------------------------
  const closedFams = new Set();
  function renderPalette() {
    const q = ($("#block-search").value || "").trim().toLowerCase();
    const html = catalog.families.map((f) => {
      const items = catalog.blocks.filter((b) => b.family === f.id && (!q || (b.title + " " + b.summary + " " + f.title + " " +
        b.params.map((p) => (p.options || []).map((o) => o[1]).join(" ")).join(" ")).toLowerCase().includes(q)));
      if (!items.length) return "";
      const closed = closedFams.has(f.id) && !q;
      return `<div class="lab-fam${closed ? " closed" : ""}" data-fam="${esc(f.id)}">
        <button type="button" aria-expanded="${!closed}"><span class="caret" aria-hidden="true">▾</span>${esc(f.title)}<span class="n">${items.length}</span></button>
        <div class="lab-tiles">${items.map((b) => `<div class="lab-tile" data-type="${esc(b.id)}" title="${esc(b.summary)}">
          ${glyph(b.family)}<div><div class="t">${esc(b.title)}</div><div class="s">${esc(b.summary)}</div></div>
          <button type="button" class="add" data-add="${esc(b.id)}" aria-label="Add ${esc(b.title)}">+</button></div>`).join("")}</div></div>`;
    }).join("");
    $("#palette-list").innerHTML = html || `<p class="lab-note">No blocks match “${esc(q)}”.</p>`;
  }

  // --- Canvas -----------------------------------------------------------------------------------------------------
  const hitStats = {};    // uid -> {hits, total} from the last run
  function paramField(b, p) {
    const id = `${b.uid}-${p.key}`;
    const v = b.params[p.key];
    const help = p.help ? `<span class="help">${esc(p.help)}</span>` : "";
    if (p.kind === "select") {
      return `<div class="lab-field"><label for="${id}">${esc(p.label)}</label><select class="lab-input" id="${id}" data-param="${p.key}">
        ${p.options.map((o) => `<option value="${esc(o[0])}"${String(o[0]) === String(v) ? " selected" : ""}>${esc(o[1])}</option>`).join("")}</select>${help}</div>`;
    }
    if (p.kind === "multi") {
      const many = p.options.length > 8;
      return `<div class="lab-field"><span class="lbl">${esc(p.label)} <span class="muted mono">${v.length}/${p.options.length}</span></span>
        ${many ? `<div class="lab-multi-tools"><button type="button" class="lab-icon-btn" data-multi-all="${p.key}">All</button>
          <button type="button" class="lab-icon-btn" data-multi-none="${p.key}">None</button></div>` : ""}
        <div class="lab-multi" role="group" aria-label="${esc(p.label)}">${p.options.map((o) =>
          `<button type="button" class="lab-chip" data-multi="${p.key}" data-value="${esc(o[0])}" aria-pressed="${v.includes(String(o[0]))}">${esc(o[1])}</button>`).join("")}</div>${help}</div>`;
    }
    if (p.kind === "toggle") {
      return `<div class="lab-field"><label class="lab-switch"><input type="checkbox" id="${id}" data-param="${p.key}"${v ? " checked" : ""}> ${esc(p.label)}</label>${help}</div>`;
    }
    const steps = (p.max - p.min) / (p.step || 1);
    const range = steps <= 1000 ? `<input type="range" min="${p.min}" max="${p.max}" step="${p.step || 1}" value="${v}" data-param="${p.key}" aria-label="${esc(p.label)}">` : "";
    return `<div class="lab-field"><label for="${id}">${esc(p.label)} <span class="muted">${esc(p.unit || "")}</span></label>
      <div class="lab-num" style="${range ? "" : "grid-template-columns:1fr"}">${range}<input class="lab-input" id="${id}" type="number" min="${p.min}" max="${p.max}" step="${p.step || 1}" value="${v}" data-param="${p.key}"></div>${help}</div>`;
  }

  function card(b) {
    const def = blocks[b.type];
    const st = hitStats[b.uid];
    return `<div class="lab-card${b.enabled ? "" : " disabled"}${b.negate ? " negated" : ""}" data-uid="${b.uid}">
      <div class="lab-card-head">
        <button type="button" class="lab-grip" data-grip="${b.uid}" aria-label="Drag ${esc(def.title)} to move it">${GRIP}</button>
        ${glyph(def.family)}
        <div class="lab-card-title"><div class="t">${b.negate ? '<span class="not">NOT</span>' : ""}${esc(def.title)}
          ${st ? `<span class="stat" title="Stocks where this block hit in the last run">hit ${st.hits}/${st.total}</span>` : ""}</div>
          <div class="sum">${esc(describe(b))}</div></div>
        <div class="lab-card-tools">
          <span class="lab-weight" title="How much this block counts in the blend score"><button type="button" data-weight="-1" aria-label="Lower weight">−</button>×${b.weight}<button type="button" data-weight="1" aria-label="Raise weight">+</button></span>
          <button type="button" class="lab-icon-btn" data-act="negate" aria-pressed="${b.negate}" title="Invert: the stock must NOT show this">NOT</button>
          <button type="button" class="lab-icon-btn" data-act="toggle" aria-pressed="${!b.enabled}" title="Switch this block off without removing it">${b.enabled ? "On" : "Off"}</button>
          <button type="button" class="lab-icon-btn" data-act="dup" title="Duplicate">Copy</button>
          <button type="button" class="lab-icon-btn" data-act="remove" title="Remove" aria-label="Remove ${esc(def.title)}">✕</button>
          <button type="button" class="lab-icon-btn" data-act="open" aria-expanded="${b.open}">${b.open ? "Done" : "Edit"}</button>
        </div>
      </div>
      ${b.open ? `<div class="lab-card-body">${def.params.map((p) => paramField(b, p)).join("")}</div>` : ""}
    </div>`;
  }

  function renderCanvas() {
    const gs = state.spec.groups;
    $("#groups").innerHTML = gs.map((g, gi) => {
      const on = g.blocks.filter((b) => b.enabled).length;
      return `<div class="lab-group${g.id === state.activeGroup ? " active" : ""}" data-group="${g.id}">
        <div class="lab-group-head">
          <input class="lab-group-name" value="${esc(g.name)}" maxlength="60" aria-label="Group name" data-gname>
          <div class="lab-seg" role="group" aria-label="How many blocks must hit">
            <button type="button" data-logic="all" aria-pressed="${g.logic === "all"}">ALL</button>
            <button type="button" data-logic="any" aria-pressed="${g.logic === "any"}">ANY</button>
            <button type="button" data-logic="atleast" aria-pressed="${g.logic === "atleast"}">AT LEAST</button></div>
          ${g.logic === "atleast" ? `<input class="lab-input lab-atleast mono" type="number" min="1" max="${Math.max(1, on)}" value="${g.min}" data-gmin aria-label="At least how many">` : ""}
          <span class="lab-group-state">${on} block${on === 1 ? "" : "s"}</span>
          ${gi > 0 || gs.length > 1 ? `<button type="button" class="lab-icon-btn" data-gremove aria-label="Remove group ${esc(g.name)}">✕</button>` : ""}
        </div>
        <div class="lab-dropzone" data-drop="${g.id}">
          ${g.blocks.length ? g.blocks.map(card).join("") : `<div class="lab-empty">Drop blocks here, or press <b>+</b> on any block.<br>
            <span class="muted">${g.logic === "all" ? "Every block in this group must hit." : g.logic === "any" ? "Any one block is enough." : `At least ${g.min} must hit.`}</span></div>`}
        </div></div>`;
    }).join("");
    $("#match").innerHTML = `<button type="button" data-match="all" aria-pressed="${state.spec.match === "all"}">every group</button>
      <button type="button" data-match="any" aria-pressed="${state.spec.match === "any"}">any group</button>`;
    $("#mode").innerHTML = `<button type="button" data-mode="strict" aria-pressed="${state.spec.mode === "strict"}" title="Only stocks that pass the group rules">Strict</button>
      <button type="button" data-mode="ranked" aria-pressed="${state.spec.mode === "ranked"}" title="Every stock, ranked by how strongly the blocks agree">Ranked</button>`;
    $("#min-score").value = state.spec.min_score;
    $("#min-score-v").textContent = state.spec.min_score;
    $("#scan-name").value = state.name;
  }

  // --- Canvas events ---------------------------------------------------------------------------------------------
  function bindCanvas() {
    const groups = $("#groups");
    groups.addEventListener("click", (e) => {
      const groupEl = e.target.closest("[data-group]");
      if (!groupEl) return;
      const g = state.spec.groups.find((x) => x.id === groupEl.dataset.group);
      state.activeGroup = g.id;
      const t = e.target.closest("button");
      if (!t) { $$(".lab-group").forEach((el) => el.classList.toggle("active", el === groupEl)); return; }
      if (t.dataset.logic) { g.logic = t.dataset.logic; return changed(); }
      if (t.hasAttribute("data-gremove")) {
        if (g.blocks.length && !t.dataset.confirm) { t.dataset.confirm = "1"; t.textContent = "Remove?"; return; }
        state.spec.groups = state.spec.groups.filter((x) => x !== g); return changed();
      }
      const cardEl = t.closest("[data-uid]");
      if (!cardEl) return;
      const found = findBlock(cardEl.dataset.uid);
      if (!found) return;
      const b = found.block;
      if (t.dataset.weight) { b.weight = Math.max(0, Math.min(10, b.weight + Number(t.dataset.weight))); return changed(); }
      if (t.dataset.multi) {
        const v = t.dataset.value, arr = b.params[t.dataset.multi];
        const i = arr.indexOf(v);
        if (i >= 0) { if (arr.length > 1) arr.splice(i, 1); else return toast("Keep at least one selected"); } else arr.push(v);
        t.setAttribute("aria-pressed", String(i < 0));
        refreshCard(b); return changed({ canvas: false });
      }
      if (t.dataset.multiAll) { b.params[t.dataset.multiAll] = blocks[b.type].params.find((p) => p.key === t.dataset.multiAll).options.map((o) => String(o[0])); return changed(); }
      if (t.dataset.multiNone) { const opts = blocks[b.type].params.find((p) => p.key === t.dataset.multiNone).options; b.params[t.dataset.multiNone] = [String(opts[0][0])]; return changed(); }
      const act = t.dataset.act;
      if (act === "negate") b.negate = !b.negate;
      else if (act === "toggle") b.enabled = !b.enabled;
      else if (act === "open") b.open = !b.open;
      else if (act === "remove") found.group.blocks.splice(found.index, 1);
      else if (act === "dup") found.group.blocks.splice(found.index + 1, 0, Object.assign(JSON.parse(JSON.stringify(b)), { uid: uid("b") }));
      else return;
      changed();
    });
    const onInput = (e) => {
      const el = e.target;
      if (el.hasAttribute("data-gname")) {
        const g = state.spec.groups.find((x) => x.id === el.closest("[data-group]").dataset.group);
        g.name = el.value || "Group"; return changed({ canvas: false });
      }
      if (el.hasAttribute("data-gmin")) {
        const g = state.spec.groups.find((x) => x.id === el.closest("[data-group]").dataset.group);
        g.min = Math.max(1, parseInt(el.value || "1", 10)); return changed({ canvas: false });
      }
      const key = el.dataset.param;
      if (!key) return;
      const found = findBlock(el.closest("[data-uid]").dataset.uid);
      const p = blocks[found.block.type].params.find((x) => x.key === key);
      let v = el.type === "checkbox" ? el.checked : el.value;
      if (p.kind === "number") {
        v = Number(v);
        if (!isFinite(v)) return;
        v = Math.min(p.max, Math.max(p.min, v));
        $$(`[data-param="${key}"]`, el.closest(".lab-card")).forEach((x) => { if (x !== el) x.value = v; });
      }
      found.block.params[key] = v;
      refreshCard(found.block);
      changed({ canvas: false });
    };
    groups.addEventListener("input", onInput);
    groups.addEventListener("change", onInput);
  }
  function refreshCard(b) {
    const el = document.querySelector(`[data-uid="${b.uid}"] .sum`);
    if (el) el.textContent = describe(b);
    const cnt = document.querySelector(`[data-uid="${b.uid}"] .lbl .mono`);
    if (cnt) {
      const p = blocks[b.type].params.find((x) => x.kind === "multi");
      if (p) cnt.textContent = `${b.params[p.key].length}/${p.options.length}`;
    }
  }

  // --- Drag and drop (pointer events: mouse, pen and touch) ------------------------------------------------------
  const drag = { src: null, ghost: null, placeholder: null, target: null, index: 0, startX: 0, startY: 0, armed: false, timer: null, pointerId: null };

  function beginDrag(e, src) {
    drag.src = src;
    const label = src.type ? blocks[src.type].title : blocks[findBlock(src.uid).block.type].title;
    const fam = src.type ? blocks[src.type].family : blocks[findBlock(src.uid).block.type].family;
    const ghost = document.createElement("div");
    ghost.className = "lab-tile lab-ghost";
    ghost.innerHTML = `${glyph(fam)}<div><div class="t">${esc(label)}</div><div class="s">Drop into a group</div></div>`;
    document.querySelector("#lab").appendChild(ghost);
    drag.ghost = ghost;
    drag.placeholder = document.createElement("div");
    drag.placeholder.className = "lab-placeholder";
    document.body.classList.add("lab-dragging");
    if (src.uid) { const el = document.querySelector(`[data-uid="${src.uid}"]`); if (el) el.style.opacity = ".35"; }
    if (window.matchMedia("(max-width: 860px)").matches) setSheet(false);
    moveDrag(e);
  }

  function moveDrag(e) {
    if (!drag.ghost) return;
    drag.ghost.style.left = `${e.clientX - 30}px`;
    drag.ghost.style.top = `${e.clientY - 20}px`;
    const under = document.elementFromPoint(e.clientX, e.clientY);
    const zone = under && under.closest("[data-drop]");
    $$(".lab-dropzone.over").forEach((z) => { if (z !== zone) z.classList.remove("over"); });
    if (!zone) { drag.target = null; drag.placeholder.remove(); autoScroll(e); return; }
    zone.classList.add("over");
    const cards = $$(".lab-card", zone).filter((c) => !drag.src.uid || c.dataset.uid !== drag.src.uid);
    let index = cards.length;
    for (let i = 0; i < cards.length; i++) {
      const r = cards[i].getBoundingClientRect();
      if (e.clientY < r.top + r.height / 2) { index = i; break; }
    }
    drag.target = zone.dataset.drop;
    drag.index = index;
    const empty = $(".lab-empty", zone);
    if (empty) empty.hidden = true;
    if (index < cards.length) zone.insertBefore(drag.placeholder, cards[index]); else zone.appendChild(drag.placeholder);
    autoScroll(e);
  }

  function autoScroll(e) {
    const edge = 60;
    if (e.clientY < edge) window.scrollBy(0, -12);
    else if (e.clientY > window.innerHeight - edge) window.scrollBy(0, 12);
  }

  function endDrag(commit) {
    clearTimeout(drag.timer);
    if (drag.ghost) {
      drag.ghost.remove();
      drag.placeholder.remove();
      document.body.classList.remove("lab-dragging");
      $$(".lab-dropzone.over").forEach((z) => z.classList.remove("over"));
      if (commit && drag.target) {
        if (drag.src.type) addBlock(drag.src.type, drag.target, drag.index);
        else {
          const found = findBlock(drag.src.uid);
          const b = found.group.blocks.splice(found.index, 1)[0];
          const g = state.spec.groups.find((x) => x.id === drag.target);
          g.blocks.splice(Math.min(drag.index, g.blocks.length), 0, b);
          state.activeGroup = g.id;
          changed();
        }
      } else renderCanvas();
    }
    document.removeEventListener("touchmove", blockScroll, { passive: false });
    Object.assign(drag, { src: null, ghost: null, placeholder: null, target: null, armed: false, timer: null, pointerId: null });
  }
  function blockScroll(ev) { if (drag.armed || drag.ghost) ev.preventDefault(); }

  function bindDrag() {
    document.addEventListener("pointerdown", (e) => {
      if (e.button !== 0 && e.pointerType === "mouse") return;
      const grip = e.target.closest("[data-grip]");
      const tile = !grip && e.target.closest(".lab-tile[data-type]");
      if (!grip && !tile) return;
      if (tile && e.target.closest("button")) return;           // the + button adds instead
      const src = grip ? { uid: grip.dataset.grip } : { type: tile.dataset.type };
      Object.assign(drag, { startX: e.clientX, startY: e.clientY, pointerId: e.pointerId, src: null, armed: false });
      const pending = src;
      if (e.pointerType === "touch" && tile) {
        // Touch on a palette tile: a short press arms the drag so normal swipes still scroll the palette
        document.addEventListener("touchmove", blockScroll, { passive: false });
        drag.timer = setTimeout(() => { drag.armed = true; drag.pending = pending; if (navigator.vibrate) navigator.vibrate(10); }, 220);
      } else {
        drag.armed = true;
        document.addEventListener("touchmove", blockScroll, { passive: false });
      }
      drag.pending = pending;
      if (grip || e.pointerType !== "touch") e.preventDefault();   // no text selection while dragging
    });
    document.addEventListener("pointermove", (e) => {
      if (drag.pointerId !== e.pointerId) return;
      if (drag.ghost) { moveDrag(e); return; }
      const dist = Math.hypot(e.clientX - drag.startX, e.clientY - drag.startY);
      if (!drag.armed) { if (dist > 8) { clearTimeout(drag.timer); drag.pointerId = null; document.removeEventListener("touchmove", blockScroll, { passive: false }); } return; }
      if (dist > 6 && drag.pending) beginDrag(e, drag.pending);
    });
    document.addEventListener("pointerup", (e) => { if (drag.pointerId === e.pointerId) endDrag(true); });
    document.addEventListener("pointercancel", (e) => { if (drag.pointerId === e.pointerId) endDrag(false); });
    document.addEventListener("keydown", (e) => { if (e.key === "Escape" && drag.ghost) endDrag(false); });
  }

  // --- Running a scan ------------------------------------------------------------------------------------------------
  function setStatus(left, right) {
    $("#status").innerHTML = `<span>${left}</span>${right ? `<span>${right}</span>` : ""}`;
  }
  function setProgress(frac, live) {
    $("#progress").style.width = `${Math.round(frac * 100)}%`;
    $("#trace").classList.toggle("live", !!live);
  }

  async function runScan() {
    if (running) { running.abort(); return; }
    const spec = specForServer();
    if (!spec.groups.some((g) => g.blocks.some((b) => b.enabled))) return toast("Add at least one block first");
    const ctrl = new AbortController();
    running = ctrl;
    $("#run").textContent = "Stop";
    results = []; openRows.clear();
    Object.keys(hitStats).forEach((k) => delete hitStats[k]);
    renderResults();
    setProgress(0.02, true);
    setStatus("Gathering the stock list…");
    try {
      const u = await api("/api/scan-lab/universe", { method: "POST", body: { universe: state.universe }, signal: ctrl.signal });
      if (!u.tickers.length) throw new Error("Pick at least one sector, list or ticker to scan");
      const total = u.tickers.length;
      let done = 0, missing = [], seconds = 0, asOf = "";
      for (let i = 0; i < total; i += BATCH) {
        const tickers = u.tickers.slice(i, i + BATCH);
        const sector_of = {}; tickers.forEach((t) => { sector_of[t] = u.sector_of[t]; });
        setStatus(`Scanning ${Math.min(i + BATCH, total)} of ${total}…`, `${results.filter((r) => r.matched).length} matches so far`);
        const out = await api("/api/scan-lab/run", { method: "POST", signal: ctrl.signal,
          body: { spec, tickers, sector_of, timeframe: state.timeframe, include_misses: true } });
        results = results.concat(out.results);
        missing = missing.concat(out.missing);
        seconds += out.seconds;
        out.results.forEach((r) => { if (r.as_of > asOf) asOf = r.as_of; });
        done += tickers.length;
        setProgress(done / total, true);
        tallyHits(); renderResults();
      }
      lastRun = { total, missing, seconds, asOf };
      const m = results.filter((r) => r.matched).length;
      setStatus(`${m} match${m === 1 ? "" : "es"} out of ${total - missing.length} stocks`,
        missing.length ? `${missing.length} without data` : `${seconds.toFixed(1)} s`);
      $("#as-of").textContent = asOf ? `prices to ${asOf}` : "";
      renderCanvas();
    } catch (err) {
      if (err.name === "AbortError") setStatus("Stopped.", `${results.length} checked`);
      else { setStatus(esc(err.message)); toast(err.message); }
    } finally {
      running = null;
      $("#run").textContent = "Run scan";
      setProgress(1, false);
    }
  }

  function tallyHits() {
    Object.keys(hitStats).forEach((k) => delete hitStats[k]);
    results.forEach((r) => r.groups.forEach((g) => g.blocks.forEach((b) => {
      const s = hitStats[b.uid] || (hitStats[b.uid] = { hits: 0, total: 0 });
      s.total += 1; s.hits += b.hit ? 1 : 0;
    })));
  }

  function spark(values) {
    if (!values || values.length < 2) return "";
    const lo = Math.min.apply(null, values), hi = Math.max.apply(null, values), span = hi - lo || 1;
    const pts = values.map((v, i) => `${(i / (values.length - 1) * 300).toFixed(1)} ${(40 - (v - lo) / span * 36).toFixed(1)}`);
    return `<svg class="lab-spark" viewBox="0 0 300 44" preserveAspectRatio="none" role="img" aria-label="Last ${values.length} closes"><path d="M${pts.join(" L")}"/></svg>`;
  }

  function renderResults() {
    const list = $("#results");
    const sort = $("#sort").value;
    let rows = results.slice();
    if (filter === "matches") rows = rows.filter((r) => r.matched);
    rows.sort((a, b) => sort === "ticker" ? a.ticker.localeCompare(b.ticker) : sort === "change" ? (b.change || 0) - (a.change || 0)
      : (b.matched - a.matched) || (b.score - a.score));
    $("#result-filter").innerHTML = `<button type="button" data-filter="matches" aria-pressed="${filter === "matches"}">Matches ${results.filter((r) => r.matched).length}</button>
      <button type="button" data-filter="all" aria-pressed="${filter === "all"}">Everything ${results.length}</button>`;
    if (!results.length) {
      if (!running) list.innerHTML = `<p class="lab-note">Pick sectors or lists above, build your scan, then press <b>Run scan</b>. Matches appear here as each batch of stocks is checked.</p>`;
      else list.innerHTML = "";
      return;
    }
    if (!rows.length) {
      list.innerHTML = `<p class="lab-note">No stock passes every rule yet. Switch to <b>Everything</b> to see the closest calls, loosen a block, or try <b>Ranked</b> mode.</p>`;
      return;
    }
    list.innerHTML = rows.slice(0, 250).map((r) => {
      const chg = r.change == null ? "" : `<span class="${r.change >= 0 ? "up" : "down"}">${r.change >= 0 ? "+" : ""}${r.change.toFixed(2)}%</span>`;
      const fired = r.fired.slice(0, 5).map((f) => `<span>${esc(f)}</span>`).join("") + (r.fired.length > 5 ? `<span>+${r.fired.length - 5}</span>` : "");
      const open = openRows.has(r.ticker);
      return `<div class="lab-row${r.matched ? " match" : ""}">
        <button type="button" data-row="${esc(r.ticker)}" aria-expanded="${open}">
          <div><div class="tk">${esc(r.ticker)} <span class="bias ${r.bias}" title="Direction the hitting blocks lean">${r.bias === "bullish" ? "▲" : r.bias === "bearish" ? "▼" : "◆"}</span></div>
            <div class="nm">${esc(r.name || "")}${r.name && r.sector ? " · " : ""}${esc(r.sector || "")}</div></div>
          <div class="px">${r.price.toFixed(r.price < 1 ? 4 : 2)}<br>${chg}</div>
          <div class="lab-meter"><div class="bar"><span style="width:${Math.max(2, r.score)}%"></span></div><span class="v">${r.score.toFixed(0)}</span></div>
          ${fired ? `<div class="lab-fired">${fired}</div>` : ""}
        </button>
        ${open ? `<div class="lab-detail">${spark(r.spark)}
          ${r.groups.map((g) => `<div class="lab-detail-group"><div class="gh"><span>${esc(g.name)} · ${g.logic === "atleast" ? `at least ${g.min}` : g.logic}</span>
            <span class="${g.passed ? "pass" : "fail"}">${g.passed ? "passed" : "failed"} · ${g.hits}/${g.blocks.length}</span></div>
            ${g.blocks.map((b) => `<div class="lab-ev"><span class="mark ${b.hit ? "hit" : "miss"}">${b.hit ? "✓" : "✕"}</span>
              <span class="d"><b>${esc(b.title)}</b> ${esc(b.detail)}</span><span class="s">${Math.round(b.strength * 100)}</span></div>`).join("")}</div>`).join("")}
          <a class="lab-open" href="/pump-research/scan?ticker=${encodeURIComponent(r.ticker)}">Open the full chart analysis →</a></div>` : ""}
      </div>`;
    }).join("") + (rows.length > 250 ? `<p class="lab-note">Showing the top 250 of ${rows.length}.</p>` : "");
  }

  // --- Presets, saved scans and alerts -----------------------------------------------------------------------------------
  function openDialog(id) { const d = $(id); if (d.showModal) d.showModal(); else d.setAttribute("open", ""); }
  function closeDialog(el) { const d = el.closest("dialog"); if (d.close) d.close(); else d.removeAttribute("open"); }

  function renderPresets() {
    $("#presets").innerHTML = catalog.presets.map((p) => {
      const fams = Array.from(new Set(p.spec.groups.flatMap((g) => g.blocks.map((b) => (blocks[b.type] || {}).family)).filter(Boolean)));
      return `<button type="button" class="lab-preset" data-preset="${esc(p.key)}">
        <span class="t">${glyph(fams[0] || "filters")}${esc(p.title)}</span><span class="s">${esc(p.tagline)}</span>
        <span class="fams">${fams.map(glyph).join("")}</span></button>`;
    }).join("");
  }

  async function refreshScans() {
    const box = $("#scans");
    box.innerHTML = `<p class="lab-note">Loading…</p>`;
    try {
      const data = await api("/api/scan-lab/scans");
      if (!data.scans.length) { box.innerHTML = `<p class="lab-note">Nothing saved yet. Build a scan and press <b>Save &amp; alert</b>.</p>`; return; }
      box.innerHTML = data.scans.map((s) => `<div class="lab-saved" data-scan="${s.id}">
        <div class="row1"><span class="nm">${esc(s.name)}</span><span class="muted mono" style="font-size:11px">${s.last_run_at ? "checked " + esc(s.last_run_at.slice(0, 16).replace("T", " ")) + " UTC" : "not checked yet"}</span></div>
        <div class="lab-chips">
          <button type="button" class="lab-chip" data-scan-act="load">Open</button>
          <button type="button" class="lab-chip" data-scan-act="alert" aria-pressed="${s.alert_enabled}">${s.alert_enabled ? "Alerts on" : "Alerts off"}</button>
          <button type="button" class="lab-chip" data-scan-act="check">Check now</button>
          <button type="button" class="lab-chip" data-scan-act="delete">Delete</button></div></div>`).join("");
      box._scans = data.scans;
    } catch (e) { box.innerHTML = `<p class="lab-note">${esc(e.message)}</p>`; }
  }

  async function refreshAlerts(render) {
    try {
      const data = await api("/api/scan-lab/alerts");
      const c = $("#alert-count");
      c.hidden = !data.unseen; c.textContent = data.unseen;
      if (!render) return;
      $("#alerts").innerHTML = data.alerts.length ? data.alerts.map((a) => `<div class="lab-alert${a.seen ? "" : " unseen"}">
          <div class="row1"><span><span class="tk">${esc(a.ticker)}</span> <span class="muted">${esc(a.sector || "")}</span></span>
            <span class="mono" style="font-size:12px">${a.score.toFixed(0)}/100 · ${esc(a.created_at.slice(0, 16).replace("T", " "))} UTC</span></div>
          <div class="muted" style="font-size:12.5px">${esc(a.scan)}${a.price ? ` · ${a.price.toFixed(2)}` : ""}</div>
          <div class="lab-fired">${(a.fired || []).slice(0, 6).map((f) => `<span>${esc(f)}</span>`).join("")}</div>
          <a class="lab-open" href="/pump-research/scan?ticker=${encodeURIComponent(a.ticker)}">Open the chart analysis →</a></div>`).join("")
        : `<p class="lab-note">No alerts yet. Save a scan with alerts on, then press <b>Check now</b> in My scans, or wait for the daily check.</p>`;
      if (data.unseen) { await api("/api/scan-lab/alerts/seen", { method: "POST", body: {} }); c.hidden = true; }
    } catch (e) { if (render) $("#alerts").innerHTML = `<p class="lab-note">${esc(e.message)}</p>`; }
  }

  const pct = (x) => (x == null ? "–" : `${Math.round(x * 100)}%`);
  async function openRadar() {
    const box = $("#radar");
    box.innerHTML = `<p class="lab-note">Loading…</p>`;
    try {
      const d = await api("/api/scan-lab/radar");
      if (!d.available) {
        box.innerHTML = `<p class="lab-note">No radar runs published yet. The <b>Daily squeeze radar</b> workflow runs after each US close once the
          project is merged (or add the <span class="mono">radar</span> label to the pull request to run it now).</p>`;
        return;
      }
      const g = (d.grades && d.grades.scans) || {};
      const scans = Object.entries(d.latest.scans).map(([key, s]) => {
        const gr = g[key];
        const learned = gr && gr.picks && gr.picks.n ? `<div class="muted" style="font-size:12.5px">Track record: ${gr.picks.n} graded picks ·
          ${pct(gr.picks.hit_20)} rose 20%+ within 10 days vs ${pct(gr.base_rate.hit_20)} of everything scanned
          ${gr.lift_at_20pct ? `(${gr.lift_at_20pct.toFixed(1)}× lift)` : ""} · ${pct(gr.picks.hit_100)} doubled</div>`
          : `<div class="muted" style="font-size:12.5px">Track record builds up as picks reach 10 trading days old.</div>`;
        const picks = s.picks.length ? s.picks.slice(0, 20).map((p) => `<div class="lab-alert"><div class="row1"><span><span class="tk">${esc(p.ticker)}</span>
            <span class="muted">${esc(p.sector || "")}</span></span><span class="mono" style="font-size:12px">${p.score.toFixed(0)}/100 · ${p.price.toFixed(2)}</span></div>
            <div class="lab-fired">${p.fired.slice(0, 6).map((f) => `<span>${esc(f)}</span>`).join("")}</div>
            <a class="lab-open" href="/pump-research/scan?ticker=${encodeURIComponent(p.ticker)}">Open the chart analysis →</a></div>`).join("")
          : `<p class="lab-note">No picks this day out of ${s.scanned.length} scanned.</p>`;
        return `<div class="lab-saved"><div class="row1"><span class="nm">${esc(s.title)}</span>
          <span class="muted mono" style="font-size:11px">${esc(d.latest.date)} · ${s.picks.length} of ${s.scanned.length}</span></div>${learned}${picks}</div>`;
      });
      box.innerHTML = scans.join("");
    } catch (e) { box.innerHTML = `<p class="lab-note">${esc(e.message)}</p>`; }
  }

  async function saveScan(asNew) {
    const body = {
      name: $("#save-name").value.trim() || state.name, spec: specForServer(), universe: state.universe, timeframe: state.timeframe,
      alert_enabled: $("#alert-on").checked, alert_min_score: Number($("#alert-score").value), alert_new_only: $("#alert-new").checked,
      alert_webhook: $("#alert-hook").value.trim(),
    };
    try {
      const saved = state.scanId && !asNew ? await api(`/api/scan-lab/scans/${state.scanId}`, { method: "PUT", body })
        : await api("/api/scan-lab/scans", { method: "POST", body });
      state.scanId = saved.id; state.name = saved.name; changed();
      closeDialog($("#save-form"));
      toast(saved.alert_enabled ? `Saved “${saved.name}” with alerts on` : `Saved “${saved.name}”`);
    } catch (e) { toast(e.message); }
  }

  function loadSaved(s) {
    const fake = { title: s.name, spec: s.spec, universe: s.universe || {} };
    state = fromPreset(fake);
    state.scanId = s.id; state.timeframe = s.timeframe || "1d";
    state.universe.tickers = (s.universe && s.universe.tickers) || [];
    state.activeGroup = state.spec.groups[0] && state.spec.groups[0].id;
    results = []; renderAll(); save();
  }

  function setSheet(open) {
    $("#palette").classList.toggle("open", open);
    $("#fab").textContent = open ? "Close blocks" : "+ Add block";
    $("#fab").setAttribute("aria-expanded", String(open));
  }

  // --- Wiring -------------------------------------------------------------------------------------------------------------
  function renderAll() { renderUniverse(); renderCanvas(); renderSentence(); renderResults(); }

  function bind() {
    $("#sectors").addEventListener("click", (e) => {
      const b = e.target.closest("[data-sector]"); if (!b) return;
      const s = b.dataset.sector, arr = state.universe.sectors, i = arr.indexOf(s);
      if (i >= 0) arr.splice(i, 1); else arr.push(s);
      renderUniverse(); changed({ canvas: false });
    });
    $("#lists").addEventListener("click", (e) => {
      const b = e.target.closest("[data-list]"); if (!b) return;
      const k = b.dataset.list, arr = state.universe.lists, i = arr.indexOf(k);
      if (i >= 0) arr.splice(i, 1); else arr.push(k);
      renderUniverse(); changed({ canvas: false });
    });
    $("#tickers").addEventListener("change", (e) => {
      state.universe.tickers = Array.from(new Set(e.target.value.toUpperCase().split(/[\s,;]+/).map((t) => t.replace("$", "").trim())
        .filter((t) => /^[A-Z0-9][A-Z0-9.\-^=]{0,11}$/.test(t)))).slice(0, 200);
      renderUniverse(); changed({ canvas: false });
    });
    $("#timeframe").addEventListener("click", (e) => {
      const b = e.target.closest("[data-tf]"); if (!b) return;
      state.timeframe = b.dataset.tf; renderUniverse(); changed({ canvas: false });
    });
    $("#match").addEventListener("click", (e) => { const b = e.target.closest("[data-match]"); if (b) { state.spec.match = b.dataset.match; changed(); } });
    $("#mode").addEventListener("click", (e) => {
      const b = e.target.closest("[data-mode]"); if (!b) return;
      state.spec.mode = b.dataset.mode;
      // Ranked keeps everything at or above the minimum score, so start from a useful bar
      if (state.spec.mode === "ranked" && !state.spec.min_score) state.spec.min_score = 50;
      changed();
    });
    $("#min-score").addEventListener("input", (e) => { state.spec.min_score = Number(e.target.value); $("#min-score-v").textContent = e.target.value; changed({ canvas: false }); });
    $("#scan-name").addEventListener("input", (e) => { state.name = e.target.value || "Untitled scan"; save(); });
    $("#add-group").addEventListener("click", () => {
      const g = makeGroup(`Group ${state.spec.groups.length + 1}`, "any"); state.spec.groups.push(g); state.activeGroup = g.id; changed();
    });
    $("#clear-scan").addEventListener("click", (e) => {
      if (!e.target.dataset.confirm) { e.target.dataset.confirm = "1"; e.target.textContent = "Clear everything?"; setTimeout(() => { e.target.textContent = "Clear"; delete e.target.dataset.confirm; }, 3000); return; }
      const g = makeGroup("Group 1"); state.spec.groups = [g]; state.activeGroup = g.id; state.scanId = null; changed();
      e.target.textContent = "Clear"; delete e.target.dataset.confirm;
    });
    $("#block-search").addEventListener("input", renderPalette);
    $("#palette-list").addEventListener("click", (e) => {
      const add = e.target.closest("[data-add]");
      if (add) { addBlock(add.dataset.add); if (window.matchMedia("(max-width: 860px)").matches) setSheet(false); return; }
      const fam = e.target.closest(".lab-fam > button");
      if (fam) { const id = fam.parentElement.dataset.fam; if (closedFams.has(id)) closedFams.delete(id); else closedFams.add(id); renderPalette(); }
    });
    $("#palette-list").addEventListener("dblclick", (e) => { const t = e.target.closest("[data-type]"); if (t) addBlock(t.dataset.type); });
    $("#fab").addEventListener("click", () => setSheet(!$("#palette").classList.contains("open")));
    $("#run").addEventListener("click", runScan);
    $("#result-filter").addEventListener("click", (e) => { const b = e.target.closest("[data-filter]"); if (b) { filter = b.dataset.filter; renderResults(); } });
    $("#sort").addEventListener("change", renderResults);
    $("#results").addEventListener("click", (e) => {
      const b = e.target.closest("[data-row]"); if (!b) return;
      const t = b.dataset.row; if (openRows.has(t)) openRows.delete(t); else openRows.add(t); renderResults();
    });
    $$("[data-close]").forEach((b) => b.addEventListener("click", () => closeDialog(b)));
    $("#open-presets").addEventListener("click", () => openDialog("#presets-dialog"));
    $("#presets").addEventListener("click", (e) => {
      const b = e.target.closest("[data-preset]"); if (!b) return;
      state = fromPreset(catalog.presets.find((p) => p.key === b.dataset.preset));
      state.activeGroup = state.spec.groups[0] && state.spec.groups[0].id;
      results = []; Object.keys(hitStats).forEach((k) => delete hitStats[k]);
      renderAll(); save(); closeDialog(b); toast(`Loaded “${state.name}”. Press Run scan, or change any block.`);
    });
    $("#open-scans").addEventListener("click", () => { openDialog("#scans-dialog"); refreshScans(); });
    $("#open-radar").addEventListener("click", () => { openDialog("#radar-dialog"); openRadar(); });
    $("#scans").addEventListener("click", async (e) => {
      const b = e.target.closest("[data-scan-act]"); if (!b) return;
      const id = Number(b.closest("[data-scan]").dataset.scan);
      const s = ($("#scans")._scans || []).find((x) => x.id === id);
      const act = b.dataset.scanAct;
      try {
        if (act === "load") { loadSaved(s); closeDialog(b); toast(`Opened “${s.name}”`); }
        else if (act === "alert") { await api(`/api/scan-lab/scans/${id}`, { method: "PUT", body: { alert_enabled: !s.alert_enabled } }); refreshScans(); }
        else if (act === "delete") {
          if (!b.dataset.confirm) { b.dataset.confirm = "1"; b.textContent = "Delete for good?"; return; }
          await api(`/api/scan-lab/scans/${id}`, { method: "DELETE" }); if (state.scanId === id) state.scanId = null; refreshScans();
        } else if (act === "check") {
          b.textContent = "Checking…"; b.disabled = true;
          const out = await api(`/api/scan-lab/scans/${id}/check`, { method: "POST", body: {} });
          toast(`${out.matched} matching, ${out.new_alerts.length} new alert${out.new_alerts.length === 1 ? "" : "s"}`);
          refreshScans(); refreshAlerts(false);
        }
      } catch (err) { toast(err.message); b.disabled = false; }
    });
    $("#open-alerts").addEventListener("click", () => { openDialog("#alerts-dialog"); $("#alerts").innerHTML = `<p class="lab-note">Loading…</p>`; refreshAlerts(true); });
    $("#open-save").addEventListener("click", () => {
      $("#save-name").value = state.name;
      $("#alert-score").value = state.spec.min_score || 0; $("#alert-score-v").textContent = $("#alert-score").value;
      $("#save-as-new").hidden = !state.scanId;
      $("#save-submit").textContent = state.scanId ? "Update scan" : "Save scan";
      openDialog("#save-dialog");
    });
    $("#alert-score").addEventListener("input", (e) => { $("#alert-score-v").textContent = e.target.value; });
    $("#save-form").addEventListener("submit", (e) => { e.preventDefault(); saveScan(false); });
    $("#save-as-new").addEventListener("click", () => saveScan(true));
  }

  async function init() {
    try {
      catalog = await api("/api/scan-lab/catalog");
    } catch (e) {
      $("#groups").innerHTML = `<p class="lab-note">Couldn't load the block library: ${esc(e.message)}. Reload the page to try again.</p>`;
      return;
    }
    catalog.blocks.forEach((b) => { blocks[b.id] = b; });
    catalog.families.forEach((f) => { families[f.id] = f; });
    state = loadDraft() || fromPreset(catalog.presets.find((p) => p.key === "momentum_breakout") || catalog.presets[0]);
    if (!state.spec.groups.length) state.spec.groups.push(makeGroup("Group 1"));
    state.activeGroup = state.activeGroup || state.spec.groups[0].id;
    renderPalette(); renderPresets(); renderAll();
    bind(); bindCanvas(); bindDrag();
    refreshAlerts(false);
    setInterval(() => refreshAlerts(false), 5 * 60 * 1000);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init); else init();
})();
