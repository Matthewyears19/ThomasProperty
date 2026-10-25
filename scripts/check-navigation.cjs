// Exercise the shipped script at desktop/mobile breakpoints without dependencies.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
function element() {
  return {
    hidden: false, attrs: {}, events: {},
    setAttribute(k, v) { this.attrs[k] = v; },
    getAttribute(k) { return this.attrs[k]; },
    addEventListener(k, fn) { this.events[k] = fn; },
    focus() { document.activeElement = this; },
    contains(el) { return this === el || (this === nav && [first, subButton].includes(el)); },
    querySelector() { return first; }
  };
}
const menu = element(), nav = element(), subButton = element(), submenu = element(), first = element();
const document = {activeElement: null, events: {}, documentElement: {classList: {add() {}}},
  querySelector(s) { return ({'.menu-toggle': menu, '#main-nav': nav, '.submenu-toggle': subButton, '#service-menu': submenu})[s] || null; },
  addEventListener(k, fn) { this.events[k] = fn; }
};
const media = {matches: false, addEventListener(k, fn) { this.change = fn; }};
vm.runInNewContext(fs.readFileSync('assets/js/site.js', 'utf8'), {document, window: {matchMedia() { return media; }}});
assert.equal(nav.hidden, false);
assert.equal(submenu.hidden, true);
subButton.events.click();
assert.equal(submenu.hidden, false);
document.events.keydown({key: 'Escape'});
assert.equal(submenu.hidden, true);
assert.equal(document.activeElement, subButton);
media.matches = true;
media.change();
assert.equal(nav.hidden, true);
assert.equal(document.activeElement, menu);
menu.events.click();
assert.equal(nav.hidden, false);
assert.equal(menu.attrs['aria-expanded'], 'true');
assert.equal(document.activeElement, first);
document.events.keydown({key: 'Escape'});
assert.equal(nav.hidden, true);
assert.equal(document.activeElement, menu);
menu.events.click();
document.events.click({target: {closest() { return null; }}});
assert.equal(nav.hidden, true);
media.matches = false;
media.change();
assert.equal(nav.hidden, false);
console.log('PASS: desktop submenu, Escape focus, mobile toggle, outside dismissal and breakpoint reset.');
