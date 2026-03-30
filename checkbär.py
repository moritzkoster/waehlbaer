from IO import (
    export_block_to_pdf,
    export_to_pdf,
    load_blocklist,
    load_unitlist,
    read_from_xlsx,
)
from main import (
    add_amtli_series,
    add_bogenscheissen_series,
    add_dusche_series,
    add_feuerwehr_series,
    add_nacht_series,
    add_wald_series,
)
from Wählbär import Allocation, Schedule


def main():
    a = Allocation(1)
    load_blocklist(a)
    load_unitlist(a)

    add_dusche_series(a)
    add_nacht_series(a)
    add_wald_series(a)
    add_bogenscheissen_series(a)
    add_feuerwehr_series(a)

    read_from_xlsx(a, filename="PRG_Programmzuteilung_allocation.xlsx")

    CLI(a)


def CLI(allocation):
    while True:
        print(
            "\nGib ein 'xe 123' um Einheit 123 zu exportieren oder 'le 123' um die Liste von Einheit 123 anzuzeigen:"
        )
        user_input = input("> ").strip()
        if user_input.lower() in ["exit", "quit", "q"]:
            break
        cmd = user_input.split(" ")[0].lower()
        args = (
            user_input[len(cmd) :].strip().split(" ")
            if len(user_input) > len(cmd)
            else []
        )

        if cmd == "xe":
            if args and args[0].lower() == "all":
                export(allocation)
            elif args:
                for unit_id in args:
                    unit = allocation.get_unit_by_ID(unit_id)
                    if unit:
                        export_to_pdf(unit)
                    else:
                        print(f"Einheit mit ID '{unit_id}' nicht gefunden.")
            else:
                print(
                    "Bitte gib eine Einheit-ID oder 'all' an, z.B. 'xe 123' oder 'xe all'."
                )

        elif cmd == "le":
            if args:
                for unit_id in args:
                    unit = allocation.get_unit_by_ID(unit_id)
                    if unit:
                        print(f"Liste Einheit {unit.ID}:")
                        for slot in unit.schedule.get_list(with_slot=True):
                            print(f"  Slot {slot['slot']}: {slot['element'].ID}")
                    else:
                        print(f"Einheit mit ID '{unit_id}' nicht gefunden.")
            else:
                print("Bitte gib eine oder mehrere Einheit-ID an, z.B. 'le 123'.")

        elif cmd == "lb":
            if args:
                for block_id in args:
                    block = allocation.get_block_by_ID(block_id)
                    if block:
                        print(f"Block {block.ID} ({block.data['fullname']}):")
                        for slot in block.schedule.get_list(with_slot=True):
                            print(f"  Slot {slot['slot']}: {slot['element'].ID}")
                    else:
                        print(f"Block mit ID '{block_id}' nicht gefunden.")
            else:
                print("Bitte gib eine oder mehrere Block-ID an, z.B. 'lb ON-05'.")

        elif cmd == "xb":
            if args and args[0].lower() == "all":
                for block in allocation.BLOCKS:
                    if block.is_active:
                        print(
                            f"Export block {block.ID} ({block.data['fullname']})...",
                        )
                        export_block_to_pdf(block)
                    else:
                        print(
                            f"Block {block.ID} ({block.data['fullname']}) ist inaktiv, überspringe..."
                        )
            elif args:
                for block_id in args:
                    block = allocation.get_block_by_ID(block_id)
                    if block:
                        print(f"Export block {block.ID} ({block.data['fullname']}):")
                        export_block_to_pdf(block)
                    else:
                        print(f"Block mit ID '{block_id}' nicht gefunden.")
            else:
                print(
                    "Bitte gib eine Block-ID oder 'all' an, z.B. 'xb ON-05' oder 'xb all'."
                )

        else:
            print("Unbekannter Befehl. Bitte versuche es erneut [xe|le|lb|xb].")


def export(allocation):
    total = len(allocation.UNITS)
    for i, unit in enumerate(allocation.UNITS):
        print(f"\r({i + 1:>3}/{total}) Export PDF for unit {unit.ID} ... ", end="")
        export_to_pdf(unit)


if __name__ == "__main__":
    main()
