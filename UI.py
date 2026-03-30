# waehlbaer/UI.py
from typing import Dict, Optional

from nicegui import ui

from IO import load_blocklist, load_unitlist, read_from_xlsx
from main import (
    add_amtli_series,
    add_bogenscheissen_series,
    add_dusche_series,
    add_feuerwehr_series,
    add_nacht_series,
    add_wald_series,
)

# Project imports (keep these so the UI can use your existing data structures)
from Wählbär import Allocation

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


class LeftDockApp:
    """
    App with left dock and three views:
    - Einheiten: top shows schedule for selected unit, bottom shows unit buttons
    - Blöcke: top shows schedule for selected block (which units visit which slots),
              bottom shows block buttons
    - Auflistung: top shows list of units for currently selected slot,
                  bottom shows a slot-picker table (each cell selects a slot)
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

        # currently selected slot for Auflistung view (default first day, first slot)
        self.selected_slot: str = "A0"

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
                ui.separator()
                ui.label("Status: ready").classes("text-xs")

            # main area
            with ui.column().style(
                "flex: 1; padding: 18px; gap: 12px;"
            ) as self.main_area:
                ui.markdown("# Wählbar - Wählbares Programm")
                ui.label("Wähle eine Ansicht in der linken Leiste.")

                # --- Einheiten view ---
                with ui.column().style("gap: 8px;") as self.view_einheiten:
                    ui.html('<div id="einheiten-title"><h3>Einheiten</h3></div>')

                    # schedule container (for unit)
                    initial_table = self._build_table_html({})
                    ui.html(
                        f'<div id="schedule-table" style="width:100%;">{initial_table}</div>'
                    ).style(
                        "width: 100%; height: 45vh; overflow: auto; border: 1px solid #ddd;"
                    )

                    # unit buttons
                    with ui.card().style("padding: 8px; height: 40vh; overflow: auto;"):
                        ui.label("Einheiten:")
                        with ui.row().style("flex-wrap: wrap; gap: 8px;"):
                            if self.allocation is not None:
                                for unit in getattr(self.allocation, "UNITS", []):
                                    group = getattr(unit, "group", "") or ""
                                    base_class = (
                                        f"unit-btn group-{group}"
                                        if group
                                        else "unit-btn"
                                    )
                                    # assign an id to help DOM selection; NiceGUI may wrap the actual label in internal nodes
                                    btn_id = f"unit-btn-{unit.ID}"
                                    btn = (
                                        ui.button(str(unit.ID))
                                        .props(f"id:{btn_id}")
                                        .classes(base_class)
                                    )
                                    # record base class
                                    self.unit_button_base_classes[unit.ID] = base_class

                                    # attach handler
                                    def make_u_handler(u, btn_ref):
                                        return lambda e=None: self.select_unit(
                                            u, btn_ref
                                        )

                                    btn.on("click", make_u_handler(unit, btn))
                                    # store button object
                                    try:
                                        self.unit_buttons[unit.ID] = btn
                                    except Exception:
                                        pass

                # --- Blöcke view ---
                with ui.column().style("gap: 8px;") as self.view_blocke:
                    ui.html('<div id="blocke-title"><h3>Blöcke</h3></div>')

                    # schedule container (for block)
                    initial_table_b = self._build_table_html({})
                    ui.html(
                        f'<div id="schedule-table-block" style="width:100%;">{initial_table_b}</div>'
                    ).style(
                        "width: 100%; height: 45vh; overflow: auto; border: 1px solid #ddd;"
                    )

                    # block buttons
                    with ui.card().style("padding: 8px; height: 40vh; overflow: auto;"):
                        ui.label("Blöcke:")
                        with ui.row().style("flex-wrap: wrap; gap: 8px;"):
                            if self.allocation is not None:
                                for block in getattr(self.allocation, "BLOCKS", []):
                                    # only create buttons for active blocks
                                    if not getattr(block, "is_active", True):
                                        continue
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
                                    btn = (
                                        ui.button(str(block.ID))
                                        .props(f"id:{btn_id}")
                                        .classes(base_class)
                                    )
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

                # --- Auflistung pro Slot ---
                with ui.column().style("gap: 8px;") as self.view_auflistung:
                    ui.html(
                        f'<div id="auflistung-title"><h3>Auflistung für Slot {DAYS[0]} {SLOTS[0]}</h3></div>'
                    )

                    # Top: list of units for currently selected slot
                    with ui.card().style(
                        "padding: 12px; height: 45vh; overflow: auto;"
                    ):
                        ui.label("Einheiten in gewähltem Slot:").style(
                            "font-size: 16px; font-weight: 600; margin-bottom: 12px;"
                        )
                        # initial empty table
                        initial_list_html = self._build_unit_list_html(
                            self.selected_slot
                        )
                        ui.html(
                            f'<div id="slot-list" style="width:100%;">{initial_list_html}</div>'
                        )

                    # Bottom: slot picker grid (same layout as schedule table but cells select slot)
                    with ui.card().style("padding: 8px; height: 40vh; overflow: auto;"):
                        ui.label("Slot wählen:")
                        # build slot-picker header row (days)
                        with ui.row().style("gap: 0; align-items: stretch;"):
                            # left corner empty to align with slot names
                            ui.label("").style("width:120px; min-width:120px;")
                            for _day in DAYS:
                                ui.label(_day).style(
                                    "flex: 1; min-width:100px; max-width:100px; text-overflow:ellipsis; overflow:hidden; white-space:nowrap; padding:6px; border:1px solid #eee; background:#fafafa;"
                                )

                        # build rows for each slot with a button per day-slot
                        if self.allocation is not None:
                            for slot_index, slot_label in enumerate(SLOTS):
                                with ui.row().style("gap: 0; align-items: stretch;"):
                                    ui.label(slot_label).style(
                                        "width:120px; min-width:120px; padding:6px; border:1px solid #eee; background:#fafafa; font-weight:600;"
                                    )
                                    for col_index, _day in enumerate(DAYS):
                                        slot_id = f"{chr(65 + col_index)}{slot_index}"  # A0..N4
                                        btn_id = f"slot-btn-{slot_id}"
                                        # small visual button for selecting the slot
                                        # store in self.slot_buttons for later toggling classes
                                        btn = (
                                            ui.button("")
                                            .props(f"id:{btn_id}")
                                            .classes("slot-btn")
                                            .style(
                                                "flex: 1; min-width:100px; max-width:100px; height:44px; margin:0; border-radius:4px; padding:6px;"
                                            )
                                        )

                                        # attach handler
                                        def make_slot_handler(sid):
                                            return lambda e=None: self.select_slot(sid)

                                        btn.on("click", make_slot_handler(slot_id))
                                        # store button object
                                        try:
                                            self.slot_buttons[slot_id] = btn
                                        except Exception:
                                            pass

        # store views for show/hide
        self._views = {
            "einheiten": self.view_einheiten,
            "blocke": self.view_blocke,
            "auflistung": self.view_auflistung,
        }

        # start with einheiten view visible
        self.show_view("einheiten")

        # CSS - target wrapper and Quasar internals to ensure colors show
        ui.add_head_html(
            """<style>
            /* base button styling and override Quasar internals where needed */
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

            /* slot picker buttons */
            .slot-btn, .slot-btn .q-btn, .slot-btn .q-btn__content, .slot-btn .q-btn__label {
                background: #ffffff !important;
                color: #000 !important;
                border: 1px solid #ddd !important;
                border-radius: 4px !important;
            }
            .slot-btn.selected, .slot-btn.selected .q-btn {
                background: #3b82f6 !important; /* blue */
                color: #fff !important;
                border-color: #2563eb !important;
                box-shadow: 0 6px 18px rgba(37,99,235,0.12) !important;
            }
            </style>"""
        )

        # After building UI elements, set the initial selected slot visual and list
        self._apply_selected_slot_visual()
        # populate initial unit list
        self._update_slot_list_html()

    # --------------------
    # View control helpers
    # --------------------
    def show_view(self, name: str) -> None:
        for k, view in self._views.items():
            if k == name:
                if hasattr(view, "show"):
                    view.show()
                else:
                    view.style("display: block !important;")
            else:
                if hasattr(view, "hide"):
                    view.hide()
                else:
                    view.style("display: none !important;")

    # --------------------
    # HTML table builder (reused for schedules)
    # --------------------
    def _build_table_html(self, occupied_map: dict) -> str:
        """
        Build and return HTML for the schedule table.
        occupied_map: dict mapping slot_id like 'A0' -> dict with keys 'text', optional 'bg', 'fg'
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
                base_style = "border:1px solid #ccc; padding:6px; height:48px; vertical-align: middle; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; width:100px; max-width:100px;"
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
                html_parts.append(f'<td style="{cell_style}">{cell_text}</td>')
            html_parts.append("</tr>")
        html_parts.append("</tbody>")
        html_parts.append("</table>")
        return "\n".join(html_parts)

    # --------------------
    # Build unit list HTML (for selected slot)
    # --------------------
    def _build_unit_list_html(self, slot_id: str) -> str:
        """
        Build an HTML table listing all units and what block they have in the given slot_id.
        Columns: Unit.ID | block.ID or 'Frei' | block.data['fullname'] | block.data['ort']
        """
        html_parts = []
        html_parts.append(
            '<table style="border-collapse: collapse; width: 100%; table-layout: fixed;">'
        )
        # header
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

        # ensure stable order
        units = sorted(
            getattr(self.allocation, "UNITS", []), key=lambda u: getattr(u, "ID", "")
        )
        for unit in units:
            # default values
            block_id_text = "Frei"
            fullname = ""
            ort = ""
            # attempt to find the element occupying that slot for this unit
            try:
                occupied = unit.schedule.get_list(with_slot=True)
                found = None
                for entry in occupied:
                    if entry.get("slot") == slot_id:
                        found = entry.get("element")
                        break
                if found is not None:
                    # if the element is an object with ID attribute (block)
                    try:
                        bid = getattr(found, "ID", None)
                        if bid is not None:
                            block_id_text = str(bid)
                        else:
                            block_id_text = str(found)
                    except Exception:
                        block_id_text = str(found)
                    # try to read data fields
                    try:
                        if hasattr(found, "data") and isinstance(found.data, dict):
                            fullname = found.data.get("fullname", "") or ""
                            ort = found.data.get("ort", "") or ""
                    except Exception:
                        pass
            except Exception:
                # in case schedule is absent or errors
                pass

            html_parts.append(
                "<tr>"
                f'<td style="border:1px solid #eee; padding:6px; width:100px; max-width:100px;">{unit.ID}</td>'
                f'<td style="border:1px solid #eee; padding:6px; width:60px; max-width:60px;">{block_id_text}</td>'
                f'<td style="border:1px solid #eee; padding:6px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">{fullname}</td>'
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
        """
        Called when a unit button is clicked.
        """
        self.current_unit = unit
        self.update_schedule()

        # update the main title
        try:
            group = {"wo": "Wölfe", "pf": "Pfadis", "pi": "Pios", "pt": "PTA"}[
                unit.group
            ]
            ui.run_javascript(
                f"var t = document.getElementById('einheiten-title'); if (t) t.innerHTML = '<h3>Einheit {unit.ID} - {unit.fullname} {group}</h3>';"
            )
        except Exception:
            pass

        # attempt to set classes on server-side button objects
        try:
            for bid, btn in self.unit_buttons.items():
                try:
                    base = self.unit_button_base_classes.get(bid, "unit-btn")
                    btn.classes(base)
                except Exception:
                    pass
            # add selected to clicked button
            btn = self.unit_buttons.get(unit.ID)
            if btn:
                try:
                    base = self.unit_button_base_classes.get(unit.ID, "unit-btn")
                    btn.classes(f"{base} selected")
                except Exception:
                    pass
        except Exception:
            pass

        # also ensure DOM-level selected class exists (in case NiceGUI wraps)
        try:
            ui.run_javascript(
                f"""(function(){{
                    document.querySelectorAll('.unit-btn').forEach(function(b){{ b.classList.remove('selected'); }});
                    var el = document.getElementById('unit-btn-{unit.ID}');
                    if (el) el.classList.add('selected');
                }})();"""
            )
        except Exception:
            pass

    def update_schedule(self) -> None:
        """
        Build schedule for current_unit and replace the schedule div's innerHTML.
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
                    block_id = getattr(elem, "ID", str(elem))
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

        html = self._build_table_html(filled)
        try:
            ui.run_javascript(
                f"document.getElementById('schedule-table').innerHTML = `{html}`;"
            )
        except Exception:
            pass

    # --------------------
    # Block selection and rendering
    # --------------------
    def select_block(self, block, button_component=None) -> None:
        """
        Called when a block button is clicked.
        """
        self.current_block = block
        self.update_block_schedule()

        # update title
        try:
            ui.run_javascript(
                f"var t = document.getElementById('blocke-title'); if (t) t.innerHTML = '<h3>Block {block.ID} - {block.data['fullname']}</h3>';"
            )
        except Exception:
            pass

        # server-side attempt to set classes
        try:
            for bid, btn in self.block_buttons.items():
                try:
                    base = self.block_button_base_classes.get(bid, "unit-btn")
                    btn.classes(base)
                except Exception:
                    pass
            btn = self.block_buttons.get(block.ID)
            if btn:
                try:
                    base = self.block_button_base_classes.get(block.ID, "unit-btn")
                    btn.classes(f"{base} selected")
                except Exception:
                    pass
        except Exception:
            pass

        # DOM-level toggle
        try:
            ui.run_javascript(
                f"""(function(){{
                    document.querySelectorAll('.unit-btn').forEach(function(b){{ b.classList.remove('selected'); }});
                    var el = document.getElementById('block-btn-{block.ID}');
                    if (el) el.classList.add('selected');
                }})();"""
            )
        except Exception:
            pass

    def update_block_schedule(self) -> None:
        """
        Build schedule for current_block: for each slot show the list of units (IDs) visiting that block.
        """
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
                    # color by unit group if available
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

    # --------------------
    # Slot selection for Auflistung pro Slot
    # --------------------
    def select_slot(self, slot_id: str) -> None:
        """
        Called when a slot cell/button is clicked in the slot picker.
        Updates internal state, visual selection, and the unit list.
        Also updates the Auflistung title to include day and slot label.
        """
        if not slot_id:
            return
        self.selected_slot = slot_id
        # update Auflistung title with day and slot label
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
        # update visual state of buttons
        self._apply_selected_slot_visual()
        # update top unit list
        self._update_slot_list_html()

    def _apply_selected_slot_visual(self) -> None:
        """
        Toggle classes for slot buttons so currently selected slot is highlighted.
        """
        try:
            for sid, btn in self.slot_buttons.items():
                try:
                    if sid == self.selected_slot:
                        btn.classes("slot-btn selected")
                    else:
                        btn.classes("slot-btn")
                except Exception:
                    pass
            # also ensure DOM-level selected class exists (in case NiceGUI wraps)
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
        except Exception:
            pass

    def _update_slot_list_html(self) -> None:
        """
        Rebuild the unit list HTML for self.selected_slot and replace the slot-list div's innerHTML.
        """
        try:
            html = self._build_unit_list_html(self.selected_slot)
            ui.run_javascript(
                f"document.getElementById('slot-list').innerHTML = `{html}`;"
            )
        except Exception:
            # fallback: nothing
            pass

    # --------------------
    # Helpers
    # --------------------
    def _next_slots(self, slot_id: str, n: int) -> list:
        """
        Return next n slot ids after slot_id (wrap days/slots).
        """
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
    # Initialize Allocation and data and create app instance
    a = Allocation(1)
    load_blocklist(a)
    load_unitlist(a, ignore_warnings=True)

    add_dusche_series(a)
    add_nacht_series(a)
    add_wald_series(a)
    add_bogenscheissen_series(a)
    add_feuerwehr_series(a)

    # Optionally read from xlsx; comment/uncomment as needed
    try:
        read_from_xlsx(a, filename="PRG_Programmzuteilung_allocation.xlsx")
    except Exception:
        pass

    a.UNITS.sort(key=lambda u: u.ID)
    a.BLOCKS.sort(key=lambda b: b.ID)

    app = LeftDockApp(allocation=a)

    ui.run(
        title="Wählbär — Einheiten & Blöcke",
        window_size=(1200, 800),
        reload=False,
        native=False,
    )
