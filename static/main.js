
"use strict";

document.addEventListener("DOMContentLoaded", function () {
    console.log("ExpenseTracker Pro JavaScript loaded!");

    // ==========================================
    // 1. HELPER: SHOW NOTIFICATION
    // ==========================================
    function showNotification(message, type = "success") {
        let toast = document.getElementById("appToast");

        if (!toast) {
            toast = document.createElement("div");
            toast.id = "appToast";
            toast.setAttribute("role", "status");
            toast.setAttribute("aria-live", "polite");

            Object.assign(toast.style, {
                position: "fixed",
                right: "20px",
                bottom: "20px",
                zIndex: "99999",
                maxWidth: "320px",
                padding: "14px 20px",
                borderRadius: "12px",
                color: "#ffffff",
                background: "#16794b",
                boxShadow: "0 8px 25px rgba(0,0,0,.3)",
                fontSize: "14px",
                opacity: "0",
                transition: "opacity .2s ease"
            });

            document.body.appendChild(toast);
        }

        toast.style.background =
            type === "error" ? "#b42332" :
            type === "warning" ? "#9a6700" : "#16794b";

        toast.textContent = message;
        toast.style.opacity = "1";

        clearTimeout(toast.hideTimer);
        toast.hideTimer = setTimeout(function () {
            toast.style.opacity = "0";
        }, 3000);
    }

    window.showAppMessage = showNotification;

    // ==========================================
    // 2. PASSWORD SHOW / HIDE
    // HTML button:
    // data-toggle-password="password"
    // ==========================================
    document.querySelectorAll("[data-toggle-password]").forEach(function (button) {
        button.addEventListener("click", function () {
            const inputId = button.getAttribute("data-toggle-password");
            const input = document.getElementById(inputId);

            if (!input) {
                showNotification("Password field not found.", "error");
                return;
            }

            const showing = input.type === "password";
            input.type = showing ? "text" : "password";
            button.textContent = showing ? "Hide" : "Show";
            button.setAttribute("aria-pressed", String(showing));
        });
    });

    // ==========================================
    // 3. SIGNUP CONFIRM PASSWORD
    // Confirm field:
    // data-confirm-password
    // ==========================================
    document.querySelectorAll("[data-confirm-password]").forEach(function (confirmInput) {
        const form = confirmInput.closest("form");
        if (!form) return;

        form.addEventListener("submit", function (event) {
            const passwordInput = form.querySelector(
                'input[name="password"], input[id="password"]'
            );

            if (!passwordInput) return;

            if (passwordInput.value !== confirmInput.value) {
                event.preventDefault();
                showNotification("Passwords do not match.", "error");
                confirmInput.focus();
            }
        });
    });

    // ==========================================
    // 4. EXPENSE AMOUNT VALIDATION
    // Add data-expense-form to the existing form.
    // ==========================================
    document.querySelectorAll("form[data-expense-form]").forEach(function (form) {
        form.addEventListener("submit", function (event) {
            const amountInput = form.querySelector(
                'input[name="amount"], input[id="amount"]'
            );

            if (!amountInput) return;

            const amount = Number(amountInput.value);

            if (
                amountInput.value.trim() === "" ||
                !Number.isFinite(amount) ||
                amount <= 0
            ) {
                event.preventDefault();
                showNotification(
                    "Please enter an amount greater than zero.",
                    "error"
                );
                amountInput.focus();
            }
        });
    });

    // ==========================================
    // 5. DELETE CONFIRMATION
    // Add data-confirm-delete to the existing
    // delete link or button.
    // ==========================================
    document.querySelectorAll("[data-confirm-delete]").forEach(function (element) {
        element.addEventListener("click", function (event) {
            const message =
                element.getAttribute("data-confirm-delete") ||
                "Are you sure you want to delete this item?";

            if (!window.confirm(message)) {
                event.preventDefault();
            }
        });
    });

    // ==========================================
    // 6. INDIAN RUPEE FORMATTING
    // Usage: formatExpenseCurrency(1500)
    // ==========================================
    window.formatExpenseCurrency = function (amount) {
        const value = Number(amount);

        if (!Number.isFinite(value)) {
            return "₹0.00";
        }

        return new Intl.NumberFormat("en-IN", {
            style: "currency",
            currency: "INR",
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(value);
    };

    // ==========================================
    // 7. LIVE DATE AND TIME
    // Add <span data-current-time></span>
    // where you want to display it.
    // ==========================================
    function updateClock() {
        const now = new Date();

        document.querySelectorAll("[data-current-time]").forEach(function (element) {
            element.textContent = now.toLocaleString("en-IN", {
                dateStyle: "medium",
                timeStyle: "medium"
            });
        });
    }

    updateClock();

    if (document.querySelector("[data-current-time]")) {
        setInterval(updateClock, 1000);
    }

    // ==========================================
    // 8. SEARCH / FILTER TABLE ROWS
    // Search input: data-table-search="expenseTable"
    // Table: id="expenseTable"
    // ==========================================
    document.querySelectorAll("[data-table-search]").forEach(function (input) {
        input.addEventListener("input", function () {
            const tableId = input.getAttribute("data-table-search");
            const table = document.getElementById(tableId);

            if (!table) return;

            const query = input.value.trim().toLowerCase();

            table.querySelectorAll("tbody tr").forEach(function (row) {
                row.hidden = !row.textContent.toLowerCase().includes(query);
            });
        });
    });

    // ==========================================
    // 9. CLEAR INPUTS IN FORMS
    // Optional button: data-clear-form="expenseForm"
    // ==========================================
    document.querySelectorAll("[data-clear-form]").forEach(function (button) {
        button.addEventListener("click", function () {
            const formId = button.getAttribute("data-clear-form");
            const form = document.getElementById(formId);

            if (!form) return;

            form.reset();
            showNotification("Form cleared.", "success");
        });
    });

    // ==========================================
    // 10. PREVENT DOUBLE FORM SUBMISSION
    // Applies to forms marked data-prevent-double-submit.
    // ==========================================
    document.querySelectorAll("form[data-prevent-double-submit]").forEach(function (form) {
        form.addEventListener("submit", function () {
            if (!form.checkValidity()) return;

            const submitButton = form.querySelector(
                'button[type="submit"], input[type="submit"]'
            );

            if (submitButton) {
                submitButton.disabled = true;
                submitButton.setAttribute("aria-busy", "true");
            }
        });
    });

    // ==========================================
    // 11. OPTIONAL BUTTON CLICK FEEDBACK
    // Add data-app-message="Your message"
    // to a non-submit button.
    // ==========================================
    document.querySelectorAll("[data-app-message]").forEach(function (button) {
        button.addEventListener("click", function () {
            showNotification(
                button.getAttribute("data-app-message") || "Done!"
            );
        });
    });

    // ==========================================
    // 12. INTERACTIVE DASHBOARD DONUT / PIE CHART
    // Works with the existing category_spending data
    // rendered by dashboard.html. No backend changes.
    // ==========================================
    const donutChart = document.getElementById("donutChart");
    const chartLegendItems = Array.from(
        document.querySelectorAll("[data-chart-category][data-chart-amount]")
    );
    const chartModeButtons = document.querySelectorAll("[data-chart-mode]");
    const chartResetButton = document.querySelector("[data-chart-reset]");

    if (donutChart && chartLegendItems.length) {
        const centerAmount = donutChart.querySelector(".donut-center strong");
        const centerLabel = donutChart.querySelector(".donut-center span");
        const originalAmount = centerAmount ? centerAmount.textContent.trim() : "";
        const originalLabel = centerLabel ? centerLabel.textContent.trim() : "Total Spent";

        function selectChartCategory(item) {
            chartLegendItems.forEach(function (legendItem) {
                const selected = legendItem === item;
                legendItem.classList.toggle("is-selected", selected);
                legendItem.setAttribute("aria-pressed", String(selected));
            });

            if (centerAmount) {
                centerAmount.textContent = window.formatExpenseCurrency(
                    item.getAttribute("data-chart-amount")
                );
            }
            if (centerLabel) {
                centerLabel.textContent = item.getAttribute("data-chart-category") || "Category";
            }
        }

        function resetChartSelection() {
            chartLegendItems.forEach(function (item) {
                item.classList.remove("is-selected");
                item.setAttribute("aria-pressed", "false");
            });
            if (centerAmount) centerAmount.textContent = originalAmount;
            if (centerLabel) centerLabel.textContent = originalLabel;
        }

        chartLegendItems.forEach(function (item) {
            item.setAttribute("aria-pressed", "false");
            item.addEventListener("click", function () {
                selectChartCategory(item);
            });
            item.addEventListener("keydown", function (event) {
                if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    selectChartCategory(item);
                }
            });
        });

        chartModeButtons.forEach(function (button) {
            button.addEventListener("click", function () {
                const mode = button.getAttribute("data-chart-mode");
                donutChart.classList.toggle("is-pie", mode === "pie");
                chartModeButtons.forEach(function (otherButton) {
                    const active = otherButton === button;
                    otherButton.classList.toggle("active", active);
                    otherButton.setAttribute("aria-pressed", String(active));
                });
            });
        });

        if (chartResetButton) {
            chartResetButton.addEventListener("click", resetChartSelection);
        }
    }

    console.log("All ExpenseTracker Pro frontend handlers initialized.");
    
    // Full expense history filters
    const expenseTable = document.getElementById("allExpensesTable");
    const searchInput = document.getElementById("expenseSearch");
    const categorySelect = document.getElementById("categoryFilter");
    const monthInput = document.getElementById("monthFilter");
    const resetButton = document.getElementById("resetExpenseFilters");

    if (expenseTable && searchInput && categorySelect && monthInput) {
        const rows = Array.from(
            expenseTable.querySelectorAll("tbody tr")
        );

        // Populate categories from the rendered table
        const categories = new Set();

        rows.forEach(function (row) {
            const cells = row.querySelectorAll("td");
            if (cells.length >= 3) {
                categories.add(cells[2].textContent.trim());
            }
        });

        Array.from(categories).sort().forEach(function (category) {
            if (!category) return;

            const option = document.createElement("option");
            option.value = category.toLowerCase();
            option.textContent = category;
            categorySelect.appendChild(option);
        });

        function filterExpenses() {
            const query = searchInput.value.trim().toLowerCase();
            const selectedCategory = categorySelect.value;
            const selectedMonth = monthInput.value;

            rows.forEach(function (row) {
                const cells = row.querySelectorAll("td");
                const text = row.textContent.toLowerCase();

                // Assumes column order: Date, Category, Description, Amount
                const dateText = cells[0]?.textContent.trim() || "";
                const category = cells[2]?.textContent.trim().toLowerCase() || "";

          const rowMonth = dateText.match(/^\d{4}-\d{2}/)?.[0] || ""; 

                const matchesSearch = text.includes(query);
                const matchesCategory =
                    !selectedCategory || category === selectedCategory;
                const matchesMonth =
                    !selectedMonth || rowMonth === selectedMonth;

                row.hidden = !(
                    matchesSearch &&
                    matchesCategory &&
                    matchesMonth
                );
            });
        }

        searchInput.addEventListener("input", filterExpenses);
        categorySelect.addEventListener("change", filterExpenses);
        monthInput.addEventListener("change", filterExpenses);

        if (resetButton) {
            resetButton.addEventListener("click", function () {
                searchInput.value = "";
                categorySelect.value = "";
                monthInput.value = "";
                filterExpenses();
            });
        }
    }

});
