import { h, badge, toast } from '../dom.js';
import { AGENT_REQUIRED, statusTone } from '../rules.js';
import { closeDrawer, getDb, openEmail, openLine, state } from '../store.js';

function pairs(rows) {
  return h('div.pairs', null, rows.filter(Boolean).map(([k, v, tone]) => h('div.pair', null,
    h('span.k', null, k),
    h('span', null, tone ? badge(String(v), tone) : String(v)))));
}

function block(title, body) {
  return h('div.block', null, h('div.label', null, title), body);
}

function timeline(events) {
  return h('div.timeline', null, events.map((e) => h('div.tl-item', null,
    h('div.tl-mark', null, h('i'), h('s')),
    h('div.tl-body', null,
      h('span.tl-when.num', null, e.at),
      h('span.tl-what', null, e.what),
      e.emailId
        ? h('button.link', {
          style: 'align-self:flex-start; font-size:11.5px; color:var(--accent-ink); font-weight:600',
          onclick: () => openEmail(e.emailId),
        }, `${e.emailId} →`)
        : null))));
}

async function copy(label, textToCopy) {
  try {
    await navigator.clipboard.writeText(textToCopy);
    toast(`${label} copied to clipboard`);
  } catch {
    toast('Clipboard unavailable in this window');
  }
}

function chaseEmail(line) {
  const what = line.agentStatus !== 'Received'
    ? `the outstanding agent details (${(line.missing.length ? line.missing : AGENT_REQUIRED).join(', ')})`
    : 'the Container Release Order';
  return [
    `To: ${line.agent.toLowerCase().replace(/[^a-z]+/g, '.').replace(/^\.|\.$/g, '')}@forwarder.com`,
    `Subject: Follow-up – ${what.startsWith('the Container') ? 'CRO' : 'agent details'} outstanding · ${line.shipment} · ${line.customer}`,
    '',
    'Dear Team,',
    '',
    `We are still awaiting ${what} for the shipment below. Confirmed delivery is ${line.confirmed}`
    + `${line.daysToDelivery < 0 ? ` (${Math.abs(line.daysToDelivery)} days ago)` : ` (in ${line.daysToDelivery} days)`},`
    + ` and the request has been open for ${line.aging} days.`,
    '',
    `Shipment: ${line.shipment} (item ${line.lineItem})`,
    `Sales order: ${line.salesOrder}`,
    `Customer: ${line.customer}`,
    `Destination: ${line.destination}`,
    `Booking: ${line.booking}`,
    `Container: ${line.container}`,
    '',
    'Please share the outstanding documents today so we can release the container on schedule.',
    '',
    'Regards,',
    'Supply Chain Planning · Midas Safety',
  ].join('\n');
}

function lineDrawer(line) {
  const db = getDb();
  const email = line.emailId ? db.byEmail[line.emailId] : null;
  const s = state.settings;
  const decision = state.decisions[line.id];

  return {
    kicker: `Shipment line · ${line.region}`,
    title: `${line.shipment} · item ${line.lineItem}`,
    subtitle: `${line.customer} · ${line.salesOrder}`,
    blocks: [
      block('Status', pairs([
        ['Overall status', line.overall, statusTone(line.overall)],
        ['Agent details', line.agentStatus, statusTone(line.agentStatus)],
        ['Missing agent fields', line.missing.length ? line.missing.join(', ') : 'none'],
        ['CRO status', line.croStatus, statusTone(line.croStatus)],
        ['CRO number', line.cro || '—'],
        ['Aging', `${line.aging} days${line.overdue ? ' · overdue' : ''}`, line.overdue ? 'red' : null],
        ['Confirmed delivery', `${line.confirmed} (${line.daysToDelivery >= 0 ? `in ${line.daysToDelivery} d` : `${Math.abs(line.daysToDelivery)} d ago`})`],
        decision ? ['Reviewer decision', decision, decision === 'Confirmed' ? 'green' : 'red'] : null,
      ])),
      block('Shipment record', pairs([
        ['Region file', `${line.region} · ${line.regionName} shipment tracker`],
        ['Destination', line.destination],
        ['Agent / forwarder', line.agent],
        ['Container', line.container],
        ['Booking', line.booking],
        ['Last updated', line.lastUpdated],
      ])),
      block('Matching logic', pairs([
        ['Match method', line.matchMethod],
        ['Match confidence', line.emailId ? `${line.confidence}%` : 'no evidence',
          !line.emailId ? 'grey' : line.confidence >= s.autoConfirm ? 'green' : line.confidence >= s.reviewThreshold ? 'amber' : 'red'],
        ['Decision', !line.emailId ? 'Waiting for evidence'
          : line.confidence >= s.autoConfirm ? 'Auto-confirmed'
            : line.confidence >= s.reviewThreshold ? 'Accepted, flagged' : 'Sent to review queue'],
        ['Matched fields', email ? email.matchedFields.join(', ') || 'none' : '—'],
        ['Source email', email ? `${email.id} · ${email.folder}` : 'no supporting email found'],
        ['Source attachment', email && email.attachment ? email.attachment : '—'],
      ])),
      block('History', timeline(line.events)),
      email ? block('Source email body', h('div.pre.num', null, `${email.subject}\n\n${email.body}`)) : null,
    ],
    actions: [
      h('button.btn.btn-primary', { onclick: () => copy('Chase email', chaseEmail(line)) }, 'Copy chase email'),
      email ? h('button.btn', { onclick: () => openEmail(email.id) }, 'Open source email') : null,
      h('button.btn', {
        onclick: () => copy('Line reference', `${line.shipment} · item ${line.lineItem} · ${line.salesOrder} · ${line.customer}`),
      }, 'Copy reference'),
    ],
  };
}

