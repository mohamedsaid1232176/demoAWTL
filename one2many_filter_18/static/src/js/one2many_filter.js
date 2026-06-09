/** @odoo-module **/

import { registry } from "@web/core/registry";

function injectFilterBox(one2manyDiv) {
    if (one2manyDiv.querySelector(".o_one2many_filter_box")) return;

    let tagValues = {};

    /* ---- CSS (merged UI from version 1) ---- */
    const style = document.createElement("style");
    style.innerHTML = `
        .o_filter_header_custom {
            background:#7B3FE4;
            color:white;
            padding:10px 14px;
            font-weight:600;
            display:flex;
            justify-content:space-between;
            align-items:center;
            cursor:pointer;
            border-radius:8px 8px 0 0;
        }
        .o_filter_body_custom {
            overflow:hidden;
            transition:max-height .3s ease;
            max-height:0;
        }
        .o_filter_body_custom.open {
            max-height:900px !important;
        }

        .floating_dropdown_panel {
            position:absolute !important;
            z-index:999999 !important;
            width:260px;
        }

        .o_filter_row {
            display:flex;
            gap:20px;
            align-items:flex-end;
            flex-wrap:wrap;
        }

        /* ⭐ NEW INPUTS FROM VERSION 1 ⭐ */

        .tag-pill {
            background:#eee8ff;
            padding:4px 8px;
            border-radius:8px;
            display:flex;
            align-items:center;
            gap:6px;
            font-size:12px;
            color:#333;
        }
        .tag-pill i { cursor:pointer; font-size:11px; }

        .value-tag {
            background:#f3f0ff;
            padding:6px 8px;
            border-radius:8px;
            border:1px solid #d7d0ff;
            display:flex;
            align-items:center;
            gap:6px;
            font-size:12px;
        }

        .value-tag select.tag-operator {
            padding:3px 6px;
            width:110px;
            height:26px;
            font-size:12px;
            border-radius:6px;
        }

        .value-tag input.tag-input {
            padding:4px 6px;
            width:120px;
            height:26px;
            font-size:12px;
            border-radius:6px;
            background:white;
        }
    `;
    document.head.appendChild(style);

    /* ---- MAIN BOX ---- */
    const box = document.createElement("div");
    box.className = "o_one2many_filter_box";
    box.style.cssText = `background:white; border:1px solid #ddd; border-radius:8px; margin-bottom:10px;`;

    box.innerHTML = `
        <div class="o_filter_header_custom">
            <span><i class="fa fa-filter"></i> Component Filters</span>
            <i class="fa fa-chevron-down o_filter_toggle_icon"></i>
        </div>

        <div class="o_filter_body_custom">
            <div class="o_filter_row" style="padding:15px;">

                <!-- FIELD -->
                <div class="o_field_dropdown_custom" style="position:relative; min-width:260px;">
                    <label style="font-size:12px;">Field</label>
                    <div class="o_select_box"
                        style="border:1px solid #bbb; padding:6px 8px; border-radius:8px;
                            min-height:36px; display:flex; flex-wrap:wrap; gap:6px;
                            background:#fafaff;">
                        <span class="o_placeholder" style="color:#888;">Select Fields</span>
                    </div>

                    <div class="o_dropdown_panel"
                        style="background:#fff; border:1px solid #ccc; border-radius:8px;
                               display:none; max-height:260px; overflow:hidden;">
                        <input type="text" placeholder="Search fields..."
                            class="o_dropdown_search"
                            style="width:100%; padding:8px; border:none; border-bottom:1px solid #eee;">
                        <ul class="o_dropdown_list"
                            style="list-style:none; padding:0; margin:0; max-height:200px; overflow:auto;">
                        </ul>
                    </div>
                </div>

                <!-- VALUES -->
                <div style="display:flex; flex-direction:column; min-width:300px;">
                    <label style="font-size:12px;">Values</label>
                    <div class="o_filter_value_box"
                        style="min-width:300px; border:1px solid #ccc; border-radius:8px;
                               padding:6px; min-height:36px; display:flex; flex-wrap:wrap;
                               gap:6px; background:#fafaff;">
                    </div>
                </div>

                <!-- LOGIC -->
                <div style="display:flex; flex-direction:column;">
                    <label style="font-size:12px;">Logic</label>
                    <select class="o_filter_logic form-select"
                        style="min-width:80px; border-radius:6px;">
                        <option>AND</option><option>OR</option>
                    </select>
                </div>

                <!-- BUTTONS -->
                <div style="display:flex; align-items:flex-end; gap:10px;">
                    <button class="btn btn-primary o_apply_one2many_filter">
                        <i class="fa fa-search"></i> Filter
                    </button>
                    <button class="btn btn-secondary o_reset_one2many_filter">
                        <i class="fa fa-undo"></i> Reset
                    </button>
                </div>

            </div>
        </div>
    `;

    one2manyDiv.prepend(box);

    /* ---- COLLAPSE ---- */
    const body   = box.querySelector(".o_filter_body_custom");
    const icon   = box.querySelector(".o_filter_toggle_icon");
    const header = box.querySelector(".o_filter_header_custom");

    header.onclick = () => {
        const opened = body.classList.contains("open");
        if (opened) {
            body.classList.remove("open");
            icon.className = "fa fa-chevron-down o_filter_toggle_icon";
        } else {
            body.classList.add("open");
            icon.className = "fa fa-chevron-up o_filter_toggle_icon";
        }
    };

    /* ---- FLOATING DROPDOWN ---- */
    const panel     = box.querySelector(".o_dropdown_panel");
    const selectBox = box.querySelector(".o_select_box");

    let extracted = false;

    function showFloatingPanel() {
        if (!extracted) {
            panel.classList.add("floating_dropdown_panel");
            document.body.appendChild(panel);
            extracted = true;
        }

        const rect = selectBox.getBoundingClientRect();
        panel.style.display = "block";
        panel.style.left = rect.left + "px";
        panel.style.top  = rect.bottom + 4 + "px";
        panel.style.width = rect.width + "px";
    }

    function hideFloatingPanel() {
        panel.style.display = "none";
    }

    selectBox.addEventListener("click", e => {
        e.stopPropagation();
        showFloatingPanel();
    });

document.addEventListener("click", e => {
        if (!panel.contains(e.target) && !selectBox.contains(e.target)) hideFloatingPanel();
    });

    /* ---- LIST + SEARCH ---- */
    const list     = panel.querySelector(".o_dropdown_list");
    const search   = panel.querySelector(".o_dropdown_search");
    const valueBox = box.querySelector(".o_filter_value_box");

    function fillFields() {
        const headerCells = one2manyDiv.querySelectorAll("thead th");
        if (!headerCells.length) return setTimeout(fillFields, 60);

        list.innerHTML = "";
        headerCells.forEach((th, idx) => {
            const name = th.innerText.trim();
            if (!name) return;

            const li = document.createElement("li");
            li.style = "padding:6px 10px; cursor:pointer;";
            li.innerHTML = `<input type="checkbox" class="o_field_option" value="${idx}"> ${name}`;
            list.appendChild(li);
        });
    }
    fillFields();

    search.oninput = () => {
        const t = search.value.toLowerCase();
        [...list.children].forEach(li =>
            li.style.display = li.innerText.toLowerCase().includes(t) ? "" : "none"
        );
    };

    /* ---- VALUE TAGS (from version 1 UI) ---- */
    list.onclick = () => {
        tagValues = {};
        valueBox.innerHTML = "";
        selectBox.innerHTML = "";

        const checked = [...panel.querySelectorAll(".o_field_option:checked")]
            .map(c => c.parentElement.innerText.trim());

        if (!checked.length)
            selectBox.innerHTML = `<span class="o_placeholder" style="color:#888;">Select Fields</span>`;

        checked.forEach(field => {
            const pill = document.createElement("span");
            pill.className = "tag-pill";
            pill.innerHTML = `${field} <i class="fa fa-times"></i>`;
            pill.querySelector("i").onclick = () => {
                panel.querySelectorAll(".o_field_option").forEach(opt => {
                    if (opt.parentElement.innerText.trim() === field)
                        opt.checked = false;
                });
                pill.remove();
                list.onclick();
            };
            selectBox.appendChild(pill);

            tagValues[field] = { operator: "contains", value: "" };

            const tag = document.createElement("span");
            tag.className = "value-tag";
            tag.innerHTML = `
                ${field}:
                <select class="tag-operator">
                    <option value="contains">contains</option>
                    <option value="=">=</option>
                    <option value="!=">!=</option>
                    <option value="gt">></option>
                    <option value="lt"><</option>
                </select>
                <input class="tag-input" placeholder="value">
                <i class="fa fa-times remove-tag"></i>
            `;

            tag.querySelector(".tag-operator").onchange = e =>
                tagValues[field].operator = e.target.value;

            tag.querySelector(".tag-input").oninput = e =>
                tagValues[field].value = e.target.value.toLowerCase().trim();

            tag.querySelector(".remove-tag").onclick = () => {
                delete tagValues[field];
                tag.remove();
                pill.remove();
            };

            valueBox.appendChild(tag);
        });
    };

    /* ---- APPLY ---- */
    box.querySelector(".o_apply_one2many_filter").onclick = () => {
        const rows   = one2manyDiv.querySelectorAll("tbody tr");
        const header = one2manyDiv.querySelectorAll("thead th");
        const logic  = box.querySelector(".o_filter_logic").value;

        rows.forEach(row => {
            const cells = [...row.querySelectorAll("td")]
                .map(td => td.innerText.toLowerCase().trim());

            const checks = [];

            for (const field in tagValues) {
                const { operator, value } = tagValues[field];
                if (!value) continue;

                const index = [...header].findIndex(h => h.innerText.trim() === field);
                if (index === -1) continue;

                const cellVal = cells[index] || "";
                let match = false;

                switch (operator) {
                    case "=":  match = (cellVal === value); break;
                    case "!=": match = (cellVal !== value); break;
                    case "gt": match = (parseFloat(cellVal) > parseFloat(value)); break;
                    case "lt": match = (parseFloat(cellVal) < parseFloat(value)); break;
                    case "contains": match = cellVal.includes(value); break;
                }

                checks.push(match);
            }

            const result = logic === "AND"
                ? checks.every(r => r)
                : checks.some(r => r);

            row.style.display = result ? "" : "none";
        });
    };

    /* ---- RESET ---- */
    box.querySelector(".o_reset_one2many_filter").onclick = () => {
        tagValues = {};
        valueBox.innerHTML = "";
        selectBox.innerHTML = `<span class="o_placeholder" style="color:#888;">Select Fields</span>`;
        panel.querySelectorAll(".o_field_option").forEach(opt => opt.checked = false);
        one2manyDiv.querySelectorAll("tbody tr").forEach(r => r.style.display = "");
    };
}

function enableGlobalOne2ManyFilter() {
    const observer = new MutationObserver(m => {
        m.forEach(mu =>
            mu.addedNodes.forEach(node => {
                if (!(node instanceof HTMLElement)) return;

                if (node.classList.contains("o_field_one2many"))
                    injectFilterBox(node);

                node.querySelectorAll?.(".o_field_one2many")
                    .forEach(div => injectFilterBox(div));
            })
        );
    });

    observer.observe(document.body, { childList: true, subtree: true });
}

registry.category("services").add("One2ManyFilterService", {
    start() { enableGlobalOne2ManyFilter(); },
});