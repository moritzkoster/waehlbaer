from Wählbär import Allocation, Schedule
import multiprocessing as mp
import time

from Utils import print_schedule, write_to_xlsx

NUM_PROCESSES = 8

# sample random blocks of top n choices, no backtracing
def the_magic_allocation_function(allocation):
    for ir in range(15):
        allocation.UNITS = sorted(allocation.UNITS, key=lambda e: e.score())
        for unit in allocation.UNITS:
            for tries in range(10):

                hp = allocation.random.choice(unit.highest_unmatched_prios(N=6))
                if not hp:
                    break
                block = allocation.get_block_by_name(hp["name"])
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
            block = allocation.get_block_by_name(block_prio["name"])
            block_slots = block.search_slots({"space": unit.nPeople})
            unit_slots = unit.search_slots()
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
                    
                    print("BACKTRACE")
                    unit.remove_block(block)
            else:
                print("NO MATCHING")

        return "BACKTRACE"
        
    recursive_allocator(allocation, 0, 1)



        

def allocate_units(allocation):
    # the_magic_allocation_function(allocation)
    more_magic_recursive_allocation_function(allocation)

def mp_worker(seed):
    allocation = Allocation(seed)
    allocation.load_example_blocklist(80)
    allocation.load_example_unitlist(80, N_Blocks=80)
    stime = time.time()
    allocation.evaluate(allocate_units)
    run_eval = time.time() - stime
    allocation.log_stats("log.txt", run_eval)
    write_to_xlsx(allocation)

    return allocation.stats()[0].sum()

seeds = range(1)

with mp.Pool(processes=NUM_PROCESSES) as pool:
        # Map the function to the seeds
        results = pool.map(mp_worker, seeds)


