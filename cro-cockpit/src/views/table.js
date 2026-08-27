import { h, badge } from '../dom.js';
import { fmtMoney, statusTone } from '../rules.js';
import { isLive, openLine, pageOf, setState, state, toggleSort, viewRows } from '../store.js';

/** key: the sort key (null = not sortable); cls: extra cell classes. */
const COLUMNS = [
  { key: 'region', label: 'Region', cell: (l) => badge(l.region, 'grey') },
  { key: 'customer', label: 'Customer', cls: 'wide', cell: (l) => l.customer },
  { key: 'salesOrder', label: 'Sales order', cls: 'num', cell: (l) => l.salesOrder },
  { key: null, label: 'Item', cls: 'num', cell: (l) => l.lineItem },
  { key: 'shipment', label: 'Shipment', cls: 'num', cell: (l) => l.shipment },
  { key: 'destination', label: 'Destination', cell: (l) => l.destination },
  { key: 'confirmed', label: 'Conf. delivery', cls: 'num', cell: (l) => l.confirmed },
  { key: 'agent', label: 'Agent', cls: 'wide', cell: (l) => l.agent },
  { key: 'agentStatus', label: 'Agent details', cell: (l) => badge(l.agentStatus, statusTone(l.agentStatus)) },
  {
    key: null,
    label: 'Missing fields',
    cls: 'missing',
    cell: (l) => (l.missing.length
      ? `${l.missing.slice(0, 2).join(', ')}${l.missing.length > 2 ? ` +${l.missing.length - 2}` : ''}`
      : '—'),
  },
  { key: null, label: 'CRO number', cls: 'num', cell: (l) => l.cro || '—' },
  { key: 'croStatus', label: 'CRO status', cell: (l) => badge(l.croStatus, statusTone(l.croStatus)) },
  { key: null, label: 'Container', cls: 'num', cell: (l) => l.container },
  { key: null, label: 'Email date', cls: 'num', cell: (l) => l.emailDate },
  { key: 'aging', label: 'Aging', right: true, cls: 'num', cell: (l) => `${l.aging} d`, tone: (l) => (l.overdue ? 'crit' : '') },
  {
    key: 'confidence',
    label: 'Match',
    right: true,
    cls: 'num',
    cell: (l) => (l.emailId ? `${l.confidence}%` : '—'),
    tone: (l) => (!l.emailId ? '' : l.confidence < state.settings.reviewThreshold ? 'crit'
      : l.confidence < state.settings.autoConfirm ? 'warn' : 'good'),
  },
  { key: 'overall', label: 'Overall', cell: (l) => badge(l.overall, statusTone(l.overall)) },
  { key: null, label: 'Source', cls: 'num link', cell: (l) => l.emailId || 'no email' },
];

/** With real trackers loaded there are no mailbox columns, but there is money. */
const LIVE_COLUMNS = [
  { key: 'region', label: 'Source', cell: (l) => badge(l.region, 'grey') },
  { key: null, label: 'Plant', cls: 'num', cell: (l) => l.plant },
  { key: 'customer', label: 'Customer', cls: 'wide', cell: (l) => l.customer },
  { key: null, label: 'Sales region', cell: (l) => l.salesRegion || '—' },
  { key: 'salesOrder', label: 'Sales order', cls: 'num', cell: (l) => l.salesOrder },
  { key: null, label: 'Item', cls: 'num', cell: (l) => l.lineItem },
  { key: null, label: 'Plan month', cls: 'num', cell: (l) => l.planMonth || '—' },
  { key: 'destination', label: 'Destination', cell: (l) => l.destination || '—' },
  { key: 'agent', label: 'Owner (AAM)', cls: 'wide', cell: (l) => l.agent },
  { key: 'confirmed', label: 'Conf. delivery', cls: 'num', cell: (l) => l.confirmed },
  {
    key: null, label: 'Days to del.', right: true, cls: 'num',
    cell: (l) => (l.daysToDelivery < 0 ? `${Math.abs(l.daysToDelivery)} late` : String(l.daysToDelivery)),
    tone: (l) => (l.daysToDelivery < 0 ? 'crit' : ''),
  },
  { key: 'agentStatus', label: 'Agent details', cell: (l) => badge(l.agentStatus, statusTone(l.agentStatus)) },
  { key: null, label: 'Booking', cell: (l) => badge(l.bookingStatus, statusTone(l.bookingStatus)) },
  { key: 'croStatus', label: 'CRO / LP', cell: (l) => badge(l.croStatus, statusTone(l.croStatus)) },
  { key: 'aging', label: 'Aging', right: true, cls: 'num', cell: (l) => `${l.aging} d`, tone: (l) => (l.overdue ? 'crit' : '') },
  { key: null, label: 'Rem. qty', right: true, cls: 'num', cell: (l) => l.remQty.toLocaleString() },
  { key: null, label: 'Bal. to ship', right: true, cls: 'num', cell: (l) => fmtMoney(l.balToShip) },
  { key: 'overall', label: 'Overall', cell: (l) => badge(l.overall, statusTone(l.overall)) },
];

