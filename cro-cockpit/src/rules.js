/**
 * Business rules and reference data for the CRO & Agent Details cockpit.
 *
 * The cockpit reconciles three regional shipment trackers (PK / BD / SL)
 * against the logistics mailbox. A shipment line is releasable only when the
 * forwarder has supplied complete agent details AND a Container Release Order
 * has been received. Everything below encodes that policy in one place.
 */

export const REGIONS = { PK: 'Pakistan', BD: 'Bangladesh', SL: 'Sri Lanka' };

/** Fields a forwarder must supply before agent details count as complete. */
export const AGENT_REQUIRED = [
  'Agent Name', 'Agent Email', 'Forwarder',
  'Contact Person', 'Contact Number', 'Booking Reference',
];

/** agentStatus | croStatus -> overall status. */
export const STATUS_MATRIX = {
  'Received|CRO Received': 'READY',
  'Received|CRO Released': 'RELEASED',
  'Received|CRO Pending': 'CRO PENDING',
  'Received|CRO Not Found': 'CRO PENDING',
  'Partially Received|CRO Received': 'ACTION REQUIRED',
  'Partially Received|CRO Pending': 'ACTION REQUIRED',
  'Partially Received|CRO Not Found': 'ACTION REQUIRED',
  'Partially Received|CRO Released': 'ACTION REQUIRED',
  'Pending|CRO Received': 'AGENT DETAILS PENDING',
  'Pending|CRO Released': 'AGENT DETAILS PENDING',
  'Pending|CRO Pending': 'ACTION REQUIRED',
  'Pending|CRO Not Found': 'ACTION REQUIRED',
};

/** Tunable policy. Editable at runtime from the Settings view. */
export const DEFAULT_SETTINGS = {
  warningDays: 3,
  criticalDays: 7,
  autoConfirm: 90,
  reviewThreshold: 70,
  autoCheckSeconds: 20,
  pageSize: 40,
  theme: 'system',
};

export const SETTINGS_BOUNDS = {
  warningDays: [1, 14],
  criticalDays: [2, 21],
  autoConfirm: [80, 100],
  reviewThreshold: [50, 95],
  autoCheckSeconds: [10, 300],
  pageSize: [20, 200],
};

export const CUSTOMERS = [
  ['Summit Gloves, Inc.', 'SL'], ['DVT Comercio, Importação E Exportaç', 'BD'],
  ['Shelby Group International, Inc.', 'BD'], ['Adolf Wurth GmbH & Co. KG', 'PK'],
  ['Clute Sociedad Comercial De', 'BD'], ['Vostok-Service-Spezkomplekt', 'BD'],
  ['Traffisafe Ltd.', 'BD'], ['Michelin Lanka (Private) Limited', 'SL'],
  ['Ceat OHT Lanka Private Limited', 'SL'], ['Liberty Glove & Safety LLC.', 'PK'],
  ['Ansell Global Trading Center (Malaysia)', 'SL'], ['Pfanner Schutzbekleidung GmbH', 'PK'],
  ['Ejendals Ab', 'PK'], ['Majestic Glove Inc.', 'PK'], ['Gordini USA', 'BD'],
  ['Ultimate Industrial', 'PK'], ['Bunzl Brands & Operations P/L', 'SL'],
  ['Mallory Safety and Supply LLC.', 'PK'], ['Safety Point Trading Company', 'PK'],
  ['Fastenal Europe B.V. (NLD)', 'BD'], ['Globus (Shetland) Ltd.', 'PK'],
  ['U Group SRL', 'SL'], ['Alif Safety Equipment Trading (L.L.C)', 'PK'],
  ['Strauss Operations GmbH & Co. KG', 'PK'], ['FrontLine Safety', 'SL'],
  ['LEBON International S.À.R.L', 'BD'], ['JS Product Inc.', 'PK'],
  ['Stauffer Glove & Safety', 'PK'], ['Juba Personal Protective Equipment S.L.', 'PK'],
  ['UVEX Arbeitschutz GmbH c/o UVEX Safety', 'PK'], ['KCL GmbH', 'BD'],
  ['Banom Inc.', 'SL'], ['NERI SAFETY SRL', 'PK'], ['Mastermans, L.L.P.', 'BD'],
  ['Protective Industrial Products Inc. USA', 'PK'], ['Bridgeway Trading LLC.', 'SL'],
  ['Nassguard Trading W.L.L.', 'PK'], ['Apex Industrial Services Co.', 'BD'],
  ['Renania Trade S.R.L.', 'PK'], ['Jomiba S.A.', 'SL'],
];

