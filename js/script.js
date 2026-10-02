/* =========================================================
   FraudShield - Main JavaScript
   Dark / Light Mode + Common UI Functions
   ========================================================= */


/* =========================================================
   DARK / LIGHT MODE
   ========================================================= */

document.addEventListener("DOMContentLoaded", function () {

    const themeToggle = document.getElementById("themeToggle");

    // Saved theme ko check karein
    const savedTheme = localStorage.getItem("fraudshield-theme");

    // Agar user ne pehle dark mode select kiya tha
    if (savedTheme === "dark") {
        document.body.classList.add("dark-mode");

        if (themeToggle) {
            themeToggle.textContent = "☀️";
        }
    }

    // Agar light mode saved hai
    else if (savedTheme === "light") {
        document.body.classList.remove("dark-mode");

        if (themeToggle) {
            themeToggle.textContent = "🌙";
        }
    }

});


/* =========================================================
   THEME TOGGLE FUNCTION
   ========================================================= */

function toggleTheme() {

    const themeToggle = document.getElementById("themeToggle");

    // Dark mode on/off
    document.body.classList.toggle("dark-mode");

    // Check current mode
    if (document.body.classList.contains("dark-mode")) {

        // Dark mode
        localStorage.setItem("fraudshield-theme", "dark");

        if (themeToggle) {
            themeToggle.textContent = "☀️";
        }

    } else {

        // Light mode
        localStorage.setItem("fraudshield-theme", "light");

        if (themeToggle) {
            themeToggle.textContent = "🌙";
        }
    }
}


/* =========================================================
   MOBILE SIDEBAR TOGGLE
   ========================================================= */

function toggleSidebar() {

    const sidebar = document.querySelector(".sidebar");

    if (sidebar) {
        sidebar.classList.toggle("active");
    }
}


/* =========================================================
   CLOSE SIDEBAR WHEN CLICKING OUTSIDE
   ========================================================= */

document.addEventListener("click", function (event) {

    const sidebar = document.querySelector(".sidebar");

    if (!sidebar) {
        return;
    }

    const clickedInsideSidebar = sidebar.contains(event.target);
    const clickedMenuButton =
        event.target.closest(".menu-toggle");

    if (
        !clickedInsideSidebar &&
        !clickedMenuButton &&
        window.innerWidth <= 768
    ) {
        sidebar.classList.remove("active");
    }

});


/* =========================================================
   SAMPLE TRANSACTION BUTTON
   ========================================================= */

function fillSampleTransaction() {

    const amountField =
        document.getElementById("amount");

    const timeField =
        document.getElementById("time");

    if (amountField) {
        amountField.value = "125.50";
    }

    if (timeField) {
        timeField.value = "14:30";
    }

}


/* =========================================================
   CONFIRM DELETE / ACTION
   ========================================================= */

function confirmAction(message) {

    if (confirm(message)) {
        return true;
    }

    return false;
}


/* =========================================================
   AUTO HIDE FLASH MESSAGES
   ========================================================= */

document.addEventListener("DOMContentLoaded", function () {

    const alerts =
        document.querySelectorAll(".alert");

    alerts.forEach(function (alert) {

        setTimeout(function () {

            alert.style.opacity = "0";

            setTimeout(function () {
                alert.remove();
            }, 500);

        }, 5000);

    });

});


/* =========================================================
   SMOOTH SCROLL
   ========================================================= */

document.querySelectorAll('a[href^="#"]').forEach(function (link) {

    link.addEventListener("click", function (event) {

        const targetId =
            this.getAttribute("href");

        if (targetId === "#") {
            return;
        }

        const target =
            document.querySelector(targetId);

        if (target) {

            event.preventDefault();

            target.scrollIntoView({
                behavior: "smooth",
                block: "start"
            });

        }

    });

});


/* =========================================================
   WINDOW RESIZE
   ========================================================= */

window.addEventListener("resize", function () {

    const sidebar =
        document.querySelector(".sidebar");

    if (!sidebar) {
        return;
    }

    // Desktop par sidebar automatically visible
    if (window.innerWidth > 768) {
        sidebar.classList.remove("active");
    }

});