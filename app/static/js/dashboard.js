(function () {
    "use strict";

    var sidebar = document.getElementById("appSidebar");
    var toggle = document.getElementById("sidebarToggle");
    var backdrop = document.getElementById("sidebarBackdrop");

    if (!sidebar || !toggle) {
        return;
    }

    function setOpen(open) {
        sidebar.classList.toggle("is-open", open);
        toggle.setAttribute("aria-expanded", open ? "true" : "false");
        if (backdrop) {
            backdrop.hidden = !open;
            backdrop.classList.toggle("is-open", open);
        }
    }

    toggle.addEventListener("click", function () {
        setOpen(!sidebar.classList.contains("is-open"));
    });

    if (backdrop) {
        backdrop.addEventListener("click", function () {
            setOpen(false);
        });
    }
})();
