/**
 * This file requires materialize.js.
 */

/**
 * Establishes the sidebar functionality for smaller devices.
 */
document.addEventListener('DOMContentLoaded', () => {
  var elems = document.querySelectorAll('.sidenav')
  var instances = M.Sidenav.init(elems, {})
});

