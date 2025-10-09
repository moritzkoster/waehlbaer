import tkinter as tk
from tkinter import ttk, messagebox

from ttkthemes import ThemedTk

from Wählbär import Allocation


class ScheduleApp:
    def __init__(self, root, allocation):
        self.root = root
        self.allocation = allocation
        self.current_unit = None
        # Days and slots
        self.days = ["Sun 12.7", "Mon 13.7", "Tue 14.7", "Wed 15.7",
                      "Thu 16.7", "Fri 17.7", "Sat 18.7",
                      "Sun 19.7", "Mon 20.7", "Tue 21.7", "Wed 22.7",
                      "Thu 23.7", "Fri 24.7", "Sat 25.7"]
        self.slots = ["0", "1", "2", "3"]
        # Setup UI
        self.setup_ui()

    def setup_ui(self):
        self.root.title("Schedule Grid")
        self.root.geometry("1000x600")
        # self.root.resizable(False, False)

        # Apply a modern theme
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("TFrame", background="#f0f0f0")
        self.style.configure("TLabel", background="#f0f0f0", font=("Helvetica", 10), padding=5)
        self.style.configure("TButton", font=("Helvetica", 10), padding=5)
        self.style.configure("TCombobox", padding=5)
        # self.style.map("TButton",
        #     foreground=[("active", "white"), ("!active", "black")],
        #     background=[("active", "#0078d7"), ("!active", "#e1e1e1")],
        #     relief=[("pressed", "sunken"), ("!pressed", "raised")]
        # )

        self.style.configure("Occupied.TButton", background="#0078d7", foreground="white")
        self.style.configure("Empty.TButton", background="#f0f0f0", foreground="black")

        # Main frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Unit selection dropdown
        self.unit_var = tk.StringVar()
        self.unit_dropdown = ttk.Combobox(
            self.main_frame, textvariable=self.unit_var,
            values=[unit.name for unit in self.allocation.UNITS],
            state="readonly", width=30
        )
        self.unit_dropdown.grid(row=0, column=0, padx=10, pady=10, columnspan=14, sticky="ew")
        self.unit_dropdown.bind("<<ComboboxSelected>>", self.on_unit_select)

        # Grid frame
        self.grid_frame = ttk.Frame(self.main_frame)
        self.grid_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        # Day labels (columns)
        for col, day in enumerate(self.days):
            label = ttk.Label(self.grid_frame, text=day, relief=tk.RIDGE, width=10, anchor="center")
            label.grid(row=0, column=col+1, padx=2, pady=2, sticky="nsew")

        # Slot labels (rows)
        for row, slot in enumerate(self.slots):
            label = ttk.Label(self.grid_frame, text=f"Slot {slot}", relief=tk.RIDGE, width=10, anchor="center")
            label.grid(row=row+1, column=0, padx=2, pady=2, sticky="nsew")

        # Buttons grid
        self.buttons = {}
        for col, day in enumerate(self.days):
            for row, slot in enumerate(self.slots):
                slot_id = f"{chr(65+col)}{slot}"
                btn = ttk.Button(
                    self.grid_frame, text="Empty",
                    command=lambda d=day, s=slot, sid=slot_id: self.on_slot_click(d, s, sid),
                    width=10
                )
                btn.grid(row=row+1, column=col+1, padx=2, pady=2, sticky="nsew")
                self.buttons[slot_id] = btn

        # Configure grid weights
        for i in range(15):
            self.grid_frame.columnconfigure(i, weight=1)
        for i in range(5):
            self.grid_frame.rowconfigure(i, weight=1)

    def on_unit_select(self, event):
        unit_name = self.unit_var.get()
        self.current_unit = next(
            (unit for unit in self.allocation.UNITS if unit.name == unit_name),
            None
        )
        self.update_grid()

    def update_grid(self):
        if not self.current_unit:
            return
        # Get occupied slots in "A0" format
        occupied = self.current_unit.schedule.get_list(with_slot=True, names_only=True)

        # Update buttons
        for slot_id, btn in self.buttons.items():
            btn.configure(text="", state=tk.NORMAL, style="Empty.TButton")
            for block in occupied:
                if block["slot"] == slot_id:
                    btn.config(text=block["name"], state=tk.NORMAL, style="Occupied.TButton")



    def on_slot_click(self, day, slot, slot_id):
        if not self.current_unit:
            return
        # Check if the slot is occupied
        occupied = self.current_unit.schedule.get_list(with_slot=True)
        for oc in occupied:
            if oc["slot"]== slot_id:
                self.show_remove_block_option(oc["element"], slot_id)
                return
        # If not occupied, show block options
        self.show_block_options(slot_id)

    def show_block_options(self, slot_id):
        block_window = tk.Toplevel(self.root)
        block_window.title("Set Block")
        block_window.geometry("300x150")
        block_window.resizable(False, False)

        ttk.Label(block_window, text="Select a block:").pack(pady=10)

        block_var = tk.StringVar()
        block_dropdown = ttk.Combobox(
            block_window, textvariable=block_var,
            values=[block.name for block in self.allocation.search_blocks(slot_id, {"space": self.current_unit.nPeople})],
            state="readonly", width=27
        )
        block_dropdown.pack(pady=5)

        def set_block():
            block_name = block_var.get()
            block = next(
                (b for b in self.allocation.BLOCKS if b.name == block_name),
                None
            )
            if block:
                free_slots = block.search_slots({"space": self.current_unit.nPeople})
                if slot_id in free_slots:
                    self.current_unit.set_block(block, slot_id)
                    self.buttons[slot_id].config(text=block_name, state=tk.NORMAL, style="Occupied.TButton")
                    block_window.destroy()
                else:
                    messagebox.showerror("Error", "Slot not available for this block.")

        ttk.Button(block_window, text="Set Block", command=set_block).pack(pady=10)

    def show_remove_block_option(self, block, slot_id):
        confirm = messagebox.askyesno("Remove Block", "Do you want to remove this block?")
        if confirm:
            self.current_unit.remove_block(block=block, slot=slot_id)
            self.buttons[slot_id].config(text="", state=tk.NORMAL, style="Empty.TButton")

# Example usage
if __name__ == "__main__":
    root = tk.Tk()

    allocation = Allocation(1)
    allocation.load_example_blocklist(80)
    allocation.load_example_unitlist(80, 80)
    allocation.load(fname="alc1.json")
    app = ScheduleApp(root, allocation)
    root.mainloop()