function emailDrawer(email) {
  const db = getDb();
  const linked = db.lines.filter((l) => l.emailId === email.id);
  const s = state.settings;

  return {
    kicker: `Source email · ${email.folder}`,
    title: email.subject,
    subtitle: `${email.received} · ${email.sender}`,
    blocks: [
      block('Headers', pairs([
        ['From', email.sender], ['To', email.to], ['CC', email.cc],
        ['Received', email.received], ['Folder', email.folder],
        ['Conversation ID', email.conversation], ['Attachment', email.attachment || 'none'],
      ])),
      block('Extracted data', pairs([
        ['Type', email.kind, email.kind === 'CRO' ? 'blue' : 'grey'],
        ['Shipment', email.shipment || 'not found'],
        ['Sales order', email.salesOrder || 'not found'],
        ['Customer', email.customer],
        ['CRO confidence', `${email.croConfidence}%`,
          email.croConfidence >= 90 ? 'green' : email.croConfidence >= 75 ? 'amber' : 'grey'],
        ['Match method', email.matchMethod],
        ['Match confidence', email.unmatched ? 'unmatched' : `${email.confidence}%`,
          email.unmatched ? 'red' : email.confidence >= s.autoConfirm ? 'green' : 'amber'],
        ['Linked shipment lines', `${linked.length} line(s)`],
      ])),
      linked.length
        ? block('Linked lines', h('div', { style: 'display:flex; flex-direction:column; gap:6px' },
          linked.map((l) => h('button.btn', {
            style: 'justify-content:flex-start',
            onclick: () => openLine(l.id),
          }, `${l.shipment} · item ${l.lineItem} · ${l.overall}`))))
        : null,
      block('Body', h('div.pre.num', null, email.body)),
    ],
    actions: [
      h('button.btn.btn-primary', {
        onclick: () => copy('Email', `${email.subject}\n\nFrom: ${email.sender}\nReceived: ${email.received}\n\n${email.body}`),
      }, 'Copy email'),
    ],
  };
}

export function drawerView() {
  const ref = state.drawer;
  if (!ref) return null;
  const db = getDb();
  const model = ref.type === 'line'
    ? (db.byLine[ref.id] ? lineDrawer(db.byLine[ref.id]) : null)
    : (db.byEmail[ref.id] ? emailDrawer(db.byEmail[ref.id]) : null);
  if (!model) return null;

  return h('div.scrim', { onclick: closeDrawer },
    h('div.drawer', {
      role: 'dialog', 'aria-modal': 'true', 'aria-label': model.title,
      onclick: (e) => e.stopPropagation(),
    },
    h('div.drawer-head', null,
      h('div', { style: 'min-width:0' },
        h('div.label', null, model.kicker),
        h('h2', null, model.title),
        h('div.drawer-sub', null, model.subtitle)),
      h('button.drawer-close', { onclick: closeDrawer, 'aria-label': 'Close panel', 'data-focus-key': 'drawer-close' }, '×')),
    h('div.drawer-body', null,
      model.blocks.filter(Boolean),
      h('div.drawer-actions', null, model.actions.filter(Boolean),
        h('button.btn', { onclick: closeDrawer }, 'Close')))));
}
