/**
 * Shell: navigation rail, topbar, filter row, and the router that picks a view.
 * Everything renders from `state`; nothing here holds state of its own.
 */

import { download, h, mount, toast } from './dom.js';
import { REGIONS } from './rules.js';
import {
  QUICK_LABELS, VIEWS, applyTheme, availableViews, checkMailbox, closeDrawer, exceptionEmails,
  exportCsv, filteredLines, getDb, initData, isLive, kpiSet, openEmail, readHash, render,
  reviewLines, setState, state, subscribe, toggleAuto,
} from './store.js';
import { dashboardView } from './views/dashboard.js';
import { tableView } from './views/table.js';
import { emailsView } from './views/emails.js';
import { reviewView } from './views/review.js';
import { exceptionsView } from './views/exceptions.js';
import { agentPerfView, regionPerfView } from './views/perf.js';
import { settingsView } from './views/settings.js';
import { drawerView } from './views/drawer.js';

const NAV = [
  ['dashboard', 'Dashboard'],
  ['monitor', 'Shipment monitor'],
  ['cro', 'CRO pending'],
  ['agent', 'Agent details'],
  ['review', 'Match review'],
  ['exceptions', 'Exceptions'],
  ['emails', 'Emails'],
  ['agentperf', 'Owner performance'],
  ['regionperf', 'Region performance'],
  ['settings', 'Settings'],
];

function navCounts() {
  const k = kpiSet();
  return {
    monitor: k.n,
    cro: k.croPend,
    agent: k.agentPend,
    review: reviewLines().length,
    exceptions: exceptionEmails().length,
    emails: getDb().emails.length,
  };
}

function rail() {
  const counts = navCounts();
  const allowed = new Set(availableViews());
  return h('nav.rail', { 'aria-label': 'Views' },
    h('div.rail-head', null,
      h('div.rail-org', null, 'Midas Safety · SCM'),
      h('div.rail-title', null, 'CRO & Agent Details', h('br'), 'Approval Cockpit')),
    h('div.rail-nav', null, NAV.filter(([id]) => allowed.has(id)).map(([id, label]) => h('button.rail-item', {
      'aria-current': state.view === id ? 'page' : null,
      onclick: () => setState({ view: id, page: 1 }),
    }, h('span', null, label), h('span.rail-count.num', null, counts[id] != null ? String(counts[id]) : '')))),
    h('div.rail-foot', null,
      h('div.label', null, 'Data sources'),
      h('div.rail-sources.num', null,
        isLive()
          ? getDb().sources.map((s) => h('span', null, `${s.region} · ${s.rows.toLocaleString()} lines`))
          : [
            h('span', null, 'PK · Shipment Tracker'),
            h('span', null, 'BD · Shipment Tracker'),
            h('span', null, 'SL · Shipment Tracker'),
          ],
        h('span', null, isLive() ? `extract ${getDb().asOf}` : 'logistics@midassafety.com'))));
}

function topbar() {
  const [title, rawSubtitle] = VIEWS[state.view];
  const subtitle = isLive() && state.view === 'dashboard'
    ? `Reconciled across the PK, BD and SL shipment trackers · extract ${getDb().asOf}`
    : rawSubtitle;
  return h('header.topbar', null,
    h('div.topbar-titles', null, h('h1', null, title), h('span.topbar-sub', null, subtitle)),
    h('div.search', null,
      h('input', {
        type: 'search',
        value: state.q,
        'data-focus-key': 'search',
        'aria-label': 'Search shipments, orders, customers, containers, CRO numbers, agents and email subjects',
        placeholder: isLive()
          ? 'Search sales order, customer, destination, owner, plant…'
          : 'Search shipment, order, customer, container, CRO, agent, email subject…',
        oninput: (e) => setState({ q: e.target.value, page: 1 }),
      }),
      h('kbd', null, '/')),
    isLive()
      ? h('div.topbar-right', null,
        h('div.sync-stamp', null,
          h('span.label', null, 'Tracker extract'),
          h('span.val.num', null, getDb().asOf)),
        h('span.badge.badge-green', null, 'LIVE DATA'))
      : h('div.topbar-right', null,
        h('div.sync-stamp', null,
          h('span.label', null, 'Last sync'),
          h('span.val.num', null, state.lastSync)),
        h('button.btn', {
          'aria-pressed': String(state.auto),
          onclick: toggleAuto,
        }, h('span', { class: `dot${state.auto ? ' on' : ''}` }),
        state.auto ? `Auto-check on · every ${state.settings.autoCheckSeconds}s` : 'Auto-check off'),
        h('button.btn.btn-primary', {
          onclick: checkMailbox,
          disabled: state.syncing,
        }, state.syncing ? 'Checking mailbox…' : 'Check mailbox')));
}

