/**
 * Deterministic demo dataset.
 *
 * Stands in for the nightly extract of the PK / BD / SL shipment trackers plus
 * the parsed contents of logistics@midassafety.com. The seed is fixed, so the
 * same book of work appears on every load and screenshots stay comparable.
 */

import {
  AGENTS, AGENT_REQUIRED, CUSTOMERS, MATCH_LEVELS, PORTS, REGIONS, TODAY,
  addDays, fmtDate, isCroReceived, pick, recompute, rng,
} from './rules.js';

const LINE_COUNT = 420;
const MAILBOX = 'logistics@midassafety.com';
const PLANNING = 'supply.planning@midassafety.com';

const senderFor = (agent) =>
  `${agent.toLowerCase().replace(/[^a-z]+/g, '.').replace(/^\.|\.$/g, '')}@forwarder.com`;

function croBody({ cro, booking, container, shipment, salesOrder, customer, vessel, etd, eta, agent }) {
  return [
    'Dear Team,', '',
    'Please find attached the Container Release Order against the below booking.', '',
    `CRO No: ${cro || '—'}`,
    `Booking No: ${booking}`,
    `Container No: ${container}`,
    `Shipment: ${shipment}`,
    `SO: ${salesOrder}`,
    `Customer: ${customer}`,
    `Vessel: MV ${vessel}`,
    `ETD: ${etd}  ETA: ${eta}`, '',
    'Regards,', agent,
  ].join('\n');
}

function agentBody({ agent, booking, container, shipment, customer, contact, phone, incomplete }) {
  return [
    'Dear Team,', '',
    'Agent details for the below shipment as requested.', '',
    `Shipping Agent: ${agent}`,
    `Forwarder: ${agent}`,
    `Booking Reference: ${booking}`,
    `Container Reference: ${container}`,
    `Shipment: ${shipment}`,
    `Customer: ${customer}`,
    incomplete ? '\n(Remaining details to follow.)' : `Contact Person: ${contact}\nContact Number: ${phone}`,
    '', 'Regards,', agent,
  ].join('\n');
}

