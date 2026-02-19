from Wählbär import Allocation, Schedule
from IO import print_schedule, write_to_xlsx, load_blocklist, load_unitlist

a = Allocation(1)
load_blocklist(a)
load_unitlist(a)
a.find_block_cats()

RED = "\033[31m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
BOLD = "\033[1m"
RESET = "\033[0m"
i = 1

# PRINT UNITS
for unit in a.UNITS:
    print(unit)

# PRINT BLOCKS
for block in a.BLOCKS:
    print(block)

# SEARCH LAGRE UNITS

for unit in a.UNITS:
    if "large_unit" in unit.tags:
        print(f"{YELLOW}{i:>2}: Large Unit{RESET}: {unit.ID} with {unit.n_people} TN"); i+=1


