# waehlbaer/UI.py
from reprlib import aRepr
from typing import Dict, List, Optional

from nicegui import ui

from IO import (
    export_block_to_pdf,
    export_to_pdf,
    load_blocklist,
    load_unitlist,
    read_from_xlsx,
    write_to_xlsx,
    NA_map,
    flache_map
)
from main import (
    add_bogenscheissen_series,
    add_dusche_series,
    add_feuerwehr_series,
    add_nacht_series,
    add_wald_series,
)

# Project imports (keep these so the UI can use your existing data structures)
from Wählbär import Allocation, Block, MetaBlock

# Days (14) and slots (5)
DAYS = [
    "So 12.7",
    "Mo 13.7",
    "Di 14.7",
    "Mi 15.7",
    "Do 16.7",
    "Fr 17.7",
    "Sa 18.7",
    "So 19.7",
    "Mo 20.7",
    "Di 21.7",
    "Mi 22.7",
    "Do 23.7",
    "Fr 24.7",
    "Sa 25.7",
]
SLOTS = ["Vormittag", "Nachmittag 1", "Nachmittag 2", "Abend", "Nacht"]  # 5 slots

# color maps
group_colors = {"wo": "#00b48f", "pf": "#4f2c1d", "pi": "#c6464a", "pt": "#e87928"}

block_category_colors = {
    "anlass": {"bg": "#000000", "fg": "#ffffff"},
    "ausflug": {"bg": "#f2c966", "fg": "#000000"},
    "wanderung": {"bg": "#00b48f", "fg": "#000000"},
    "sportaktivitat": {"bg": "#c6464a", "fg": "#000000"},
    "programmflache": {"bg": "#e87928", "fg": "#000000"},
    "wald": {"bg": "#e87928", "fg": "#000000"},
    "nacht": {"bg": "#e87928", "fg": "#000000"},
    "wasser": {"bg": "#608ee4", "fg": "#000000"},
    "flussbaden": {"bg": "#608ee4", "fg": "#000000"},
    "si-mo": {"bg": "#608ee4", "fg": "#000000"},
    "dusche": {"bg": "#608ee4", "fg": "#000000"},
    "workshop": {"bg": "#4f2c1d", "fg": "#ffffff"},
}

def block_button_name(ID):
    if ID.startswith("ON-05") and len(ID) == 7:
        return NA_map(ID)
    elif ID.startswith("ON-08") and len(ID) == 7:
        return flache_map(ID)
    else:
        return ID

