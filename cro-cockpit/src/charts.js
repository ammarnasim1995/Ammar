/**
 * Charts. Two forms earn their place here:
 *   · the 14-day trend — change over time for two same-unit series, so one
 *     line chart on one axis (never two axes, never a stacked pair of
 *     unrelated measures);
 *   · the aging distribution — parts of a whole per region, so a stacked bar
 *     on an ordinal severity ramp.
 * Both carry a hover layer, a legend, and readable labels, because colour
 * alone is never allowed to be the only encoding.
 */

import { h, svg } from './dom.js';
import { TODAY, addDays, MONTHS } from './rules.js';

const PAD = { top: 12, right: 40, bottom: 20, left: 30 };

function niceMax(v) {
  if (v <= 5) return 5;
  const step = Math.pow(10, Math.floor(Math.log10(v))) / 2;
  return Math.ceil(v / step) * step;
}

const dayLabel = (daysAgo) => {
  const d = addDays(TODAY, -daysAgo);
  return `${String(d.getDate()).padStart(2, '0')} ${MONTHS[d.getMonth()]}`;
};

/**
 * @param {{daysAgo:number, received:number, pending:number}[]} points
 */
export function trendChart(points) {
  const W = 520; const H = 176;
  const max = niceMax(Math.max(1, ...points.map((p) => Math.max(p.received, p.pending))));
  const innerW = W - PAD.left - PAD.right;
  const innerH = H - PAD.top - PAD.bottom;
  const x = (i) => PAD.left + (innerW * i) / (points.length - 1);
  const y = (v) => PAD.top + innerH - (innerH * v) / max;

  const path = (key) => points.map((p, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)},${y(p[key]).toFixed(1)}`).join(' ');
  const area = (key) => `${path(key)} L${x(points.length - 1).toFixed(1)},${y(0)} L${x(0).toFixed(1)},${y(0)} Z`;

  const ticks = [0, max / 2, max];
  const tip = h('div.chart-tip', { role: 'status' });
  const crosshair = svg('line.crosshair', { x1: 0, x2: 0, y1: PAD.top, y2: PAD.top + innerH, opacity: 0 });

  const last = points[points.length - 1];

  const chart = svg('svg.chart', {
    viewBox: `0 0 ${W} ${H}`, preserveAspectRatio: 'none',
    role: 'img', style: 'height:176px',
    'aria-label': `CRO received versus CRO pending over 14 days. Latest: ${last.received} received, ${last.pending} pending.`,
  },
  ticks.map((t) => svg('g', null,
    svg('line.grid-line', { x1: PAD.left, x2: PAD.left + innerW, y1: y(t), y2: y(t) }),
    svg('text.axis-text', { x: PAD.left - 6, y: y(t) + 3, 'text-anchor': 'end' }, String(Math.round(t))))),
  crosshair,
  svg('path', { d: area('received'), fill: 'var(--s-received-fill)' }),
  svg('path', { d: area('pending'), fill: 'var(--s-pending-fill)' }),
  svg('path.series-line', { d: path('received'), stroke: 'var(--s-received)' }),
  svg('path.series-line', { d: path('pending'), stroke: 'var(--s-pending)' }),
  svg('circle.end-dot', { cx: x(points.length - 1), cy: y(last.received), r: 4, fill: 'var(--s-received)' }),
  svg('circle.end-dot', { cx: x(points.length - 1), cy: y(last.pending), r: 4, fill: 'var(--s-pending)' }),
  svg('text.axis-text', {
    x: x(points.length - 1) + 8, y: y(last.received) + 3, fill: 'var(--s-received)', style: 'font-weight:600',
  }, String(last.received)),
  svg('text.axis-text', {
    x: x(points.length - 1) + 8, y: y(last.pending) + 3, fill: 'var(--s-pending)', style: 'font-weight:600',
  }, String(last.pending)),
  points.map((p, i) => (i % 3 === 0 || i === points.length - 1
    ? svg('text.axis-text', { x: x(i), y: H - 5, 'text-anchor': 'middle' }, dayLabel(p.daysAgo).slice(0, 2))
    : null)),
  points.map((p, i) => {
    const band = innerW / (points.length - 1);
    return svg('rect.hit', {
      x: x(i) - band / 2, y: PAD.top, width: band, height: innerH,
      onmouseenter: () => {
        crosshair.setAttribute('x1', x(i));
        crosshair.setAttribute('x2', x(i));
        crosshair.setAttribute('opacity', 1);
        tip.replaceChildren(
          h('div.tip-title', null, dayLabel(p.daysAgo)),
          h('div.tip-row', null, h('span', null, h('i', { style: 'background:var(--s-received)' }), ' CRO received'), h('span.num', null, String(p.received))),
          h('div.tip-row', null, h('span', null, h('i', { style: 'background:var(--s-pending)' }), ' CRO pending'), h('span.num', null, String(p.pending))),
        );
        tip.dataset.show = '1';
        tip.style.left = `${(x(i) / W) * 100}%`;
        tip.style.top = '4px';
        tip.style.transform = i > points.length / 2 ? 'translateX(calc(-100% - 12px))' : 'translateX(12px)';
      },
      onmouseleave: () => { tip.dataset.show = '0'; crosshair.setAttribute('opacity', 0); },
    });
  }));

  return h('div.chart-holder', null, chart, tip,
    h('div.legend', { style: 'margin-top:8px' },
      h('span.key', null, h('i', { style: 'background:var(--s-received)' }), 'CRO received (cumulative)'),
      h('span.key', null, h('i', { style: 'background:var(--s-pending)' }), 'CRO pending (open on the day)')));
}

/**
 * Stacked severity bar. Segments are separated by a 2px surface gap and every
 * segment wide enough carries its count, so the reading never depends on hue.
 */
export function agingStack(row, onBucket) {
  const tip = h('div.chart-tip');
  const bar = h('div.stack', { role: 'img', 'aria-label': `${row.name}: ${row.buckets.map((b) => `${b.count} at ${b.label}`).join(', ')}` },
    row.buckets.filter((b) => b.count > 0).map((b) => h('button', {
      style: `flex: ${b.share} 1 0; background:${b.fill}; color:${b.ink}`,
      title: `${b.label} — ${b.count} lines`,
      onclick: () => onBucket && onBucket(b),
      onmouseenter: (e) => {
        tip.replaceChildren(
          h('div.tip-title', null, `${b.label} · ${row.name}`),
          h('div.tip-row', null, h('span', null, 'Lines waiting'), h('span.num', null, String(b.count))),
          h('div.tip-row', null, h('span', null, 'Share'), h('span.num', null, `${Math.round(b.share)}%`)),
        );
        tip.dataset.show = '1';
        const host = e.currentTarget.closest('.chart-holder').getBoundingClientRect();
        const cell = e.currentTarget.getBoundingClientRect();
        tip.style.left = `${cell.left - host.left + cell.width / 2}px`;
        tip.style.top = '-8px';
        tip.style.transform = 'translate(-50%, -100%)';
      },
      onmouseleave: () => { tip.dataset.show = '0'; },
    }, b.share > 7 ? String(b.count) : '')));

  return h('div.chart-holder', null, bar, tip);
}

export function agingLegend(buckets) {
  return h('div.legend', null, buckets.map((b) => h('span.key', null,
    h('i', { style: `background:${b.fill}` }), b.label)));
}

/**
 * Blocked vs releasable balance by plan month. Same unit on one axis, so the
 * two parts stack honestly into the month's total.
 */
export function monthValueChart(rows, fmtMoney) {
  const max = Math.max(1, ...rows.map((r) => r.blocked + r.ready));
  const tip = h('div.chart-tip');
  const bars = rows.map((r) => {
    const total = r.blocked + r.ready;
    const show = (e) => {
      tip.replaceChildren(
        h('div.tip-title', null, r.month),
        h('div.tip-row', null, h('span', null, h('i', { style: 'background:var(--s-pending)' }), ' Blocked'), h('span.num', null, fmtMoney(r.blocked))),
        h('div.tip-row', null, h('span', null, h('i', { style: 'background:var(--s-received)' }), ' Releasable'), h('span.num', null, fmtMoney(r.ready))),
        h('div.tip-row', null, h('span', null, 'Lines'), h('span.num', null, String(r.lines))),
      );
      tip.dataset.show = '1';
      const host = e.currentTarget.closest('.chart-holder').getBoundingClientRect();
      const cell = e.currentTarget.getBoundingClientRect();
      tip.style.left = `${cell.left - host.left + cell.width / 2}px`;
      tip.style.top = '0px';
      tip.style.transform = 'translate(-50%, -100%)';
    };
    return h('div', {
      style: 'flex:1; max-width:120px; display:flex; flex-direction:column; justify-content:flex-end; gap:3px; height:100%; min-width:0',
      onmouseenter: show,
      onmouseleave: () => { tip.dataset.show = '0'; },
    },
    h('div', { style: `height:${(r.blocked / max) * 100}%; background:var(--s-pending); border-radius:3px 3px 0 0` }),
    h('div', { style: `height:${(r.ready / max) * 100}%; background:var(--s-received); border-radius:0 0 3px 3px` }),
    h('div.axis-label.num', { style: 'font-size:9.5px; color:var(--ink-3); text-align:center; white-space:nowrap; overflow:hidden' }, r.month));
  });

  return h('div.chart-holder', null,
    h('div', { style: 'display:flex; align-items:flex-end; gap:6px; height:168px' }, bars),
    tip,
    h('div.legend', { style: 'margin-top:8px' },
      h('span.key', null, h('i', { style: 'background:var(--s-pending)' }), 'Blocked — agent details or CRO outstanding'),
      h('span.key', null, h('i', { style: 'background:var(--s-received)' }), 'Releasable')));
}

/** Horizontal proportion bar used inside region and KPI cards. */
export function meter(percent, color) {
  return h('div.bar', null, h('i', { style: `width:${Math.max(0, Math.min(100, percent))}%; background:${color}` }));
}
