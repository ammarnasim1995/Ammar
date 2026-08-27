import { h, badge } from '../dom.js';
import { emailRows, getDb, openEmail, state } from '../store.js';

export function emailsView() {
  const rows = emailRows();
  if (!rows.length) {
    return h('div.card', null, h('div.empty', null,
      h('strong', null, 'No parsed emails match'),
      'Try a different region or clear the search box.'));
  }

  const db = getDb();
  return h('div', { style: 'display:flex; flex-direction:column; gap:10px' },
    rows.map((e) => h('button.email-card', {
      onclick: () => openEmail(e.id),
      'aria-label': `Open email: ${e.subject}`,
    },
    h('div.email-main', null,
      h('div.email-subject', null,
        badge(e.kind, e.kind === 'CRO' ? 'blue' : 'grey'),
        e.isNew ? badge('NEW', 'green') : null,
        e.unmatched ? badge('UNMATCHED', 'red') : null,
        h('span.s', null, e.subject)),
      h('div.email-meta.num', null,
        [e.received, e.sender, e.folder, e.attachment].filter(Boolean).join('  ·  ')),
      h('div.email-snippet', null, e.body.split('\n').filter((x) => x.trim())[1] || '')),
    h('div.email-fields', null,
      h('div.label', null, 'Extracted'),
      h('div.row', null, h('span', null, 'Shipment'), h('span.num', null, e.shipment || '—')),
      h('div.row', null, h('span', null, 'Order'), h('span.num', null, e.salesOrder || '—')),
      h('div.row', null, h('span', null, 'Match'), h('span.num', null, e.unmatched ? 'none' : `${e.confidence}%`)),
      h('div.row', null, h('span', null, 'Line'),
        h('span.num', null, e.lineId && db.byLine[e.lineId] ? db.byLine[e.lineId].shipment : '—'))))),
    rows.length >= 60
      ? h('div.card-foot', null, `Showing the 60 most recent parsed emails${state.region !== 'All' ? ` for ${state.region}` : ''}.`)
      : null);
}
