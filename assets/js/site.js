'use strict';

const menuButton = document.querySelector('.menu-toggle');
const nav = document.querySelector('#main-nav');
const submenuButton = document.querySelector('.submenu-toggle');
const submenu = document.querySelector('#service-menu');
const mobile = window.matchMedia('(max-width: 900px)');

function closeSubmenu() {
  submenuButton.setAttribute('aria-expanded', 'false');
  submenu.hidden = true;
}

function closeMenu(returnFocus = false) {
  menuButton.setAttribute('aria-expanded', 'false');
  if (mobile.matches) nav.hidden = true;
  closeSubmenu();
  if (returnFocus) menuButton.focus();
}

function setLayout() {
  const focusWasInNav = nav.contains(document.activeElement);
  closeMenu();
  nav.hidden = mobile.matches;
  if (mobile.matches && focusWasInNav) menuButton.focus();
}

document.documentElement.classList.add('js');
setLayout();
mobile.addEventListener('change', setLayout);
menuButton.addEventListener('click', () => {
  const opening = menuButton.getAttribute('aria-expanded') !== 'true';
  menuButton.setAttribute('aria-expanded', String(opening));
  nav.hidden = !opening;
  if (opening) nav.querySelector('a').focus();
  else closeSubmenu();
});
submenuButton.addEventListener('click', () => {
  const opening = submenuButton.getAttribute('aria-expanded') !== 'true';
  submenuButton.setAttribute('aria-expanded', String(opening));
  submenu.hidden = !opening;
});
document.addEventListener('keydown', (event) => {
  if (event.key !== 'Escape') return;
  if (!submenu.hidden) {
    closeSubmenu();
    submenuButton.focus();
  } else if (mobile.matches && !nav.hidden) closeMenu(true);
});
document.addEventListener('click', (event) => {
  if (!event.target.closest('.services-nav')) closeSubmenu();
  if (mobile.matches && !event.target.closest('.site-header')) closeMenu();
});
document.addEventListener('focusin', (event) => {
  if (!event.target.closest('.services-nav')) closeSubmenu();
  if (mobile.matches && !event.target.closest('.site-header')) closeMenu();
});

// Phase 1 only: select the relevant draft service. No network or storage.
const serviceSelect = document.querySelector('#service');
if (serviceSelect) {
  const service = new URLSearchParams(window.location.search).get('service');
  if ([...serviceSelect.options].some(option => option.value === service)) serviceSelect.value = service;
}
