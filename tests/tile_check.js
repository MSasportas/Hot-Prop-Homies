/* Runs in the page. Returns one entry per problem found on the rendered view: any ellipsis, clipped or sideways-scrolling text,
   a line cut by an overflow:hidden ancestor, a word split across two lines (a break after a hyphen between two letters is allowed; a record like 2-3 or a number like 1-800 is not), or the page scrolling sideways. */
() => {
  const out = [];
  const root = document.documentElement;
  const SLACK = 1;
  const label = (el) => el.tagName.toLowerCase() + (typeof el.className === 'string' && el.className.trim() ? '.' + el.className.trim().split(/\s+/).join('.') : '');
  const where = (el) => [el, el.parentElement, el.parentElement && el.parentElement.parentElement].filter(Boolean).map(label).join(' < ');
  const clipsX = (cs) => cs.overflowX !== 'visible';
  const clipsY = (cs) => cs.overflowY !== 'visible';
  const scrolls = (v) => v === 'auto' || v === 'scroll';
  const add = (kind, el, detail) => out.push({ kind: kind, where: where(el), text: (el.textContent || '').trim().slice(0, 40), detail: detail || '' });

  if (root.scrollWidth > root.clientWidth) out.push({ kind: 'page-scrolls-sideways', where: 'html', text: '', detail: root.scrollWidth + '>' + root.clientWidth });

  for (const el of document.querySelectorAll('#app *, #tabs *')) {
    if (el.closest('.sr, [hidden]')) continue;
    const cs = getComputedStyle(el), box = el.getBoundingClientRect();
    if (cs.display === 'none' || cs.visibility === 'hidden' || (!box.width && !box.height)) continue;
    const own = Array.from(el.childNodes).filter((n) => n.nodeType === 3).map((n) => n.textContent).join('');
    const text = (el.textContent || '').trim();

    if (cs.textOverflow === 'ellipsis') add('text-overflow-ellipsis', el);
    if (own.indexOf('…') >= 0) add('ellipsis-character', el);
    if (cs.webkitLineClamp !== 'none' && cs.webkitLineClamp) add('line-clamp', el);

    if (clipsX(cs) && !scrolls(cs.overflowX) && el.scrollWidth > el.clientWidth + SLACK) add('clipped-sideways', el, el.scrollWidth + '>' + el.clientWidth);
    if (clipsY(cs) && !scrolls(cs.overflowY) && el.scrollHeight > el.clientHeight + SLACK) add('clipped-below', el, el.scrollHeight + '>' + el.clientHeight);
    if (scrolls(cs.overflowX) && el.scrollWidth > el.clientWidth + SLACK) add('scrolls-sideways', el, el.scrollWidth + '>' + el.clientWidth);
    if (!el.children.length && text && box.right > root.clientWidth + SLACK) add('text-past-the-screen-edge', el);

    if (!el.children.length && text) {
      const range = document.createRange();
      range.selectNodeContents(el);
      const rect = range.getBoundingClientRect();
      for (let a = el.parentElement; a && a.id !== 'app'; a = a.parentElement) {
        const ac = getComputedStyle(a), ar = a.getBoundingClientRect();
        if (clipsX(ac) && !scrolls(ac.overflowX) && (rect.right > ar.right + SLACK || rect.left < ar.left - SLACK)) { add('text-cut-by-parent-sideways', el, label(a)); break; }
        if (clipsY(ac) && !scrolls(ac.overflowY) && ar.height > 0 && (rect.bottom > ar.bottom + SLACK || rect.top < ar.top - SLACK)) { add('text-cut-by-parent-below', el, label(a)); break; }
      }
    }
  }

  const walker = document.createTreeWalker(document.getElementById('app'), NodeFilter.SHOW_TEXT);
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    const el = n.parentElement;
    if (!el || el.closest('.sr, [hidden]')) continue;
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') continue;
    const re = /\S{3,}/g;
    for (let m = re.exec(n.textContent); m; m = re.exec(n.textContent)) {
      let split = false;
      for (let i = 1; i < m[0].length && !split; i++) {
        const before = document.createRange(), after = document.createRange();
        before.setStart(n, m.index + i - 1); before.setEnd(n, m.index + i);
        after.setStart(n, m.index + i); after.setEnd(n, m.index + i + 1);
        const a = before.getClientRects()[0], b = after.getClientRects()[0];
        const hyphenBetweenLetters = m[0][i - 1] === '-' && /[A-Za-z]/.test(m[0][i - 2] || '') && /[A-Za-z]/.test(m[0][i]);
        split = !!(a && b && Math.abs(a.top - b.top) > a.height / 2 && !hyphenBetweenLetters);
      }
      if (split) out.push({ kind: 'word-split-across-lines', where: where(el), text: m[0], detail: '' });
    }
  }
  return out;
}
