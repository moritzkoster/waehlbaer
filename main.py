from Wählbär import Allocation, Schedule
import multiprocessing as mp
import time

from Utils import print_schedule

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

def allocate_units(allocation):
    the_magic_allocation_function(allocation)

def mp_worker(seed):
    allocation = Allocation(seed)
    allocation.load_example_blocklist(80)
    allocation.load_example_unitlist(80, N_Blocks=80)
    stime = time.time()
    allocation.evaluate(allocate_units)
    run_eval = time.time() - stime
    allocation.log_stats("log.txt", run_eval)
    return allocation.stats()[0].sum()

seeds = range(8)

with mp.Pool(processes=NUM_PROCESSES) as pool:
        # Map the function to the seeds
        results = pool.map(mp_worker, seeds)

print(results)

