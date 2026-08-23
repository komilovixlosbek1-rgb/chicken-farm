// Chicken Farm Mini App
// app.js
// Asosiy JavaScript funksiyalar shu faylda bo'ladi.

const tg = window.Telegram?.WebApp;
const API_URL =
    localStorage.getItem("CHICKEN_API_URL") ||
    "https://chicken-farm-630z.onrender.com";

let appData = null;
let miningRemaining = 0;
let miningInterval = null;


// ================================
// TELEGRAM
// ================================

function initTelegram() {
    if (!tg) return;

    tg.ready();
    tg.expand();

    if (tg.setBackgroundColor) {
        tg.setBackgroundColor("bg_color");
    }

    if (tg.setHeaderColor) {
        tg.setHeaderColor("secondary_bg_color");
    }
}


// ================================
// INIT DATA
// ================================

function getInitData() {
    if (tg && tg.initData) {
        return tg.initData;
    }

    return "";
}


// ================================
// API
// ================================

async function apiRequest(endpoint, options = {}) {

    const headers = {
        "Content-Type": "application/json",
        "X-Telegram-Init-Data": getInitData(),
        ...(options.headers || {})
    };

    const response = await fetch(
        API_URL + endpoint,
        {
            ...options,
            headers
        }
    );

    let data = {};

    try {
        data = await response.json();
    } catch {
        data = {};
    }

    if (!response.ok) {
        throw new Error(
            data.detail ||
            data.message ||
            "Server xatosi"
        );
    }

    return data;
}


// ================================
// NUMBER
// ================================

function formatNumber(number) {
    return Number(number || 0).toLocaleString("uz-UZ");
}


// ================================
// TOAST
// ================================

function showToast(message, type = "success") {

    const toast = document.getElementById("toast");
    const text = document.getElementById("toastText");
    const icon = document.getElementById("toastIcon");

    if (!toast || !text || !icon) return;

    const icons = {
        success: "✅",
        error: "❌",
        warning: "⚠️",
        info: "ℹ️"
    };

    text.textContent = message;
    icon.textContent = icons[type] || "ℹ️";

    toast.className = "toast show " + type;

    setTimeout(() => {
        toast.classList.remove("show");
    }, 3000);
}


// ================================
// PAGE
// ================================

function showPage(page) {

    document.querySelectorAll(".page").forEach(element => {
        element.classList.remove("active");
    });

    const target = document.getElementById("page-" + page);

    if (target) {
        target.classList.add("active");
    }

    document.querySelectorAll(".nav-item").forEach(item => {

        item.classList.remove("active");

        if (item.dataset.page === page) {
            item.classList.add("active");
        }
    });

    window.scrollTo(0, 0);

    if (page === "farm") {
        loadDashboard();
    }

    if (page === "eggs") {
        loadDashboard();
    }

    if (page === "mining") {
        loadMining();
    }
}


// ================================
// DASHBOARD
// ================================

