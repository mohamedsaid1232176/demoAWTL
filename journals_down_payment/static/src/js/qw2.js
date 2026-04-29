///** @odoo-module **/
//
//import { rpc } from "@web/core/network/rpc";
//
//console.log("🔄 select_down_payment_payments.js loaded");
//
//// 🔹 اختر فقط journals المرتبطة بالمدفوعات اللي down_payment = true
//async function openAndToggleDownPayment(selectMode) {
//    const toggleBtn = document.querySelector('button.o-dropdown[data-all-journals-toggle="true"]');
//    if (!toggleBtn) {
//        console.error("⛔ زر All Journals مش لاقيه!");
//        return;
//    }
//
//    // افتح المنيو مؤقتًا
//    ["mousedown", "mouseup", "click"].forEach(ev =>
//        toggleBtn.dispatchEvent(new MouseEvent(ev, { bubbles: true }))
//    );
//
//    const checkMenu = setInterval(async () => {
//        const menu = document.querySelector(".o-dropdown--menu");
//        if (menu && menu.querySelector(".o-dropdown-item")) {
//            clearInterval(checkMenu);
//
//            // 🔹 جلب جميع Journals المرتبطة بمدفوعات Down Payment
//            const payments = await rpc("/web/dataset/call_kw", {
//                model: "account.payment",
//                method: "search_read",
//                args: [],
//                kwargs: {
//                    domain: [["down_payment", "=", true], ["move_id", "!=", false]],
//                    fields: ["journal_id"],
//                },
//            });
//
//            if (!payments.length) {
//                console.warn("⚠️ مفيش مدفوعات Down Payment موجودة");
//                return;
//            }
//
//            // الحصول على قائمة فريدة من journal names
//            const journalIds = [...new Set(payments.map(p => p.journal_id[0]))];
//            const journals = await rpc("/web/dataset/call_kw", {
//                model: "account.journal",
//                method: "search_read",
//                args: [],
//                kwargs: {
//                    domain: [["id", "in", journalIds]],
//                    fields: ["id", "name"],
//                },
//            });
//
//            if (!journals.length) return;
//
//            const journalNames = journals.map(j => j.name);
//            const items = menu.querySelectorAll(".o-dropdown-item");
//
//            items.forEach(item => {
//                const text = item.innerText.trim();
//                if (selectMode) {
//                    // ✅ اختار فقط Journals المرتبطة بـ Down Payment
//                    if (journalNames.some(name => text.includes(name)) && !item.classList.contains("selected")) {
//                        item.click();
//                    }
//                    // الغي أي journal غير مرتبط بـ Down Payment
//                    if (!journalNames.some(name => text.includes(name)) && item.classList.contains("selected")) {
//                        item.click();
//                    }
//                } else {
//                    // 🧹 الغي كل الاختيارات
//                    if (item.classList.contains("selected")) item.click();
//                }
//            });
//
//            console.log(
//                selectMode
//                    ? `✅ تم اختيار Journals المرتبطة بـ Down Payment فقط`
//                    : "🧹 تم إزالة كل الاختيارات"
//            );
//
//            // 🔒 اقفل القائمة مباشرة بعد التحديد
//            toggleBtn.click();
//        }
//    }, 200);
//}
//
//// 🔹 علم زرار All Journals
//function markAllJournalsButton() {
//    const btn = [...document.querySelectorAll("button.o-dropdown")]
//        .find(b => b.querySelector("i.fa-book"));
//    if (btn && !btn.hasAttribute("data-all-journals-toggle")) {
//        btn.setAttribute("data-all-journals-toggle", "true");
//        console.log("📌 زر All Journals اتعلم بـ data-attr");
//    }
//}
//
//// 🔹 Inject زر جديد جوه Posted Entries menu
//function injectDownPaymentButton() {
//    const unfoldAll = document.querySelector(".o-dropdown-item.filter_show_all_hook");
//    if (unfoldAll && !unfoldAll.parentElement.querySelector(".filter_down_payment_hook")) {
//        const newItem = document.createElement("span");
//        newItem.className = "o-dropdown-item dropdown-item o-navigable filter_down_payment_hook";
//        newItem.setAttribute("role", "menuitem");
//        newItem.setAttribute("tabindex", "0");
//        newItem.style.cursor = "pointer";
//
//        const isSelected = localStorage.getItem("down_payment_selected") === "true";
//        newItem.innerText = isSelected ? "📖 Only Down Payment Entries ✅" : "📖 Only Down Payment Entries";
//
//        newItem.addEventListener("click", async () => {
//            // Toggle state
//            const newState = !(localStorage.getItem("down_payment_selected") === "true");
//            localStorage.setItem("down_payment_selected", newState ? "true" : "false");
//            newItem.innerText = newState ? "📖 Only Down Payment Entries ✅" : "📖 Only Down Payment Entries";
//
//            // علم زر All Journals الأصلي
//            markAllJournalsButton();
//
//            // نفذ العملية
//            await openAndToggleDownPayment(newState);
//        });
//
//        unfoldAll.insertAdjacentElement("afterend", newItem);
//        console.log("✅ زر Only Down Payment Entries اتضاف جوه Posted Entries menu.");
//    }
//}
//
//// 🔹 مراقبة DOM
//function startObserver() {
//    if (!document.body) return;
//
//    const observer = new MutationObserver(() => {
//        injectDownPaymentButton();
//        markAllJournalsButton();
//    });
//
//    observer.observe(document.body, { childList: true, subtree: true });
//
//    // نادِ الدوال مباشرة عند تحميل الصفحة
//    injectDownPaymentButton();
//    markAllJournalsButton();
//}
//
//if (document.readyState === "loading") {
//    document.addEventListener("DOMContentLoaded", startObserver);
//} else {
//    startObserver();
//}


