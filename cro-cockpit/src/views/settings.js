import { h, toast } from '../dom.js';
import { SETTINGS_BOUNDS } from '../rules.js';
import { resetSettings, setSetting, state } from '../store.js';

function slider(key, name, help, unit) {
  const [min, max] = SETTINGS_BOUNDS[key];
  const value = state.settings[key];
  return h('div.setting', null,
    h('div.setting-top', null,
      h('span.setting-name', null, name),
      h('span.num', { style: 'font-weight:600' }, `${value}${unit}`)),
    h('input', {
      type: 'range', min, max, value, 'aria-label': name,
      oninput: (e) => setSetting(key, e.target.value),
    }),
    h('div.setting-help', null, help));
}

function segmented(name, help, options, current, onPick) {
  return h('div.setting', null,
    h('div.setting-top', null, h('span.setting-name', null, name)),
    h('div.seg', null, options.map(([value, label]) => h('button.btn', {
      'aria-pressed': String(value === current),
      onclick: () => onPick(value),
    }, label))),
    h('div.setting-help', null, help));
}

export function settingsView() {
  return h('div.settings', null,
    h('div.card', null,
      h('div.card-head', null, h('h2', null, 'Business rules'),
        h('span.card-hint', null, 'applied to every view immediately')),
      h('div.card-body', null,
        slider('criticalDays', 'Overdue after', 'A pending line becomes overdue — and its agent counts a critical — once it has waited this long.', ' days'),
        slider('warningDays', 'Warn after', 'Used for early-warning shading before a line is formally overdue.', ' days'),
        slider('reviewThreshold', 'Review threshold', 'Matches below this confidence go to the review queue instead of updating a line silently.', '%'),
        slider('autoConfirm', 'Auto-confirm at', 'At or above this confidence the parser accepts a match without a human.', '%'))),
    h('div.card', null,
      h('div.card-head', null, h('h2', null, 'Mailbox'),
        h('span.card-hint', null, 'logistics@midassafety.com')),
      h('div.card-body', null,
        slider('autoCheckSeconds', 'Auto-check interval', 'How often the cockpit polls the mailbox while auto-check is on.', ' s'),
        slider('pageSize', 'Rows per page', 'Table page size in the shipment monitor and its filtered views.', ' rows'))),
    h('div.card', null,
      h('div.card-head', null, h('h2', null, 'Appearance')),
      h('div.card-body', null,
        segmented('Theme', 'System follows the device setting.',
          [['system', 'System'], ['light', 'Light'], ['dark', 'Dark']],
          state.settings.theme, (v) => setSetting('theme', v)))),
    h('div', null,
      h('button.btn', {
        onclick: () => { resetSettings(); toast('Settings restored to defaults'); },
      }, 'Restore defaults')));
}
