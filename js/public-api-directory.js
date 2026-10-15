(function () {
  "use strict";
  function init() {
    var input = document.getElementById("pub-search");
    var status = document.getElementById("pub-result-status");
    var empty = document.getElementById("pub-no-results");
    var buttons = Array.from(document.querySelectorAll(".pub-filters [data-filter]"));
    var cards = Array.from(document.querySelectorAll("#pub-grid .pub-card"));
    if (!input || !status || !empty || !cards.length) return;
    var active = "all";
    function update() {
      var query = input.value.trim().toLocaleLowerCase();
      var count = 0;
      cards.forEach(function (card) {
        var typeMatches = active === "all" || card.dataset.kind === active;
        var textMatches = !query || (card.dataset.search || "").includes(query);
        var visible = typeMatches && textMatches;
        card.hidden = !visible;
        if (visible) count += 1;
      });
      empty.hidden = count !== 0;
      status.textContent = "当前展示 " + count + " / " + cards.length + " 个入口；未进行实时可用性探测。";
      buttons.forEach(function (button) {
        var selected = button.dataset.filter === active;
        button.classList.toggle("is-active", selected);
        button.setAttribute("aria-pressed", String(selected));
      });
    }
    input.addEventListener("input", update);
    buttons.forEach(function (button) {
      button.addEventListener("click", function () {
        active = button.dataset.filter;
        update();
      });
    });
    update();
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
