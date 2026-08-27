import { h, badge, toast } from '../dom.js';
import { exceptionEmails, filteredLines, getDb, linkEmail, openEmail } from '../store.js';

/**
 * Emails the parser could not tie to any shipment line. A planner links one by
 * hand: pick the shipment, and the line advances exactly as an auto-match would.
 */
export function exceptionsView() {
  const emails = exceptionEmails();
  if (!emails.length) {
    return h('div.card', null, h('div.empty', null,
      h('strong', null, 'No exceptions'),
      'Every parsed email in this region found a shipment line. Run a mailbox check to see how unparsed mail lands here.'));
  }

  const db = getDb();
  const candidates = filteredLines().slice(0, 300);

  return h('div', { style: 'display:flex; flex-direction:column; gap:12px' },
    emails.map((e) => {
      const select = h('select', { 'aria-label': `Shipment line for ${e.subject}` },
        h('option', { value: '' }, 'Select a shipment line…'),
        candidates.map((l) => h('option', { value: l.id },
          `${l.shipment} · item ${l.lineItem} · ${l.customer.slice(0, 34)}`)));

      return h('div.card', { style: 'padding:15px 16px; display:flex; flex-direction:column; gap:11px' },
        h('div.review-top', null,
          h('span', { style: 'font-weight:600; font-size:12.5px' }, e.subject),
          badge('Unmatched', 'red')),
        h('div.review-ctx.num', null, [e.received, e.sender, e.folder, e.attachment].filter(Boolean).join(' · ')),
        h('div.review-email', null,
          h('span', { style: 'font-size:11.5px; color:var(--ink-2)' }, e.matchMethod),
          h('span', { style: 'font-size:11.5px' }, `Sender's forwarder: ${e.sender.split('@')[0].replace(/\./g, ' ')}`)),
        h('div.linker', null,
          select,
          h('button.btn.btn-primary', {
            onclick: () => {
              if (!select.value) { toast('Pick a shipment line first'); return; }
              const shipment = db.byLine[select.value].shipment;
              linkEmail(e.id, select.value);
              toast(`${e.id} linked to ${shipment}`);
            },
          }, 'Link to line'),
          h('button.link', { style: 'margin-left:auto', onclick: () => openEmail(e.id) }, 'View email →')));
    }));
}
