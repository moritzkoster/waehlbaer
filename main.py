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

def allocate_cat(a, cat, print_enabled=False):  
    for unit in a.UNITS:
        if unit.general[cat]:
            unmatched = unit.get_all_unmatched_by_cat(cat)
            if unmatched:
                for prio in unmatched:
                    block = a.get_block_by_ID(prio["ID"])
                    assigned = try_assign(unit, block, print_enabled)
                    if assigned:
                        break
            
def allocate_block(a, blockID, print_enabled=False):
    block = a.get_block_by_ID(blockID)
    for unit in a.UNITS: 
        assigned = try_assign(unit, block, print_enabled)

def allocate_block_vp_first(a, blockID, print_enabled=False):
    block = a.get_block_by_ID(blockID)
    a.UNITS = sorted(a.UNITS, key=lambda u: u.prios[block.ID], reverse=True)
    for unit in a.UNITS:
        if unit.prios.get(block.ID, 0) >= 0:
            assigned = try_assign(unit, block, print_enabled)


def allocate_flussbaden(allocation, print_enabled=False): # TODO
    for unit in allocation.UNITS:
        if unit.general["flussbaden"]:
            for ID in ["OFF-21", "OFF-22", "OFF-23"]:
                block = allocation.get_block_by_ID(ID)  
                assigned = try_assign(unit, block, print_enabled)
                if assigned:
                    break

def allocate_wanderung(allocation, print_enabled=False):
    for unit in allocation.UNITS:
        if unit.general["wanderung"]:
            
            assigned = False
            if "ein_zwei" in unit.general and unit.general["ein_zwei"] == "Zweitageswanderung":
                zt_prios = get_zt_prios(unit)
                for prio in zt_prios:
                    block = allocation.get_block_by_ID(prio["ID"])  
                    assigned = try_assign(unit, block, print_enabled)
                    if assigned:
                        break
                if not assigned:
                    et_prios = get_et_prios(unit)
                    for prio in et_prios:
                        block = allocation.get_block_by_ID(prio["ID"])  
                        assigned = try_assign(unit, block, print_enabled)
                        if assigned:
                            break
            else:
                et_prios = get_et_prios(unit)
                for prio in et_prios:
                    block = allocation.get_block_by_ID(prio["ID"])  
                    assigned = try_assign(unit, block, print_enabled)
                    if assigned:
                        break
                if not assigned:
                    zt_prios = get_zt_prios(unit)
                    for prio in zt_prios:
                        block = allocation.get_block_by_ID(prio["ID"])  
                        assigned = try_assign(unit, block, print_enabled)
                        if assigned:
                            break

    
def get_zt_prios(unit):
    prios = []
    for prio in unit.prios_sorted["wanderung"]:
        if prio["ID"] in ["OFF-17", "OFF-18", "OFF-19"]:
            prios.append({"ID": prio["ID"], "value": prio["value"]})
    return sorted(prios, key=lambda e: e["value"], reverse=True)

def get_et_prios(unit):
    prios = []
    for prio in unit.prios_sorted["wanderung"]:
        if prio["ID"] in ["OFF-8", "OFF-9", "OFF-10", "OFF-11", "OFF-12", "OFF-13", "OFF-14", "OFF-15", "OFF-16"]:
            prios.append({"ID": prio["ID"], "value": prio["value"]})
    return sorted(prios, key=lambda e: e["value"], reverse=True)  

def try_assign(unit, block, print_enabled=False):
    block_result = block.search_slots({"space": unit.n_people, "group": unit.group}, return_reason=True)
    if not block_result.slots:
        if print_enabled:
            print(f"{YELLOW}No block-slots found for block {block.ID} and unit {unit.ID}{RESET}")# N={unit.n_people}, G={unit.group}")
            print_reasons(block_result)
        return False
    unit_result = unit.search_slots(block.data, return_reason=True)
    if not unit_result.slots:
        if print_enabled:
            print(f"{YELLOW}No unit-slots found for unit {unit.ID} and block {block.ID}{RESET}")
            print_reasons(unit_result)
        return False
    matching = Schedule.matching_slots(unit_result.slots, block_result.slots)
    if matching:
        if "tags" in block.data and "sauber" in block.data["tags"]:
            matching = calculate_sauber_distance(unit, matching)
            # print(f"Matching slots with sauber distances: {matching}")
            matching = sorted(matching, key=lambda e: e["sauber_distance"], reverse=True)

        block.set_unit(unit, matching[0])
        return True
    else:
        if print_enabled:
            print(f"{YELLOW}No matching slots for block {block.ID} and unit {unit.ID}{RESET}")
    return False

def sort_by_score(a):
    a.UNITS = sorted(a.UNITS, key=lambda e: e.score())

