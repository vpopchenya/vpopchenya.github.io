(function () {
  "use strict";

  // Tell the CSS that this script is running, so it can switch off the reveal safety net.
  document.documentElement.classList.add("reveal-ready");

  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Background drifts slower than the page while scrolling.
  var bgItems = document.querySelectorAll(".bg-item");
  if (!reduce && bgItems.length) {
    var ticking = false;
    var shift = function () {
      var y = window.scrollY;
      bgItems.forEach(function (el) {
        el.style.setProperty("--y", (-y * parseFloat(el.dataset.speed)).toFixed(1) + "px");
      });
      ticking = false;
    };
    window.addEventListener("scroll", function () {
      if (!ticking) { ticking = true; requestAnimationFrame(shift); }
    }, { passive: true });
    shift();
  }

  // Cards: the colored light follows the pointer.
  document.querySelectorAll(".card").forEach(function (card) {
    card.addEventListener("pointermove", function (e) {
      var r = card.getBoundingClientRect();
      card.style.setProperty("--mx", (e.clientX - r.left) + "px");
      card.style.setProperty("--my", (e.clientY - r.top) + "px");
    });
  });

  // Sections reveal once when scrolled into view.
  var items = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window && !reduce) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); }
      });
    }, { threshold: 0, rootMargin: "0px 0px -12% 0px" }); // works for sections of any height
    items.forEach(function (el) { io.observe(el); });
  } else {
    items.forEach(function (el) { el.classList.add("in"); });
  }
})();