export function buildDataset(settings) {
  const r = rng(20260821);
  const lines = [];
  const emails = [];
  let emailSeq = 1000;

  for (let i = 0; i < LINE_COUNT; i++) {
    const [customer, region] = CUSTOMERS[i % CUSTOMERS.length];
    const agent = pick(r, AGENTS[region]);
    const salesOrder = `SO-${41000 + Math.floor(r() * 8000)}`;
    const shipment = `SH-${region}-${26000 + Math.floor(r() * 3000)}`;
    const lineItem = String((i % 6) * 10 + 10);
    const confirmed = addDays(TODAY, Math.floor(r() * 46) - 8);

    const roll = r();
    const agentStatus = roll < 0.72 ? 'Received' : roll < 0.87 ? 'Partially Received' : 'Pending';
    const croRoll = r();
    const croStatus = agentStatus === 'Pending'
      ? (croRoll < 0.35 ? 'CRO Received' : croRoll < 0.9 ? 'CRO Pending' : 'CRO Not Found')
      : (croRoll < 0.62 ? 'CRO Received' : croRoll < 0.72 ? 'CRO Released'
        : croRoll < 0.94 ? 'CRO Pending' : 'CRO Not Found');

    const missing = agentStatus === 'Received' ? []
      : agentStatus === 'Pending' ? AGENT_REQUIRED.slice()
        : AGENT_REQUIRED.filter(() => r() < 0.34).slice(0, 3);
    if (agentStatus === 'Partially Received' && missing.length === 0) missing.push('Contact Number');

    const hasEmail = agentStatus !== 'Pending' || croStatus !== 'CRO Not Found';
    const emailDate = hasEmail ? addDays(TODAY, -Math.floor(r() * 19) - 1) : null;
    const aging = emailDate
      ? Math.round((TODAY - emailDate) / 86400000)
      : Math.floor(r() * 22) + 3;

    // Weighted towards the top of the ladder: most emails quote a clean reference.
    const level = MATCH_LEVELS[Math.floor(Math.pow(r(), 1.7) * MATCH_LEVELS.length)];
    const confidence = level[1] || 62 + Math.floor(r() * 26);

    const container = `${['MSKU', 'TGHU', 'CMAU', 'HLXU'][Math.floor(r() * 4)]}${1000000 + Math.floor(r() * 8999999)}`;
    const booking = `BKG${700000 + Math.floor(r() * 99999)}`;
    const cro = isCroReceived(croStatus)
      ? `CRO-${region}-${String(confirmed.getMonth() + 1).padStart(2, '0')}${String(confirmed.getDate()).padStart(2, '0')}-${1000 + Math.floor(r() * 8999)}`
      : '';

    const line = {
      id: `L${i}`,
      region,
      regionName: REGIONS[region],
      customer,
      salesOrder,
      lineItem,
      shipment,
      destination: pick(r, PORTS[region]),
      confirmed: fmtDate(confirmed),
      confirmedTs: +confirmed,
      daysToDelivery: Math.round((confirmed - TODAY) / 86400000),
      agent,
      agentStatus,
      missing,
      cro,
      croStatus,
      container,
      booking,
      emailDate: emailDate ? fmtDate(emailDate) : '—',
      aging,
      confidence: hasEmail ? confidence : 0,
      matchMethod: hasEmail ? level[0] : 'No evidence in mailbox',
      emailId: null,
      attachment: '',
      lastUpdated: `${fmtDate(addDays(TODAY, -Math.floor(r() * 3)))} 08:3${Math.floor(r() * 9)}`,
      events: [],
    };

    if (hasEmail) {
      const kind = isCroReceived(croStatus) ? 'CRO' : 'Agent Details';
      const id = `EM-${++emailSeq}`;
      const email = {
        id,
        region,
        customer,
        shipment,
        salesOrder,
        kind,
        subject: `${kind === 'CRO' ? 'CRO / Container Release – ' : 'Agent details – '}${shipment} · ${customer.split(',')[0]}`,
        sender: senderFor(agent),
        to: MAILBOX,
        cc: PLANNING,
        received: `${fmtDate(emailDate)} ${String(7 + Math.floor(r() * 10)).padStart(2, '0')}:${String(Math.floor(r() * 60)).padStart(2, '0')}`,
        folder: kind === 'CRO' ? 'Logistics / CRO' : 'Logistics / Agent Details',
        conversation: `AAQkAG${100000 + Math.floor(r() * 899999)}`,
        attachment: kind === 'CRO'
          ? (r() < 0.6 ? `CRO_${shipment}.pdf` : `Release_Order_${booking}.xlsx`)
          : (r() < 0.4 ? `Agent_Details_${shipment}.xlsx` : ''),
        matchMethod: level[0],
        confidence,
        matchedFields: ['Customer', 'Destination']
          .concat(confidence >= 84 ? ['Shipment ID'] : [])
          .concat(confidence >= 93 ? ['Container'] : []),
        croConfidence: isCroReceived(croStatus) ? (cro && confidence >= 90 ? 100 : confidence >= 84 ? 90 : 75) : 50,
        lineId: line.id,
        body: kind === 'CRO'
          ? croBody({
            cro, booking, container, shipment, salesOrder, customer, agent,
            vessel: pick(r, ['Northern Grace', 'Ocean Trader', 'Asian Pearl', 'Blue Meridian']),
            etd: fmtDate(addDays(confirmed, -6)),
            eta: fmtDate(addDays(confirmed, 12)),
          })
          : agentBody({
            agent, booking, container, shipment, customer,
            contact: pick(r, ['A. Rahman', 'S. Fernando', 'M. Iqbal', 'T. Das']),
            phone: `+9${Math.floor(r() * 9)} 3${Math.floor(1000000 + r() * 8999999)}`,
            incomplete: missing.length > 0,
          }),
      };
      emails.push(email);
      line.emailId = id;
      line.attachment = email.attachment;
      line.events.push({
        at: email.received,
        what: `${kind} email parsed · ${level[0]} · ${confidence}% confidence`,
        emailId: id,
      });
    }

    line.events.unshift({ at: line.confirmed, what: `Line loaded from ${region} shipment tracker` });
    recompute(line, settings);
    lines.push(line);
  }

  // Unread mailbox: the queue "Check mailbox" drains, worst-aged first.
  const ir = rng(90210);
  const inbox = lines
    .filter((l) => /CRO Pending|CRO Not Found/.test(l.croStatus) || l.agentStatus !== 'Received')
    .sort((a, b) => b.aging - a.aging)
    .filter(() => ir() < 0.55)
    .map((l) => ({
      lineId: l.id,
      kind: /CRO Pending|CRO Not Found/.test(l.croStatus) ? 'CRO' : 'Agent Details',
      parseFail: ir() < 0.07,
      lowConf: ir() < 0.13,
    }));

  return {
    lines,
    emails,
    byEmail: Object.fromEntries(emails.map((e) => [e.id, e])),
    byLine: Object.fromEntries(lines.map((l) => [l.id, l])),
    inbox,
    inboxAt: 0,
    emailSeq,
  };
}