export const AGENTS = {
  PK: ['Oceanic Freight (Pvt) Ltd', 'Indus Marine Agency', 'Karachi Container Lines'],
  BD: ['Delta Forwarders BD', 'Meghna Shipping Agency', 'Chattogram Cargo Services'],
  SL: ['Lanka Cargo Lines', 'Serendib Marine Logistics', 'Colombo Freight Partners'],
};

export const PORTS = {
  PK: ['Hamburg', 'Rotterdam', 'New York', 'Jebel Ali', 'Antwerp'],
  BD: ['Le Havre', 'Genoa', 'Savannah', 'Gdansk', 'Barcelona'],
  SL: ['Long Beach', 'Felixstowe', 'Melbourne', 'Valencia', 'Busan'],
};

/** Match ladder: the reference the parser found, and how much it is trusted. */
export const MATCH_LEVELS = [
  ['Level 1 · Exact Shipment ID', 100],
  ['Level 2 · Sales Order', 96],
  ['Level 3 · Customer + Shipment', 88],
  ['Level 4 · Container Number', 93],
  ['Level 5 · Booking / BL Reference', 84],
  ['Level 6 · Fuzzy (customer + destination + date)', 0], // scored at generation time
];

/** Aging buckets, ordered worst-last. Colours come from the --age-* ramp. */
export const AGING_BUCKETS = [
  ['0–1 d', 0, 1, 'var(--age-1)', 'var(--age-ink-1)'],
  ['2–3 d', 2, 3, 'var(--age-2)', 'var(--age-ink-1)'],
  ['4–7 d', 4, 7, 'var(--age-3)', 'var(--age-ink-5)'],
  ['8–14 d', 8, 14, 'var(--age-4)', 'var(--age-ink-5)'],
  ['> 14 d', 15, 9999, 'var(--age-5)', 'var(--age-ink-5)'],
];

/** The clock the demo dataset is anchored to. */
export const TODAY = new Date(2026, 7, 21);

export const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

export function fmtDate(d) {
  return `${String(d.getDate()).padStart(2, '0')}-${MONTHS[d.getMonth()]}-${d.getFullYear()}`;
}

export function fmtStamp(d) {
  return `${fmtDate(d)} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
}

export function addDays(d, n) {
  const x = new Date(d);
  x.setDate(x.getDate() + n);
  return x;
}

/** Compact money for KPI tiles and table cells. */
export function fmtMoney(v) {
  const n = Number(v) || 0;
  if (Math.abs(n) >= 1e6) return `$${(n / 1e6).toFixed(1)}M`;
  if (Math.abs(n) >= 1e3) return `$${Math.round(n / 1e3)}k`;
  return `$${Math.round(n)}`;
}

export function pct(n, d) {
  return d ? `${Math.round((n / d) * 1000) / 10}%` : '—';
}

/** Mulberry32 — deterministic so every reload shows the same book of work. */
export function rng(seed) {
  return function next() {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function pick(r, arr) {
  return arr[Math.floor(r() * arr.length)];
}

export const isCroReceived = (s) => /CRO Received|CRO Released/.test(s);
export const isCroPending = (s) => /CRO Pending|CRO Not Found/.test(s);
export const isReleasable = (s) => /READY|RELEASED/.test(s);

/** Map any status string onto one of the five reserved status tones. */
export function statusTone(s) {
  if (/READY|RELEASED|Received$|Confirmed|Complete/.test(s)) return 'green';
  if (/Partial|Watch/.test(s)) return 'amber';
  if (/PENDING|Pending|ACTION|Overdue|Invalid|Rejected|Escalate|Unmatched/.test(s)) return 'red';
  if (/REVIEW|Review/.test(s)) return 'blue';
  return 'grey';
}

/** Recompute the derived fields of a line after any status change. */
export function recompute(line, settings) {
  line.overall = STATUS_MATRIX[`${line.agentStatus}|${line.croStatus}`] || 'UNKNOWN';
  if (line.confidence < settings.reviewThreshold && line.emailId) line.overall = 'REVIEW REQUIRED';
  line.overdue = /PENDING|ACTION/.test(line.overall) && line.aging > settings.criticalDays;
  return line;
}

/** Work priority: delivery pressure first, then how long it has been waiting. */
export function priorityScore(line) {
  let s = line.aging * 2 + (line.overdue ? 20 : 0);
  if (line.daysToDelivery < 0) s += 40;
  else if (line.daysToDelivery < 7) s += 25;
  else if (line.daysToDelivery < 14) s += 12;
  if (line.overall === 'ACTION REQUIRED') s += 15;
  return s;
}

export function priorityLabel(score) {
  return score > 70 ? 'Critical' : score > 48 ? 'High' : 'Medium';
}