async function loadDashboard() {

    try {

        const data = await apiRequest("/api/dashboard");

        appData = data;

        const user = data.user || {};

        const firstName =
            user.first_name ||
            "Fermer";

        const userName =
            document.getElementById("userName");

        const welcomeName =
            document.getElementById("welcomeName");

        if (userName) {
            userName.textContent = firstName;
        }

        if (welcomeName) {
            welcomeName.textContent =
                "Xush kelibsiz, " + firstName + "!";
        }


        // BALANCE

        const balance =
            document.getElementById("balance");

        if (balance) {
            balance.textContent =
                formatNumber(data.balance);
        }


        // EGGS

        const eggs =
            document.getElementById("eggCount");

        if (eggs) {
            eggs.textContent =
                formatNumber(data.eggs);
        }

        const eggStorage =
            document.getElementById("eggStorage");

        if (eggStorage) {
            eggStorage.textContent =
                formatNumber(data.eggs);
        }


        // CAPACITY

        const capacity =
            Number(data.egg_capacity || 1000);

        const capacityElement =
            document.getElementById("eggCapacity");

        if (capacityElement) {
            capacityElement.textContent =
                formatNumber(capacity);
        }


        // STORAGE

        const storage =
            document.getElementById("storageCount");

        if (storage) {
            storage.textContent =
                formatNumber(data.eggs) +
                "/" +
                formatNumber(capacity);
        }


        // CHICKENS

        const chickens =
            document.getElementById("chickenCount");

        if (chickens) {
            chickens.textContent =
                formatNumber(data.total_chickens);
        }


        // PROGRESS

        const eggAmount =
            Number(data.eggs || 0);

        const percentage =
            Math.min(
                100,
                (eggAmount / capacity) * 100
            );

        const progress =
            document.getElementById("eggProgress");

        if (progress) {
            progress.style.width =
                percentage + "%";
        }


        // FARM

        renderFarm(
            data.chickens || []
        );


        // WITHDRAW

        const withdrawBalance =
            document.getElementById(
                "withdrawBalance"
            );

        if (withdrawBalance) {
            withdrawBalance.textContent =
                formatNumber(data.balance) +
                " coin";
        }


        // CARD

        if (
            data.settings &&
            data.settings.card_number
        ) {

            const card =
                document.getElementById(
                    "paymentCard"
                );

            if (card) {
                card.textContent =
                    data.settings.card_number;
            }
        }

    } catch (error) {

        console.error(error);

        showToast(
            "❌ " + error.message,
            "error"
        );
    }
}


// ================================
// FARM
// ================================

function renderFarm(chickens) {

    const container =
        document.getElementById("farmList");

    if (!container) return;


    if (!chickens || chickens.length === 0) {

        container.innerHTML = `

            <div class="empty-state">

                <div class="empty-icon">
                    🐔
                </div>

                <div class="empty-title">
                    Hali tovuq yo‘q
                </div>

                <div class="empty-text">
                    Fermangizni rivojlantirish uchun
                    birinchi tovuqni sotib oling.
                </div>

                <button
                    class="primary-button"
                    onclick="showPage('shop')"
                >
                    🛒 Tovuq sotib olish
                </button>

            </div>
        `;

        return;
    }


    const icons = {
        1: "🐔",
        2: "🐓",
        3: "🦃"
    };

    const rates = {
        1: 1,
        2: 3,
        3: 8
    };


    container.innerHTML =
        chickens.map(chicken => {

            const level =
                Number(chicken.level || 1);

            const count =
                Number(chicken.count || 0);

            const production =
                (rates[level] || 1) * count;

            return `

                <div class="farm-card">

                    <div class="farm-chicken">
                        ${icons[level] || "🐔"}
                    </div>

                    <div class="farm-info">

                        <div class="farm-level">
                            Lv.${level} Tovuq
                        </div>

                        <div class="farm-count">
                            ${formatNumber(count)} ta
                        </div>

                        <div class="farm-production">
                            🥚 ${formatNumber(production)}
                            tuxum / daqiqa
                        </div>

                    </div>

                    <div class="farm-status">
                        ⚡ Ishlayapti
                    </div>

                </div>
            `;

        }).join("");
}


// ================================
// BUY CHICKEN
// ================================

async function buyChicken(level) {

    const prices = {
        1: 1000,
        2: 5000,
        3: 15000
    };

    const price = prices[level];

    if (!price) {
        showToast(
            "❌ Tovuq darajasi noto‘g‘ri",
            "error"
        );
        return;
    }


    const confirmed =
        confirm(
            `Lv.${level} tovuqni ${formatNumber(price)} coin ga sotib olasizmi?`
        );

    if (!confirmed) return;


    try {

        showToast(
            "⏳ Sotib olinmoqda...",
            "info"
        );

        const result =
            await apiRequest(
                "/api/chicken/buy",
                {
                    method: "POST",
                    body: JSON.stringify({
                        level: level
                    })
                }
            );

        showToast(
            result.message ||
            "🎉 Tovuq sotib olindi!",
            "success"
        );

        await loadDashboard();

        showPage("farm");

    } catch (error) {

        showToast(
            "❌ " + error.message,
            "error"
        );
    }
}


