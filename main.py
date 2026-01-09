from Wählbär import Allocation, Schedule
import multiprocessing as mp
import time


from IO import print_schedule, write_to_xlsx, load_blocklist, load_unitlist

NUM_PROCESSES = 8

# sample random blocks of top n choices, no backtracing
# 

RED = "\033[31m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
BOLD = "\033[1m"
RESET = "\033[0m"


def allocate_wanderungen(a): # TODO
    a.UNITS = sorted(a.UNITS, key=lambda e: e.score())
    for unit in a.UNITS:
        if unit.general["wanderung"]:
            hp = unit.get_highest_unmatched_by_cat("wanderung")
            block = a.get_block_by_ID(hp["ID"])
            block_slots = block.search_slots({"space": unit.n_people, "group": unit.group})
            unit_slots = unit.search_slots({"cat": block.data["cat"]})
            matching = Schedule.matching_slots(unit_slots, block_slots)
            if matching:
                unit.set_block(block, matching[0])


def allocate_cat(a, cat):  
    for unit in a.UNITS:
        if unit.general[cat]:
            unmatched = unit.get_all_unmatched_by_cat(cat)
            if unmatched:
                for prio in unmatched:
                    block = a.get_block_by_ID(prio["ID"])
                    block_slots = block.search_slots({"space": unit.n_people, "group": unit.group})
                    unit_slots = unit.search_slots({"cat": block.data["cat"]})
                    matching = Schedule.matching_slots(unit_slots, block_slots)
                    if matching:
                        unit.set_block(block, matching[0])
                        break
                    else:
                        print(f"{YELLOW}Could not assign {cat} {prio['ID']} to unit {unit.ID}{RESET}")

def sort_by_score(a):
    a.UNITS = sorted(a.UNITS, key=lambda e: e.score())
            

def allocate_amtli(allocation): # TODO
    pass

def allocate_dusche(allocation): # TODO
    dusch_block = allocation.get_block_by_ID("OTH-DU")
    for unit in allocation.UNITS:
        block_slots = dusch_block.search_slots({"space": unit.n_people, "group": unit.group})
        unit_slots = unit.search_slots(dusch_block.data)
        matching = Schedule.matching_slots(unit_slots, block_slots)
        if matching:
            dusch_block.set_unit(unit, matching[0])
        else:
            print(f"{YELLOW}Could not assign 'dusche' to unit {unit.ID}{RESET}")

def allocate_flussbaden(allocation): # TODO
    for unit in allocation.UNITS:
        if unit.general["flussbaden"]:
            for ID in ["OFF-21", "OFF-22", "OFF-23"]:
                block = allocation.get_block_by_ID(ID)  

                block_slots = block.search_slots({"space": unit.n_people, "group": unit.group})
                unit_slots = unit.search_slots(block.data)
                matching = Schedule.matching_slots(unit_slots, block_slots)
                if matching:
                    block.set_unit(unit, matching[0])
                    break
                else:
                    print(f"{YELLOW}Could not assign 'flussbaden' to unit {unit.ID}{RESET}")
          

# ...

def abera_kadabera_simsalabim(allocation):
    allocation.generate_block_series(
        "OTH-DU", 
        5, 
        {
            "fullname": "Dusche", 
            "cat": "dusche", 
            "js_type": "None", 
            "space": 30, 
            "length": 1, 
            "group": ["wo", "pf", "pi"], 
            "tags": set(["same_day"]), 
            "on_times": [0, 1, 2, 3],
            "on_days": [1, 2, 3, 4, 5, 7, 8, 9, 10, 11],
            "verteilungsprio": 5
        }
    )
    allocation.find_block_cats()
    # allocation.print_unitlist()
    # allocation.print_blocklist()
    allocate_cat(allocation, "wanderung")  
    sort_by_score(allocation) 
    allocate_cat(allocation, "si-mo") 
    sort_by_score(allocation) 
    allocate_cat(allocation, "workshop") 
    sort_by_score(allocation) 
    allocate_cat(allocation, "sportaktivitat") 
    sort_by_score(allocation) 
    allocate_cat(allocation, "wasser")
    sort_by_score(allocation) 
    allocate_flussbaden(allocation)

    allocate_dusche(allocation) 

    allocate_amtli(allocation)
    # ...


def allocate_units(allocation):
    # the_magic_allocation_function(allocation)
    abera_kadabera_simsalabim(allocation)

def mp_worker(seed):
    allocation = Allocation(seed)
    # allocation.load_example_blocklist(80)
    # allocation.load_example_unitlist(80, N_Blocks=80)
    load_blocklist(allocation)
    load_unitlist(allocation)
    
    stime = time.time()
    allocation.evaluate(allocate_units)
    run_eval = time.time() - stime
    allocation.log_stats("log.txt", run_eval)
    allocation.save("a1.json")
    write_to_xlsx(allocation, fname="alc1.xlsx")

    return allocation.stats()[0].sum()

seeds = range(1)

# with mp.Pool(processes=NUM_PROCESSES) as pool:
#         # Map the function to the seeds
#         results = pool.map(mp_worker, seeds)
mp_worker(1)


def the_magic_allocation_function(allocation):
    for ir in range(15):
        allocation.UNITS = sorted(allocation.UNITS, key=lambda e: e.score())
        for unit in allocation.UNITS:
            for tries in range(10):

                hp = allocation.random.choice(unit.highest_unmatched_prios(N=6))
                if not hp:
                    break
                block = allocation.get_block_by_ID(hp["ID"])
                block_slots = block.search_slots({"space": unit.nPeople})
                unit_slots = unit.search_slots(block)
                matching = Schedule.matching_slots(unit_slots, block_slots)
                if matching:
                    unit.set_block(block, str(allocation.random.choice(matching)))
                    break

# ich glaub die isch ned ganz richtig, aber mengmal gits absolut insane gueti performance
# score vo 0.96 in 2s, fasch scho verdächtig guet 
def more_magic_recursive_allocation_function(allocation):
    def recursive_allocator(allocation, unit_idx, rnd):
        if unit_idx == 0:
            allocation.UNITS = sorted(allocation.UNITS, key=lambda e: e.score())
        unit = allocation.UNITS[unit_idx]

        for block_prio in unit.highest_unmatched_prios(4):
            block = allocation.get_block_by_ID(block_prio["ID"])
            block_slots = block.search_slots({"space": unit.n_people, "group": unit.data["group"]})
            unit_slots = unit.search_slots({"cat": block.data["cat"]})
            matching = Schedule.matching_slots(unit_slots, block_slots)
            if matching:
                for slot in matching:

                    unit.set_block(block, slot)

                    if unit_idx == len(allocation.UNITS) -1 and rnd == 11:
                        allocation.save("alc1.json")
                        return "FINISH" # finish calculation
                    
                    new_unit_idx, new_rnd = 0, 0
                    if unit_idx == len(allocation.UNITS) -1:
                        new_unit_idx = 0
                        new_rnd = rnd + 1
                    else: 
                        new_unit_idx = unit_idx + 1
                        new_rnd = rnd
                    
                    print(f"set for round {rnd} and unit {unit_idx}")
                    
                    resp = recursive_allocator(allocation, new_unit_idx, new_rnd)
                    if resp == "FINISH":
                        return "FINISH"
                    
                    print(f"Remove last block of round {rnd} and unit {unit_idx}")
                    unit.remove_block(block)
            # else:
                # print("NO MATCHING")

        print(f"BACKTRACE: Could not find a block for round {rnd} and unit {unit_idx}")
        return "BACKTRACE"
        
    recursive_allocator(allocation, 0, 1)




