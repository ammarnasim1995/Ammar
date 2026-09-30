import { h, badge } from '../dom.js';
import { agingLegend, agingStack, meter, monthValueChart, trendChart } from '../charts.js';
import { fmtMoney, pct } from '../rules.js';
import {
  actionQueue, agentStats, agingBuckets, agingMatrix, blockedByWindow, isLive, kpiSet, openLine,
  regionStats, setState, state, trendSeries,
} from '../store.js';

const TONE_INK = { green: 'var(--good)', amber: 'var(--warn)', red: 'var(--crit)', blue: 'var(--accent-ink)' };
const TONE_FILL = { green: 'var(--good)', amber: 'var(--warn)', red: 'var(--crit)', blue: 'var(--accent)' };

function kpi({ label, value, share, sub, tone, total }) {
  return h('div.kpi', null,
    h('div.label', null, label),
    h('div.kpi-val', null,
      h('span.n.num', null, value.toLocaleString()),
      h('span.pct.num', { style: `color:${TONE_INK[tone] || 'var(--ink-2)'}` }, share)),
    meter(total ? (value / total) * 100 : 0, TONE_FILL[tone] || 'var(--ink-3)'),
    h('div.kpi-sub', null, sub));
}

function kpiRow() {
  const k = kpiSet();
  const n = k.n;
  const live = isLive();
  return h('div.grid-kpi', null,
    kpi({ label: 'Total shipment lines', value: n, share: '100%', sub: 'PK + BD + SL normalised', tone: 'blue', total: n }),
    kpi({ label: 'Agent details received', value: k.agentRecv, share: pct(k.agentRecv, n), sub: `${k.agentPend} lines incomplete or pending`, tone: 'green', total: n }),
    kpi({
      label: 'CRO received', value: k.croRecv, share: pct(k.croRecv, n),
      sub: live ? 'container release / liner permit on file' : `incl. ${k.released} released`,
      tone: 'green', total: n,
    }),
    kpi({ label: 'Ready for release', value: k.ready, share: pct(k.ready, n), sub: 'agent details + CRO both confirmed', tone: 'green', total: n }),
    kpi({
      label: 'CRO pending', value: k.croPend, share: pct(k.croPend, n),
      sub: live ? 'no release order recorded against the line' : 'no valid CRO evidence in mailbox',
      tone: 'amber', total: n,
    }),
    kpi({
      label: 'Agent details pending', value: k.agentPend, share: pct(k.agentPend, n),
      sub: live ? 'forwarder has not returned the details' : `${k.partial} partial · ${k.none} none`,
      tone: 'amber', total: n,
    }),
    kpi({ label: 'Action required', value: k.action, share: pct(k.action, n), sub: 'both sides incomplete', tone: 'red', total: n }),
    live
      ? kpi({
        label: 'Past confirmed delivery', value: k.lateLines, share: pct(k.lateLines, n),
        sub: 'delivery date passed, still not releasable', tone: 'red', total: n,
      })
      : kpi({
        label: 'Overdue', value: k.overdue, share: pct(k.overdue, n),
        sub: `pending more than ${state.settings.criticalDays} days`, tone: 'red', total: n,
      }));
}

/** Value at stake — only meaningful once real order values are loaded. */
function valueRow() {
  const k = kpiSet();
  return h('div.grid-3', null,
    h('div.kpi', null,
      h('div.label', null, 'Balance to ship'),
      h('div.kpi-val', null, h('span.n.num', null, fmtMoney(k.valueTotal))),
      meter(100, 'var(--accent)'),
      h('div.kpi-sub', null, `${k.n.toLocaleString()} open lines in this filter`)),
    h('div.kpi', null,
      h('div.label', null, 'Blocked value'),
      h('div.kpi-val', null,
        h('span.n.num', null, fmtMoney(k.valueBlocked)),
        h('span.pct.num', { style: 'color:var(--warn)' }, pct(k.valueBlocked, k.valueTotal))),
      meter(k.valueTotal ? (k.valueBlocked / k.valueTotal) * 100 : 0, 'var(--warn)'),
      h('div.kpi-sub', null, 'agent details or CRO still outstanding')),
    h('div.kpi', null,
      h('div.label', null, 'Past confirmed delivery'),
      h('div.kpi-val', null,
        h('span.n.num', null, fmtMoney(k.valueLate)),
        h('span.pct.num', { style: 'color:var(--crit)' }, `${k.lateLines} lines`)),
      meter(k.valueTotal ? (k.valueLate / k.valueTotal) * 100 : 0, 'var(--crit)'),
      h('div.kpi-sub', null, 'delivery date passed, still not releasable')));
}

