from Wählbär import Allocation, Schedule
import multiprocessing as mp
import time


from IO import print_schedule, write_to_xlsx, load_blocklist, load_unitlist, FORMAT

# RED = "\033[31m"
# YELLOW = "\033[33m"
# GREEN = "\033[32m"
# BOLD = "\033[1m"
# RESET = "\033[0m"

def allocate_cat(a, cat, print_enabled=False):  
    for unit in a.UNITS:
        if unit.general[cat]:
            unmatched = unit.get_all_unmatched_by_cat(cat)
            if unmatched:
                for prio in unmatched:
                    if prio["value"] >= 0:
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

def allocate_nacht(allocation, print_enabled=False):
    block = allocation.get_block_by_ID("ON-05")  
    for unit in allocation.UNITS:
        if not unit.is_nacht_satisfied():
            assigned = try_assign(unit, block, print_enabled)

def allocate_wald(allocation, print_enabled=False):
    block = allocation.get_block_by_ID("ON-08")  
    for unit in allocation.UNITS:
        if not unit.is_wald_satisfied():
            assigned = try_assign(unit, block, print_enabled)

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
        if prio["ID"] in ["OFF-17", "OFF-18", "OFF-19"] and prio["value"] >= 0:
            prios.append({"ID": prio["ID"], "value": prio["value"]})
    return sorted(prios, key=lambda e: e["value"], reverse=True)

def get_et_prios(unit):
    prios = []
    for prio in unit.prios_sorted["wanderung"]:
        if prio["ID"] in ["OFF-8", "OFF-9", "OFF-10", "OFF-11", "OFF-12", "OFF-13", "OFF-14", "OFF-15", "OFF-16"] and prio["value"] >= 0:
            prios.append({"ID": prio["ID"], "value": prio["value"]})
    return sorted(prios, key=lambda e: e["value"], reverse=True)  

def try_assign(unit, block, print_enabled=False):
    block_result = block.search_slots({"space": unit.n_people, "group": unit.group}, return_reason=True)
    if not block_result.slots:
        if print_enabled:
            print(f"{FORMAT.YELLOW}No block-slots found for block {block.ID} and unit {unit.ID}{FORMAT.RESET}")# N={unit.n_people}, G={unit.group}")
            print_reasons(block_result)
        return False
    unit_result = unit.search_slots(block.data, return_reason=True)
    if not unit_result.slots:
        if print_enabled:
            print(f"{FORMAT.YELLOW}No unit-slots found for unit {unit.ID} and block {block.ID}{FORMAT.RESET}")
            print_reasons(unit_result)
        return False
    matching = Schedule.matching_slots(unit_result.slots, block_result.slots)
    if matching:
        if "tags" in block.data and "sauber" in block.data["tags"]:
            matching = calculate_sauber_distance(unit, matching)
            # print(f"Matching slots with sauber distances: {matching}")
            matching = sorted(matching, key=lambda e: e["sauber_distance"], reverse=True)

        block.set_unit(unit,matching[0])
        return True
    else:
        if print_enabled:
            print(f"{FORMAT.YELLOW}No matching slots for block {block.ID} and unit {unit.ID}{FORMAT.RESET}")
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


def add_freizeit(allocation):
    block_freizeit = allocation.get_block_by_ID("ON-39")
    block_freizeit.data["tags"].add("same_day")
    for unit in allocation.UNITS:
        if Schedule.to_idx(block_freizeit.data["on_slots"][0])[0] in unit.present_on:
            unit.set_block(block_freizeit,block_freizeit.data["on_slots"][0])
        if Schedule.to_idx(block_freizeit.data["on_slots"][1])[0] in unit.present_on:
            unit.set_block(block_freizeit,block_freizeit.data["on_slots"][1])

def add_pfadifun(allocation):
    block_pfadifun = allocation.get_block_by_ID("ON-01")
    block_pfadifun.data["tags"].add("same_day")
    
    for unit in allocation.UNITS:
        if "pfadifun" in unit.general and unit.general["pfadifun"]:
            unit.set_block(block_pfadifun,block_pfadifun.data["on_slots"][0])
    