def calculate_sauber_distance(unit, matching_slots):
    matched_with_distances = []
    for ms in matching_slots:
        if type(ms) == dict:
            slot = ms["slot"]
        else:
            slot = ms
        mindist = 99
        for entry in unit.schedule.get_list(with_slot=True):
            if "tags" in entry["element"].data and "sauber" in entry["element"].data["tags"]:
                mindist = min(mindist, abs(Schedule.to_idx(slot)[0] - Schedule.to_idx(entry["slot"])[0]))
        
        mindist = min(mindist, abs(Schedule.to_idx(slot)[0] - unit.present_on[0])) # distance to start
        mindist = min(mindist, abs(Schedule.to_idx(slot)[0] - unit.present_on[-1])) # distance to end
        if type(ms) == dict:
            ms["sauber_distance"] = mindist
            matched_with_distances.append(ms)
        else:
            matched_with_distances.append({"slot": slot, "sauber_distance": mindist})
    return matched_with_distances


def abera_kadabera_simsalabim(allocation):
    add_dusche_series(allocation)
    add_amtli_series(allocation)
    
    allocation.find_block_cats()
    # allocation.print_unitlist()
    # allocation.print_blocklist()

    # print(allocation.BLOCKS[5].__dict__); exit()
    add_freizeit(allocation)
    # allocate_cat(allocation, "wanderung", print_enabled=True)
    allocate_wanderung(allocation, print_enabled=True)
    sort_by_score(allocation) 
    allocate_cat(allocation, "ausflug", print_enabled=True)  
    sort_by_score(allocation)
    allocate_cat(allocation, "si-mo",   print_enabled=True) 
    sort_by_score(allocation) 
    allocate_cat(allocation, "workshop", print_enabled=True) 
    sort_by_score(allocation) 
    allocate_cat(allocation, "sportaktivitat", print_enabled=True) 
    sort_by_score(allocation) 
    allocate_cat(allocation, "wasser", print_enabled=True)
    sort_by_score(allocation) 
    allocate_cat(allocation, "workshop", print_enabled=True)
    sort_by_score(allocation)
    allocate_cat(allocation, "sportaktivitat", print_enabled=True)
    sort_by_score(allocation)
    allocate_cat(allocation, "sportaktivitat", print_enabled=True)
    sort_by_score(allocation) 
    allocate_cat(allocation, "wald", print_enabled=True)
    sort_by_score(allocation)
    allocate_cat(allocation, "wald", print_enabled=True)
    sort_by_score(allocation)
    allocate_cat(allocation, "wald", print_enabled=True)
    sort_by_score(allocation)
    allocate_cat(allocation, "nacht", print_enabled=True)
    sort_by_score(allocation)
    allocate_cat(allocation, "nacht", print_enabled=True)
    sort_by_score(allocation)
    allocate_flussbaden(allocation, print_enabled=True)
    # sort_by_score(allocation)
    # allocate_flussbaden(allocation, print_enabled=True) # Only one flussbaden block
    sort_by_score(allocation) 
    allocate_cat(allocation, "programmflache", print_enabled=True)
    sort_by_score(allocation)
    allocate_cat(allocation, "programmflache", print_enabled=True)
    sort_by_score(allocation) 
    allocate_block(allocation, "OTH-DU", print_enabled=True)
    sort_by_score(allocation)
    allocate_block(allocation, "OTH-DU", print_enabled=True)
    allocate_block(allocation, "OTH-AM", print_enabled=True)

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
    allocation.print_stats()
    write_to_xlsx(allocation, fname="alc1.xlsx")

    return allocation.stats()[0].sum()

def print_reasons(search_result):
    print(f" - " + "\n - ".join(search_result.reason))

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
            "verteilungsprio": 5,
            "mix_units": False
        }
    )

def add_amtli_series(allocation):
    allocation.generate_block_series(
        "OTH-AM", 
        4, 
        {
            "fullname": "Amtli", 
            "cat": "amtli", 
            "js_type": "None", 
            "space": 99, 
            "length": 1, 
            "group": ["wo", "pf", "pi"], 
            "tags": set(["same_day"]), 
            "on_times": [0, 1, 2],
            "on_days": [1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12],
            "verteilungsprio": 5,
            "mix_units": False
        }
    )


def add_freizeit(allocation):
    block_freizeit = allocation.get_block_by_ID("ON-39")
    block_freizeit.data["tags"].add("same_day")
    for unit in allocation.UNITS:
        if Schedule.to_idx(block_freizeit.data["on_slots"][0])[0] in unit.present_on:
            unit.set_block(block_freizeit,block_freizeit.data["on_slots"][0])
        if Schedule.to_idx(block_freizeit.data["on_slots"][1])[0] in unit.present_on:
            unit.set_block(block_freizeit,block_freizeit.data["on_slots"][1])


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