class LeftDockApp:
    """
    App with left dock and three views:
    - Einheiten: top shows schedule for selected unit, an Export PDF button, bottom shows unit buttons
    - Blöcke: top shows schedule for selected block (which units visit which slots),
              bottom shows block buttons (only for active blocks) and an Export PDF button
    - Auflistung: top shows list of units for currently selected slot,
                  bottom shows a slot-picker table (each cell selects a slot)

    Additional features:
    - Per-cell edit button in Einheiten view opens a block picker dialog with checkboxes
    - Change log records every allocation change in human-readable German
    - Save dialog shows the full change log and requires confirmation before writing
    - Edit dialogs for unit and block schedules (text-based)
    - Staging of changes in `pending_changes` (not applied immediately)
    - Review dialog summarizing pending changes and a Confirm button to apply them
    """

    def __init__(self, allocation: Optional[Allocation] = None):
        self.allocation = allocation
        self.current_unit = None
        self.current_block = None

        # store NiceGUI button objects for highlighting (if supported)
        self.unit_buttons: Dict[str, object] = {}
        self.block_buttons: Dict[str, object] = {}

        # store slot buttons for "Auflistung pro Slot"
        self.slot_buttons: Dict[str, object] = {}

        # base CSS class names that we assigned to buttons (so we can reset)
        self.unit_button_base_classes: Dict[str, str] = {}
        self.block_button_base_classes: Dict[str, str] = {}
        self.slot_button_base_classes: Dict[str, str] = {}

        # currently selected slot for Auflistung view (default first day, first slot)
        self.selected_slot: str = "A0"

        # Pending changes staged by the user
        self.pending_changes: List[dict] = []

        # Change log: human-readable German strings of every applied allocation change
        self.change_log: List[str] = []

        # Build layout: sidebar + main area
        with ui.row().style("height: 100vh; gap: 0;"):
            # sidebar
            with ui.column().style(
                "width: 280px; min-width: 240px; background: #f5f7fa; padding: 12px; gap: 12px;"
            ) as self.sidebar:
                ui.markdown("**Navigation**").style("margin-bottom: 6px;")
                ui.button(
                    "Einheiten", on_click=lambda: self.show_view("einheiten")
                ).props("unelevated").style(
                    "width: 100%; min-height: 44px; text-align: left; padding-left: 12px;"
                )
                ui.button("Blöcke", on_click=lambda: self.show_view("blocke")).props(
                    "unelevated"
                ).style(
                    "width: 100%; min-height: 44px; text-align: left; padding-left: 12px;"
                )
                ui.button(
                    "Auflistung pro Slot", on_click=lambda: self.show_view("auflistung")
                ).props("unelevated").style(
                    "width: 100%; min-height: 44px; text-align: left; padding-left: 12px;"
                )
                ui.button(
                    "Speichern...",
                    on_click=lambda e=None: self.open_save_dialog(),
                ).props("unelevated").style(
                    "width: 100%; min-height: 44px; text-align: left; padding-left: 12px; background:#f3f4f6;"
                ).props("color=orange")
                ui.separator()
                ui.label("Status: ready").classes("text-xs")

            # main area
            with ui.column().style(
                "flex: 1; padding: 18px; gap: 12px;"
            ) as self.main_area:
                ui.markdown("# Wählbär - Wählbares Programm")
                ui.label("Wähle eine Ansicht in der linken Leiste.")

                # --- Einheiten view ---
                with ui.column().style("gap: 8px;") as self.view_einheiten:
                    ui.html('<div id="einheiten-title"><h3>Einheiten</h3></div>')

                    # schedule container (for unit)
                    initial_table = self._build_table_html({}, editable=False)
                    ui.html(
                        f'<div id="schedule-table" style="width:100%;">{initial_table}</div>'
                    ).style(
                        "width: 100%; height: 45vh; overflow: auto; border: 1px solid #ddd;"
                    )

                    # actions for unit view
                    with ui.row().style("gap: 8px;"):
                        ui.button(
                            "Export PDF",
                            on_click=lambda e=None: self.export_current_unit_pdf(),
                        ).props("unelevated").style("min-width:140px;")
                        # ui.button(
                        #     "Edit Schedule",
                        #     on_click=lambda e=None: self.open_unit_edit_dialog(),
                        # ).props("unelevated").style("min-width:140px;")
                        # ui.button(
                        #     "Review & Save",
                        #     on_click=lambda e=None: self.open_review_dialog(),
                        # ).props("unelevated").style("min-width:140px;")

                    # unit buttons
                    with ui.card().style("padding: 8px; height: 40vh; overflow: auto;"):
                        ui.label("Einheiten:")
                        with ui.row().style("flex-wrap: wrap; gap: 8px;"):
                            if self.allocation is not None:
                                for unit in getattr(self.allocation, "UNITS", []):
                                    # print(f"creating button for unit: {unit.ID}")
                                    group = getattr(unit, "group", "") or ""
                                    base_class = (
                                        f"unit-btn group-{group}"
                                        if group
                                        else "unit-btn"
                                    )
                                    btn_id = f"unit-btn-{unit.ID}"
                                    btn = ui.button(str(unit.ID)).props(f"id:{btn_id}")
                                    self.unit_button_base_classes[unit.ID] = base_class

                                    def make_u_handler(u, btn_ref):
                                        return lambda e=None: self.select_unit(
                                            u, btn_ref
                                        )

                                    btn.on("click", make_u_handler(unit, btn))
                                    try:
                                        self.unit_buttons[unit.ID] = btn
                                    except Exception:
                                        pass

                                    try:
                                        ui.run_javascript(
                                            f"var el = document.getElementById('{btn_id}'); if (el) el.className = '{base_class}';"
                                        )
                                    except Exception:
                                        pass

                # --- Blöcke view ---
                with ui.column().style("gap: 8px;") as self.view_blocke:
                    ui.html('<div id="blocke-title"><h3>Blöcke</h3></div>')

                    initial_table_b = self._build_table_html({})
                    ui.html(
                        f'<div id="schedule-table-block" style="width:100%;">{initial_table_b}</div>'
                    ).style(
                        "width: 100%; height: 45vh; overflow: auto; border: 1px solid #ddd;"
                    )

                    with ui.row().style("gap: 8px;"):
                        ui.button(
                            "Export PDF",
                            on_click=lambda e=None: self.export_current_block_pdf(),
                        ).props("unelevated").style("min-width:140px;")
                        # ui.button(
                        #     "Edit Schedule",
                        #     on_click=lambda e=None: self.open_block_edit_dialog(),
                        # ).props("unelevated").style("min-width:140px;")
                        # ui.button(
                        #     "Review & Save",
                        #     on_click=lambda e=None: self.open_review_dialog(),
                        # ).props("unelevated").style("min-width:140px;")

                    with ui.card().style("padding: 8px; height: 40vh; overflow: auto;"):
                        ui.label("Blöcke:")
                        with ui.row().style("flex-wrap: wrap; gap: 8px;"):
                            if self.allocation is not None:
                                for block in getattr(self.allocation, "BLOCKS", []):
                                    try:
                                        if hasattr(block, "is_active") and not getattr(
                                            block, "is_active", True
                                        ):
                                            continue
                                    except Exception:
                                        pass
                                    group = ""
                                    try:
                                        group = block.data.get("group", "") or ""
                                    except Exception:
                                        group = ""
                                    base_class = (
                                        f"unit-btn group-{group}"
                                        if group
                                        else "unit-btn"
                                    )
                                    btn_id = f"block-btn-{block.ID}"

                                    btn = ui.button(block_button_name(str(block.ID))).props(f"id:{btn_id}")
                                    self.block_button_base_classes[block.ID] = (
                                        base_class
                                    )

                                    def make_b_handler(b, btn_ref):
                                        return lambda e=None: self.select_block(
                                            b, btn_ref
                                        )

                                    btn.on("click", make_b_handler(block, btn))
                                    try:
                                        self.block_buttons[block.ID] = btn
                                    except Exception:
                                        pass

                                    try:
                                        ui.run_javascript(
                                            f"var el = document.getElementById('{btn_id}'); if (el) el.className = '{base_class}';"
                                        )
                                    except Exception:
                                        pass

                # --- Auflistung pro Slot ---
                with ui.column().style("gap: 8px;") as self.view_auflistung:
                    ui.html(
                        f'<div id="auflistung-title"><h3>Auflistung für Slot {DAYS[0]} {SLOTS[0]}</h3></div>'
                    )

                    with ui.card().style(
                        "padding: 12px; height: 45vh; overflow: auto;"
                    ):
                        ui.label("Einheiten in gewähltem Slot:")
                        initial_list_html = self._build_unit_list_html(
                            self.selected_slot
                        )
                        ui.html(
                            f'<div id="slot-list" style="width:100%">{initial_list_html}</div>'
                        )

                    with ui.card().style("padding: 8px; height: 40vh; overflow: auto;"):
                        ui.label("Slot wählen:")
                        with ui.row().style("gap: 0; align-items: stretch;"):
                            ui.label("").style("width:120px; min-width:120px;")
                            for _day in DAYS:
                                ui.label(_day).style(
                                    "flex: 1; min-width:100px; max-width:100px; text-overflow:ellipsis; overflow:hidden; white-space:nowrap; padding:6px; border:1px solid #eee; background:#fafafa;"
                                )

                        if self.allocation is not None:
                            for slot_index, slot_label in enumerate(SLOTS):
                                with ui.row().style("gap: 0; align-items: stretch;"):
                                    ui.label(slot_label).style(
                                        "width:120px; min-width:120px; padding:6px; border:1px solid #eee; background:#fafafa; font-weight:600;"
                                    )
                                    for col_index, _day in enumerate(DAYS):
                                        slot_id = f"{chr(65 + col_index)}{slot_index}"
                                        btn_id = f"slot-btn-{slot_id}"
                                        btn = (
                                            ui.button("")
                                            .props(f"id:{btn_id}")
                                            .style(
                                                "flex: 1; min-width:100px; max-width:100px; height:44px; margin:0; border-radius:4px; padding:6px;"
                                            )
                                        )

                                        def make_slot_handler(sid):
                                            return lambda e=None: self.select_slot(sid)

                                        btn.on("click", make_slot_handler(slot_id))
                                        try:
                                            self.slot_buttons[slot_id] = btn
                                        except Exception:
                                            pass

                                        try:
                                            ui.run_javascript(
                                                f"var el = document.getElementById('{btn_id}'); if (el) el.className = 'slot-btn';"
                                            )
                                        except Exception:
                                            pass

        print("UI initialized with sidebar and main area, views created.")

        self._views = {
            "einheiten": self.view_einheiten,
            "blocke": self.view_blocke,
            "auflistung": self.view_auflistung,
        }

        self.show_view("einheiten")

        ui.add_head_html(
            """<style>
            .unit-btn, .unit-btn .q-btn, .unit-btn .q-btn__content, .unit-btn .q-btn__label {
                color: white !important;
                border-radius: 6px !important;
                padding: 6px 10px !important;
                border: none !important;
                display: inline-flex !important;
                align-items: center !important;
                justify-content: center !important;
                min-width: 44px !important;
                cursor: pointer !important;
                transition: transform 0.08s ease, box-shadow 0.08s ease, opacity 0.08s ease !important;
                user-select: none !important;
                text-decoration: none !important;
            }
            .unit-btn .q-btn__content { display: inline-flex !important; align-items: center !important; justify-content: center !important; }
            .unit-btn:hover, .unit-btn .q-btn:hover { transform: translateY(-1px); opacity: 0.97; }
            .unit-btn:active, .unit-btn .q-btn:active { transform: translateY(0); }
            .unit-btn.selected, .unit-btn.selected .q-btn { outline: none !important; box-shadow: 0 6px 18px rgba(0,0,0,0.10) !important; border: 2px solid rgba(0,0,0,0.08) !important; }
            .group-wo, .group-wo .q-btn { background: #00b48f !important; }
            .group-pf, .group-pf .q-btn { background: #4f2c1d !important; }
            .group-pi, .group-pi .q-btn { background: #c6464a !important; }
            .group-pt, .group-pt .q-btn { background: #e87928 !important; }
            .unit-btn { margin: 2px !important; line-height: 1 !important; }

            .slot-btn, .slot-btn .q-btn, .slot-btn .q-btn__content, .slot-btn .q-btn__label {
                background: #ffffff !important;
                color: #000 !important;
                border: 1px solid #ddd !important;
                border-radius: 4px !important;
            }
            .slot-btn.selected, .slot-btn.selected .q-btn {
                background: #3b82f6 !important;
                color: #fff !important;
                border-color: #2563eb !important;
                box-shadow: 0 6px 18px rgba(37,99,235,0.12) !important;
            }

            /* Cell edit button inside schedule table */
            .cell-edit-btn {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                width: 22px;
                height: 22px;
                border-radius: 4px;
                border: 1px solid #bbb;
                background: #fff;
                cursor: pointer;
                font-size: 12px;
                line-height: 1;
                padding: 0;
                margin-left: 4px;
                vertical-align: middle;
                opacity: 0.7;
                transition: opacity 0.12s, background 0.12s;
                flex-shrink: 0;
            }
            .cell-edit-btn:hover {
                opacity: 1;
                background: #e8f0fe;
                border-color: #3b82f6;
            }
            .cell-edit-btn:active {
                background: #c7d9fa;
            }
            </style>"""
        )

        self._apply_selected_slot_visual()
        self._update_slot_list_html()

    # --------------------
    # View control helpers
    # --------------------
    def show_view(self, name: str) -> None:
        for k, view in self._views.items():
            if k == name:
                if hasattr(view, "show"):
                    try:
                        view.show()
                    except Exception:
                        view.style("display: block !important;")
                else:
                    view.style("display: block !important;")
            else:
                if hasattr(view, "hide"):
                    try:
                        view.hide()
                    except Exception:
                        view.style("display: none !important;")
                else:
                    view.style("display: none !important;")

    # --------------------
    # HTML table builder (reused for schedules)
    # --------------------
    def _build_table_html(self, occupied_map: dict, editable: bool = False) -> str:
        """
        Build and return HTML for the schedule table.
        occupied_map: dict mapping slot_id like 'A0' -> dict with keys 'text', optional 'bg', 'fg'
        editable: if True, each cell gets a small pencil button that calls
                  window._waehlbaer_editCell(slot_id) — which is bridged to Python via the
                  NiceGUI element's onclick mechanism set up separately.
        """
        html_parts = []
        html_parts.append(
            '<table style="border-collapse: collapse; width: 100%; table-layout: fixed;">'
        )
        # header
        html_parts.append("<thead>")
        html_parts.append("<tr>")
        html_parts.append(
            '<th style="border:1px solid #ccc; padding:6px; background:#f0f0f0; width:120px; max-width:120px;"></th>'
        )
        for day in DAYS:
            html_parts.append(
                f'<th style="border:1px solid #ccc; padding:6px; background:#f0f0f0; width:100px; max-width:100px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">{day}</th>'
            )
        html_parts.append("</tr>")
        html_parts.append("</thead>")

        # body
        html_parts.append("<tbody>")
        for slot_index, slot_label in enumerate(SLOTS):
            html_parts.append("<tr>")
            html_parts.append(
                f'<td style="border:1px solid #ccc; padding:6px; background:#fafafa; font-weight:600; width:60px; max-width:120px;">{slot_label}</td>'
            )
            for col_index, _day in enumerate(DAYS):
                slot_id = f"{chr(65 + col_index)}{slot_index}"  # A0..N4
                val = occupied_map.get(slot_id, "")
                base_style = (
                    "border:1px solid #ccc; padding:6px; height:48px; vertical-align: middle; "
                    "overflow:hidden; width:100px; max-width:100px; position: relative;"
                )
                if val:
                    cell_text = val.get("text", "")
                    cell_bg = val.get("bg", "")
                    cell_fg = val.get("fg", "")
                    cell_style = base_style
                    if cell_bg:
                        cell_style += f" background: {cell_bg};"
                    if cell_fg:
                        cell_style += f" color: {cell_fg};"
                else:
                    cell_style = base_style
                    cell_text = ""

                if editable:
                    # Edit button calls a global JS function bridged to Python
                    edit_btn = (
                        f'<button class="cell-edit-btn" '
                        f"onclick=\"window._waehlbaer_editCell('{slot_id}')\" "
                        f'title="Slot bearbeiten">✏️</button>'
                    )
                    cell_content = (
                        f'<span style="overflow:hidden; text-overflow:wrap; white-space:nowrap; '
                        f'flex:1; display:inline-block; vertical-align:middle;" data-tooltip="{cell_text}">{cell_text}</span>'
                        f"{edit_btn}"
                    )
                    cell_inner_style = (
                        "display:flex; align-items:center; justify-content:space-between; "
                        "width:100%; height:100%;"
                    )
                    html_parts.append(
                        f'<td style="{cell_style}">'
                        f'<div style="{cell_inner_style}">{cell_content}</div>'
                        f"</td>"
                    )
                else:
                    html_parts.append(
                        f'<td style="{cell_style}; text-overflow:ellipsis; white-space:nowrap;">'
                        f"{cell_text}</td>"
                    )
            html_parts.append("</tr>")
        html_parts.append("</tbody>")
        html_parts.append("</table>")
        return "\n".join(html_parts)

    # --------------------
    # Cell edit dialog (block picker per slot)
    # --------------------
    def _register_cell_edit_bridge(self) -> None:
        """
        Inject a JS function window._waehlbaer_editCell(slotId) that sends a message
        back to Python by appending a hidden form + submitting, or via NiceGUI's
        run_javascript + element event trick.
        We use ui.run_javascript to define the bridge each time the schedule is refreshed.
        """
        js = r"""
        window._waehlbaer_editCell = function(slotId) {
            console.log("JS function called for slotId:", slotId);
            // Trigger a NiceGUI element click that carries the slot id.
            // We set a global variable and click a hidden trigger element.
            window._waehlbaer_pending_slot = slotId;
            var trigger = document.getElementById('_waehlbaer_cell_edit_trigger');
            if (trigger) {console.log("Triggering cell edit for slot:", slotId); trigger.click();}
        };
        """
        try:
            ui.run_javascript(js)
        except Exception:
            pass

    def open_cell_edit_dialog(self, slot_id: str) -> None:
        print(f"Opening cell edit dialog for slot: {slot_id}")
        """
        Open a dialog for the given slot_id that lets the user pick which block(s)
        should be assigned to that slot for the currently selected unit.
        Confirming immediately applies the change and logs it.
        """
        if not self.current_unit:
            ui.notify("Keine Einheit ausgewählt", color="warning")
            return
        if not self.allocation:
            return

        unit = self.current_unit

        # Resolve human-readable slot label for display and log
        try:
            day_index = ord(slot_id[0]) - 65
            slot_index = int(slot_id[1:])
            day_label = DAYS[day_index] if 0 <= day_index < len(DAYS) else slot_id
            slot_label_str = (
                SLOTS[slot_index] if 0 <= slot_index < len(SLOTS) else slot_id
            )
            slot_display = f"{day_label} {slot_label_str}"
        except Exception:
            slot_display = slot_id

        # Find which block is currently in this slot for this unit
        current_block_id = ""
        try:
            for entry in unit.schedule.get_list(with_slot=True):
                if entry.get("slot") == slot_id:
                    elem = entry.get("element")
                    if elem is not None:
                        current_block_id = str(getattr(elem, "ID", ""))
                    break
        except Exception:
            pass

        # Collect all active blocks
        active_blocks = []
        try:
            for block in getattr(self.allocation, "BLOCKS", []):
                try:
                    if hasattr(block, "is_active") and not getattr(
                        block, "is_active", True
                    ):
                        continue
                except Exception:
                    pass
                active_blocks.append(block)
        except Exception:
            pass

        # Build dialog
        with ui.dialog() as dlg:
            with ui.card().style("min-width: 480px; max-width: 640px; padding: 20px;"):
                ui.markdown(
                    f"### Block wählen\n"
                    f"**Einheit:** {unit.ID} – {getattr(unit, 'fullname', '')}  \n"
                    f"**Slot:** {slot_display}"
                ).style("margin-bottom: 12px;")

                if not active_blocks:
                    ui.label("Keine aktiven Blöcke gefunden.")
                else:
                    ui.label("Wähle einen Block (oder keinen für «Frei»):").style(
                        "font-weight: 600; margin-bottom: 8px;"
                    )

                    # Radio-style: one block per slot (or none)
                    # We use checkboxes but enforce single selection via a dict
                    # Actually: use a single radio group via ui.radio if available,
                    # otherwise use a select dropdown for clarity.
                    # Using a scrollable list of radio options:

                    block_options = {"": "— Frei (kein Block) —"}
                    for b in active_blocks:
                        try:
                            fullname = (
                                b.data.get("fullname", "")
                                if hasattr(b, "data") and isinstance(b.data, dict)
                                else ""
                            )
                        except Exception:
                            fullname = ""
                        label = f"{block_button_name(b.ID)}"
                        if fullname:
                            label += f"  –  {fullname}"
                        block_options[str(b.ID)] = label

                    selected_val = ui.radio(
                        options=block_options,
                        value=current_block_id
                        if current_block_id in block_options
                        else "",
                    ).style("max-height: 340px; overflow-y: auto; display: block;")

                ui.separator().style("margin: 12px 0;")

                with ui.row().style("gap: 8px; justify-content: flex-end;"):

                    def on_cancel(e=None):
                        dlg.close()

                    def on_confirm(e=None):
                        dlg.close()
                        new_bid = selected_val.value if active_blocks else ""
                        self._apply_cell_edit(
                            unit=unit,
                            slot_id=slot_id,
                            slot_display=slot_display,
                            old_bid=current_block_id,
                            new_bid=new_bid,
                        )

                    ui.button("Abbrechen", on_click=on_cancel).props("unelevated flat")
                    ui.button("Bestätigen", on_click=on_confirm).props(
                        "unelevated"
                    ).style("background: #3b82f6; color: white;")

        dlg.open()

    def _apply_cell_edit(
        self,
        unit,
        slot_id: str,
        slot_display: str,
        old_bid: str,
        new_bid: str,
    ) -> None:
        """
        Immediately apply a block assignment change for a unit at a specific slot,
        then write a log entry and refresh the schedule view.
        """
        if old_bid == new_bid:
            ui.notify("Keine Änderung vorgenommen.", color="info")
            return

        errors = []

        try:
            # Remove the old block if present
            if old_bid:
                old_block = self.allocation.get_block_by_ID(old_bid)
                if old_block:
                    try:
                        unit.schedule.remove_block(old_block, slot_id)
                    except Exception:
                        try:
                            unit.schedule.remove_entry(old_block, slot_id)
                        except Exception as ex:
                            errors.append(f"Entfernen fehlgeschlagen: {ex}")
                else:
                    errors.append(f"Alter Block '{old_bid}' nicht gefunden")

            # Add the new block if present
            if new_bid:
                new_block = self.allocation.get_block_by_ID(new_bid)
                if new_block:
                    try:
                        unit.schedule.set_block(new_block, slot_id)
                    except Exception as ex:
                        errors.append(f"Hinzufügen fehlgeschlagen: {ex}")
                else:
                    errors.append(f"Neuer Block '{new_bid}' nicht gefunden")
        except Exception as ex:
            errors.append(str(ex))

        # Build log entry
        unit_label = f"Einheit {unit.ID}"
        slot_label_log = slot_display

        if errors:
            log_entry = (
                f"[FEHLER] Slot {slot_label_log} bei {unit_label}: " + "; ".join(errors)
            )
            ui.notify(f"Fehler: {'; '.join(errors)}", color="negative")
        else:
            log_parts = []
            if old_bid and new_bid:
                log_parts.append(
                    f"Block {old_bid} entfernt bei {unit_label} in Slot {slot_label_log}."
                )
                log_parts.append(
                    f"Block {new_bid} hinzugefügt bei {unit_label} in Slot {slot_label_log}."
                )
            elif old_bid and not new_bid:
                log_parts.append(
                    f"Block {old_bid} entfernt bei {unit_label} in Slot {slot_label_log} (Slot freigegeben)."
                )
            elif new_bid and not old_bid:
                log_parts.append(
                    f"Block {new_bid} hinzugefügt bei {unit_label} in Slot {slot_label_log}."
                )
            log_entry = " | ".join(log_parts)
            ui.notify(log_entry, color="positive")

        self.change_log.append(log_entry)

        # Refresh schedule
        try:
            self.allocation.remve_KC_from_all_blocks()
            self.update_schedule()
            self._update_slot_list_html()
        except Exception:
            pass

    # --------------------
    # Build unit list HTML (for selected slot)
    # --------------------
    def _build_unit_list_html(self, slot_id: str) -> str:
        html_parts = []
        html_parts.append(
            '<table style="border-collapse: collapse; width: 100%; table-layout: fixed;">'
        )
        html_parts.append("<thead>")
        html_parts.append("<tr>")
        headers = ["Einheit", "Block", "Titel", "Ort"]
        for h in headers:
            html_parts.append(
                f'<th style="border:1px solid #ccc; padding:6px; background:#f0f0f0; text-align:left;">{h}</th>'
            )
        html_parts.append("</tr>")
        html_parts.append("</thead>")

        html_parts.append("<tbody>")
        if not self.allocation:
            html_parts.append("</tbody></table>")
            return "\n".join(html_parts)

        units = sorted(
            getattr(self.allocation, "UNITS", []), key=lambda u: getattr(u, "ID", "")
        )
        for unit in units:
            block_id_text = "Frei"
            fullname = ""
            ort = ""
            try:
                occupied = unit.schedule.get_list(with_slot=True)
                found = None
                for entry in occupied:
                    start_slot = entry.get("slot")
                    elem = entry.get("element")
                    if not start_slot or elem is None:
                        continue
                    length = 1
                    try:
                        if hasattr(elem, "data") and isinstance(elem.data, dict):
                            length = int(elem.data.get("length", 1))
                    except Exception:
                        length = 1

                    slots_covered = [start_slot]
                    if length > 1:
                        try:
                            slots_covered.extend(
                                self._next_slots(start_slot, length - 1)
                            )
                        except Exception:
                            pass

                    if slot_id in slots_covered:
                        found = elem
                        break

                if found is not None:
                    try:
                        bid = getattr(found, "ID", None)
                        if bid is not None:
                            block_id_text = str(bid)
                        else:
                            block_id_text = str(found)
                    except Exception:
                        block_id_text = str(found)
                    try:
                        if hasattr(found, "data") and isinstance(found.data, dict):
                            fullname = found.data.get("fullname", "") or ""
                            ort = found.data.get("ort", "") or ""
                    except Exception:
                        pass
            except Exception:
                pass

            html_parts.append(
                "<tr>"
                f'<td style="border:1px solid #eee; padding:6px; width:100px; max-width:100px;">{unit.ID}</td>'
                f'<td style="border:1px solid #eee; padding:6px; width:60px; max-width:60px;">{block_id_text}</td>'
                f'<td style="border:1px solid #eee; padding:6px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="{fullname}">{fullname}</td>'
                f'<td style="border:1px solid #eee; padding:6px; width:120px; max-width:120px;">{ort}</td>'
                "</tr>"
            )

        html_parts.append("</tbody>")
        html_parts.append("</table>")
        return "\n".join(html_parts)

    # --------------------
    # Unit selection and rendering
    # --------------------
    def select_unit(self, unit, button_component=None) -> None:
        self.current_unit = unit
        self.update_schedule()

        try:
            group = {"wo": "Wölfe", "pf": "Pfadis", "pi": "Pios", "pt": "PTA"}[
                unit.group
            ]
            ui.run_javascript(
                f"var t = document.getElementById('einheiten-title'); if (t) t.innerHTML = '<h3>Einheit {unit.ID} - {unit.fullname} {group}</h3>';"
            )
        except Exception:
            pass

        for b in self.unit_buttons.values():
            b.props("text-color=white")

        button_component.props("text-color=black")

    def update_schedule(self) -> None:
        """
        Build schedule for current_unit and replace the schedule div's innerHTML.
        The table is rendered with edit buttons (editable=True) since a unit is selected.
        Also (re-)registers the JS bridge for cell edit clicks.
        """
        if not self.current_unit:
            filled = {}
        else:
            try:
                occupied = self.current_unit.schedule.get_list(with_slot=True)
                filled = {}
                for entry in occupied:
                    slot = entry.get("slot")
                    elem = entry.get("element")
                    if not slot or elem is None:
                        continue
                    block_id = block_button_name(getattr(elem, "ID", str(elem)))
                    length = 1
                    try:
                        if hasattr(elem, "data") and isinstance(elem.data, dict):
                            length = int(elem.data.get("length", 1))
                    except Exception:
                        length = 1
                    cat = ""
                    try:
                        if hasattr(elem, "data") and isinstance(elem.data, dict):
                            cat = elem.data.get("cat", "")
                    except Exception:
                        cat = ""
                    bg = None
                    fg = None
                    try:
                        if cat and cat in block_category_colors:
                            bg = block_category_colors[cat].get("bg")
                            fg = block_category_colors[cat].get("fg")
                    except Exception:
                        pass
                    filled[slot] = {"text": str(block_id), "bg": bg, "fg": fg}
                    if length > 1:
                        next_slots = self._next_slots(slot, length - 1)
                        for ns in next_slots:
                            filled[ns] = {"text": str(block_id), "bg": bg, "fg": fg}
            except Exception:
                filled = {}

        # Render with edit buttons only when a unit is selected
        editable = self.current_unit is not None
        html = self._build_table_html(filled, editable=editable)
        try:
            ui.run_javascript(
                f"document.getElementById('schedule-table').innerHTML = `{html}`;"
            )
        except Exception:
            pass

        # Re-register the JS bridge after innerHTML replacement
        if editable:
            self._register_cell_edit_bridge()

    def export_current_unit_pdf(self) -> None:
        try:
            if not self.current_unit:
                ui.notify("Keine Einheit ausgewählt", color="warning")
                return
            try:
                export_to_pdf(self.current_unit)
                ui.notify(
                    f"PDF exportiert für Einheit {getattr(self.current_unit, 'ID', '')}"
                )
            except Exception as e:
                ui.notify(f"Export fehlgeschlagen: {e}", color="negative")
        except Exception:
            pass

    # --------------------
    # Block selection and rendering
    # --------------------
    def select_block(self, block, button_component=None) -> None:
        self.current_block = block
        self.update_block_schedule()

        try:
            ui.run_javascript(
                f"var t = document.getElementById('blocke-title'); if (t) t.innerHTML = '<h3>Block {block_button_name(block.ID)} - {block.data['fullname']}</h3>';"
            )
        except Exception:
            pass

        try:
            ui.run_javascript(
                f"""(function(){{
                    document.querySelectorAll('.unit-btn').forEach(function(b){{ b.classList.remove('selected'); }});
                    var el = document.getElementById('block-btn-{block.ID}');
                    if (el) {{
                        if (!el.classList.contains('unit-btn')) el.classList.add('unit-btn');
                        el.classList.add('selected');
                    }}
                }})();"""
            )
        except Exception:
            pass

    def update_block_schedule(self) -> None:
        if not self.current_block:
            filled = {}
        else:
            try:
                occupied = self.current_block.schedule.get_list(with_slot=True)
                filled = {}
                for entry in occupied:
                    slot = entry.get("slot")
                    unit_obj = entry.get("element")
                    if not slot or unit_obj is None:
                        continue
                    unit_id = getattr(unit_obj, "ID", str(unit_obj))
                    bg = ""
                    fg = "#000"
                    try:
                        g = getattr(unit_obj, "group", "") or ""
                        if g and g in group_colors:
                            bg = group_colors[g]
                            fg = "#ffffff"
                    except Exception:
                        pass
                    if slot in filled and filled[slot].get("text"):
                        filled[slot]["text"] = f"{filled[slot]['text']}, {unit_id}"
                    else:
                        filled[slot] = {"text": str(unit_id), "bg": bg, "fg": fg}
            except Exception:
                filled = {}

        html = self._build_table_html(filled)
        try:
            ui.run_javascript(
                f"document.getElementById('schedule-table-block').innerHTML = `{html}`;"
            )
        except Exception:
            pass

    def export_current_block_pdf(self) -> None:
        try:
            if not self.current_block:
                ui.notify("Kein Block ausgewählt", color="warning")
                return
            try:
                export_block_to_pdf(self.current_block)
                ui.notify(
                    f"PDF exportiert für Block {getattr(self.current_block, 'ID', '')}"
                )
            except Exception as e:
                ui.notify(f"Export fehlgeschlagen: {e}", color="negative")
        except Exception:
            pass

    # --------------------
    # Save allocation — now shows change log and requires confirmation
    # --------------------
    def open_save_dialog(self) -> None:
        """
        Open a dialog that shows the full change log and asks for confirmation
        before writing to xlsx. The user must confirm the log before saving.
        """
        if not self.allocation:
            ui.notify("Keine Allocation vorhanden", color="warning")
            return
        print("Opening save dialog with change log:")

        with ui.dialog() as dlg:
            with ui.card().style("min-width: 560px; max-width: 800px; padding: 20px;"):
                ui.markdown("### Allocation speichern")

                # Show change log
                if self.change_log:
                    ui.markdown(
                        f"**Änderungsprotokoll** ({len(self.change_log)} Einträge):"
                    ).style("margin-bottom: 4px;")
                    with ui.card().style(
                        "background: #f8fafc; border: 1px solid #e2e8f0; "
                        "padding: 12px; max-height: 320px; overflow-y: auto; "
                        "font-family: monospace; font-size: 13px; line-height: 1.6;"
                    ):
                        for i, entry in enumerate(self.change_log, start=1):
                            # Color errors differently
                            color = (
                                "#dc2626" if entry.startswith("[FEHLER]") else "#1e293b"
                            )
                            ui.html(
                                f'<div style="color:{color}; padding: 2px 0; '
                                f'border-bottom: 1px solid #f1f5f9;">'
                                f'<span style="color:#94a3b8; margin-right:8px;">{i}.</span>'
                                f"{entry}"
                                f"</div>"
                            )
                else:
                    ui.html(
                        '<div style="color: #64748b; font-style: italic; padding: 12px 0;">'
                        "Keine Änderungen protokolliert seit dem letzten Start."
                        "</div>"
                    )

                ui.separator().style("margin: 12px 0;")
                ui.markdown(
                    "Bitte überprüfe das Protokoll. Danach Dateinamen und optional einen Kommentar eingeben und bestätigen:"
                ).style("color: #475569; font-size: 14px;")

                fname = ui.input("Dateiname", value="temp.xlsx").style(
                    "width: 100%; margin-top: 8px;"
                )

                comment = ui.input(
                    "Kommentar", placeholder="Optional: Zusätzliche Anmerkungen"
                ).style("width: 100%; margin-top: 8px;")

                ui.label(
                    "Der Kommentar wird zusammen mit den Änderungen im Excel-File gespeichert."
                ).style("color: #64748b; font-size: 13px; margin-top: 4px;")

                ui.separator().style("margin: 12px 0;")

                with ui.row().style("gap: 8px; justify-content: flex-end;"):

                    def on_cancel(e=None):
                        dlg.close()

                    def on_confirm(e=None):
                        dlg.close()
                        try:
                            # Combine change log and comment into log_data
                            log_data = "'"

                            # Add comment if provided
                            if comment.value:
                                log_data += f"=== Kommentar ===\n{comment.value}\n\n"

                            # Add change log entries
                            if self.change_log:
                                log_data += "=== Änderungen ===\n"
                                # Add timestamp to log
                                from datetime import datetime

                                log_data += f"Datum: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

                                # Add base file information if available
                                if hasattr(self.allocation, "loaded_from"):
                                    log_data += f"Basiert auf: {self.allocation.loaded_from}\n\n"

                                # Format log entries with numbering
                                log_data += "\n".join(
                                    f"{i + 1}. {entry}"
                                    for i, entry in enumerate(self.change_log)
                                )

                            # Save the file
                            write_to_xlsx(
                                self.allocation, fname=fname.value, comment=log_data
                            )

                            # Copy to history folder with datetime extension
                            import os
                            import shutil
                            from datetime import datetime

                            # Create history folder if it doesn't exist
                            history_path = "history"
                            if not os.path.exists(history_path):
                                os.makedirs(history_path)

                            # Generate filename with datetime
                            base_name = os.path.splitext(fname.value)[0]
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            history_filename = f"{base_name}_{timestamp}.xlsx"
                            history_filepath = os.path.join(
                                history_path, history_filename
                            )

                            # Copy the file to history folder
                            try:
                                shutil.copy2("saves/" + fname.value, history_filepath)
                                ui.notify(
                                    f"Allocation gespeichert: {fname.value}\nKopie in History: {history_filename}",
                                    color="positive",
                                )
                            except Exception as copy_error:
                                print(
                                    f"Error occurred while copying to history: {copy_error}"
                                )
                                ui.notify(
                                    f"Allocation gespeichert: {fname.value}\nSpeichern fehlgeschlagen: {copy_error}",
                                    color="negative",
                                )

                            # Clear log after confirmed save
                            self.change_log.clear()
                        except Exception as exc:
                            print(f"Error occurred while saving: {exc}")
                            ui.notify(
                                f"Speichern fehlgeschlagen: {exc}", color="negative"
                            )

                    ui.button("Abbrechen", on_click=on_cancel).props("unelevated flat")
                    ui.button("✓ Bestätigen und speichern", on_click=on_confirm).props(
                        "unelevated"
                    ).style("background: #16a34a; color: white;")

        dlg.open()

    # --------------------
    # Slot selection for Auflistung pro Slot
    # --------------------
    def select_slot(self, slot_id: str) -> None:
        if not slot_id:
            return
        self.selected_slot = slot_id
        try:
            day_index = ord(slot_id[0]) - 65
            slot_index = int(slot_id[1:])
            day_label = DAYS[day_index] if 0 <= day_index < len(DAYS) else slot_id
            slot_label = SLOTS[slot_index] if 0 <= slot_index < len(SLOTS) else slot_id
            ui.run_javascript(
                f"var t = document.getElementById('auflistung-title'); if (t) t.innerHTML = '<h3>Auflistung für Slot {day_label} {slot_label}</h3>';"
            )
        except Exception:
            pass
        self._apply_selected_slot_visual()
        self._update_slot_list_html()

    def _apply_selected_slot_visual(self) -> None:
        try:
            ui.run_javascript(
                f"""(function(){{
                    document.querySelectorAll('.slot-btn').forEach(function(b){{ b.classList.remove('selected'); }});
                    var el = document.getElementById('slot-btn-{self.selected_slot}');
                    if (el) el.classList.add('selected');
                }})();"""
            )
        except Exception:
            pass

    def _update_slot_list_html(self) -> None:
        try:
            html = self._build_unit_list_html(self.selected_slot)
            ui.run_javascript(
                f"document.getElementById('slot-list').innerHTML = `{html}`;"
            )
        except Exception:
            pass

    # --------------------
    # Helpers
    # --------------------
    def _next_slots(self, slot_id: str, n: int) -> list:
        slots = []
        if not slot_id or n <= 0:
            return slots
        try:
            day_char = slot_id[0]
            time_part = slot_id[1:]
            day = ord(day_char) - 65
            time = int(time_part)
        except Exception:
            return slots
        for _ in range(n):
            time += 1
            if time >= len(SLOTS):
                time = 0
                day += 1
            if day >= len(DAYS):
                break
            slots.append(f"{chr(65 + day)}{time}")
        return slots


