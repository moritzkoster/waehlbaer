from Wählbär import Allocation, Schedule
from IO import print_schedule, write_to_xlsx, load_blocklist, load_unitlist, export_TN_overwiew_to_xlsx
from checkbär import add_dusche_series, add_nacht_series, add_wald_series, add_bogenscheissen_series, add_feuerwehr_series, read_from_xlsx

RED = "\033[31m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
BOLD = "\033[1m"
RESET = "\033[0m"

a = Allocation(1)
load_blocklist(a)
load_unitlist(a)

add_dusche_series(a)
add_nacht_series(a)
add_wald_series(a)
add_bogenscheissen_series(a)
add_feuerwehr_series(a)

read_from_xlsx(a, filename="PRG_Programmzuteilung_allocation.xlsx")

export_TN_overwiew_to_xlsx(a, fname="TN_Overview.xlsx")

N = 0
for unit in a.UNITS:
    for ass in unit.schedule.get_list():
        N +=  1

print(f"Total assignments: {N}")
# PRINT UNITS

# for unit in a.UNITS:
#     print(unit)

# # PRINT BLOCKS
# for block in a.BLOCKS:
#     print(block)

# # SEARCH LAGRE UNITS

# for unit in a.UNITS:
#     if "large_unit" in unit.tags:
#         print(f"{YELLOW}{i:>2}: Large Unit{RESET}: {unit.ID} with {unit.n_people} TN"); i+=1


