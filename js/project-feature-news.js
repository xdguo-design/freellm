/* P1-N1: downgrade the homepage feature after its configured display period.
   The external reading link stays available after the spotlight expires. */
(() => {
  'use strict';
  const feature = document.getElementById('project-feature-news');
  if (!feature) return;

  const cutoff = Date.parse(feature.getAttribute('data-spotlight-until') || '');
  // Fail closed: an invalid date must never cause permanent "HOT" promotion.
  if (Number.isFinite(cutoff) && Date.now() < cutoff) return;

  feature.classList.add('fl-project-news--archive');
  const status = feature.querySelector('.fl-project-news-status');
  if (status) status.textContent = '项目关联阅读';
})();
