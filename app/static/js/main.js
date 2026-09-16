(function () {
    "use strict";

    var toggle = document.querySelector(".navbar-toggler");
    var nav = document.querySelector("#mainNav");
    if (!toggle || !nav) {
        return;
    }

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
})();
