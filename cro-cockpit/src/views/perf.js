import { h, badge } from '../dom.js';
import { agingLegend, agingStack, meter } from '../charts.js';
import { pct } from '../rules.js';
import { agentStats, agingBuckets, agingMatrix, isLive, regionStats, setState, state } from '../store.js';

export function agentPerfView() {
  const rows = agentStats();
  if (!rows.length) {
    return h('div.card', null, h('div.empty', null,
      h('strong', null, 'No forwarders in this filter'),
      'Widen the region or quick filter to compare agents.'));
  }

  return h('div.card', null,
    h('div.card-head', null,
      h('h2', null, isLive() ? 'Owner (AAM) performance' : 'Agent / forwarder performance'),
      h('span.card-hint', null, isLive()
        ? 'ranked by CRO pending, then aging · the trackers carry no forwarder, so lines are ranked by their area account manager'
        : 'ranked by CRO pending, then aging · reflects the active filters')),
    h('div.table-wrap', null,
      h('table', null,
        h('thead', null, h('tr', null,
          h('th', null, isLive() ? 'Owner (AAM)' : 'Agent'), h('th', null, 'Source'), h('th.right', null, 'Total'),
          h('th.right', null, 'Agent details'), h('th.right', null, 'CRO received'),
          h('th.right', null, 'CRO pending'), h('th.right', null, 'Ready'),
          h('th.right', null, 'Avg aging'), h('th.right', null, 'Overdue'), h('th', null, 'Rating'))),
        h('tbody', null, rows.map((a) => {
          const rate = a.croRecv / a.total;
          const rating = rate > 0.72 ? 'On track' : rate > 0.6 ? 'Watch' : 'Escalate';
          return h('tr', null,
            h('td', null, a.agent),
            h('td', null, badge(a.region, 'grey')),
            h('td.right.num', null, String(a.total)),
            h('td.right.num', null, pct(a.agentRecv, a.total)),
            h('td.right.num', null, pct(a.croRecv, a.total)),
            h('td.right.num.warn', null, String(a.pending)),
            h('td.right.num', null, pct(a.ready, a.total)),
            h('td.right.num', null, `${a.avgAging} d`),
            h('td.right.num', { class: a.critical > 12 ? 'crit' : '' }, String(a.critical)),
            h('td', null, badge(rating, rating === 'On track' ? 'green' : rating === 'Watch' ? 'amber' : 'red')));
        })))),
    h('div.card-foot', null, `Overdue counts lines waiting more than ${state.settings.criticalDays} days.`));
}

function regionCard(s) {
  const metrics = [
    ['Agent details received', s.agentPct, s.share((l) => l.agentStatus === 'Received'), 'var(--good)'],
    ['CRO received', s.croPct, s.share((l) => /CRO Received|CRO Released/.test(l.croStatus)), 'var(--good)'],
    ['CRO pending', s.croPendPct, s.share((l) => /CRO Pending|CRO Not Found/.test(l.croStatus)), 'var(--warn)'],
    ['Ready for release', s.readyPct, s.share((l) => /READY|RELEASED/.test(l.overall)), 'var(--accent)'],
    ['Overdue', String(s.overdue), s.share((l) => l.overdue), 'var(--crit)'],
  ];

  const pendingByCustomer = {};
  s.ls.filter((l) => /CRO Pending|CRO Not Found/.test(l.croStatus))
    .forEach((l) => { pendingByCustomer[l.customer] = (pendingByCustomer[l.customer] || 0) + 1; });
  const top = Object.entries(pendingByCustomer).sort((a, b) => b[1] - a[1]).slice(0, 3);

  return h('div.card', { style: 'padding:15px 16px; display:flex; flex-direction:column; gap:12px' },
    h('div', { style: 'display:flex; align-items:baseline; justify-content:space-between; gap:10px' },
      h('span.trunc', { style: 'font-size:14px; font-weight:600' }, s.name),
      h('span.num', { style: 'font-size:11.5px; color:var(--ink-2)' }, `${s.lines} lines`)),
    metrics.map(([label, value, share, color]) => h('div.metric', null,
      h('div.metric-top', null, h('span', null, label), h('span.num', null, value)),
      meter(share, color))),
    h('div', { style: 'border-top:1px solid var(--line-2); padding-top:10px; display:flex; flex-direction:column; gap:5px' },
      h('div.label', null, 'Top pending customers'),
      top.length ? top.map(([name, lines]) => h('div', { style: 'display:flex; justify-content:space-between; gap:8px; font-size:11.5px' },
        h('span.trunc', null, name),
        h('span.num', { style: 'color:var(--warn)' }, String(lines))))
        : h('span', { style: 'font-size:11.5px; color:var(--ink-3)' }, 'none pending')),
    h('button.btn', {
      style: 'justify-content:center',
      onclick: () => setState({ view: 'monitor', region: s.code, page: 1 }),
    }, 'Drill into monitor'));
}

export function regionPerfView() {
  const matrix = agingMatrix();
  return h('div', { style: 'display:flex; flex-direction:column; gap:16px' },
    h('div.grid-3', null, regionStats().map(regionCard)),
    h('div.card', null,
      h('div.card-head', null,
        h('h2', null, 'Aging distribution by region'),
        h('span.card-hint', null, 'lines still waiting for agent details or a CRO')),
      h('div.card-body', null,
        matrix.map((row) => h('div.aging-row', null,
          h('span', { style: 'font-size:12px; font-weight:500' }, `${row.name} (${row.total})`),
          agingStack(row, () => setState({ view: 'monitor', region: row.name.slice(0, 2), quick: 'CRO Pending', page: 1 })))),
        agingLegend(agingBuckets().map(([label, , , fill]) => ({ label, fill }))))));
}
