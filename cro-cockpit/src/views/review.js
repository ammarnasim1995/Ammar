import { h, badge, toast } from '../dom.js';
import { confirmMatch, getDb, openEmail, rejectMatch, reviewLines, state } from '../store.js';

const ALL_REFS = ['Shipment ID', 'Container', 'Booking', 'Sales Order'];

export function reviewView() {
  const lines = reviewLines();
  if (!lines.length) {
    return h('div.card', null, h('div.empty', null,
      h('strong', null, 'Review queue is clear'),
      `Every match sits at or above the ${state.settings.reviewThreshold}% confidence threshold.`));
  }

  const db = getDb();
  return h('div.grid-2', null, lines.map((l) => {
    const email = db.byEmail[l.emailId];
    const decision = state.decisions[l.id];
    return h('div.card.review-card', null,
      h('div.review-top', null,
        h('span.num', { style: 'font-weight:600; font-size:13px' }, l.shipment),
        badge(`Confidence ${l.confidence}%`, l.confidence < 60 ? 'red' : 'amber')),
      h('div.review-ctx', null,
        `${l.customer} · ${l.region} · ${l.salesOrder} · item ${l.lineItem} · ${l.matchMethod}`),
      h('div.review-email', null,
        h('span', { style: 'font-size:12px; font-weight:600' }, email.subject),
        h('span.num', { style: 'font-size:11px; color:var(--ink-2)' },
          [email.received, email.sender, email.attachment].filter(Boolean).join(' · '))),
      h('div.review-fields', null,
        h('div.col', null,
          h('div.label', { style: 'color:var(--good)' }, 'Matched'),
          email.matchedFields.length
            ? email.matchedFields.map((m) => h('div.matched', null, m))
            : h('div', { style: 'color:var(--ink-3)' }, 'nothing')),
        h('div.col', null,
          h('div.label', { style: 'color:var(--crit)' }, 'Not matched'),
          ALL_REFS.filter((x) => !email.matchedFields.includes(x)).map((m) => h('div.unmatched', null, m)))),
      h('div.review-actions', null,
        h('button.btn.btn-primary', {
          onclick: () => { confirmMatch(l.id); toast(`${l.shipment} confirmed — line advanced`); },
        }, 'Confirm match'),
        h('button.btn.btn-reject', {
          onclick: () => { rejectMatch(l.id); toast(`${l.shipment} rejected — email sent to exceptions`); },
        }, 'Reject'),
        h('button.link', { onclick: () => openEmail(email.id) }, 'View email →'),
        decision ? badge(decision, decision === 'Confirmed' ? 'green' : 'red') : null));
  }));
}
