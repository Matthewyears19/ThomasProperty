'use strict';

const filters = document.querySelector('.project-filters');
if (filters) {
  const cards = [...document.querySelectorAll('.project-card')];
  const count = document.querySelector('#project-count');
  filters.hidden = false;
  filters.addEventListener('click', event => {
    const button = event.target.closest('button[data-filter]');
    if (!button || !filters.contains(button)) return;
    const category = button.dataset.filter;
    for (const filter of filters.querySelectorAll('button')) filter.setAttribute('aria-pressed', String(filter === button));
    let visible = 0;
    for (const card of cards) {
      card.hidden = category !== 'all' && card.dataset.category !== category;
      if (!card.hidden) visible++;
    }
    count.textContent = `${visible} ${visible === 1 ? 'project' : 'projects'} shown`;
  });
}
