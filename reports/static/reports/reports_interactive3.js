
(function () {

    "use strict";

    const reportDataElement =
        document.getElementById("report-data");

    if (!reportDataElement) {
        return;
    }

    let reportData;

    try {
        reportData =
            JSON.parse(reportDataElement.textContent);
    } catch (error) {
        console.error(
            "Unable to parse report data:",
            error
        );
        return;
    }

    const reportType =
        document.getElementById("reportType");

    const dateFrom =
        document.getElementById("dateFrom");

    const dateTo =
        document.getElementById("dateTo");

    const statusFilter =
        document.getElementById("statusFilter");

    const chartType =
        document.getElementById("chartType");

    const applyFilters =
        document.getElementById("applyFilters");

    const clearFilters =
        document.getElementById("clearFilters");

    const exportCsv =
        document.getElementById("exportCsv");

    const printReport =
        document.getElementById("printReport");

    const totalRecords =
        document.getElementById("totalRecords");

    const filteredRecords =
        document.getElementById("filteredRecords");

    const summaryReport =
        document.getElementById("summaryReport");

    const tableTitle =
        document.getElementById("tableTitle");

    const tableCount =
        document.getElementById("tableCount");

    const tableHead =
        document.getElementById("reportTableHead");

    const tableBody =
        document.getElementById("reportTableBody");

    const emptyMessage =
        document.getElementById("emptyMessage");

    const chartTitle =
        document.getElementById("chartTitle");

    const statusMessage =
        document.getElementById("statusMessage");

    const canvas =
        document.getElementById("reportChart");

    const ctx =
        canvas.getContext("2d");


    const reportNames = {
        service_requests: "Service Requests",
        invoices: "Invoices",
        employees: "Employees",
        equipment: "Equipment"
    };


    const reportColumns = {

        service_requests: [
            {
                key: "number",
                label: "Service Request"
            },
            {
                key: "customer",
                label: "Customer"
            },
            {
                key: "service_type",
                label: "Service Type"
            },
            {
                key: "status",
                label: "Status"
            },
            {
                key: "start_date",
                label: "Start Date"
            },
            {
                key: "end_date",
                label: "End Date"
            }
        ],

        invoices: [
            {
                key: "number",
                label: "Invoice"
            },
            {
                key: "customer",
                label: "Customer"
            },
            {
                key: "status",
                label: "Payment Status"
            },
            {
                key: "issue_date",
                label: "Issue Date"
            },
            {
                key: "due_date",
                label: "Due Date"
            }
        ],

        employees: [
            {
                key: "employee_number",
                label: "Employee Number"
            },
            {
                key: "first_name",
                label: "First Name"
            },
            {
                key: "last_name",
                label: "Last Name"
            },
            {
                key: "position",
                label: "Position"
            },
            {
                key: "department",
                label: "Department"
            },
            {
                key: "status",
                label: "Status"
            }
        ],

        equipment: [
            {
                key: "name",
                label: "Name"
            },
            {
                key: "category",
                label: "Category"
            },
            {
                key: "make",
                label: "Make"
            },
            {
                key: "model",
                label: "Model"
            },
            {
                key: "stock_number",
                label: "Stock Number"
            },
            {
                key: "quantity",
                label: "Quantity"
            }
        ]
    };


    let currentRows = [];


    function getRows() {

        return Array.isArray(
            reportData[reportType.value]
        )
            ? reportData[reportType.value]
            : [];
    }


    function getDateField(row) {

        switch (reportType.value) {

            case "service_requests":
                return row.start_date || "";

            case "invoices":
                return row.issue_date || "";

            case "employees":
                return "";

            case "equipment":
                return "";

            default:
                return "";
        }
    }


    function populateStatusFilter(rows) {

        const currentValue =
            statusFilter.value;

        statusFilter.innerHTML = "";

        const allOption =
            document.createElement("option");

        allOption.value = "";
        allOption.textContent = "All Statuses";

        statusFilter.appendChild(allOption);

        const statuses = new Set();

        rows.forEach(function (row) {

            if (row.status !== undefined &&
                row.status !== null &&
                String(row.status).trim() !== "") {

                statuses.add(
                    String(row.status)
                );
            }
        });

        Array.from(statuses)
            .sort(function (a, b) {
                return a.localeCompare(b);
            })
            .forEach(function (status) {

                const option =
                    document.createElement("option");

                option.value = status;
                option.textContent = status;

                statusFilter.appendChild(option);
            });

        if (
            Array.from(statuses).includes(currentValue)
        ) {
            statusFilter.value =
                currentValue;
        }
    }


    function filterRows() {

        const rows = getRows();

        const from =
            dateFrom.value || "";

        const to =
            dateTo.value || "";

        const status =
            statusFilter.value || "";

        return rows.filter(function (row) {

            const rowDate =
                getDateField(row);

            if (from && rowDate && rowDate < from) {
                return false;
            }

            if (to && rowDate && rowDate > to) {
                return false;
            }

            if (status) {

                const rowStatus =
                    String(row.status || "");

                if (rowStatus !== status) {
                    return false;
                }
            }

            return true;
        });
    }


    function formatDate(value) {

        if (!value) {
            return "";
        }

        const parts =
            String(value).split("-");

        if (parts.length !== 3) {
            return value;
        }

        return (
            parts[1] +
            "/" +
            parts[2] +
            "/" +
            parts[0]
        );
    }


    function formatCellValue(key, value) {
        if (
            value === null ||
            value === undefined ||
            String(value).trim() === ""
        ) {
            return "N/A";
        }

        if (
            key === "start_date" ||
            key === "end_date" ||
            key === "issue_date" ||
            key === "due_date"
        ) {
            return formatDate(value);
        }

        return String(value);
    }


    function renderTable(rows) {

        tableHead.innerHTML = "";
        tableBody.innerHTML = "";

        const columns =
            reportColumns[reportType.value] || [];

        const headerRow =
            document.createElement("tr");

        columns.forEach(function (column) {

            const th =
                document.createElement("th");

            th.textContent =
                column.label;

            headerRow.appendChild(th);
        });

        tableHead.appendChild(headerRow);

        if (!rows.length) {

            emptyMessage.style.display =
                "block";

            return;
        }

        emptyMessage.style.display =
            "none";

        rows.forEach(function (row) {

            const tr =
                document.createElement("tr");

            columns.forEach(function (column) {

                const td =
                    document.createElement("td");

                td.textContent =
                    formatCellValue(
                        column.key,
                        row[column.key]
                    );

                tr.appendChild(td);
            });

            tableBody.appendChild(tr);
        });
    }


    function clearCanvas() {

        ctx.clearRect(
            0,
            0,
            canvas.width,
            canvas.height
        );
    }


    function resizeCanvas() {

        const rect =
            canvas.getBoundingClientRect();

        const width =
            Math.max(
                600,
                Math.floor(rect.width)
            );

        const height = 350;

        const ratio =
            window.devicePixelRatio || 1;

        canvas.width =
            width * ratio;

        canvas.height =
            height * ratio;

        canvas.style.height =
            height + "px";

        ctx.setTransform(
            ratio,
            0,
            0,
            ratio,
            0,
            0
        );

        return {
            width: width,
            height: height
        };
    }


    function getStatusCounts(rows) {

        const counts = {};

        rows.forEach(function (row) {

            const status =
                String(
                    row.status || "Unknown"
                );

            counts[status] =
                (counts[status] || 0) + 1;
        });

        return counts;
    }


    function getCategoryCounts(rows) {

        const counts = {};

        rows.forEach(function (row) {

            let category = "Unknown";

            if (
                reportType.value ===
                "service_requests"
            ) {
                category =
                    row.service_type ||
                    "Unknown";
            }

            else if (
                reportType.value ===
                "employees"
            ) {
                category =
                    row.department ||
                    "Unknown";
            }

            else if (
                reportType.value ===
                "equipment"
            ) {
                category =
                    row.category ||
                    "Unknown";
            }

            else if (
                reportType.value ===
                "invoices"
            ) {
                category =
                    row.customer ||
                    "Unknown";
            }

            counts[category] =
                (counts[category] || 0) + 1;
        });

        return counts;
    }


    function getMonthlyCounts(rows) {

        const counts = {};

        rows.forEach(function (row) {

            const date =
                getDateField(row);

            if (!date) {
                return;
            }

            const month =
                date.substring(0, 7);

            counts[month] =
                (counts[month] || 0) + 1;
        });

        return counts;
    }


    function drawBarChart(counts, title) {

        clearCanvas();

        const dimensions =
            resizeCanvas();

        const width =
            dimensions.width;

        const height =
            dimensions.height;

        chartTitle.textContent =
            title;

        const labels =
            Object.keys(counts);

        if (!labels.length) {

            ctx.fillStyle = "#666";
            ctx.font = "16px Arial";
            ctx.textAlign = "center";

            ctx.fillText(
                "No chart data available",
                width / 2,
                height / 2
            );

            return;
        }

        labels.sort(function (a, b) {
            return counts[b] - counts[a];
        });

        const maxItems = 12;

        const displayLabels =
            labels.slice(0, maxItems);

        const values =
            displayLabels.map(function (label) {
                return counts[label];
            });

        const maxValue =
            Math.max.apply(null, values);

        const left =
            60;

        const right =
            20;

        const top =
            30;

        const bottom =
            75;

        const chartWidth =
            width - left - right;

        const chartHeight =
            height - top - bottom;

        const barWidth =
            chartWidth / displayLabels.length * 0.65;

        const gap =
            chartWidth / displayLabels.length * 0.35;

        ctx.font = "12px Arial";

        displayLabels.forEach(function (
            label,
            index
        ) {

            const value =
                counts[label];

            const slot =
                chartWidth /
                displayLabels.length;

            const x =
                left +
                index * slot +
                gap / 2;

            const barHeight =
                maxValue > 0
                    ? (value / maxValue) *
                      chartHeight
                    : 0;

            const y =
                top +
                chartHeight -
                barHeight;

            ctx.fillStyle =
                "#444";

            ctx.fillRect(
                x,
                y,
                barWidth,
                barHeight
            );

            ctx.fillStyle =
                "#222";

            ctx.textAlign =
                "center";

            ctx.fillText(
                String(value),
                x + barWidth / 2,
                y - 6
            );

            ctx.save();

            ctx.translate(
                x + barWidth / 2,
                height - 15
            );

            ctx.rotate(-Math.PI / 4);

            ctx.fillStyle =
                "#444";

            ctx.fillText(
                String(label).substring(
                    0,
                    18
                ),
                0,
                0
            );

            ctx.restore();
        });

        ctx.strokeStyle =
            "#999";

        ctx.beginPath();

        ctx.moveTo(
            left,
            top
        );

        ctx.lineTo(
            left,
            top + chartHeight
        );

        ctx.lineTo(
            width - right,
            top + chartHeight
        );

        ctx.stroke();
    }


    function drawChart(rows) {

        if (chartType.value === "monthly") {

            drawBarChart(
                getMonthlyCounts(rows),
                "Monthly Activity"
            );

            return;
        }

        if (chartType.value === "category") {

            drawBarChart(
                getCategoryCounts(rows),
                "Category / Type"
            );

            return;
        }

        drawBarChart(
            getStatusCounts(rows),
            "Status Distribution"
        );
    }


    function renderReport() {

        const rows =
            getRows();

        const filtered =
            filterRows();

        currentRows =
            filtered;

        const reportName =
            reportNames[
                reportType.value
            ] || "Report";

        totalRecords.textContent =
            rows.length;

        filteredRecords.textContent =
            filtered.length;

        summaryReport.textContent =
            reportName;

        tableTitle.textContent =
            reportName;

        tableCount.textContent =
            filtered.length +
            (
                filtered.length === 1
                    ? " record"
                    : " records"
            );

        renderTable(filtered);

        drawChart(filtered);

        statusMessage.textContent =
            "Showing " +
            filtered.length +
            " of " +
            rows.length +
            " records.";
    }


    function csvEscape(value) {

        const stringValue =
            value === null ||
            value === undefined
                ? ""
                : String(value);

        return '"' +
            stringValue.replace(
                /"/g,
                '""'
            ) +
            '"';
    }


    function exportReportCsv() {

        const columns =
            reportColumns[reportType.value] || [];

        const lines = [];

        lines.push(
            columns
                .map(function (column) {
                    return csvEscape(
                        column.label
                    );
                })
                .join(",")
        );

        currentRows.forEach(function (row) {

            lines.push(
                columns
                    .map(function (column) {

                        return csvEscape(
                            formatCellValue(
                                column.key,
                                row[column.key]
                            )
                        );

                    })
                    .join(",")
            );
        });

        const csv =
            lines.join("\r\n");

        const blob =
            new Blob(
                [csv],
                {
                    type:
                        "text/csv;charset=utf-8;"
                }
            );

        const url =
            URL.createObjectURL(blob);

        const link =
            document.createElement("a");

        const reportName =
            reportType.value;

        link.href = url;

        link.download =
            reportName +
            "_report.csv";

        document.body.appendChild(link);

        link.click();

        document.body.removeChild(link);

        URL.revokeObjectURL(url);
    }


    function updateForReportType() {

        const rows =
            getRows();

        populateStatusFilter(rows);

        /*
         * Date filters only apply to reports
         * that actually contain date information.
         */
        const dateControls =
            [
                dateFrom,
                dateTo
            ];

        const dateEnabled =
            reportType.value ===
                "service_requests" ||
            reportType.value ===
                "invoices";

        dateControls.forEach(function (control) {

            control.disabled =
                !dateEnabled;

            if (!dateEnabled) {
                control.value = "";
            }
        });

        renderReport();
    }


    reportType.addEventListener(
        "change",
        function () {

            updateForReportType();
        }
    );


    statusFilter.addEventListener(
        "change",
        function () {

            renderReport();
        }
    );


    chartType.addEventListener(
        "change",
        function () {

            drawChart(currentRows);
        }
    );


    applyFilters.addEventListener(
        "click",
        function () {

            if (
                dateFrom.value &&
                dateTo.value &&
                dateFrom.value >
                    dateTo.value
            ) {

                statusMessage.textContent =
                    "Date From cannot be later than Date To.";

                return;
            }

            renderReport();
        }
    );


    clearFilters.addEventListener(
        "click",
        function () {

            dateFrom.value = "";
            dateTo.value = "";

            statusFilter.value = "";

            renderReport();
        }
    );


    exportCsv.addEventListener(
        "click",
        function () {

            exportReportCsv();
        }
    );


    printReport.addEventListener(
        "click",
        function () {

            window.print();
        }
    );


    window.addEventListener(
        "resize",
        function () {

            drawChart(currentRows);
        }
    );


    /*
     * Initial render
     */
    updateForReportType();

})();