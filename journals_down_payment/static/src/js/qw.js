///** @odoo-module **/
//
//import { rpc } from "@web/core/network/rpc";
//
//console.log("🔄 partner_ledger_filter.js loaded (Dynamic Down Payment Journal)");
//
//// ✅ افتح All Journals dropdown واعمل logic
//async function openAndToggleAllJournals(selectMode, callback) {
//    const toggleBtn = document.querySelector('button.o-dropdown[data-all-journals-toggle="true"]');
//    if (!toggleBtn) {
//        console.error("⛔ زر All Journals مش لاقيه!");
//        return;
//    }
//
//    // افتح المنيو (simulate click)
//    ["mousedown", "mouseup", "click"].forEach(ev =>
//        toggleBtn.dispatchEvent(new MouseEvent(ev, { bubbles: true }))
//    );
//
//    const checkMenu = setInterval(async () => {
//        const menu = document.querySelector(".o-dropdown--menu");
//        if (menu && menu.querySelector(".o-dropdown-item")) {
//            clearInterval(checkMenu);
//
//            // 🟢 هات الجورنال اللي down_payment = true
//            const [downJournal] = await rpc("/web/dataset/call_kw", {
//                model: "account.journal",
//                method: "search_read",
//                args: [],
//                kwargs: {
//                    domain: [["down_payment", "=", true]],
//                    fields: ["id", "name"],
//                    limit: 1,
//                },
//            });
//
//            if (!downJournal) {
//                console.warn("⚠️ مفيش جورنال عنده down_payment = true");
//                return;
//            }
//
//            const items = menu.querySelectorAll(".o-dropdown-item");
//            items.forEach(item => {
//                const text = item.innerText.trim();
//
//                if (selectMode) {
//                    // ✅ نخلي بس الجورنال اللي جبناه متعلم
//                    if (text.includes(downJournal.name) && !item.classList.contains("selected")) {
//                        item.click();
//                    }
//                    if (!text.includes(downJournal.name) && item.classList.contains("selected")) {
//                        item.click();
//                    }
//                } else {
//                    // 🧹 عكس العملية: نشيل كل الاختيارات
//                    if (item.classList.contains("selected")) {
//                        item.click();
//                    }
//                }
//            });
//
//            console.log(
//                selectMode
//                    ? `✅ متعلم بس الجورنال: ${downJournal.name}`
//                    : "🧹 اتشالت كل الاختيارات!"
//            );
//
//            if (callback) callback();
//        }
//    }, 200);
//}
//
//// ✅ علم زرار All Journals أول ما يظهر
//function markAllJournalsButton() {
//    const btn = [...document.querySelectorAll("button.o-dropdown")]
//        .find(b => b.querySelector("i.fa-book")); // 👈 نحدد الزر من الأيقونة
//    if (btn && !btn.hasAttribute("data-all-journals-toggle")) {
//        btn.setAttribute("data-all-journals-toggle", "true");
//        console.log("📌 زر All Journals اتعلم بـ data-attr");
//    }
//}
//
//// ✅ Inject زر جوة Posted Entries menu
//function injectAllJournalsButton() {
//    const unfoldAll = document.querySelector(".o-dropdown-item.filter_show_all_hook");
//    if (unfoldAll && !unfoldAll.parentElement.querySelector(".filter_all_journals_hook")) {
//        const newItem = document.createElement("span");
//        newItem.className = "o-dropdown-item dropdown-item o-navigable filter_all_journals_hook";
//        newItem.setAttribute("role", "menuitem");
//        newItem.setAttribute("tabindex", "0");
//        newItem.style.cursor = "pointer";
//
//        // اقرأ الحالة من localStorage
//        const isSelected = localStorage.getItem("all_journals_selected") === "true";
//        newItem.innerText = isSelected ? "📖 Down Payment Journal ✅" : "📖 Down Payment Journal";
//
//        newItem.addEventListener("click", () => {
//            // ✅ اقفل منيو Posted Entries
//            const postedEntriesMenu = newItem.closest(".o-dropdown--menu");
//            if (postedEntriesMenu) {
//                const parentDropdown = postedEntriesMenu.closest(".o-dropdown");
//                if (parentDropdown) {
//                    const toggle = parentDropdown.querySelector("button");
//                    if (toggle) toggle.click();
//                }
//            }
//
//            // ✅ علم زر All Journals الأصلي
//            markAllJournalsButton();
//
//            // 🔄 Toggle state
//            const newState = !(localStorage.getItem("all_journals_selected") === "true");
//            localStorage.setItem("all_journals_selected", newState ? "true" : "false");
//
//            // ✅ نفذ العملية
//            openAndToggleAllJournals(newState, () => {
//                newItem.innerText = newState
//                    ? "📖 Down Payment Journal ✅"
//                    : "📖 Down Payment Journal";
//            });
//        });
//
//        unfoldAll.insertAdjacentElement("afterend", newItem);
//        console.log("✅ زر Down Payment Journal اتضاف جوه Posted Entries menu.");
//    }
//}
//
//// ✅ مراقبة DOM
//function startObserver() {
//    if (!document.body) return;
//
//    const observer = new MutationObserver(() => {
//        injectAllJournalsButton();
//        markAllJournalsButton();
//    });
//
//    observer.observe(document.body, { childList: true, subtree: true });
//
//    // ناديلهم مرة مبدئية
//    injectAllJournalsButton();
//    markAllJournalsButton();
//}
//
//if (document.readyState === "loading") {
//    document.addEventListener("DOMContentLoaded", startObserver);
//} else {
//    startObserver();
//}