/**
 * Parse the next batch of unread mail and advance the lines it evidences.
 * Returns a log the UI shows, including the parse failures that land in
 * Exceptions instead of updating a line.
 */
export function processMailbox(db, settings, now = new Date()) {
  const stamp = `${fmtDate(now)} ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
  const batch = db.inbox.slice(db.inboxAt, db.inboxAt + 3 + Math.floor(Math.random() * 5));
  db.inboxAt += batch.length;

  const log = [];
  let updated = 0; let errors = 0; let review = 0;

  batch.forEach((item) => {
    const line = db.byLine[item.lineId];
    if (!line) return;

    const id = `EM-${++db.emailSeq}`;
    const isCro = item.kind === 'CRO';
    const cro = isCro
      ? `CRO-${line.region}-${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}-${1000 + Math.floor(Math.random() * 8999)}`
      : line.cro;
    const confidence = item.parseFail ? 0 : item.lowConf ? 58 + Math.floor(Math.random() * 10) : 96;

    const email = {
      id,
      region: line.region,
      customer: line.customer,
      shipment: item.parseFail ? '' : line.shipment,
      salesOrder: item.parseFail ? '' : line.salesOrder,
      kind: item.kind,
      subject: `${isCro ? 'CRO / Container Release – ' : 'Agent details – '}${line.shipment} · ${line.customer.split(',')[0]}`,
      sender: senderFor(line.agent),
      to: MAILBOX,
      cc: PLANNING,
      received: stamp,
      folder: isCro ? 'Logistics / CRO' : 'Logistics / Agent Details',
      conversation: `AAQkAG${100000 + Math.floor(Math.random() * 899999)}`,
      attachment: isCro ? `CRO_${line.shipment}.pdf` : `Agent_Details_${line.shipment}.xlsx`,
      matchMethod: item.parseFail
        ? 'Unparsed – no recognisable reference'
        : item.lowConf ? 'Level 6 · Fuzzy (customer + destination + date)' : 'Level 1 · Exact Shipment ID',
      confidence,
      matchedFields: item.parseFail ? []
        : item.lowConf ? ['Customer', 'Destination'] : ['Shipment ID', 'Customer', 'Container', 'Booking'],
      croConfidence: isCro ? (item.parseFail ? 0 : item.lowConf ? 70 : 100) : 50,
      isNew: true,
      unmatched: item.parseFail,
      lineId: item.parseFail ? null : line.id,
      body: isCro
        ? croBody({
          cro, booking: line.booking, container: line.container, shipment: line.shipment,
          salesOrder: line.salesOrder, customer: line.customer, agent: line.agent,
          vessel: 'Ocean Trader', etd: line.confirmed, eta: line.confirmed,
        })
        : agentBody({
          agent: line.agent, booking: line.booking, container: line.container,
          shipment: line.shipment, customer: line.customer,
          contact: 'A. Rahman', phone: `+92 3${Math.floor(1000000 + Math.random() * 8999999)}`,
          incomplete: false,
        }),
    };

    db.emails.unshift(email);
    db.byEmail[id] = email;

    if (item.parseFail) {
      errors++;
      log.push({
        shipment: line.shipment, kind: item.kind, tone: 'red', emailId: id,
        note: 'no recognisable reference — routed to exceptions',
      });
      return;
    }

    const from = line.overall;
    line.emailId = id;
    line.emailDate = fmtDate(now);
    line.aging = 0;
    line.confidence = confidence;
    line.matchMethod = email.matchMethod;
    line.attachment = email.attachment;
    line.lastUpdated = stamp;
    if (isCro) { line.croStatus = 'CRO Received'; line.cro = cro; } else { line.agentStatus = 'Received'; line.missing = []; }
    recompute(line, settings);
    line.events.push({
      at: stamp,
      what: `${item.kind} email parsed · ${from} → ${line.overall}`,
      emailId: id,
    });

    if (line.overall === 'REVIEW REQUIRED') review++; else updated++;
    log.push({
      shipment: line.shipment,
      kind: item.kind,
      tone: line.overall === 'REVIEW REQUIRED' ? 'amber' : 'green',
      emailId: id,
      note: from === line.overall
        ? `${item.kind} recorded · still ${line.overall}`
        : `${from} → ${line.overall}${line.overall === 'REVIEW REQUIRED' ? ` (${confidence}% match)` : ''}`,
    });
  });

  return {
    stamp,
    log,
    parsed: batch.length,
    updated,
    errors,
    review,
    remaining: db.inbox.length - db.inboxAt,
  };
}
