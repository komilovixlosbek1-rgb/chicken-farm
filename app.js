```javascript
// =========================================================
// 🐔 CHICKEN FARM MINI APP
// app.js — yangi API bilan moslashtirilgan
// =========================================================

const tg = window.Telegram?.WebApp;

const API_URL =
    localStorage.getItem("CHICKEN_API_URL") ||
    "https://chicken-farm-630z.onrender.com";

let appData = null;
let appConfig = null;

let miningRemaining = 0;
let miningInterval = null;


// =========================================================
// TELEGRAM
// =========================================================

function initTelegram() {
    if (!tg) return;

    tg.ready();
    tg.expand();

    try {
        if (tg.setBackgroundColor) {
            tg.setBackgroundColor("#ffffff");
        }

        if (tg.setHeaderColor) {
            tg.setHeaderColor("#ffffff");
        }
    } catch (e) {
        console.log("Telegram UI:", e);
    }
}


// =========================================================
// TELEGRAM INIT DATA
// =========================================================

function getInitData() {
    return tg?.initData || "";
}


// =========================================================
// API REQUEST
// =========================================================

async function apiRequest(endpoint, options = {}) {

    const headers = {
        "Content-Type": "application/json",
        "X-Telegram-Init-Data": getInitData(),
        ...(options.headers || {})
    };

    let response;

    try {
        response = await fetch(
            API_URL + endpoint,
            {
                ...options,
                headers
            }
        );
    } catch (error) {
        throw new Error(
            "Server bilan bog‘lanib bo‘lmadi"
        );
    }

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


// =========================================================
// NUMBER
// =========================================================

function formatNumber(number) {

    return Number(number || 0)
        .toLocaleString("uz-UZ");
}


// =========================================================
// TOAST
// =========================================================

function showToast(
    message,
    type = "success"
) {

    const toast =
        document.getElementById("toast");

    const text =
        document.getElementById("toastText");

    const icon =
        document.getElementById("toastIcon");

    if (!toast || !text || !icon) {

        alert(message);
        return;
    }

    const icons = {
        success: "✅",
        error: "❌",
        warning: "⚠️",
        info: "ℹ️"
    };

    text.textContent = message;

    icon.textContent =
        icons[type] || "ℹ️";

    toast.className =
        "toast show " + type;

    setTimeout(() => {
        toast.classList.remove("show");
    }, 3000);
}


// =========================================================
// PAGE
// =========================================================

function showPage(page) {

    document
        .querySelectorAll(".page")
        .forEach(element => {
            element.classList.remove("active");
        });

    const target =
        document.getElementById(
            "page-" + page
        );

    if (target) {
        target.classList.add("active");
    }

    document
        .querySelectorAll(".nav-item")
        .forEach(item => {

            item.classList.remove("active");

            if (item.dataset.page === page) {
                item.classList.add("active");
            }
        });

    window.scrollTo(0, 0);


    if (
        page === "farm" ||
        page === "dashboard"
    ) {
        loadDashboard();
    }

    if (page === "eggs") {
        loadDashboard();
    }

    if (page === "mining") {
        loadMining();
    }
}


// =========================================================
// LOAD CONFIG
// =========================================================

async function loadConfig() {

    try {

        appConfig =
            await apiRequest("/api/config");

        console.log(
            "CONFIG:",
            appConfig
        );

        updateConfigUI();

        return appConfig;

    } catch (error) {

        console.error(
            "Config error:",
            error
        );

        return null;
    }
}


// =========================================================
// UPDATE CONFIG UI
// =========================================================

function updateConfigUI() {

    if (!appConfig) return;


    // -----------------------------------------
    // CHICKEN PRICES
    // -----------------------------------------

    const chickens =
        appConfig.chickens || {};


    for (let level = 1; level <= 3; level++) {

        const price =
            chickens[level]?.price;

        if (price === undefined) {
            continue;
        }


        const elements =
            document.querySelectorAll(
                `[data-chicken-price="${level}"]`
            );

        elements.forEach(element => {

            element.textContent =
                formatNumber(price) + " coin";

        });
    }


    // -----------------------------------------
    // EGG RATE
    // -----------------------------------------

    const eggRate =
        Number(
            appConfig.egg_exchange_rate || 10
        );

    document
        .querySelectorAll(
            "[data-egg-rate]"
        )
        .forEach(element => {

            element.textContent =
                `🥚 ${eggRate} tuxum = 1 coin`;

        });


    // -----------------------------------------
    // DEPOSIT MIN
    // -----------------------------------------

    const depositMin =
        Number(
            appConfig.deposit_min || 5000
        );

    document
        .querySelectorAll(
            "[data-deposit-min]"
        )
        .forEach(element => {

            element.textContent =
                formatNumber(depositMin) +
                " coin";

        });


    // -----------------------------------------
    // WITHDRAW MIN
    // -----------------------------------------

    const withdrawMin =
        Number(
            appConfig.withdraw_min || 10000
        );

    document
        .querySelectorAll(
            "[data-withdraw-min]"
        )
        .forEach(element => {

            element.textContent =
                formatNumber(withdrawMin) +
                " coin";

        });
}


// =========================================================
// DASHBOARD
// =========================================================

async function loadDashboard() {

    try {

        const data =
            await apiRequest(
                "/api/dashboard"
            );

        appData = data;


        // -----------------------------------------
        // USER
        // -----------------------------------------

        const user =
            data.user || {};

        const firstName =
            user.first_name ||
            "Fermer";


        const userName =
            document.getElementById(
                "userName"
            );

        const welcomeName =
            document.getElementById(
                "welcomeName"
            );


        if (userName) {

            userName.textContent =
                firstName;
        }


        if (welcomeName) {

            welcomeName.textContent =
                "Xush kelibsiz, " +
                firstName +
                "!";
        }


        // -----------------------------------------
        // BALANCE
        // -----------------------------------------

        const balance =
            document.getElementById(
                "balance"
            );

        if (balance) {

            balance.textContent =
                formatNumber(
                    data.balance
                );
        }


        // -----------------------------------------
        // EGGS
        // -----------------------------------------

        const eggs =
            Number(data.eggs || 0);


        const eggCount =
            document.getElementById(
                "eggCount"
            );

        if (eggCount) {

            eggCount.textContent =
                formatNumber(eggs);
        }


        const eggStorage =
            document.getElementById(
                "eggStorage"
            );

        if (eggStorage) {

            eggStorage.textContent =
                formatNumber(eggs);
        }


        // -----------------------------------------
        // CAPACITY
        // -----------------------------------------

        const capacity =
            Number(
                data.egg_capacity || 1000
            );


        const eggCapacity =
            document.getElementById(
                "eggCapacity"
            );

        if (eggCapacity) {

            eggCapacity.textContent =
                formatNumber(capacity);
        }


        const storage =
            document.getElementById(
                "storageCount"
            );

        if (storage) {

            storage.textContent =
                formatNumber(eggs) +
                "/" +
                formatNumber(capacity);
        }


        // -----------------------------------------
        // CHICKENS
        // -----------------------------------------

        const totalChickens =
            Number(
                data.total_chickens || 0
            );


        const chickenCount =
            document.getElementById(
                "chickenCount"
            );

        if (chickenCount) {

            chickenCount.textContent =
                formatNumber(
                    totalChickens
                );
        }


        // -----------------------------------------
        // EGG PROGRESS
        // -----------------------------------------

        const percentage =
            capacity > 0
                ? Math.min(
                    100,
                    (eggs / capacity) * 100
                )
                : 0;


        const progress =
            document.getElementById(
                "eggProgress"
            );

        if (progress) {

            progress.style.width =
                percentage + "%";
        }


        // -----------------------------------------
        // FARM
        // -----------------------------------------

        renderFarm(
            data.chickens || []
        );


        // -----------------------------------------
        // WITHDRAW BALANCE
        // -----------------------------------------

        const withdrawBalance =
            document.getElementById(
                "withdrawBalance"
            );

        if (withdrawBalance) {

            withdrawBalance.textContent =
                formatNumber(
                    data.balance
                ) + " coin";
        }


        // -----------------------------------------
        // PAYMENT SETTINGS
        // -----------------------------------------

        updatePaymentSettings(
            data.settings || {}
        );


    } catch (error) {

        console.error(
            "Dashboard:",
            error
        );

        showToast(
            "❌ " + error.message,
            "error"
        );
    }
}


// =========================================================
// PAYMENT SETTINGS
// =========================================================

function updatePaymentSettings(settings) {

    // Eski karta
    const card =
        settings.card_number || "";


    const paymentCard =
        document.getElementById(
            "paymentCard"
        );

    if (
        paymentCard &&
        card
    ) {

        paymentCard.textContent =
            card;
    }


    // Ethereum
    const eth =
        settings.ethereum_address ||
        settings.eth_address ||
        "";


    document
        .querySelectorAll(
            "[data-ethereum-address]"
        )
        .forEach(element => {

            element.textContent =
                eth || "Admin hali kiritmagan";

        });


    // USDT Ethereum
    const usdtEth =
        settings.usdt_ethereum_address ||
        settings.usdt_eth_address ||
        "";


    document
        .querySelectorAll(
            "[data-usdt-ethereum-address]"
        )
        .forEach(element => {

            element.textContent =
                usdtEth ||
                "Admin hali kiritmagan";

        });
}


// =========================================================
// FARM
// =========================================================

function renderFarm(chickens) {

    const container =
        document.getElementById(
            "farmList"
        );

    if (!container) return;


    if (
        !chickens ||
        chickens.length === 0
    ) {

        container.innerHTML = `

            <div class="empty-state">

                <div class="empty-icon">
                    🐔
                </div>

                <div class="empty-title">
                    Hali tovuq yo‘q
                </div>

                <div class="empty-text">
                    Fermangizni rivojlantirish
                    uchun birinchi tovuqni
                    sotib oling.
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
                Number(
                    chicken.level || 1
                );

            const count =
                Number(
                    chicken.count || 0
                );

            const production =
                (
                    rates[level] || 1
                ) * count;


            return `

                <div class="farm-card">

                    <div class="farm-chicken">
                        ${
                            icons[level] ||
                            "🐔"
                        }
                    </div>

                    <div class="farm-info">

                        <div class="farm-level">
                            Lv.${level} Tovuq
                        </div>

                        <div class="farm-count">
                            ${formatNumber(count)} ta
                        </div>

                        <div class="farm-production">
                            🥚
                            ${formatNumber(production)}
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


// =========================================================
// BUY CHICKEN
// =========================================================

async function buyChicken(level) {

    level = Number(level);


    if (
        ![1, 2, 3].includes(level)
    ) {

        showToast(
            "❌ Tovuq darajasi noto‘g‘ri",
            "error"
        );

        return;
    }


    const price =
        Number(
            appConfig?.chickens?.[
                String(level)
            ]?.price
        ) ||
        {
            1: 1000,
            2: 5000,
            3: 15000
        }[level];


    const confirmed =
        confirm(
            `Lv.${level} tovuqni ` +
            `${formatNumber(price)} coin ` +
            `ga sotib olasizmi?`
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


    } catch (error) {

        showToast(
            "❌ " + error.message,
            "error"
        );
    }
}


// =========================================================
// EGGS
// =========================================================

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
            "🥚 Tuxumlar almashtirildi!",
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


// =========================================================
// MINING
// =========================================================

async function loadMining() {

    try {

        const data =
            await apiRequest(
                "/api/mining"
            );


        miningRemaining =
            Number(
                data.remaining || 0
            );


        updateMiningUI();


        if (miningInterval) {

            clearInterval(
                miningInterval
            );
        }


        miningInterval =
            setInterval(() => {

                if (
                    miningRemaining > 0
                ) {

                    miningRemaining--;

                    updateMiningUI();

                } else {

                    updateMiningUI();
                }

            }, 1000);


    } catch (error) {

        console.error(
            "Mining:",
            error
        );


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


// =========================================================
// MINING UI
// =========================================================

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


    const bonus =
        Number(
            appConfig?.mining?.bonus ||
            100
        );


    if (
        miningRemaining <= 0
    ) {

        timer.textContent =
            "🎉 Bonus tayyor!";


        button.disabled = false;

        button.textContent =
            `🎁 ${formatNumber(bonus)} Coin olish`;

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
        `Keyingi bonus: ` +
        `${String(hours).padStart(2, "0")}:` +
        `${String(minutes).padStart(2, "0")}:` +
        `${String(seconds).padStart(2, "0")}`;
}


// =========================================================
// CLAIM MINING
// =========================================================

async function claimMining() {

    if (
        miningRemaining > 0
    ) {
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
            "🎉 Mining bonusi olindi!",
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


// =========================================================
// DEPOSIT
// =========================================================

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


    const minimum =
        Number(
            appConfig?.deposit_min ||
            5000
        );


    if (
        !amount ||
        amount < minimum
    ) {

        showToast(
            `❌ Minimal depozit ` +
            `${formatNumber(minimum)} coin`,
            "error"
        );

        return;
    }


    try {

        showToast(
            "⏳ Depozit yuborilmoqda...",
            "info"
        );


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


        const amountInput =
            document.getElementById(
                "depositAmount"
            );

        const proofInput =
            document.getElementById(
                "depositProof"
            );


        if (amountInput) {
            amountInput.value = "";
        }


        if (proofInput) {
            proofInput.value = "";
        }


    } catch (error) {

        showToast(
            "❌ " + error.message,
            "error"
        );
    }
}


// =========================================================
// WITHDRAW
// =========================================================

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


    const minimum =
        Number(
            appConfig?.withdraw_min ||
            10000
        );


    if (
        !amount ||
        amount < minimum
    ) {

        showToast(
            `❌ Minimal chiqarish ` +
            `${formatNumber(minimum)} coin`,
            "error"
        );

        return;
    }


    if (!card) {

        showToast(
            "❌ Karta yoki kripto manzilini kiriting",
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

        showToast(
            "⏳ Withdraw yuborilmoqda...",
            "info"
        );


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
            "✅ Withdraw so‘rovi yuborildi!",
            "success"
        );


        const amountInput =
            document.getElementById(
                "withdrawAmount"
            );

        const cardInput =
            document.getElementById(
                "withdrawCard"
            );

        const nameInput =
            document.getElementById(
                "withdrawName"
            );


        if (amountInput) {
            amountInput.value = "";
        }

        if (cardInput) {
            cardInput.value = "";
        }

        if (nameInput) {
            nameInput.value = "";
        }


        await loadDashboard();


    } catch (error) {

        showToast(
            "❌ " + error.message,
            "error"
        );
    }
}


// =========================================================
// THEME
// =========================================================

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


    try {

        if (
            tg &&
            tg.setHeaderColor
        ) {

            tg.setHeaderColor(
                dark
                    ? "#17212b"
                    : "#ffffff"
            );
        }

    } catch (e) {}
}


// =========================================================
// LOAD THEME
// =========================================================

function loadTheme() {

    const saved =
        localStorage.getItem(
            "chicken-theme"
        );


    if (
        saved === "dark"
    ) {

        document.documentElement
            .classList.add("dark");


        const button =
            document.getElementById(
                "themeButton"
            );


        if (button) {

            button.textContent =
                "☀️";
        }
    }
}


// =========================================================
// MODAL
// =========================================================

function openModal(
    title,
    text,
    icon = "🐔"
) {

    const modal =
        document.getElementById(
            "modal"
        );


    if (!modal) return;


    const modalIcon =
        document.getElementById(
            "modalIcon"
        );

    const modalTitle =
        document.getElementById(
            "modalTitle"
        );

    const modalText =
        document.getElementById(
            "modalText"
        );


    if (modalIcon) {
        modalIcon.textContent = icon;
    }


    if (modalTitle) {
        modalTitle.textContent = title;
    }


    if (modalText) {
        modalText.textContent = text;
    }


    modal.classList.remove(
        "hidden"
    );
}


// =========================================================
// CLOSE MODAL
// =========================================================

function closeModal() {

    const modal =
        document.getElementById(
            "modal"
        );


    if (modal) {

        modal.classList.add(
            "hidden"
        );
    }
}


// =========================================================
// AUTH
// =========================================================

async function authenticate() {

    try {

        const result =
            await apiRequest(
                "/api/auth",
                {
                    method: "POST"
                }
            );


        console.log(
            "AUTH:",
            result
        );


        return result;


    } catch (error) {

        console.error(
            "Auth error:",
            error
        );

        throw error;
    }
}


// =========================================================
// START APP
// =========================================================

async function startApp() {

    initTelegram();

    loadTheme();


    const loadingScreen =
        document.getElementById(
            "loadingScreen"
        );


    const app =
        document.getElementById(
            "app"
        );


    try {

        if (
            !tg ||
            !tg.initData
        ) {

            if (loadingScreen) {
                loadingScreen.classList.add(
                    "hidden"
                );
            }

            if (app) {
                app.classList.remove(
                    "hidden"
                );
            }

            showToast(
                "⚠️ Mini App'ni Telegram ichida oching",
                "warning"
            );

            return;
        }


        // 1. AUTH

        await authenticate();


        // 2. CONFIG

        await loadConfig();


        // 3. DASHBOARD

        await loadDashboard();


        // 4. UI

        if (loadingScreen) {

            loadingScreen.classList.add(
                "hidden"
            );
        }


        if (app) {

            app.classList.remove(
                "hidden"
            );
        }


    } catch (error) {

        console.error(
            "START APP ERROR:",
            error
        );


        if (loadingScreen) {

            loadingScreen.classList.add(
                "hidden"
            );
        }


        if (app) {

            app.classList.remove(
                "hidden"
            );
        }


        showToast(
            "❌ " + error.message,
            "error"
        );
    }
}


// =========================================================
// DOM READY
// =========================================================

document.addEventListener(
    "DOMContentLoaded",
    () => {

        startApp();

    }
);


// =========================================================
// TELEGRAM BACK BUTTON
// =========================================================

if (
    tg &&
    tg.BackButton
) {

    tg.BackButton.onClick(
        () => {

            showPage("dashboard");

            tg.BackButton.hide();

        }
    );
}


// =========================================================
// TELEGRAM MAIN BUTTON
// =========================================================

if (
    tg &&
    tg.MainButton
) {

    tg.MainButton.hide();
}


// =========================================================
// GLOBAL EXPORT
// HTML onclick uchun kerak
// =========================================================

window.showPage =
    showPage;

window.buyChicken =
    buyChicken;

window.exchangeEggs =
    exchangeEggs;

window.loadMining =
    loadMining;

window.claimMining =
    claimMining;

window.makeDeposit =
    makeDeposit;

window.makeWithdraw =
    makeWithdraw;

window.toggleTheme =
    toggleTheme;

window.openModal =
    openModal;

window.closeModal =
    closeModal;

window.loadDashboard =
    loadDashboard;

window.loadConfig =
    loadConfig;
```

