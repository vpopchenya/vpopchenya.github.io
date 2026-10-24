(function () {
  "use strict";

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
    }, { threshold: 0.15 });
    items.forEach(function (el) { io.observe(el); });
  } else {
    items.forEach(function (el) { el.classList.add("in"); });
  }

  // "Order" buttons in the price cards pre-select the matching plan in the form.
  var form = document.getElementById("order-form");

  // "Other" opens a field to say what exactly is needed; "Not sure" shows a short hint.
  function syncChoice() {
    if (!form) { return; }
    var chosen = form.querySelector('input[name="type"]:checked');
    var isOther = !!(chosen && chosen.hasAttribute("data-other"));
    document.getElementById("other-box").hidden = !isOther;
    form.elements["other"].required = isOther;
    document.getElementById("unsure-hint").hidden = !(chosen && chosen.hasAttribute("data-unsure"));
  }
  if (form) {
    form.addEventListener("change", syncChoice);
    form.addEventListener("reset", function () { setTimeout(syncChoice, 0); });
  }

  document.querySelectorAll("[data-plan]").forEach(function (link) {
    link.addEventListener("click", function () {
      var choice = form && form.elements["type"];
      if (choice) { choice.value = link.dataset.plan; syncChoice(); }
    });
  });

  // Contact form: sent to Web3Forms (https://web3forms.com).
  // The access key goes into data-key on the <form>. It is meant to be public.
  // With no key the form shows a message and sends nothing.
  if (!form) { return; }
  var status = form.querySelector(".form-status");
  var submit = form.querySelector("button[type=submit]");

  function say(kind, text) {
    status.className = "form-status" + (kind ? " " + kind : "");
    status.textContent = text;
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    if (!form.reportValidity()) { return; }
    if (form.elements["botcheck"].checked) { return; } // a bot filled the hidden field

    var key = form.dataset.key;
    if (!key) { say("err", form.dataset.msgNokey); return; }

    var f = form.elements;
    var payload = {
      access_key: key,
      subject: form.dataset.subject,
      from_name: form.dataset.fromName,
      name: f["name"].value.trim(),
      contact: f["contact"].value.trim(),
      type: f["type"].value,
      other: f["other"].value.trim(),
      message: f["message"].value.trim(),
      botcheck: false
    };

    submit.disabled = true;
    say("", form.dataset.msgSending);

    var ctrl = new AbortController();
    var timer = setTimeout(function () { ctrl.abort(); }, 15000);

    fetch(form.dataset.endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Accept": "application/json" },
      body: JSON.stringify(payload),
      signal: ctrl.signal,
      credentials: "omit",
      referrerPolicy: "no-referrer"
    })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (d && d.success) { form.reset(); say("ok", form.dataset.msgOk); }
        else { say("err", form.dataset.msgErr); }
      })
      .catch(function () { say("err", form.dataset.msgErr); })
      .then(function () { clearTimeout(timer); submit.disabled = false; });
  });
})();