const columns = () => (isLive() ? LIVE_COLUMNS : COLUMNS);

function headerCell(col) {
  if (!col.key) return h('th', { class: col.right ? 'right' : '' }, col.label);
  const active = state.sort.key === col.key;
  const dir = active ? state.sort.dir : null;
  return h('th', {
    class: `sortable${col.right ? ' right' : ''}`,
    'aria-sort': active ? (dir === 'asc' ? 'ascending' : 'descending') : null,
  }, h('button', { onclick: () => toggleSort(col.key) },
    col.label,
    h('span.arrow', null, active ? (dir === 'asc' ? '▲' : '▼') : '↕')));
}

function bodyRow(line) {
  return h('tr.clickable', {
    tabindex: 0,
    onclick: () => openLine(line.id),
    onkeydown: (e) => { if (e.key === 'Enter') openLine(line.id); },
  }, columns().map((col) => {
    const classes = [col.cls, col.right ? 'right' : '', col.tone ? col.tone(line) : ''].filter(Boolean).join(' ');
    return h('td', { class: classes }, col.cell(line));
  }));
}

function pager({ page, pages }) {
  if (pages <= 1) return null;
  const go = (p) => setState({ page: Math.min(pages, Math.max(1, p)) });
  return h('div.pager', null,
    h('button.btn', { onclick: () => go(page - 1), disabled: page === 1, 'aria-label': 'Previous page' }, '‹ Prev'),
    h('span.page.num', null, `Page ${page} of ${pages}`),
    h('button.btn', { onclick: () => go(page + 1), disabled: page === pages, 'aria-label': 'Next page' }, 'Next ›'));
}

export function tableView(title) {
  const rows = viewRows();
  const paged = pageOf(rows);
  const hint = state.view === 'agent'
    ? 'missing fields shown per line'
    : 'select any row for full traceability';

  return h('div.card', null,
    h('div.card-head', null,
      h('h2', null, title),
      h('span.card-hint', null, hint),
      h('div.right', null, h('span.num', null, `${rows.length.toLocaleString()} lines`))),
    rows.length
      ? h('div.table-wrap', { 'data-scroll': '' },
        h('table', null,
          h('thead', null, h('tr', null, columns().map(headerCell))),
          h('tbody', null, paged.slice.map(bodyRow))))
      : h('div.empty', null,
        h('strong', null, 'No lines match'),
        'Clear the search box or pick a different quick filter.'),
    h('div.card-foot', { style: 'display:flex; align-items:center; gap:12px; flex-wrap:wrap' },
      h('span', null, rows.length
        ? `Showing ${paged.slice.length} of ${rows.length.toLocaleString()} matching lines · sources: PK/BD/SL shipment trackers + logistics@midassafety.com · sync ${state.lastSync}`
        : `0 of ${rows.length} lines`),
      h('div', { style: 'margin-left:auto' }, pager(paged))));
}
