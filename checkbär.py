from Wählbär import Allocation, Schedule
from IO import export_to_pdf, read_from_xlsx, load_blocklist, load_unitlist

def main():
    a = Allocation(1)
    load_blocklist(a)
    load_unitlist(a)

    add_dusche_series(a)
    add_nacht_series(a)
    add_wald_series(a)
    add_bogenscheissen_series(a)
    add_feuerwehr_series(a)

    read_from_xlsx(a)

    CLI(a)


def CLI(allocation):
    while True:
        print("\nGib ein 'xe 123' um Einheit 123 zu exportieren oder 'le 123' um die Liste von Einheit 123 anzuzeigen:")
        user_input = input("> ").strip()
        if user_input.lower() in ["exit", "quit", "q"]:
            break
        if user_input.startswith("xe ") and user_input != "xe all":
            unit_id = user_input[3:].strip()
            unit = allocation.get_unit_by_ID(unit_id)
            if unit:
                export_to_pdf(unit)
            else:
                print(f"Einheit mit ID '{unit_id}' nicht gefunden.")
        elif user_input.startswith("xe all"):
            export(allocation)
        elif user_input.startswith("le "):
            unit_id = user_input[3:].strip()
            unit = allocation.get_unit_by_ID(unit_id)
            if unit:
                print(f"Liste Einheit {unit.ID}:")
                for slot in unit.schedule.get_list(with_slot=True):
                    print(f"  Slot {slot['slot']}: {slot['element'].ID}")
            else:
                print(f"Einheit mit ID '{unit_id}' nicht gefunden.")


def add_dusche_series(allocation):
    allocation.generate_block_series(
        "OTH-DU", 
        4, 
        {
            "fullname": "Dusche", 
            "cat": "dusche", 
            "js_type": "None", 
            "space": 99, 
            "length": 1, 
            "group": ["wo", "pf", "pi"], 
            "tags": set(["same_day"]), 
            "on_times": [0, 1, 2, 3],
            "on_days": [1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12],
            "on_slots": ['C0', 'C1', 'C2', 'C3', 'D0', 'D1', 'D2', 'D3', 'E0', 'E1', 'E2', 'E3', 'F0', 'F1', 'F2', 'F3', 'G0', 'G1', 'G2', 'G3', "I0", "I1", "I2", "I3", "J0", "J1", "J2", "J3", "K0", "K1", "K2", "K3", "L0", "L1", "L2", "L3"],
            "verteilungsprio": 5,
            "state": "Aktiv",
            "mix_units": False
        }
    )

def add_nacht_series(allocation):
    main_block = allocation.get_block_by_ID("ON-05")
    index = allocation.BLOCKS.index(main_block)
    allocation.BLOCKS.remove(main_block)
    main_block.data["tags"].add("same_day")
    allocation.generate_block_series(
        "ON-05",
        10,
        main_block.data,
        index=index
    )

def add_wald_series(allocation):
    main_block = allocation.get_block_by_ID("ON-08")
    index = allocation.BLOCKS.index(main_block)
    allocation.BLOCKS.remove(main_block)
    main_block.data["tags"].add("same_day")
    allocation.generate_block_series(
        "ON-08",
        8,
        main_block.data,
        index=index
    )

def add_feuerwehr_series(allocation):
    main_block = allocation.get_block_by_ID("OFF-3")
    index = allocation.BLOCKS.index(main_block)
    allocation.BLOCKS.remove(main_block)
    allocation.generate_block_series(
        "OFF-3",
        5,
        main_block.data,
        index=index
    )

def add_bogenscheissen_series(allocation):
    main_block = allocation.get_block_by_ID("OFF-2")
    index = allocation.BLOCKS.index(main_block)
    allocation.BLOCKS.remove(main_block)
    allocation.generate_block_series(
        "OFF-2",
        4,
        main_block.data,
        index=index
    )

    allocation.get_block_by_ID("OFF-2_A").data["on_slots"] = ['D1', 'G0']
    
    data_afternoon = main_block.data.copy()
    data_afternoon["on_slots"] = ['G1']

    allocation.get_block_by_ID("OFF-2_B").data = data_afternoon
    allocation.get_block_by_ID("OFF-2_C").data = data_afternoon
    allocation.get_block_by_ID("OFF-2_D").data = data_afternoon

def export(allocation):
    total = len(allocation.UNITS)
    for i, unit in enumerate(allocation.UNITS):
        print(f"\r({i+1:>3}/{total}) Export PDF for unit {unit.ID} ... ", end="")
        export_to_pdf(unit)


if __name__ == "__main__":
    main()