function syncBanner() {
  const summary = state.syncSummary;
  if (!summary) return null;

  if (summary.empty) {
    return h('div.synclog', { role: 'status' },
      h('div.synclog-head', null,
        h('strong', null, 'Mailbox empty'),
        h('span.synclog-sum', null, 'Every unread logistics email in this demo mailbox has been parsed.'),
        h('button.btn.btn-ghost', {
          style: 'margin-left:auto',
          onclick: () => setState({ syncSummary: null, syncLog: [] }),
        }, 'Dismiss')));
  }

  return h('div.synclog', { role: 'status', 'aria-live': 'polite' },
    h('div.synclog-head', null,
      h('strong', null, 'Mailbox check complete'),
      h('span.synclog-sum.num', null,
        `${summary.parsed} new email(s) parsed · ${summary.updated} line(s) advanced · `
        + `${summary.review} to review · ${summary.errors} unparsed`
        + (summary.remaining != null ? ` · ${summary.remaining} unread left` : '')),
      h('button.btn.btn-ghost', {
        style: 'margin-left:auto',
        onclick: () => setState({ syncSummary: null, syncLog: [] }),
      }, 'Dismiss')),
    state.syncLog.length
      ? h('div.synclog-rows', null, state.syncLog.map((x) => h('button.synclog-row', {
        onclick: () => openEmail(x.emailId),
      },
      h('span.badge', { class: x.kind === 'CRO' ? 'badge-blue' : 'badge-grey' }, x.kind),
      h('span.shp.num', null, x.shipment),
      h('span', { class: `tone-${x.tone}` }, x.note))))
      : null);
}

function filters() {
  const chip = (label, active, onclick, ariaLabel) => h('button.chip', {
    'aria-pressed': String(active), 'aria-label': ariaLabel || label, onclick,
  }, label);

  const db = getDb();
  const shown = filteredLines().length;
  const unparsed = db.emails.filter((e) => e.unmatched).length;

  return h('div.filters', null,
    h('span.label', null, 'Region'),
    ['All', 'PK', 'BD', 'SL'].map((code) => chip(
      code === 'All' ? 'All regions' : `${code} · ${REGIONS[code]}`,
      state.region === code,
      () => setState({ region: code, page: 1 }),
    )),
    h('span.divider'),
    h('span.label', null, 'Quick'),
    Object.keys(QUICK_LABELS).map((key) => chip(
      QUICK_LABELS[key], state.quick === key, () => setState({ quick: key, page: 1 }),
    )),
    h('div.filters-right', null,
      h('span.filter-count.num', null,
        isLive()
          ? `${shown.toLocaleString()} of ${db.lines.length.toLocaleString()} lines · extract ${db.asOf}`
          : `${shown.toLocaleString()} of ${db.lines.length.toLocaleString()} lines · `
            + `${db.emails.length} emails parsed · ${unparsed} unparsed`),
      h('button.btn', {
        onclick: () => {
          const { csv, count } = exportCsv();
          download(`cro_cockpit_${state.view}_${state.region}.csv`, csv);
          toast(`${count.toLocaleString()} lines exported`);
        },
      }, 'Export CSV')));
}

function currentView() {
  switch (state.view) {
    case 'monitor': case 'cro': case 'agent': return tableView(VIEWS[state.view][0]);
    case 'emails': return emailsView();
    case 'review': return reviewView();
    case 'exceptions': return exceptionsView();
    case 'agentperf': return agentPerfView();
    case 'regionperf': return regionPerfView();
    case 'settings': return settingsView();
    default: return dashboardView();
  }
}

function shell() {
  return h('div.app', null,
    rail(),
    h('div.main', null,
      topbar(),
      syncBanner(),
      state.view === 'settings' ? null : filters(),
      h('main.content', { id: 'content' }, currentView())),
    drawerView());
}

function keyboard(e) {
  if (e.key === 'Escape') {
    if (state.drawer) closeDrawer();
    else if (state.q) setState({ q: '', page: 1 });
    return;
  }
  const typing = /^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement?.tagName || '');
  if (e.key === '/' && !typing) {
    e.preventDefault();
    document.querySelector('[data-focus-key="search"]')?.focus();
  }
}

export async function start(root) {
  readHash();
  applyTheme();
  subscribe(() => mount(root, shell()));
  window.addEventListener('hashchange', () => { readHash(); render(); });
  window.addEventListener('keydown', keyboard);
  render();
  if (await initData()) render();
}