// ================================
// EGGS → COIN
// ================================

async function exchangeEggs() {

    try {

        const result =
            await apiRequest(
                "/api/eggs/exchange",
                {
                    method: "POST"
                }
            );

        showToast(
            result.message ||
            "🥚 Tuxumlar coinga almashtirildi!",
            "success"
        );

        await loadDashboard();

    } catch (error) {

        showToast(
            "❌ " + error.message,
            "error"
        );
    }
}


// ================================
// MINING
// ================================

async function loadMining() {

    try {

        const data =
            await apiRequest(
                "/api/mining"
            );

        miningRemaining =
            Number(data.remaining || 0);

        updateMiningUI();


        if (miningInterval) {
            clearInterval(miningInterval);
        }


        miningInterval =
            setInterval(() => {

                if (miningRemaining > 0) {

                    miningRemaining--;

                    updateMiningUI();
                }

            }, 1000);

    } catch (error) {

        const timer =
            document.getElementById(
                "miningTimer"
            );

        if (timer) {
            timer.textContent =
                "Server bilan bog‘lanib bo‘lmadi";
        }
    }
}


function updateMiningUI() {

    const timer =
        document.getElementById(
            "miningTimer"
        );

    const button =
        document.getElementById(
            "claimMiningButton"
        );

    if (!timer || !button) return;


    if (miningRemaining <= 0) {

        timer.textContent =
            "🎉 Bonus tayyor!";

        button.disabled = false;

        button.textContent =
            "🎁 100 Coin olish";

        return;
    }


    button.disabled = true;

    button.textContent =
        "⏳ Kutilmoqda...";


    const hours =
        Math.floor(
            miningRemaining / 3600
        );

    const minutes =
        Math.floor(
            (miningRemaining % 3600) / 60
        );

    const seconds =
        miningRemaining % 60;


    timer.textContent =
        `Keyingi bonus: ${
            String(hours).padStart(2, "0")
        }:${
            String(minutes).padStart(2, "0")
        }:${
            String(seconds).padStart(2, "0")
        }`;
}


async function claimMining() {

    if (miningRemaining > 0) {
        return;
    }


    try {

        const result =
            await apiRequest(
                "/api/mining/claim",
                {
                    method: "POST"
                }
            );

        showToast(
            result.message ||
            "🎉 +100 coin olindi!",
            "success"
        );

        await loadDashboard();

        await loadMining();

    } catch (error) {

        showToast(
            "❌ " + error.message,
            "error"
        );
    }
}


// ================================
// DEPOSIT
// ================================

async function makeDeposit() {

    const amount =
        Number(
            document.getElementById(
                "depositAmount"
            )?.value
        );

    const proof =
        document.getElementById(
            "depositProof"
        )?.value.trim() || "";


    if (!amount || amount < 5000) {

        showToast(
            "❌ Minimal depozit 5 000 coin",
            "error"
        );

        return;
    }


    try {

        const result =
            await apiRequest(
                "/api/deposit",
                {
                    method: "POST",

                    body: JSON.stringify({
                        amount: amount,
                        proof: proof
                    })
                }
            );


        showToast(
            result.message ||
            "✅ Depozit so‘rovi yuborildi!",
            "success"
        );


        document.getElementById(
            "depositAmount"
        ).value = "";

        document.getElementById(
            "depositProof"
        ).value = "";

    } catch (error) {

        showToast(
            "❌ " + error.message,
            "error"
        );
    }
}


// ================================
// WITHDRAW
// ================================

