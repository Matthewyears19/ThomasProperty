import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';

test('gallery progressively enhances filtering and restores every card with All projects', () => {
  const buttons = ['all', 'painting', 'cleaning'].map(filter => ({dataset: {filter}, attrs: {}, setAttribute(key, value) {this.attrs[key] = value;}}));
  const cards = ['painting', 'painting', 'cleaning'].map(category => ({dataset: {category}, hidden: false}));
  const count = {textContent: ''};
  const filters = {hidden: true, addEventListener(_name, fn) {this.click = fn;}, contains(button) {return buttons.includes(button);}, querySelectorAll() {return buttons;}};
  const document = {querySelector(selector) {return selector === '.project-filters' ? filters : count;}, querySelectorAll() {return cards;}};
  vm.runInNewContext(readFileSync(new URL('../assets/js/gallery.js', import.meta.url), 'utf8'), {document});
  assert.equal(filters.hidden, false);
  filters.click({target: {closest() {return buttons[2];}}});
  assert.deepEqual(cards.map(card => card.hidden), [true, true, false]);
  assert.equal(count.textContent, '1 project shown');
  assert.equal(buttons[2].attrs['aria-pressed'], 'true');
  filters.click({target: {closest() {return buttons[0];}}});
  assert.equal(cards.every(card => !card.hidden), true);
  assert.equal(count.textContent, '3 projects shown');
});

test('gallery script does nothing on a page without a filter', () => {
  vm.runInNewContext(readFileSync(new URL('../assets/js/gallery.js', import.meta.url), 'utf8'), {document: {querySelector() {return null;}}});
});