if __name__ == "__main__":
    a = Allocation(1)
    load_blocklist(a)
    load_unitlist(a, ignore_warnings=True)

    add_dusche_series(a)
    add_nacht_series(a)
    add_wald_series(a)
    add_bogenscheissen_series(a)
    add_feuerwehr_series(a)

    # Ask user to select a file to load at startup

    with (
        ui.dialog() as file_dialog,
        ui.card().style("min-width: 400px; padding: 20px;"),
    ):
        import glob
        import os

        ui.markdown("### Wähle eine Allocation-Datei zum Laden aus")

        # Get all XLSX files in saves folder
        saves_dir = "saves"
        xlsx_files = glob.glob(os.path.join(saves_dir, "*.xlsx"))

        # Sort by modification time (newest first)
        xlsx_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)

        # Create radio buttons for file selection
        if xlsx_files:
            file_radio = ui.radio(
                {
                    os.path.basename(
                        f
                    ): f"{os.path.basename(f)} {'(neustes)' if f == xlsx_files[0] else ''}"
                    for f in xlsx_files
                }
            ).style("margin-bottom: 16px;")
        else:
            ui.label("No allocation files found in the saves folder.")
            file_radio = None

        def load_file():
            if file_radio and file_radio.value:
                selected_file = file_radio.value.split(" ")[0]  # Get the actual filename without "(latest)"

                # Show loading indicator
                ui.notify("Lade Datei...", color="info")

                # Run file loading in a separate thread to keep GUI responsive
                import threading

                def load_in_thread():
                    try:
                        print(f"Loading allocation from file: {selected_file}")
                        read_from_xlsx(a, filename=selected_file)

                        # Store the loaded file name
                        a.loaded_from = selected_file
                        print(f"Allocation loaded from {a.loaded_from}")

                        # Close dialog and notify success
                        file_dialog.close()
                        print("File dialog closed after loading.")
                        ui.notify("File loaded successfully!")

                    except Exception as e:
                        print(f"Error loading file: {e}")
                        ui.notify(f"Failed to load file: {e}", color="negative")

                # Start the loading thread
                threading.Thread(target=load_in_thread, daemon=True).start()
            else:
                ui.notify("Please select a file", color="warning")

        with ui.row().style("gap: 8px; justify-content: flex-end;"):
            ui.button("Abbrechen", on_click=file_dialog.close).props("flat")
            ui.button("Laden", on_click=load_file).props("unelevated")

    file_dialog.open()

    a.UNITS.sort(key=lambda u: u.ID)

    a.BLOCKS = [b for b in a.BLOCKS if not isinstance(b, MetaBlock)]  # Filter out inactive blocks
    def sort_key(b):
        try:
            # Extract the numeric part after the dash in the ID for sorting
            return int(b.ID.split("_")[0].split("-")[1]) + b.ID.split("_")[0].split("-")[0] == "OFF" * 1000
        except Exception as e:
            print(e)
            return float('inf')  # Place any blocks with unexpected IDs at the end
    a.BLOCKS.sort(key=sort_key)

    app = LeftDockApp(allocation=a)

    # Wire up the hidden JS bridge trigger element.
    # This invisible button is clicked by window._waehlbaer_editCell() in the browser,
    # which passes the slot id via window._waehlbaer_pending_slot.
    trigger_btn = (
        ui.button("")
        .props("id=_waehlbaer_cell_edit_trigger")
        .style("display:none; position:absolute; pointer-events:none;")
    )

    async def _on_cell_edit_trigger(e=None):
        print("Cell edit trigger clicked")
        # Read the slot id that was stored in the JS global by the edit button
        try:
            result = await ui.run_javascript(
                "window._waehlbaer_pending_slot || ''", timeout=2
            )
            slot_id = str(result).strip()
            if slot_id:
                app.open_cell_edit_dialog(slot_id)
        except Exception:
            pass

    trigger_btn.on("click", _on_cell_edit_trigger)

    ui.run(
        title="Wählbär — Einheiten & Blöcke",
        window_size=(1200, 800),
        reload=False,
        native=False,
    )
