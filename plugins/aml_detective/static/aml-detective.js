/*
 * AML Detective - Airflow 3.1 React plugin.
 * No build step: this file uses the React instance the Airflow UI shares on globalThis.
 */
(function () {
  "use strict";

  const React = globalThis.React;
  if (!React) {
    console.error("AML Detective: the Airflow UI did not expose React on globalThis.React.");
    return;
  }
  const h = React.createElement;
  const { useState, useEffect, useRef, useMemo } = React;

  const injectedBase = "__AMLD_API_BASE__";
  const API = injectedBase.indexOf("__") === 0 ? "/aml-detective" : injectedBase;
  const PLAYER_KEY = "aml-detective-player";

  // ------------------------------------------------------------------------ styles
  const CSS = `
.amld { --manila:#E6D8B5; --paper:#FBF7EC; --ink:#1E2B3A; --graphite:#5E5A50; --rule:#CFC3A3;
  --red:#A8231B; --green:#2E6A3C; --marker:#F3E3A0; --sheet:#D6C69C;
  background:var(--manila); color:var(--ink); border-radius:6px; padding:20px 24px 32px;
  font-family:"IBM Plex Sans Condensed","Arial Narrow",Arial,sans-serif; font-size:15px; line-height:1.45;
  font-variant-numeric:tabular-nums; min-height:calc(100vh - 140px); }
.amld *, .amld *::before, .amld *::after { box-sizing:border-box; }
.amld :focus-visible { outline:2px solid var(--ink); outline-offset:2px; }
.amld h1, .amld h2, .amld h3 { font-family:"Source Serif 4",Georgia,serif; margin:0; font-weight:600; letter-spacing:-0.005em; }
.amld h1 { font-size:1.75rem; }
.amld h2 { font-size:1.25rem; margin-bottom:10px; }
.amld h3 { font-size:1.05rem; margin-bottom:6px; }
.amld p { margin:0 0 8px; max-width:70ch; }
.amld button { font:inherit; cursor:pointer; }
.amld-top { display:flex; flex-wrap:wrap; gap:8px 24px; align-items:baseline; justify-content:space-between; margin-bottom:18px; }
.amld-sub { color:var(--graphite); font-size:0.9rem; }
.amld-score { font-family:"Source Serif 4",Georgia,serif; font-size:1.5rem; font-weight:600; }
.amld-score small { font-family:inherit; font-size:0.85rem; color:var(--graphite); font-weight:400; margin-left:6px; }
.amld-desk { display:grid; grid-template-columns:260px minmax(0,1fr); gap:20px; align-items:start; }
.amld-desk > * { min-width:0; }
@media (max-width:960px){ .amld-desk { grid-template-columns:minmax(0,1fr); } }
@media (max-width:600px){ .amld { padding:12px 10px 24px; } .amld-file { padding:16px 14px; box-shadow:3px 3px 0 var(--sheet); } .amld-stamp { font-size:1.4rem; top:56px; right:12px; } }
.amld-queue { display:flex; flex-direction:column; gap:6px; }
.amld-tab { text-align:left; background:var(--paper); border:1px solid var(--rule); border-left:5px solid var(--rule);
  border-radius:3px 8px 8px 3px; padding:9px 12px; color:var(--ink); }
.amld-tab[aria-current="true"] { border-left-color:var(--ink); box-shadow:3px 3px 0 var(--sheet); }
.amld-tab.is-good { border-left-color:var(--green); }
.amld-tab.is-bad { border-left-color:var(--red); }
.amld-tab strong { display:block; font-weight:600; }
.amld-tab span { font-size:0.85rem; color:var(--graphite); }
.amld-file { position:relative; background:var(--paper); border:1px solid var(--rule); border-radius:2px;
  box-shadow:5px 5px 0 var(--sheet); padding:24px 28px; }
.amld-filehead { display:flex; flex-wrap:wrap; justify-content:space-between; gap:6px 20px; align-items:baseline;
  border-bottom:2px solid var(--ink); padding-bottom:10px; margin-bottom:18px; }
.amld-risk { font-size:0.95rem; }
.amld-risk b { font-size:1.2rem; }
.amld-grid2 { display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1.3fr); gap:24px; margin-bottom:22px; }
@media (max-width:760px){ .amld-grid2 { grid-template-columns:1fr; } }
.amld-kyc { display:grid; grid-template-columns:auto 1fr; gap:4px 14px; margin:0; }
.amld-kyc dt { color:var(--graphite); }
.amld-kyc dd { margin:0; }
.amld-note { font-family:"Source Serif 4",Georgia,serif; font-style:italic; margin-top:10px; padding-left:12px;
  border-left:3px solid var(--rule); max-width:60ch; }
.amld-hits { list-style:none; margin:0; padding:0; display:flex; flex-direction:column; gap:6px; }
.amld-hit { width:100%; text-align:left; background:transparent; border:1px solid var(--rule); border-radius:4px;
  padding:8px 10px; color:var(--ink); }
.amld-hit[aria-pressed="true"] { background:var(--marker); border-color:#C9B45A; }
.amld-hit b { margin-right:6px; }
.amld-hit span { display:block; color:var(--graphite); font-size:0.9rem; }
.amld-hitnote { font-size:0.85rem; color:var(--graphite); margin-top:6px; }
.amld-compare { width:100%; border-collapse:collapse; margin-top:8px; font-size:0.9rem; }
.amld-compare th, .amld-compare td { border-bottom:1px solid var(--rule); padding:4px 6px; text-align:left; }
.amld-compare th { font-weight:600; color:var(--graphite); }
.amld-section { margin-bottom:22px; }
.amld-graph { width:100%; height:auto; display:block; background:#FFFDF6; border:1px solid var(--rule); }
.amld-ledgerwrap { overflow-x:auto; border:1px solid var(--rule); }
.amld-ledger { width:100%; border-collapse:collapse; font-size:0.92rem; }
.amld-ledger th { position:sticky; top:0; background:var(--paper); text-align:left; font-weight:600; color:var(--graphite);
  border-bottom:2px solid var(--ink); padding:6px 10px; }
.amld-ledger td { padding:5px 10px; border-bottom:1px solid #EAE1CB; white-space:nowrap; }
.amld-ledger td.num, .amld-ledger th.num { text-align:right; }
.amld-ledger tr.is-marked td { background:var(--marker); }
.amld-ledger .muted { color:var(--graphite); }
.amld-decide { border-top:2px solid var(--ink); padding-top:16px; }
.amld-typos { display:flex; flex-wrap:wrap; gap:6px 16px; border:0; padding:0; margin:0 0 14px; }
.amld-typos legend { padding:0; margin-bottom:8px; font-weight:600; }
.amld-typos label { display:flex; gap:6px; align-items:center; cursor:pointer; }
.amld-actions { display:flex; flex-wrap:wrap; gap:10px; align-items:center; }
.amld-btn { border-radius:4px; padding:9px 16px; border:2px solid var(--ink); background:transparent; color:var(--ink); font-weight:600; }
.amld-btn.close { border-color:var(--green); color:var(--green); }
.amld-btn.sar { background:var(--red); border-color:var(--red); color:#FFF8F0; }
.amld-btn.primary { background:var(--ink); color:var(--paper); }
.amld-btn:disabled { opacity:0.5; cursor:not-allowed; }
.amld-warn { color:var(--red); font-size:0.9rem; }
.amld-timer { margin-left:auto; color:var(--graphite); font-size:0.9rem; }
.amld-stamp { position:absolute; top:70px; right:28px; transform:rotate(-9deg); border:4px solid currentColor;
  border-radius:6px; padding:6px 16px; font-family:"Source Serif 4",Georgia,serif; font-weight:700;
  font-size:2rem; letter-spacing:0.08em; opacity:0.82; mix-blend-mode:multiply; pointer-events:none;
  animation:amld-stamp 220ms cubic-bezier(.2,1.4,.4,1) both; }
.amld-stamp.sar { color:var(--red); }
.amld-stamp.close { color:var(--green); }
@keyframes amld-stamp { from { transform:rotate(-9deg) scale(1.9); opacity:0; } to { transform:rotate(-9deg) scale(1); opacity:0.82; } }
@media (prefers-reduced-motion:reduce){ .amld-stamp { animation:none; } }
.amld-debrief { background:#FFFDF6; border:1px solid var(--rule); border-left:5px solid var(--ink); padding:14px 16px; }
.amld-debrief.good { border-left-color:var(--green); }
.amld-debrief.bad { border-left-color:var(--red); }
.amld-debrief .pts { font-family:"Source Serif 4",Georgia,serif; font-size:1.3rem; font-weight:600; }
.amld-debrief p { font-family:"Source Serif 4",Georgia,serif; line-height:1.6; }
.amld-center { max-width:620px; margin:48px auto; }
.amld-center .amld-file { padding:32px 36px; }
.amld-field { display:flex; flex-direction:column; gap:6px; margin:18px 0; }
.amld-field input { font:inherit; padding:9px 12px; border:1px solid var(--graphite); border-radius:4px; background:#FFFDF6; color:var(--ink); max-width:320px; }
.amld-report td, .amld-report th { padding:6px 10px; border-bottom:1px solid var(--rule); text-align:left; }
.amld-report { border-collapse:collapse; width:100%; margin:8px 0 20px; }
.amld-report .num { text-align:right; }
`;

  if (typeof document !== "undefined" && !document.getElementById("amld-styles")) {
    const fonts = document.createElement("link");
    fonts.rel = "stylesheet";
    fonts.href = "https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Condensed:wght@400;600&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;0,8..60,700;1,8..60,400&display=swap";
    document.head.appendChild(fonts);
    const style = document.createElement("style");
    style.id = "amld-styles";
    style.textContent = CSS;
    document.head.appendChild(style);
  }

  // ------------------------------------------------------------------------ helpers
  const money = (n) => "$" + Math.round(n).toLocaleString("en-US");
  const money2 = (n) => "$" + n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const shortDate = (iso) => new Date(iso + "T00:00:00").toLocaleDateString("en-US", { month: "short", day: "numeric" });
  const clock = (s) => Math.floor(s / 60) + ":" + String(Math.floor(s % 60)).padStart(2, "0");
  const trunc = (s, n) => (s.length > n ? s.slice(0, n - 1) + "\u2026" : s);
  function runLabel(shift) {
    if (shift.source !== "dag") return "Practice shift";
    const m = /^(\w+?)__(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2})/.exec(shift.run_id || "");
    if (!m) return "Run " + shift.run_id;
    const kind = { manual: "Manual run", scheduled: "Scheduled run", asset_triggered: "Asset-triggered run" }[m[1]] || "Run";
    return kind + ", " + shortDate(m[2]) + " at " + m[3] + " UTC";
  }
  const CHANNEL = { cash: "Cash", wire: "Wire", ach: "ACH", card: "Card", p2p: "P2P transfer" };
  const HIGH_RISK = { KP: 1, IR: 1, MM: 1 };

  async function api(path, options) {
    const res = await fetch(API + path, Object.assign({ headers: { "Content-Type": "application/json" } }, options));
    if (!res.ok) {
      let detail = res.status + " " + res.statusText;
      try { const body = await res.json(); if (body.detail) detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail); } catch (e) { /* not json */ }
      throw new Error(detail);
    }
    return res.json();
  }

  function readPlayer() { try { return localStorage.getItem(PLAYER_KEY) || ""; } catch (e) { return ""; } }
  function savePlayer(p) { try { localStorage.setItem(PLAYER_KEY, p); } catch (e) { /* storage blocked */ } }

  function isGood(result) { return result && result.points > 0; }

  // ------------------------------------------------------------------------ network graph
  function NetworkGraph({ c, marked }) {
    const W = 640, H = 300, cx = W / 2, cy = H / 2;
    const nodes = useMemo(() => {
      const agg = {};
      c.transactions.forEach((t) => {
        if (t.channel === "card") return;
        const key = t.counterparty_id || (t.channel === "cash" ? "cash" : null);
        if (!key) return;
        if (!agg[key]) {
          const cp = c.counterparties[t.counterparty_id];
          const watch = (c.hits.find((x) => x.code === "R05") || { matches: [] }).matches || [];
          agg[key] = {
            key,
            label: cp ? cp.name : "Cash",
            country: cp ? cp.country : "",
            flagged: !!(cp && (HIGH_RISK[cp.country] || watch.some((m) => m.counterparty_id === key))),
            inAmt: 0, outAmt: 0, txnIds: [],
          };
        }
        agg[key][t.direction === "in" ? "inAmt" : "outAmt"] += t.amount;
        agg[key].txnIds.push(t.id);
      });
      const list = Object.values(agg).sort((a, b) => (b.inAmt + b.outAmt) - (a.inAmt + a.outAmt));
      const shown = list.slice(0, 12);
      const max = Math.max(1, ...shown.map((n) => n.inAmt + n.outAmt));
      shown.forEach((n, i) => {
        const angle = (i / shown.length) * Math.PI * 2 - Math.PI / 2;
        n.x = cx + Math.cos(angle) * 250;
        n.y = cy + Math.sin(angle) * 112;
        n.w = 1.5 + 6 * Math.sqrt((n.inAmt + n.outAmt) / max);
        n.dir = n.inAmt >= n.outAmt ? "in" : "out";
        n.above = n.y < cy - 20;
      });
      shown.hidden = list.length - shown.length;
      return shown;
    }, [c]);

    const markedSet = new Set(marked || []);
    const kids = [
      h("defs", { key: "d" },
        ["ink", "red"].map((k) => h("marker", { key: k, id: "amld-arrow-" + k, viewBox: "0 0 10 10", refX: 9, refY: 5, markerWidth: 11, markerHeight: 11, markerUnits: "userSpaceOnUse", orient: "auto-start-reverse" },
          h("path", { d: "M0,0 L10,5 L0,10 z", fill: k === "red" ? "#A8231B" : "#1E2B3A" })))),
    ];
    nodes.forEach((n) => {
      const isMarked = n.txnIds.some((id) => markedSet.has(id));
      const color = n.flagged ? "#A8231B" : "#1E2B3A";
      // shorten the line so arrows don't disappear under the circles
      const dx = cx - n.x, dy = cy - n.y, len = Math.hypot(dx, dy);
      const ux = dx / len, uy = dy / len;
      const x1 = n.x + ux * 12, y1 = n.y + uy * 12, x2 = cx - ux * 30, y2 = cy - uy * 30;
      const [sx, sy, ex, ey] = n.dir === "in" ? [x1, y1, x2, y2] : [x2, y2, x1, y1];
      kids.push(h("line", {
        key: "l" + n.key, x1: sx, y1: sy, x2: ex, y2: ey, stroke: color, strokeWidth: n.w,
        strokeOpacity: markedSet.size && !isMarked ? 0.25 : 0.85,
        markerEnd: "url(#amld-arrow-" + (n.flagged ? "red" : "ink") + ")",
      }));
      kids.push(h("g", { key: "n" + n.key, opacity: markedSet.size && !isMarked ? 0.45 : 1 },
        isMarked ? h("circle", { cx: n.x, cy: n.y, r: 14, fill: "#F3E3A0" }) : null,
        h("circle", { cx: n.x, cy: n.y, r: 8, fill: n.flagged ? "#A8231B" : "#FBF7EC", stroke: color, strokeWidth: 2 }),
        h("text", { x: n.x, y: n.above ? n.y - 30 : n.y + 24, textAnchor: "middle", fontSize: 12, fill: "#1E2B3A", fontFamily: "IBM Plex Sans Condensed, Arial Narrow, sans-serif" },
          trunc(n.label, 20) + (n.country && n.country !== "US" ? " (" + n.country + ")" : "")),
        h("text", { x: n.x, y: n.above ? n.y - 16 : n.y + 38, textAnchor: "middle", fontSize: 11, fill: "#5E5A50", fontFamily: "IBM Plex Sans Condensed, Arial Narrow, sans-serif" },
          (n.inAmt ? "in " + money(n.inAmt) : "") + (n.inAmt && n.outAmt ? ", " : "") + (n.outAmt ? "out " + money(n.outAmt) : ""))));
    });
    kids.push(h("circle", { key: "subj", cx, cy, r: 26, fill: "#1E2B3A" }));
    kids.push(h("text", { key: "subjt", x: cx, y: cy + 4, textAnchor: "middle", fontSize: 11, fill: "#FBF7EC", fontWeight: 600, fontFamily: "IBM Plex Sans Condensed, Arial Narrow, sans-serif" }, "Subject"));
    if (nodes.hidden > 0) {
      kids.push(h("text", { key: "more", x: W - 10, y: H - 10, textAnchor: "end", fontSize: 11, fill: "#5E5A50" }, "+" + nodes.hidden + " smaller counterparties"));
    }
    return h("svg", {
      className: "amld-graph", viewBox: "-60 -20 " + (W + 120) + " " + (H + 60), role: "img",
      "aria-label": "Money flows between the subject and " + nodes.length + " counterparties. Red marks a high-risk country or watchlist match.",
    }, kids);
  }

  // ------------------------------------------------------------------------ case file
  function CaseFile({ c, typologies, result, onDecide, busy }) {
    const [activeRule, setActiveRule] = useState(null);
    const [typology, setTypology] = useState("");
    const [warn, setWarn] = useState("");
    const [elapsed, setElapsed] = useState(0);
    const openedAt = useRef(Date.now());

    useEffect(() => {
      if (result) return undefined;
      const t = setInterval(() => setElapsed((Date.now() - openedAt.current) / 1000), 1000);
      return () => clearInterval(t);
    }, [result]);

    const a = c.account;
    const hit = c.hits.find((x) => x.code === activeRule);
    const marked = hit ? hit.txn_ids : [];
    const markedSet = new Set(marked);
    const watch = c.hits.find((x) => x.code === "R05");

    function decide(disposition) {
      if (disposition === "sar" && !typology) {
        setWarn("Pick the typology you are reporting, then file the SAR.");
        return;
      }
      setWarn("");
      onDecide(disposition, disposition === "sar" ? typology : null, (Date.now() - openedAt.current) / 1000);
    }

    const ledgerRows = c.transactions.map((t) => {
      const cp = t.counterparty_id ? c.counterparties[t.counterparty_id] : null;
      const who = cp ? cp.name + (cp.country !== "US" ? " (" + cp.country_name + ")" : "") : (t.memo || "");
      return h("tr", { key: t.id, className: markedSet.has(t.id) ? "is-marked" : "" },
        h("td", null, shortDate(t.date)),
        h("td", null, CHANNEL[t.channel] || t.channel),
        h("td", null, who, cp && t.memo ? h("span", { className: "muted" }, "  " + t.memo) : null),
        h("td", { className: "num" }, t.direction === "in" ? money2(t.amount) : ""),
        h("td", { className: "num" }, t.direction === "out" ? money2(t.amount) : ""));
    });

    return h("article", { className: "amld-file", "aria-labelledby": "amld-case-title" },
      result ? h("div", { className: "amld-stamp " + result.disposition, "aria-hidden": "true" },
        result.disposition === "sar" ? "SAR FILED" : "CLOSED") : null,

      h("header", { className: "amld-filehead" },
        h("div", null,
          h("h2", { id: "amld-case-title", style: { marginBottom: 2 } }, a.name),
          h("div", { className: "amld-sub" }, c.case_id + ", account " + a.id)),
        h("div", { className: "amld-risk" }, "Risk score ", h("b", null, c.risk_score))),

      h("div", { className: "amld-grid2" },
        h("section", null,
          h("h3", null, "Customer profile"),
          h("dl", { className: "amld-kyc" },
            h("dt", null, "Type"), h("dd", null, a.kind === "individual" ? "Individual" : "Business"),
            h("dt", null, "Occupation"), h("dd", null, a.occupation),
            h("dt", null, "Expected monthly"), h("dd", null, money(a.expected_monthly)),
            h("dt", null, "Customer since"), h("dd", null, new Date(a.opened + "T00:00:00").getFullYear())),
          h("p", { className: "amld-note" }, a.kyc_notes)),
        h("section", null,
          h("h3", null, "Why this alerted"),
          h("ul", { className: "amld-hits" },
            c.hits.map((x) => h("li", { key: x.code },
              h("button", {
                type: "button", className: "amld-hit", "aria-pressed": activeRule === x.code ? "true" : "false",
                disabled: !x.txn_ids.length,
                onClick: () => setActiveRule(activeRule === x.code ? null : x.code),
              }, h("b", null, x.code), x.name, h("span", null, x.detail))))),
          h("p", { className: "amld-hitnote" }, "Select a rule to highlight the transactions behind it."),
          watch ? h("table", { className: "amld-compare" },
            h("caption", { style: { textAlign: "left", fontWeight: 600, marginBottom: 4 } }, "Watchlist comparison"),
            h("thead", null, h("tr", null, h("th", null, ""), h("th", null, "Counterparty"), h("th", null, "List entry"))),
            h("tbody", null, watch.matches.map((m) => [
              h("tr", { key: m.counterparty_id + "n" }, h("th", null, "Name"), h("td", null, m.counterparty.name), h("td", null, m.entry.name)),
              h("tr", { key: m.counterparty_id + "d" }, h("th", null, "Date of birth"), h("td", null, m.counterparty.dob || "Not on file"), h("td", null, m.entry.dob || "Not listed")),
              h("tr", { key: m.counterparty_id + "c" }, h("th", null, "Nationality"), h("td", null, m.counterparty.nationality || "Not on file"), h("td", null, m.entry.nationality)),
              h("tr", { key: m.counterparty_id + "p" }, h("th", null, "Program"), h("td", null, m.counterparty.note || ""), h("td", null, m.entry.program)),
            ]))) : null)),

      h("section", { className: "amld-section" },
        h("h3", null, "Money flows, last 30 days"),
        h(NetworkGraph, { c, marked })),

      h("section", { className: "amld-section" },
        h("h3", null, "Statement"),
        h("div", { className: "amld-ledgerwrap" },
          h("table", { className: "amld-ledger" },
            h("thead", null, h("tr", null, h("th", null, "Date"), h("th", null, "Channel"), h("th", null, "Counterparty or memo"),
              h("th", { className: "num" }, "Money in"), h("th", { className: "num" }, "Money out"))),
            h("tbody", null, ledgerRows)))),

      result
        ? h("section", { className: "amld-debrief " + (isGood(result) ? "good" : "bad"), "aria-live": "polite" },
            h("div", { className: "pts" }, (result.points > 0 ? "+" : "") + result.points + " points"),
            h("h3", null, result.headline),
            h("p", null, result.debrief),
            result.speed_bonus ? h("div", { className: "amld-sub" }, "Includes a " + result.speed_bonus + "-point speed bonus.") : null)
        : h("section", { className: "amld-decide" },
            h("fieldset", { className: "amld-typos" },
              h("legend", null, "If you escalate, what is the typology?"),
              Object.entries(typologies).map(([k, label]) => h("label", { key: k },
                h("input", { type: "radio", name: "amld-typology-" + c.case_id, value: k, checked: typology === k, onChange: () => { setTypology(k); setWarn(""); } }),
                label))),
            h("div", { className: "amld-actions" },
              h("button", { type: "button", className: "amld-btn close", disabled: busy, onClick: () => decide("close") }, "Close alert"),
              h("button", { type: "button", className: "amld-btn sar", disabled: busy, onClick: () => decide("sar") }, "Escalate and file SAR"),
              warn ? h("span", { className: "amld-warn", role: "alert" }, warn) : null,
              h("span", { className: "amld-timer" }, "On this case " + clock(elapsed)))));
  }

  // ------------------------------------------------------------------------ screens
  function Intro({ shift, onStart }) {
    const [name, setName] = useState(readPlayer());
    const s = shift.stats;
    return h("div", { className: "amld-center" },
      h("div", { className: "amld-file" },
        h("h1", null, "AML Detective"),
        h("p", { className: "amld-sub", style: { marginTop: 4 } },
          shift.source === "dag" ? "Shift from " + runLabel(shift).toLowerCase() + " of aml_detective_case_factory" : "Practice shift. Trigger aml_detective_case_factory to open a fresh one."),
        h("p", { style: { marginTop: 16 } },
          "Overnight, the monitoring pipeline screened " + s.accounts + " accounts and " + s.transactions.toLocaleString("en-US") +
          " transactions and raised " + s.alerts + " alerts. Some are money laundering. Some are ordinary customers who happened to trip a rule."),
        h("p", null, "Work each case: read the profile, follow the money, then close it or escalate it with a SAR. A missed SAR costs the most."),
        h("form", { onSubmit: (e) => { e.preventDefault(); if (name.trim()) { savePlayer(name.trim()); onStart(name.trim()); } } },
          h("div", { className: "amld-field" },
            h("label", { htmlFor: "amld-name" }, "Analyst name for the leaderboard"),
            h("input", { id: "amld-name", value: name, maxLength: 40, autoComplete: "nickname", onChange: (e) => setName(e.target.value) })),
          h("button", { type: "submit", className: "amld-btn primary", disabled: !name.trim() }, "Start shift"))));
  }

  function Report({ shift, player, results, onBack }) {
    const [board, setBoard] = useState(null);
    const [error, setError] = useState("");
    useEffect(() => {
      api("/api/leaderboard?batch_id=" + encodeURIComponent(shift.batch_id))
        .then(setBoard).catch((e) => setError("Leaderboard unavailable: " + e.message));
    }, [shift.batch_id]);
    const total = Object.values(results).reduce((n, r) => n + r.points, 0);
    const missed = Object.values(results).filter((r) => r.outcome === "missed_sar").length;
    return h("div", { className: "amld-center", style: { maxWidth: 760 } },
      h("div", { className: "amld-file" },
        h("h1", null, "Shift report"),
        h("p", { className: "amld-sub" }, player + ", " + shift.batch_id),
        h("p", { className: "amld-score", style: { margin: "14px 0" } }, total + " points",
          h("small", null, missed ? missed + (missed === 1 ? " missed SAR" : " missed SARs") : "no missed SARs")),
        h("table", { className: "amld-report" },
          h("thead", null, h("tr", null, h("th", null, "Case"), h("th", null, "Your call"), h("th", null, "Answer"), h("th", { className: "num" }, "Points"))),
          h("tbody", null, shift.cases.map((c) => {
            const r = results[c.case_id];
            return h("tr", { key: c.case_id },
              h("td", null, c.account.name),
              h("td", null, r ? (r.disposition === "sar" ? "Escalated" : "Closed") : "Not worked"),
              h("td", null, r ? (r.truth.disposition === "sar" ? "SAR: " + r.truth.typology_label : "False positive") : ""),
              h("td", { className: "num" }, r ? r.points : ""));
          }))),
        h("h2", null, "Leaderboard for this shift"),
        error ? h("p", { className: "amld-warn" }, error) : null,
        board ? h("table", { className: "amld-report" },
          h("thead", null, h("tr", null, h("th", null, "Analyst"), h("th", { className: "num" }, "Cases"), h("th", { className: "num" }, "Missed SARs"), h("th", { className: "num" }, "Score"))),
          h("tbody", null, board.rows.map((row) => h("tr", { key: row.player, style: row.player === player ? { fontWeight: 600 } : null },
            h("td", null, row.player), h("td", { className: "num" }, row.cases), h("td", { className: "num" }, row.missed_sars), h("td", { className: "num" }, row.score))))) : (error ? null : h("p", null, "Loading leaderboard.")),
        h("button", { type: "button", className: "amld-btn", onClick: onBack }, "Back to the case queue")));
  }

  // ------------------------------------------------------------------------ app
  function AMLDetective() {
    const [shift, setShift] = useState(null);
    const [error, setError] = useState("");
    const [player, setPlayer] = useState("");
    const [results, setResults] = useState({});
    const [activeId, setActiveId] = useState(null);
    const [screen, setScreen] = useState("intro");
    const [busy, setBusy] = useState(false);
    const [postError, setPostError] = useState("");

    useEffect(() => {
      api("/api/shift").then(setShift).catch((e) =>
        setError("The case queue did not load from " + API + "/api/shift (" + e.message + "). Check Admin > Plugins for aml_detective, then restart the API server."));
    }, []);

    async function start(name) {
      setPlayer(name);
      let prior = {};
      try {
        const p = await api("/api/progress?batch_id=" + encodeURIComponent(shift.batch_id) + "&player=" + encodeURIComponent(name));
        prior = p.cases || {};
      } catch (e) { /* new player or API hiccup: start fresh */ }
      setResults(prior);
      const first = shift.cases.find((c) => !prior[c.case_id]) || shift.cases[0];
      setActiveId(first.case_id);
      setScreen("desk");
    }

    async function decide(disposition, typology, seconds) {
      setBusy(true); setPostError("");
      try {
        const r = await api("/api/verdict", {
          method: "POST",
          body: JSON.stringify({ batch_id: shift.batch_id, case_id: activeId, disposition, typology, player, seconds }),
        });
        setResults((prev) => Object.assign({}, prev, { [activeId]: r }));
      } catch (e) {
        setPostError("Your decision was not saved: " + e.message + ". Try again.");
      } finally { setBusy(false); }
    }

    let body;
    if (error) body = h("div", { className: "amld-center" }, h("div", { className: "amld-file" }, h("h1", null, "AML Detective"), h("p", { className: "amld-warn", role: "alert" }, error)));
    else if (!shift) body = h("div", { className: "amld-center" }, h("p", null, "Loading the case queue."));
    else if (!shift.cases.length) body = h("div", { className: "amld-center" }, h("div", { className: "amld-file" }, h("h1", null, "No alerts this shift"),
      h("p", null, "The last screening run raised no alerts. Trigger aml_detective_case_factory to generate a new shift.")));
    else if (screen === "intro") body = h(Intro, { shift, onStart: start });
    else if (screen === "report") body = h(Report, { shift, player, results, onBack: () => setScreen("desk") });
    else {
      const done = shift.cases.filter((c) => results[c.case_id]).length;
      const score = Object.values(results).reduce((n, r) => n + r.points, 0);
      const current = shift.cases.find((c) => c.case_id === activeId) || shift.cases[0];
      const nextOpen = shift.cases.find((c) => !results[c.case_id] && c.case_id !== current.case_id);
      body = h(React.Fragment, null,
        h("header", { className: "amld-top" },
          h("div", null,
            h("h1", null, "AML Detective"),
            h("div", { className: "amld-sub" }, shift.stats.accounts + " accounts screened, " + shift.stats.alerts + " alerts. " +
              runLabel(shift))),
          h("div", { className: "amld-score" }, score + " points", h("small", null, done + " of " + shift.cases.length + " cases worked"))),
        h("div", { className: "amld-desk" },
          h("nav", { className: "amld-queue", "aria-label": "Case queue" },
            shift.cases.map((c) => {
              const r = results[c.case_id];
              return h("button", {
                key: c.case_id, type: "button", "aria-current": c.case_id === current.case_id ? "true" : "false",
                className: "amld-tab" + (r ? (isGood(r) ? " is-good" : " is-bad") : ""),
                onClick: () => setActiveId(c.case_id),
              }, h("strong", null, c.account.name),
                h("span", null, r ? (r.disposition === "sar" ? "SAR filed, " : "Closed, ") + (r.points > 0 ? "+" : "") + r.points : "Risk " + c.risk_score + ", " + c.hits.map((x) => x.code).join(" ")));
            }),
            done === shift.cases.length ? h("button", { type: "button", className: "amld-btn primary", style: { marginTop: 10 }, onClick: () => setScreen("report") }, "See shift report") : null),
          h("div", null,
            postError ? h("p", { className: "amld-warn", role: "alert" }, postError) : null,
            h(CaseFile, { key: current.case_id, c: current, typologies: shift.typologies, result: results[current.case_id], onDecide: decide, busy }),
            results[current.case_id] && nextOpen
              ? h("div", { style: { marginTop: 16 } }, h("button", { type: "button", className: "amld-btn primary", onClick: () => setActiveId(nextOpen.case_id) }, "Open next case"))
              : null)));
    }
    return h("div", { className: "amld" }, body);
  }

  globalThis["AML Detective"] = AMLDetective; // matches the react_apps name
  globalThis.AirflowPlugin = AMLDetective;     // fallback Airflow looks for
})();