def add_wolfstrail(allocation):
    wolfstrail_block = allocation.get_block_by_ID("ON-16")
    units_first_week = []
    units_second_week = []
    for unit in allocation.UNITS:
        if "wolfstrail" in unit.general and unit.general["wolfstrail"]:
            if unit.present_on[0] == 1:
                units_first_week.append(unit)
            else:
                units_second_week.append(unit)
                
    print(len(units_first_week), len(units_second_week))

    # TODO zuweisen von hand:
    wolfstrail_block.set_unit(units_first_week[0], "D1")
    wolfstrail_block.set_unit(units_first_week[1], "D1")
    wolfstrail_block.set_unit(units_first_week[2], "D1")
    wolfstrail_block.set_unit(units_first_week[3], "B2")
    wolfstrail_block.set_unit(units_first_week[4], "B2")
    wolfstrail_block.set_unit(units_first_week[5], "B2")
    wolfstrail_block.set_unit(units_first_week[6], "B2")
    wolfstrail_block.set_unit(units_first_week[7], "B1")
    wolfstrail_block.set_unit(units_first_week[8], "B1")
    wolfstrail_block.set_unit(units_first_week[9], "B1")
    # wolfstrail_block.set_unit(units_first_week[10], "B1")

    # Second week assignments
    wolfstrail_block.set_unit(units_second_week[0], "L1")
    wolfstrail_block.set_unit(units_second_week[1], "L1")
    wolfstrail_block.set_unit(units_second_week[2], "L1")
    wolfstrail_block.set_unit(units_second_week[3], "I2")
    wolfstrail_block.set_unit(units_second_week[4], "I2")
    wolfstrail_block.set_unit(units_second_week[5], "I2")
    wolfstrail_block.set_unit(units_second_week[6], "I2")
    wolfstrail_block.set_unit(units_second_week[7], "I1")
    wolfstrail_block.set_unit(units_second_week[8], "I1")
    wolfstrail_block.set_unit(units_second_week[9], "I1")
    wolfstrail_block.set_unit(units_second_week[10], "I1")



def abera_kadabera_simsalabim(allocation):
    add_dusche_series(allocation)
    add_amtli_series(allocation)
    add_nacht_series(allocation)
    add_wald_series(allocation)
    add_feuerwehr_series(allocation)
    add_bogenscheissen_series(allocation)

    twin_blocks(allocation, "ON-28", "ON-29")
    twin_blocks(allocation, "ON-36", "ON-37")

    allocation.get_block_by_ID("ON-05").data["cat"] = "nacht"
    allocation.get_block_by_ID("ON-08").data["cat"] = "wald"    
    
    allocation.find_block_cats()
    # allocation.print_unitlist()
    # allocation.print_blocklist()

    add_freizeit(allocation)
    add_pfadifun(allocation)
    add_wolfstrail(allocation)
    add_anlässe(allocation)

    allocate_wanderung(allocation, print_enabled=False)
    sort_by_score(allocation) 
    allocate_cat(allocation, "ausflug", print_enabled=False)  
    sort_by_score(allocation)
    allocate_cat(allocation, "si-mo",   print_enabled=False) 
    sort_by_score(allocation) 
    allocate_cat(allocation, "workshop", print_enabled=False) 
    sort_by_score(allocation) 
    allocate_cat(allocation, "sportaktivitat", print_enabled=False) 
    sort_by_score(allocation) 
    allocate_cat(allocation, "wasser", print_enabled=False)
    sort_by_score(allocation) 
    allocate_cat(allocation, "workshop", print_enabled=False)
    sort_by_score(allocation)
    allocate_cat(allocation, "sportaktivitat", print_enabled=False)
    sort_by_score(allocation)
    allocate_cat(allocation, "sportaktivitat", print_enabled=False)
    
    for i in range(6): # assigne 6 rounds of wald
        sort_by_score(allocation)
        allocate_wald(allocation, print_enabled=False)
    for i in range(4): # assign 4 rounds of nachtaktivität
        sort_by_score(allocation)
        allocate_nacht(allocation, print_enabled=False)
    
    sort_by_score(allocation)
    allocate_flussbaden(allocation, print_enabled=False)
   
    sort_by_score(allocation) 
    allocate_cat(allocation, "programmflache", print_enabled=False)
    sort_by_score(allocation)
    allocate_cat(allocation, "programmflache", print_enabled=False)
    sort_by_score(allocation) 
    allocate_block(allocation, "OTH-DU", print_enabled=False)
    sort_by_score(allocation)
    allocate_block(allocation, "OTH-DU", print_enabled=False)

    allocate_block(allocation, "OTH-AM", print_enabled=False)

    allocation.remve_KC_from_all_blocks() # remove KC from blocks, so that they can be assigned to other units if needed


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

