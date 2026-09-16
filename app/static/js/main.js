(function () {
    "use strict";

    var toggle = document.querySelector(".navbar-toggler");
    var nav = document.querySelector("#mainNav");

    if (toggle && nav) {
        nav.querySelectorAll("a.nav-link, a.btn").forEach(function (link) {
            link.addEventListener("click", function () {
                if (window.getComputedStyle(toggle).display === "none") {
                    return;
                }
                if (nav.classList.contains("show") && window.bootstrap) {
                    var collapse = window.bootstrap.Collapse.getInstance(nav);
                    if (collapse) {
                        collapse.hide();
                    }
                }
            });
        });
    }

    var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    var reveals = document.querySelectorAll(".reveal");

    if (reduceMotion || !("IntersectionObserver" in window)) {
        reveals.forEach(function (el) {
            el.classList.add("is-visible");
        });
        return;
    }

    var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
            if (entry.isIntersecting) {
                entry.target.classList.add("is-visible");
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.12,
        rootMargin: "0px 0px -40px 0px"
    });

    reveals.forEach(function (el) {
        observer.observe(el);
    });
})();
