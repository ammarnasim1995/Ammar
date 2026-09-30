/**
 * Live-data mode.
 *
 * Adapts records produced by tools/import_trackers.py into the shape the views
 * already speak. Where the trackers genuinely hold no equivalent — there is no
 * forwarder column, and no mailbox is connected — the field is left empty
 * rather than invented, and the views that depend on it are hidden.
 */

import { recompute } from './rules.js';

const REGION_NAMES = { PK: 'Pakistan', BD: 'Bangladesh', SL: 'Sri Lanka' };

function toLine(rec, index) {
  const confirmed = rec.confirmed ? new Date(rec.confirmed) : null;
  const evidence = [
    rec.agentDate && { at: rec.agentDate, what: `Agent details received` },
    rec.bookingDate && { at: rec.bookingDate, what: `Booking ${rec.bookingStatus.toLowerCase()}` },
    rec.croDate && { at: rec.croDate, what: `CRO / liner permit received` },
  ].filter(Boolean).sort((a, b) => a.at.localeCompare(b.at));

  return {
    id: rec.id || `L${index}`,
    region: rec.region,
    regionName: rec.regionName || REGION_NAMES[rec.region],
    customer: rec.customer,
    salesOrder: rec.salesOrder,
    lineItem: rec.lineItem,
    // The trackers key a line by sales order + item; there is no separate
    // shipment number until a booking exists, so the sales order is the
    // reference a planner quotes.
    shipment: rec.salesOrder,
    destination: rec.destination,
    salesRegion: rec.salesRegion,
    plant: rec.plant,
    planMonth: rec.planMonth,
    shipMode: rec.shipMode,
    userStatus: rec.userStatus,
    confirmed: rec.confirmed || '—',
    confirmedTs: confirmed ? +confirmed : 0,
    daysToDelivery: rec.daysToDelivery ?? 0,
    // No forwarder column exists; the accountable owner is the area account
    // manager, so that is who the performance view ranks.
    agent: rec.owner,
    kam: rec.kam,
    agentStatus: rec.agentStatus,
    missing: rec.agentStatus === 'Received' ? [] : ['Agent details'],
    bookingStatus: rec.bookingStatus,
    cro: '',
    croStatus: rec.croStatus,
    croDate: rec.croDate,
    container: '',
    booking: '',
    emailDate: rec.croDate || rec.agentDate || '—',
    aging: rec.aging,
    confidence: 100,
    matchMethod: 'Read from the regional shipment tracker',
    emailId: null,
    attachment: '',
    confQty: rec.confQty,
    remQty: rec.remQty,
    asp: rec.asp,
    confValue: rec.confValue,
    balToShip: rec.balToShip,
    readiness: rec.readiness,
    remarks: rec.remarks,
    lastUpdated: rec.punched,
    events: [
      { at: rec.punched, what: `Line punched into the ${rec.region} shipment tracker` },
      ...evidence,
    ],
  };
}

/** Build a db in the same shape the demo generator produces. */
export function datasetToDb(payload, settings) {
  const lines = payload.lines.map(toLine).map((l) => {
    recompute(l, settings);
    // Lines here age in months, so "pending for N days" flags almost
    // everything. What actually hurts is missing the customer's date.
    l.overdue = l.daysToDelivery < 0 && !/READY|RELEASED/.test(l.overall);
    return l;
  });
  return {
    live: true,
    asOf: payload.asOf,
    sources: payload.sources || [],
    lines,
    emails: [],
    byEmail: {},
    byLine: Object.fromEntries(lines.map((l) => [l.id, l])),
    inbox: [],
    inboxAt: 0,
    emailSeq: 0,
  };
}

/**
 * Look for real data: embedded by the build, else fetched next to the page.
 * Returns null when there is none, and the demo dataset is used instead.
 */
export async function loadDataset() {
  if (globalThis.__COCKPIT_DATASET__) return globalThis.__COCKPIT_DATASET__;
  try {
    const res = await fetch('src/dataset.json', { cache: 'no-store' });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}
