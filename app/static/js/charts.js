(function () {
    "use strict";

    var node = document.getElementById("dashboard-charts");
    if (!node || typeof Chart === "undefined") {
        return;
    }

    var data;
    try {
        data = JSON.parse(node.textContent);
    } catch (err) {
        return;
    }

    var green = "#0f3d2e";
    var gold = "#c9a227";
    var sage = "#4f8f6e";
    var sand = "#c4a574";
    var colors = [green, gold, sage, sand, "#7aa88a", "#8b5e3c"];

    function labelsAndTotals(rows) {
        rows = rows || [];
        return {
            labels: rows.map(function (row) { return row.label; }),
            totals: rows.map(function (row) { return Number(row.total) || 0; })
        };
    }

    function bar(id, rows, label) {
        var canvas = document.getElementById(id);
        if (!canvas) {
            return;
        }
        var packed = labelsAndTotals(rows);
        new Chart(canvas, {
            type: "bar",
            data: {
                labels: packed.labels,
                datasets: [{ label: label, data: packed.totals, backgroundColor: green }]
            },
            options: { responsive: true, plugins: { legend: { display: false } } }
        });
    }

    function doughnut(id, rows) {
        var canvas = document.getElementById(id);
        if (!canvas) {
            return;
        }
        var packed = labelsAndTotals(rows);
        new Chart(canvas, {
            type: "doughnut",
            data: {
                labels: packed.labels,
                datasets: [{ data: packed.totals, backgroundColor: colors }]
            },
            options: { responsive: true }
        });
    }

    bar("chartSalesByType", data.sales_by_type, "ZMW");
    bar("chartMonthly", data.monthly_sales, "ZMW");
    doughnut("chartLotStatus", data.lot_status);
    doughnut("chartPaymentStatus", data.payment_status);
})();