async function makeWithdraw() {

    const amount =
        Number(
            document.getElementById(
                "withdrawAmount"
            )?.value
        );

    const card =
        document.getElementById(
            "withdrawCard"
        )?.value.trim() || "";

    const name =
        document.getElementById(
            "withdrawName"
        )?.value.trim() || "";


    if (!amount || amount < 10000) {

        showToast(
            "❌ Minimal chiqarish 10 000 coin",
            "error"
        );

        return;
    }


    if (!card) {

        showToast(
            "❌ Karta raqamini kiriting",
            "error"
        );

        return;
    }


    if (!name) {

        showToast(
            "❌ Ism-sharifni kiriting",
            "error"
        );

        return;
    }


    try {

        const result =
            await apiRequest(
                "/api/withdraw",
                {
                    method: "POST",

                    body: JSON.stringify({
                        amount: amount,
                        card: card,
                        name: name
                    })
                }
            );


        showToast(
            result.message ||
            "✅ Pul chiqarish so‘rovi yuborildi!",
            "success"
        );


        document.getElementById(
            "withdrawAmount"
        ).value = "";

        document.getElementById(
            "withdrawCard"
        ).value = "";

        document.getElementById(
            "withdrawName"
        ).value = "";


        await loadDashboard();

    } catch (error) {

        showToast(
            "❌ " + error.message,
            "error"
        );
    }
}


// ================================
// THEME
// ================================

function toggleTheme() {

    const html =
        document.documentElement;

    const dark =
        html.classList.toggle("dark");


    localStorage.setItem(
        "chicken-theme",
        dark ? "dark" : "light"
    );


    const button =
        document.getElementById(
            "themeButton"
        );

    if (button) {

        button.textContent =
            dark ? "☀️" : "🌙";
    }


    if (tg && tg.setHeaderColor) {

        tg.setHeaderColor(
            dark
                ? "#17212b"
                : "#ffffff"
        );
    }
}


function loadTheme() {

    const saved =
        localStorage.getItem(
            "chicken-theme"
        );


    if (saved === "dark") {

        document.documentElement
            .classList.add("dark");


        const button =
            document.getElementById(
                "themeButton"
            );

        if (button) {
            button.textContent = "☀️";
        }
    }
}


// ================================
// MODAL
// ================================

function openModal(
    title,
    text,
    icon = "🐔"
) {

    const modal =
        document.getElementById("modal");

    if (!modal) return;


    document.getElementById(
        "modalIcon"
    ).textContent = icon;

    document.getElementById(
        "modalTitle"
    ).textContent = title;

    document.getElementById(
        "modalText"
    ).textContent = text;


    modal.classList.remove("hidden");
}


function closeModal() {

    const modal =
        document.getElementById("modal");

    if (modal) {
        modal.classList.add("hidden");
    }
}


// ================================
// START APP
// ================================

async function startApp() {

    initTelegram();

    loadTheme();


    const loadingScreen =
        document.getElementById(
            "loadingScreen"
        );

    const app =
        document.getElementById("app");


    try {

        if (tg && tg.initData) {

            await loadDashboard();

        } else {

            showToast(
                "⚠️ Telegram Mini App ichida oching",
                "warning"
            );
        }


        if (loadingScreen) {
            loadingScreen.classList.add("hidden");
        }

        if (app) {
            app.classList.remove("hidden");
        }

    } catch (error) {

        console.error(error);


        if (loadingScreen) {
            loadingScreen.classList.add("hidden");
        }

        if (app) {
            app.classList.remove("hidden");
        }

        showToast(
            "❌ " + error.message,
            "error"
        );
    }
}


// ================================
// DOM READY
// ================================

document.addEventListener(
    "DOMContentLoaded",
    () => {
        startApp();
    }
);


// ================================
// TELEGRAM BACK BUTTON
// ================================

if (tg && tg.BackButton) {

    tg.BackButton.onClick(() => {

        showPage("dashboard");

        tg.BackButton.hide();
    });
}


// ================================
// TELEGRAM MAIN BUTTON
// ================================

if (tg && tg.MainButton) {
    tg.MainButton.hide();
}