function regionCards() {
  return h('div.card', null,
    h('div.card-head', null, h('h2', null, 'Region performance'), h('span.card-hint', null, 'select a region to drill into the monitor')),
    h('div.card-body', null,
      h('div.grid-3', null, regionStats().map((s) => h('button.region-card', {
        onclick: () => setState({ view: 'monitor', region: s.code, page: 1 }),
        'aria-label': `${s.name}: ${s.readyPct} ready for release. Open the monitor filtered to ${s.code}.`,
      },
      h('div.region-top', null,
        h('span.region-name.trunc', null, s.name),
        h('span.num', { style: 'font-size:11px; color:var(--ink-2)' }, `${s.lines} lines`)),
      h('div.region-big.num', null, s.readyPct),
      h('div.label', null, 'Ready for release'),
      h('div.region-rows', null,
        h('div', null, h('span', null, 'Agent details'), h('span.num', null, s.agentPct)),
        h('div', null, h('span', null, 'CRO received'), h('span.num', null, s.croPct)),
        h('div', null, h('span', null, isLive() ? 'Past delivery date' : 'Overdue'),
          h('span.num', { style: s.overdue > 25 ? 'color:var(--crit)' : '' }, String(s.overdue)))))))));
}

function trendCard() {
  if (isLive()) {
    return h('div.card', null,
      h('div.card-head', null,
        h('h2', null, 'Balance to ship by delivery window'),
        h('span.card-hint', null, 'how much is blocked, and how soon it is due')),
      h('div.card-body', null, monthValueChart(blockedByWindow(), fmtMoney)));
  }
  return h('div.card', null,
    h('div.card-head', null,
      h('h2', null, '14-day trend'),
      h('span.card-hint', null, 'CRO evidence arriving vs still open')),
    h('div.card-body', null, trendChart(trendSeries())));
}

function agentPendingCard() {
  const rows = agentStats().slice(0, 6);
  return h('div.card', null,
    h('div.card-head', null,
      h('h2', null, isLive() ? 'CRO pending by owner' : 'CRO pending by agent'),
      h('span.card-hint', null, 'ranked by pending lines')),
    h('div.table-wrap', null,
      h('table', null,
        h('thead', null, h('tr', null,
          h('th', null, isLive() ? 'Owner (AAM)' : 'Agent'),
          h('th.right', null, 'Lines'),
          h('th.right', null, 'Avg aging'),
          h('th.right', null, 'Critical'))),
        h('tbody', null, rows.length ? rows.map((a) => h('tr', null,
          h('td', { style: 'font-weight:500' }, a.agent),
          h('td.right.num', null, String(a.pending)),
          h('td.right.num', null, `${a.avgAging} d`),
          h('td.right', null, badge(String(a.critical), a.critical > 12 ? 'red' : a.critical > 5 ? 'amber' : 'grey'))))
          : [h('tr', null, h('td', { colspan: 4 }, h('div.empty', null, 'No agents match the current filters')))]))));
}

function actionCard() {
  const rows = actionQueue();
  return h('div.card', null,
    h('div.card-head', null,
      h('h2', null, 'Action required'),
      h('span.card-hint', null, 'priority = delivery date + pending status + aging')),
    h('div.table-wrap', null,
      h('table', null,
        h('thead', null, h('tr', null,
          h('th', null, 'Priority'), h('th', null, 'Shipment'), h('th', null, 'Customer'),
          h('th', null, 'Issue'), h('th.right', null, 'Aging'), h('th', null, 'Next action'))),
        h('tbody', null, rows.length ? rows.map(({ line, priority, issue, action }) => h('tr.clickable', {
          tabindex: 0,
          onclick: () => openLine(line.id),
          onkeydown: (e) => { if (e.key === 'Enter') openLine(line.id); },
        },
        h('td', null, badge(priority, priority === 'Critical' ? 'red' : priority === 'High' ? 'amber' : 'grey')),
        h('td.num', null, line.shipment),
        h('td.wide', null, line.customer),
        h('td', null, issue),
        h('td.right.num', { class: line.overdue ? 'crit' : '' }, `${line.aging} d`),
        h('td', { style: 'color:var(--ink-2)' }, action)))
          : [h('tr', null, h('td', { colspan: 6 }, h('div.empty', null,
            h('strong', null, 'Nothing waiting'),
            'Every line in this filter has both agent details and a CRO.')))]))));
}

function agingCard() {
  const matrix = agingMatrix();
  return h('div.card', null,
    h('div.card-head', null,
      h('h2', null, 'Aging of open lines'),
      h('span.card-hint', null, 'how long each region has been waiting for evidence')),
    h('div.card-body', null,
      matrix.map((row) => h('div.aging-row', null,
        h('span', { style: 'font-size:12px; font-weight:500' }, row.name),
        agingStack(row, () => setState({ view: 'monitor', region: row.name.slice(0, 2), quick: 'CRO Pending', page: 1 })))),
      agingLegend(agingBuckets().map(([label, , , fill]) => ({ label, fill })))));
}

export function dashboardView() {
  return h('div', { style: 'display:flex; flex-direction:column; gap:18px' },
    kpiRow(),
    isLive() ? valueRow() : null,
    h('div.grid-2', null, regionCards(), trendCard()),
    h('div.grid-split', null, agentPendingCard(), actionCard()),
    agingCard());
}
