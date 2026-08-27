/**
 * Application state: filters, derived metrics and the actions that mutate the
 * book of work. Views read from here and never hold state of their own.
 *
 * Two things persist between visits (localStorage, best-effort): the policy
 * settings and the reviewer's own decisions. Everything else lives in the URL
 * so a filtered view can be pasted into a message.
 */

import { buildDataset, processMailbox } from './data.js';
import {
  AGING_BUCKETS, DEFAULT_SETTINGS, REGIONS, SETTINGS_BOUNDS,
  isCroPending, isCroReceived, isReleasable, pct, priorityLabel, priorityScore, recompute,
} from './rules.js';

const STORE_KEY = 'cro-cockpit/v1';

export const VIEWS = {
  dashboard: ['Executive dashboard', 'Reconciled view across PK, BD and SL trackers against the logistics mailbox'],
  monitor: ['Shipment monitor', 'Every shipment line with its agent-details and CRO evidence'],
  cro: ['CRO pending', 'Lines with no valid Container Release Order evidence'],
  agent: ['Agent details', 'Lines where required agent fields are missing or incomplete'],
  agentperf: ['Agent performance', 'Forwarder-wise CRO turnaround and pending exposure'],
  regionperf: ['Region performance', 'PK / BD / SL comparison and aging distribution'],
  emails: ['Emails', 'Parsed logistics emails and the fields extracted from each'],
  review: ['Match review queue', 'Matches the parser could not confirm on its own'],
  exceptions: ['Exceptions', 'Emails no shipment line could be found for — link them by hand'],
  settings: ['Settings', 'Policy thresholds, mailbox behaviour and appearance'],
};

const QUICK_FILTERS = {
  All: () => true,
  'CRO Pending': (l) => isCroPending(l.croStatus),
  'Agent Pending': (l) => l.agentStatus !== 'Received',
  'Action Required': (l) => l.overall === 'ACTION REQUIRED',
  Overdue: (l) => l.overdue,
  Ready: (l) => isReleasable(l.overall),
  Review: (l) => l.overall === 'REVIEW REQUIRED',
};

export const QUICK_LABELS = {
  All: 'No filter',
  'CRO Pending': 'Only CRO pending',
  'Agent Pending': 'Only agent pending',
  'Action Required': 'Only action required',
  Overdue: 'Only overdue',
  Ready: 'Only ready',
  Review: 'Review required',
};

