/**
 * A 60-line DOM layer. The cockpit re-renders the whole shell on every state
 * change — at this data volume that is cheaper than a diffing library, and it
 * keeps every view a pure function of state. Focus, caret and scroll are
 * carried across renders so typing in the search box survives a repaint.
 */

/** h('div.card', { onClick }, child, child) — tag supports .class and #id. */
export function h(spec, props, ...children) {
  const [tag, ...classes] = String(spec).split('.');
  const el = document.createElement(tag || 'div');
  if (classes.length) el.className = classes.join(' ');

  for (const [k, v] of Object.entries(props || {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k === 'class') el.className = `${el.className} ${v}`.trim();
    else if (k === 'style' && typeof v === 'object') Object.assign(el.style, v);
    else if (k === 'html') el.innerHTML = v;
    else if (k.startsWith('on')) el.addEventListener(k.slice(2).toLowerCase(), v);
    else if (k === 'value') el.value = v;
    else if (v === true) el.setAttribute(k, '');
    else el.setAttribute(k, v);
  }

  append(el, children);
  return el;
}

function append(el, children) {
  for (const c of children.flat(4)) {
    if (c === null || c === undefined || c === false) continue;
    el.appendChild(c instanceof Node ? c : document.createTextNode(String(c)));
  }
  return el;
}

/** Namespaced sibling of h() for chart marks. */
export function svg(spec, props, ...children) {
  const [tag, ...classes] = String(spec).split('.');
  const el = document.createElementNS('http://www.w3.org/2000/svg', tag);
  if (classes.length) el.setAttribute('class', classes.join(' '));
  for (const [k, v] of Object.entries(props || {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k.startsWith('on')) el.addEventListener(k.slice(2).toLowerCase(), v);
    else el.setAttribute(k, v);
  }
  return append(el, children);
}

export const text = (s) => document.createTextNode(s);

export function badge(label, tone) {
  return h('span', { class: `badge badge-${tone}` }, label);
}

export function labelled(s) {
  return h('div.label', null, s);
}

/** Replace the contents of root, restoring what the user was interacting with. */
export function mount(root, node) {
  const active = document.activeElement;
  const key = active && active.dataset ? active.dataset.focusKey : null;
  const caret = key && 'selectionStart' in active ? active.selectionStart : null;
  const scroller = root.querySelector('[data-scroll]');
  const scrollTop = scroller ? scroller.scrollTop : 0;

  root.replaceChildren(node);

  if (key) {
    const next = root.querySelector(`[data-focus-key="${key}"]`);
    if (next) {
      next.focus({ preventScroll: true });
      if (caret !== null && 'setSelectionRange' in next) {
        try { next.setSelectionRange(caret, caret); } catch { /* not a text input */ }
      }
    }
  }
  const nextScroller = root.querySelector('[data-scroll]');
  if (nextScroller && scrollTop) nextScroller.scrollTop = scrollTop;
}

let toastTimer = null;

/** One-line confirmation of something that just happened. */
export function toast(message) {
  document.querySelector('.toast')?.remove();
  const el = h('div.toast', { role: 'status', 'aria-live': 'polite' }, message);
  document.body.appendChild(el);
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.remove(), 2600);
}

/** Trigger a client-side file download (CSV export). */
export function download(filename, content, mime = 'text/csv;charset=utf-8') {
  const url = URL.createObjectURL(new Blob([content], { type: mime }));
  const a = h('a', { href: url, download: filename });
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