def add_anlässe(allocation):

    eroffnungsfeier = allocation.get_block_by_ID("ON-40")
    schluss_wölfe = allocation.get_block_by_ID("ON-41")
    eroffnung_wolfe = allocation.get_block_by_ID("ON-42")
    schlussfeier = allocation.get_block_by_ID("ON-43")
    anreise_wölfe = allocation.get_block_by_ID("ON-44")


    for unit in allocation.UNITS:
        if Schedule.to_idx(eroffnungsfeier.data["on_slots"][0])[0] in unit.present_on:
            unit.set_block(eroffnungsfeier, eroffnungsfeier.data["on_slots"][0])
        if Schedule.to_idx(schluss_wölfe.data["on_slots"][0])[0] in unit.present_on and unit.group == "wo":
            unit.set_block(schluss_wölfe, schluss_wölfe.data["on_slots"][0])
        if Schedule.to_idx(eroffnung_wolfe.data["on_slots"][0])[0] in unit.present_on and unit.group == "wo":
            unit.set_block(eroffnung_wolfe, eroffnung_wolfe.data["on_slots"][0])
        if Schedule.to_idx(schlussfeier.data["on_slots"][0])[0] in unit.present_on:
            unit.set_block(schlussfeier, schlussfeier.data["on_slots"][0])
        if Schedule.to_idx(anreise_wölfe.data["on_slots"][0])[0] in unit.present_on and unit.group == "wo":
            unit.set_block(anreise_wölfe, anreise_wölfe.data["on_slots"][0])
        if Schedule.to_idx(anreise_wölfe.data["on_slots"][1])[0] in unit.present_on and unit.group == "wo":
            unit.set_block(anreise_wölfe, anreise_wölfe.data["on_slots"][1])

        
     


def add_amtli_series(allocation):
    allocation.generate_block_series(
        "OTH-AM", 
        0, 
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
            "on_slots": ['B0', 'B1', 'B2', 'C0', 'C1', 'C2', 'D0', 'D1', 'D2', 'E0', 'E1', 'E2', 'F0', 'F1', 'F2', 'G0', 'G1', 'G2', "H0", "H1", "H2", "I0", "I1", "I2", "J0", "J1", "J2", "K0", "K1", "K2", "L0", "L1", "L2", "M0", "M1", "M2"],
            "state": "Aktiv",
            "verteilungsprio": 5,
            "mix_units": False
        }
    )


def twin_blocks(allocation, blockID1, blockID2):
    block1 = allocation.get_block_by_ID(blockID1)
    block2 = allocation.get_block_by_ID(blockID2)
    block1.twin_block = block2
    block2.twin_block = block1
  

def main(seed):


    allocation = Allocation(seed) # crete allocation with seed for reproducibility (seed is unused in this version)

    load_blocklist(allocation) # load blocks from xlsx
    load_unitlist(allocation) # load units from xlsx
    
    stime = time.time() # save start time for runtime evaluation

    abera_kadabera_simsalabim(allocation) # do magic stuff

    run_eval = time.time() - stime # calculate runtime
    allocation.log_stats("log.txt", run_eval)
    allocation.save("a1.json") 
    allocation.print_stats() 
    write_to_xlsx(allocation, fname="alc1.xlsx")

    return allocation.stats()[0].sum()

if __name__ == "__main__": 
    main(1) # exectue main allocation function with seed 1