function readStored() {
  try {
    const raw = localStorage.getItem(STORE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch { return {}; }
}

function writeStored(patch) {
  try {
    localStorage.setItem(STORE_KEY, JSON.stringify({ ...readStored(), ...patch }));
  } catch { /* private mode, blocked storage — settings just don't persist */ }
}

const stored = readStored();

export const state = {
  view: 'dashboard',
  region: 'All',
  quick: 'All',
  q: '',
  page: 1,
  sort: { key: 'priority', dir: 'desc' },
  drawer: null,
  syncing: false,
  auto: false,
  lastSync: '21-Aug-2026 08:30',
  syncLog: [],
  syncSummary: null,
  remaining: null,
  settings: { ...DEFAULT_SETTINGS, ...(stored.settings || {}) },
  decisions: stored.decisions || {},
};

let db = buildDataset(state.settings);
let listeners = [];
let autoTimer = null;

export function subscribe(fn) { listeners.push(fn); }
export function render() { listeners.forEach((fn) => fn()); }

export function setState(patch, { silent = false } = {}) {
  Object.assign(state, patch);
  if (!silent) { writeHash(); render(); }
}

export const getDb = () => db;

/* ------------------------------------------------------------- settings -- */

export function setSetting(key, value) {
  const bounds = SETTINGS_BOUNDS[key];
  let v = value;
  if (bounds) v = Math.min(bounds[1], Math.max(bounds[0], Number(value)));
  state.settings = { ...state.settings, [key]: v };
  writeStored({ settings: state.settings });
  db.lines.forEach((l) => recompute(l, state.settings));
  if (key === 'autoCheckSeconds' && state.auto) startAuto();
  if (key === 'theme') applyTheme();
  render();
}

export function applyTheme() {
  const t = state.settings.theme;
  if (t === 'system') document.documentElement.removeAttribute('data-theme');
  else document.documentElement.setAttribute('data-theme', t);
}

export function resetSettings() {
  state.settings = { ...DEFAULT_SETTINGS };
  writeStored({ settings: state.settings });
  db.lines.forEach((l) => recompute(l, state.settings));
  applyTheme();
  render();
}

/* --------------------------------------------------------------- routing -- */

const HASH_KEYS = ['view', 'region', 'quick', 'q', 'page'];

export function readHash() {
  const params = new URLSearchParams(location.hash.replace(/^#/, ''));
  const patch = {};
  for (const key of HASH_KEYS) {
    const v = params.get(key);
    if (v === null) continue;
    if (key === 'page') patch.page = Math.max(1, Number(v) || 1);
    else if (key === 'view' && !VIEWS[v]) continue;
    else if (key === 'quick' && !QUICK_FILTERS[v]) continue;
    else if (key === 'region' && v !== 'All' && !REGIONS[v]) continue;
    else patch[key] = v;
  }
  Object.assign(state, patch);
}

function writeHash() {
  const params = new URLSearchParams();
  if (state.view !== 'dashboard') params.set('view', state.view);
  if (state.region !== 'All') params.set('region', state.region);
  if (state.quick !== 'All') params.set('quick', state.quick);
  if (state.q) params.set('q', state.q);
  if (state.page > 1) params.set('page', state.page);
  const hash = params.toString();
  const next = `${location.pathname}${location.search}${hash ? `#${hash}` : ''}`;
  history.replaceState(null, '', next);
}

/* ------------------------------------------------------------- selectors -- */

export function filteredLines() {
  const q = state.q.trim().toLowerCase();
  const quick = QUICK_FILTERS[state.quick] || QUICK_FILTERS.All;
  return db.lines.filter((l) => {
    if (state.region !== 'All' && l.region !== state.region) return false;
    if (!quick(l)) return false;
    if (!q) return true;
    const email = l.emailId ? db.byEmail[l.emailId] : null;
    return [l.shipment, l.salesOrder, l.customer, l.container, l.agent, l.cro, l.booking, l.destination, email && email.subject]
      .join(' ').toLowerCase().includes(q);
  });
}

const SORTERS = {
  priority: (l) => priorityScore(l),
  region: (l) => l.region,
  customer: (l) => l.customer,
  salesOrder: (l) => l.salesOrder,
  shipment: (l) => l.shipment,
  destination: (l) => l.destination,
  confirmed: (l) => l.confirmedTs,
  agent: (l) => l.agent,
  agentStatus: (l) => l.agentStatus,
  croStatus: (l) => l.croStatus,
  aging: (l) => l.aging,
  confidence: (l) => l.confidence,
  overall: (l) => l.overall,
};

export function viewRows() {
  let rows = filteredLines();
  if (state.view === 'cro') rows = rows.filter((l) => isCroPending(l.croStatus));
  if (state.view === 'agent') rows = rows.filter((l) => l.agentStatus !== 'Received');
  const get = SORTERS[state.sort.key] || SORTERS.priority;
  const dir = state.sort.dir === 'asc' ? 1 : -1;
  return rows.slice().sort((a, b) => {
    const x = get(a); const y = get(b);
    if (x === y) return a.shipment.localeCompare(b.shipment);
    return (typeof x === 'string' ? x.localeCompare(y) : x - y) * dir;
  });
}

export function pageOf(rows) {
  const size = state.settings.pageSize;
  const pages = Math.max(1, Math.ceil(rows.length / size));
  const page = Math.min(state.page, pages);
  return { page, pages, size, slice: rows.slice((page - 1) * size, page * size) };
}

export function toggleSort(key) {
  const same = state.sort.key === key;
  setState({ sort: { key, dir: same && state.sort.dir === 'desc' ? 'asc' : 'desc' }, page: 1 });
}

const isReleasableLine = (l) => isReleasable(l.overall);

export function kpiSet() {
  const all = filteredLines();
  const n = all.length;
  const count = (f) => all.filter(f).length;
  const agentRecv = count((l) => l.agentStatus === 'Received');
  const croRecv = count((l) => isCroReceived(l.croStatus));
  const croPend = count((l) => isCroPending(l.croStatus));
  const ready = count(isReleasableLine);
  const action = count((l) => l.overall === 'ACTION REQUIRED');
  const overdue = count((l) => l.overdue);
  const review = count((l) => l.overall === 'REVIEW REQUIRED');

  return {
    n, agentRecv, croRecv, croPend, ready, action, overdue, review,
    agentPend: n - agentRecv,
    released: count((l) => l.croStatus === 'CRO Released'),
    partial: count((l) => l.agentStatus === 'Partially Received'),
    none: count((l) => l.agentStatus === 'Pending'),
  };
}



export function regionStats() {
  return ['PK', 'BD', 'SL'].map((code) => {
    const ls = db.lines.filter((l) => l.region === code);
    const c = (f) => ls.filter(f).length;
    return {
      code,
      name: `${code} · ${REGIONS[code]}`,
      lines: ls.length,
      ls,
      readyPct: pct(c(isReleasableLine), ls.length),
      agentPct: pct(c((l) => l.agentStatus === 'Received'), ls.length),
      croPct: pct(c((l) => isCroReceived(l.croStatus)), ls.length),
      croPendPct: pct(c((l) => isCroPending(l.croStatus)), ls.length),
      overdue: c((l) => l.overdue),
      share: (f) => (ls.length ? Math.round((c(f) / ls.length) * 100) : 0),
    };
  });
}

/** Forwarder aggregation — respects the active filters, unlike a static report. */
export function agentStats() {
  const agg = {};
  filteredLines().forEach((l) => {
    const a = agg[l.agent] || (agg[l.agent] = {
      agent: l.agent, region: l.region, total: 0, agentRecv: 0, croRecv: 0,
      pending: 0, ready: 0, agingSum: 0, critical: 0,
    });
    a.total++;
    if (l.agentStatus === 'Received') a.agentRecv++;
    if (isCroReceived(l.croStatus)) a.croRecv++;
    else {
      a.pending++;
      a.agingSum += l.aging;
      if (l.aging > state.settings.criticalDays) a.critical++;
    }
    if (isReleasable(l.overall)) a.ready++;
  });
  return Object.values(agg)
    .map((a) => ({ ...a, avgAging: a.pending ? Math.round((a.agingSum / a.pending) * 10) / 10 : 0 }))
    .sort((x, y) => y.pending - x.pending || y.avgAging - x.avgAging);
}

/**
 * 14-day trend, derived rather than fabricated: on day D, a line counts as
 * "CRO received" once its evidence email had arrived (aging >= days since D),
 * and as "CRO pending" while it was already waiting on that day.
 */
export function trendSeries() {
  const all = filteredLines();
  const received = all.filter((l) => isCroReceived(l.croStatus));
  const pending = all.filter((l) => isCroPending(l.croStatus));
  return Array.from({ length: 14 }, (_, i) => {
    const daysAgo = 13 - i;
    return {
      daysAgo,
      received: received.filter((l) => l.aging >= daysAgo).length,
      pending: pending.filter((l) => l.aging >= daysAgo).length,
    };
  });
}

export function agingMatrix() {
  return regionStats().map((s) => {
    const waiting = s.ls.filter((l) => isCroPending(l.croStatus) || l.agentStatus !== 'Received');
    return {
      name: s.name,
      total: waiting.length,
      buckets: AGING_BUCKETS.map(([label, lo, hi, fill, ink]) => {
        const count = waiting.filter((l) => l.aging >= lo && l.aging <= hi).length;
        return { label, count, fill, ink, share: waiting.length ? (count / waiting.length) * 100 : 0 };
      }),
    };
  });
}

export function actionQueue(limit = 9) {
  return filteredLines()
    .filter((l) => /PENDING|ACTION|REVIEW/.test(l.overall))
    .map((l) => ({ line: l, score: priorityScore(l) }))
    .sort((a, b) => b.score - a.score)
    .slice(0, limit)
    .map(({ line, score }) => ({
      line,
      priority: priorityLabel(score),
      issue: line.overall === 'CRO PENDING' ? 'CRO pending'
        : line.overall === 'AGENT DETAILS PENDING' ? 'Agent details pending'
          : line.overall === 'REVIEW REQUIRED' ? 'Low-confidence match'
            : `Agent details ${line.agentStatus === 'Pending' ? 'missing' : 'partial'} + CRO pending`,
      action: line.overall === 'REVIEW REQUIRED' ? 'Review match manually'
        : /CRO/.test(line.overall) ? 'Follow up logistics for CRO' : 'Request missing agent fields',
    }));
}

export function reviewLines() {
  return db.lines.filter((l) => l.overall === 'REVIEW REQUIRED' && l.emailId)
    .filter((l) => state.region === 'All' || l.region === state.region);
}

export function exceptionEmails() {
  return db.emails.filter((e) => e.unmatched)
    .filter((e) => state.region === 'All' || e.region === state.region);
}

export function emailRows(limit = 60) {
  const q = state.q.trim().toLowerCase();
  return db.emails.filter((e) => {
    if (state.region !== 'All' && e.region !== state.region) return false;
    if (!q) return true;
    return `${e.subject} ${e.sender} ${e.customer} ${e.shipment}`.toLowerCase().includes(q);
  }).slice(0, limit);
}

/* --------------------------------------------------------------- actions -- */

export function openLine(id) { setState({ drawer: { type: 'line', id } }); }
export function openEmail(id) { setState({ drawer: { type: 'email', id } }); }
export function closeDrawer() { setState({ drawer: null }); }

export function checkMailbox() {
  if (state.syncing) return;
  if (db.inboxAt >= db.inbox.length) {
    setState({ syncSummary: { empty: true }, syncLog: [], lastSync: state.lastSync, remaining: 0 });
    return;
  }
  setState({ syncing: true });
  setTimeout(() => {
    const result = processMailbox(db, state.settings);
    setState({
      syncing: false,
      lastSync: result.stamp,
      syncLog: result.log,
      syncSummary: result,
      remaining: result.remaining,
    });
  }, 700);
}

function startAuto() {
  clearInterval(autoTimer);
  autoTimer = setInterval(checkMailbox, state.settings.autoCheckSeconds * 1000);
}

export function toggleAuto() {
  const auto = !state.auto;
  clearInterval(autoTimer);
  if (auto) startAuto();
  setState({ auto });
}

function saveDecision(lineId, decision) {
  state.decisions = { ...state.decisions, [lineId]: decision };
  writeStored({ decisions: state.decisions });
}

/** Accept the parser's match: the line advances as if it had matched cleanly. */
export function confirmMatch(lineId) {
  const line = db.byLine[lineId];
  const email = line.emailId ? db.byEmail[line.emailId] : null;
  if (!line || !email) return;
  line.confidence = Math.max(line.confidence, state.settings.autoConfirm);
  line.matchMethod = `${email.matchMethod} · confirmed by reviewer`;
  if (email.kind === 'CRO') {
    line.croStatus = 'CRO Received';
    if (!line.cro) line.cro = `CRO-${line.region}-MANUAL-${line.id.slice(1)}`;
  } else {
    line.agentStatus = 'Received';
    line.missing = [];
  }
  recompute(line, state.settings);
  line.events.push({ at: state.lastSync, what: `Match confirmed by reviewer → ${line.overall}`, emailId: email.id });
  saveDecision(lineId, 'Confirmed');
  render();
}

/** Reject it: the evidence is unlinked and the line goes back to waiting. */
export function rejectMatch(lineId) {
  const line = db.byLine[lineId];
  if (!line) return;
  const email = line.emailId ? db.byEmail[line.emailId] : null;
  if (email) { email.unmatched = true; email.lineId = null; }
  line.emailId = null;
  line.attachment = '';
  line.confidence = 0;
  line.matchMethod = 'Rejected by reviewer — awaiting new evidence';
  if (email && email.kind === 'CRO') { line.croStatus = 'CRO Not Found'; line.cro = ''; }
  else { line.agentStatus = 'Pending'; }
  recompute(line, state.settings);
  line.events.push({ at: state.lastSync, what: 'Match rejected by reviewer — email sent to exceptions' });
  saveDecision(lineId, 'Rejected');
  render();
}

/** Attach an unmatched email to a line by hand, from the Exceptions view. */
export function linkEmail(emailId, lineId) {
  const email = db.byEmail[emailId];
  const line = db.byLine[lineId];
  if (!email || !line) return;
  email.unmatched = false;
  email.lineId = line.id;
  email.shipment = line.shipment;
  email.salesOrder = line.salesOrder;
  email.confidence = state.settings.autoConfirm;
  email.matchMethod = 'Linked manually by planner';
  email.matchedFields = ['Shipment ID', 'Customer'];
  line.emailId = email.id;
  line.attachment = email.attachment;
  line.confidence = state.settings.autoConfirm;
  line.matchMethod = 'Linked manually by planner';
  line.emailDate = email.received.split(' ')[0];
  line.aging = 0;
  if (email.kind === 'CRO') { line.croStatus = 'CRO Received'; } else { line.agentStatus = 'Received'; line.missing = []; }
  recompute(line, state.settings);
  line.events.push({ at: email.received, what: `Email linked manually → ${line.overall}`, emailId: email.id });
  render();
}

const CSV_COLUMNS = [
  ['region', 'Region'], ['customer', 'Customer'], ['salesOrder', 'Sales order'], ['lineItem', 'Item'],
  ['shipment', 'Shipment'], ['destination', 'Destination'], ['confirmed', 'Confirmed delivery'],
  ['agent', 'Agent'], ['agentStatus', 'Agent details'], ['missing', 'Missing fields'],
  ['cro', 'CRO number'], ['croStatus', 'CRO status'], ['container', 'Container'], ['booking', 'Booking'],
  ['emailDate', 'Email date'], ['aging', 'Aging (days)'], ['confidence', 'Match %'],
  ['matchMethod', 'Match method'], ['overall', 'Overall'], ['emailId', 'Source email'],
];

export function exportCsv() {
  const rows = viewRows();
  const cell = (l, key) => {
    const v = key === 'missing' ? l.missing.join('; ') : l[key];
    return `"${String(v ?? '').replace(/"/g, '""')}"`;
  };
  const csv = [CSV_COLUMNS.map(([, label]) => `"${label}"`).join(',')]
    .concat(rows.map((l) => CSV_COLUMNS.map(([key]) => cell(l, key)).join(',')))
    .join('\r\n');
  return { csv: `﻿${csv}`, count: rows.length };
}
