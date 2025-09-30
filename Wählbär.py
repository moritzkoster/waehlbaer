import numpy as np
import pandas as pd
import json
import random
import os

SLOTS_PER_DAY = 4
DAYS = 14

NRANKS = 5

class Schedule: 
    def __init__(self, owner):
        self.calendar = [[[] for _ in range(SLOTS_PER_DAY)] for __ in range(DAYS)]
        self.owner = owner

    def __getitem__(self, ipt):
        day, time = self.to_idx(ipt)
        return self.calendar[day][time]
    
    def clear(self):
        self.calendar = [[[] for _ in range(SLOTS_PER_DAY)] for __ in range(DAYS)]

    def get_block(self, ipt):
        # day, slot = self.ipt_to_idx(ipt)
        return self[ipt]

    def get_list(self, with_slot=False, names_only=False):
        l = []
        for idd, day in enumerate(self.calendar):
            for it, time in enumerate(day):
                for entry in time:
                    if with_slot:
                        if names_only:
                            l.append({"slot": self.idx2str(idd, it), "name": entry.name})
                        else:
                            l.append({"slot": self.idx2str(idd, it), "element": entry})
                    else:
                        if names_only:
                            l.append(entry.name)
                        else:
                            l.append(entry)
        return l
    
    @staticmethod
    def to_idx(ipt):
        if type(ipt) == tuple or type(ipt) == str:
            if len(ipt) > 2:
                print(f"ERROR: weird input: '{ipt}' len to long")
            day, time = ipt
        else:
            print(f"ERROR: weird input: '{type(ipt)}' not tuple or str")

        if type(day) == str:
            if ord(day) >=97:
                day = ord(day) - 97
            else:
                day = ord(day) - 65
        time = int(time)
        
        if day >= DAYS:
            print("INDEX OF DAY TOO LARGE")
            return None
        if time >= SLOTS_PER_DAY:
            print("INDEX OF SLOT TOO LARGE")
            return None
        return day, time
    
    def idx2str(self, day, time):
        return chr(day+65)+str(time)
    
    
    def set_entry(self, entry, slot):
        self[slot].append(entry)
  
    # sets block for unit
    def set_block(self, block, slot):
        self.set_entry(block, slot)
        block.schedule.set_entry(self.owner, slot)

    # sets unit for block
    def set_unit(self, unit, slot):
        self.set_entry(unit, slot)
        unit.schedule.set_entry(self.owner, slot)

    def remove_entry(self, entry=None, slot=None):
        if type(entry) != Block and type(entry) != Unit:
            print(f"ERROR: entry type ({type(entry)}) is wrong, expected 'Block()' or 'Unit()'"); return 0
        if not entry and not slot:
            print("ERROR: bro what?? remove what?"); return 0
    
        if entry and slot:
            if entry in self.schedule[slot]:
                self.schedule[slot].remove()
                return 0
        
        if entry:
            for idd, day in enumerate(self.schedule.calendar):
                for itt, time in enumerate(day):
                    if entry in time:
                        self.schedule[(idd, itt)].remove(entry)
                        return 0
            print(f"ERROR: couldnt find entry with name {entry.name} in schedule"); return 0
        
        if slot:
            if len(self.schedule[slot]) == 1:
                self.schedule[slot].clear()
                return 0
            if len(self.schedule[slot]) == 0:
                print("ERROR: slot already empty"); return 0
            print(f"ERROR: more than one block in slot. Be more specific"); return 0

    def remove_block(self, block=None, slot=None):
        if type(self.owner) == Block: print("ERROR: cannot remove block from Block()")
        self.remove_entry(block, slot)
        block.schedule.remove_entry(self.owner, slot)
    
    def remove_unit(self, unit=None, slot=None):
        if type(self.owner) == Unit: print("ERROR: cannot remove unit from Unit()")
        self.remove_entry(unit, slot)
        unit.schedule.remove_entry(self.owner, slot)

    def free_slots(self):
        slot_list = []
        for idd, day in enumerate(self.calendar):
            for iss, slot in enumerate(day):
                if type(self.owner) == Block:

                    if self.owner.get_space((idd, iss)) > 0:
                        slot_list.append({"slot":self.idx2str(idd, iss), "space": self.owner.get_space((idd, iss))})
                else:
                    if slot == []:
                        slot_list.append(self.idx2str(idd, iss))
        return slot_list
    
    @staticmethod
    def matching_slots(first, second):
        matching = []
        for slot in first:
            if slot in second:
                matching.append(slot)
        return matching
    
def soft_assign_musthave_blocks(slot, self, block_req):
    # TODO: check if it is possible the have 2d hike and staff later
    return True

def no_two_on_same_day(slot, self, block):
    for time in self.schedule.calendar[Schedule.to_idx(slot)[0]]:
        if time:
            return False
    return True  

def no_two_water_activities(slot, self, block_req):
    for idd, day in enumerate(self.schedule.calendar):
        for iss, time in enumerate(day):
            for block in time:
                if hasattr(block, "cath") and block.cath == "water_activity":
                    return False
    return True 

UNIT_RULES = [
    soft_assign_musthave_blocks,
    no_two_on_same_day,
    no_two_water_activities
]


BLOCK_RULES = [
    lambda slot, self, unit_req : self.get_space(slot) >= unit_req["space"],
    lambda slot, self, unit_req : False if "on_days"     in self.requirements and Schedule.to_idx(slot)[0] not in self.requirements["on_days"]  else True,
    lambda slot, self, unit_req : False if "on_times"    in self.requirements and Schedule.to_idx(slot)[1] not in self.requirements["on_times"] else True,
    lambda slot, self, unit_req : False if "not_in_slot" in self.requirements and slot in self.requirements["not_in_slot"] else True,

    lambda slot, self, unit_req : False if "on_days"  in unit_req and Schedule.to_idx(slot)[0] not in unit_req["on_days"]  else True,
    lambda slot, self, unit_req : False if "on_times" in unit_req and Schedule.to_idx(slot)[1] not in unit_req["on_times"] else True,
]

class Block:
    def __init__(self, name, requirements):
        self.name = name
        self.requirements = requirements
        self.schedule = Schedule(self)

        self.rules = BLOCK_RULES

    def get_space(self, slot):
        taken = 0
        for unit in self.schedule[slot]:
            taken += unit.nPeople
        return self.requirements["space"] - taken
    
    def set_unit(self, unit, slot):
        self.schedule.set_unit(unit, slot)  

    def remove_unit(self, unit=None, slot=None):
        self.schedule.remove_unit(self, unit, slot)
  
    # returns free slots of block
    # accounts for other units, block requirements
    # groups slots per day, so that days are filled first
    # returns [[best1, best2], [sec1, ...]]

    def search_slots(self, requirements):
        slots = []

        for iss, slot in enumerate(self.schedule.free_slots()):
            matching = True
            for rule in self.rules:
                if not rule(slot["slot"], self, requirements):
                    matching = False
                    break
            if matching:
                slots.append(slot["slot"])
        return slots

    def to_dict(self):
        unit_list = self.schedule.get_list(with_slot=True, names_only=True)
        d = {
            "type": "block",
            "name": self.name,
            "requirements": self.requirements,
            "schedule": unit_list
            }
        return d

class Unit: 
    def __init__(self, name, nPeople, prios):
        self.name = name
        self.nPeople = nPeople
        self.prios = sorted(prios, key=lambda d: d['rank'])
        
        self.schedule = Schedule(self)
        self.rules = UNIT_RULES

    def set_block(self, block, slot):
        self.schedule.set_block(block, slot)
    
    def remove_block(self, block=None, slot=None):
        self.schedule.remove_block(block, slot)
    
    def remove_block(self, entry=None, slot=None):
        if type(entry) != Block and type(entry) :
                print(f"ERROR: entry type ({type(entry)}) is wrong, expected 'Block()' or 'Unit()'"); return 0
        if entry and slot:
            if entry in self.schedule[slot]:
                self.schedule[slot].remove()
                return 0
        if entry:
            for idd, day in enumerate(self.schedule.calendar):
                for itt, time in enumerate(day):
                    if entry in time:
                        self.schedule[(idd, itt)].remove(entry)
                        return 0
            print(f"ERROR: couldnt find entry with name {entry.name} in schedule"); return 0
        
        if slot:
            if len(self.schedule[slot]) == 1:
                self.schedule[slot].clear()
                return 0
            if len(self.schedule[slot]) == 0:
                print("ERROR: slot already empty"); return 0
            print(f"ERROR: more than one block in slot. Be more specific"); return 0
        
        print("ERROR: bro what?? remove what?"); return 0
    
    def rank(self, block):
        blockname = str_from_block(block)

        for prio in self.prios:
            if blockname == prio["name"]:
                return prio["rank"]
        print("ERROR: block not in Prio")
        return NRANKS
    
    # define how the score is calculated 
    # TODO: Is this the Way???
    def score(self):
        return self.score_sum_norm()
    
    def score_sum_prios(self):  
        score = 0     
        for block in self.schedule.get_list():
            score += NRANKS - (self.rank(block)) # TODO: is this the way???
        return score
   
    def score_top_N(self, N, p=False):
        score = 0
        sorter = lambda d: d["rank"] - 0.1 * self.has_block(d)
        top_N = sorted(self.prios, key=sorter)[:N]

        if p:
            for p in top_N:
                print(f"{p['rank']}: {self.has_block(p)} ", end="")
            print("")

        for block in top_N:
            if self.has_block(block):
                score += 1 
        return score

    def score_sum_norm(self):
        if not hasattr(self, "norm_const"):
            self.norm_const = np.array([NRANKS - p["rank"] for p in self.prios]).sum()
            if self.norm_const == 0: 
                print("WARNING: all prios are 5")
                return 1
        sum_ = 0
        for prio in self.prios:
            sum_ += self.has_block(prio) * (NRANKS - prio["rank"])
        return sum_ / self.norm_const
    
    def has_block(self, block):
        blockname = str_from_block(block)

        for block in self.schedule.get_list():
            if block.name == blockname:
                return True
        return False
    
    # returns free slots for blocks
    # accounts for: need for visit day, 1d/2d hike, ...
    # accounts for block requirements (1 slot, 2 slots, ...)
    def search_slots(self, block_req):
        slots = []
        free_slots = self.schedule.free_slots()
        if free_slots:
            for iss, slot in enumerate(self.schedule.free_slots()):
                matching = True
                for rule in self.rules:
                    if not rule(slot, self, block_req):
                        matching = False
                        break
                if matching: slots.append(slot)
            return slots
        else:
            return None


    def get_unmatched_prios(self):
        prios = []
        for prio in self.prios:
            if not self.has_block(prio):
                prios.append(prio)
        return sorted(prios, key=lambda d: d["rank"])
    
    def highest_unmatched_prios(self, N=5):
        prios = self.get_unmatched_prios()
        if prios:
            rank_min = prios[0]["rank"]
            highest_prios = [prios[0]]
            for p in prios:
                # if self.check_possibility(self.allocation.get_block_by_name(p["name"])):
                if p["rank"] == rank_min:
                    highest_prios.append(p)
                    continue
                if len(highest_prios) < N:
                    highest_prios.append(p)
                    rank_min = p["rank"]
            return highest_prios
        return []
      

        
    # Monte Carlo sampling a priority according to the rank
    def mc_prio(self):
        blocks = [] 
        block_map = [0]
        for prio in self.prios:
            if not self.has_block(prio):
                blocks.append(prio["name"])
                weight = NRANKS - prio["rank"] +1 # change the weight calculation
                block_map.append(block_map[-1] + weight)
        
        sample = np.random.random() * block_map[-1]
        for ix, x in enumerate(block_map[:-1]):
            if sample > block_map[ix] and sample < block_map[ix+1]:
                return blocks[ix]
    
    # random block if top N unmatched prios
    def sample_top_N_prios(self, N):
        prios = self.get_unmatched_prios()
        if len(prios) >= N:
            return random.choice(prios[:N])
        else:
            return random.choice(prios)

    def set_block(self, block, slot):
        self.schedule.set_block(block, slot)
    
    def check_possibility(self, p, slot):
        possible = False
        for rule in self.rules:
            block = self.allocation.get_block_by_name(p["name"])
            if not rule(self, block, slot):
                possible = False
        return possible


class Allocation:
    def __init__(self, seed):

        self.BLOCKS = []
        self.UNITS = []
        self.seed = seed
        self.random = np.random

    def evaluate(self, alloc_func):
        # random.seed(self.seed)
        np.random.seed(self.seed)
        alloc_func(self)

    def save(self, fname, path="saves"):
        l = []
        for block in self.BLOCKS:
            l.append(block.to_dict())
        with open(os.path.join(path, fname), "w") as file:
            file.write(json.dumps(l, indent=4))

    def load(self, fname, path="saves"):
        with open(os.path.join(path, fname), "r") as file:
            data = json.load(file)
        for d in data:
            if d["type"] == "block":
                block = self.get_block_by_name(d["name"])
                for entry in d["schedule"]:
                    block.set_unit(self.get_unit_by_name(entry["name"]), entry["slot"] )
            # should not be necessary
            # if d["type"] == "unit":
            #     unit = get_unit_by_name(d["name"])
            #     for entry in d["schedule"]:
            #         unit.set_block(get_unit_by_name(entry["unit"]), entry["slot"] )

    def clear_schedules(self):
        for block in self.BLOCKS:
            block.schedule.clear()
        for unit in self.BLOCKS:
            unit.schedule.clear()

    def clear_lists(self):
        self.BLOCKS.clear()
        self.UNITS.clear()

    def get_block_by_name(self, name):
        for block in self.BLOCKS:
            if block.name == name:
                return block
        return None

    def get_unit_by_name(self, name):
        for unit in self.UNITS:
            if unit.name == name:
                return unit
        return None
    
    def append_block(self, block):
        if type(block) != Block: print(f"ERROR: type is not block but '{type(block)}'"); return 0
        self.BLOCKS.append(block)
        block.allocation = self
    
    def append_unit(self, unit):
        if type(unit) != Unit: print(f"ERROR: type is not block but '{type(unit)}'"); return 0
        self.UNITS.append(unit)
        unit.allocation = self

    def load_blocklist(ipt):
        # TODO: load bocklist
        pass

    def load_unitlist(ipt):
        # TODO: load unit list
        pass

    def load_example_blocklist(self, N = 10):
        random.seed(41)
        for i in range(N):
            length = random.choice([1, 2, 4])
            if length == 2:
                on_times = [1]
            elif length == 4:
                on_times = [0]
            else:
                on_times = [0, 1, 2]
            self.append_block(
                Block(
                    "block"+str(i+1),
                    {   
                        "space": 24* random.randint(1, 2),
                        "length": length,
                        # "on_days": [0, 1, 2, 3, 4, 5, 6],
                        "on_times": on_times
                    }
                )
            )
        

    def load_example_unitlist(self, N = 10, N_Blocks=10):
        random.seed(41)
        for i in range(N):
            self.append_unit(
                Unit(
                    "unit"+str(i+1),
                    random.randint(12,24),
                    prios=[{"name": "block"+str(ii+1), "rank": min(5, random.randint(1, 20))} for ii in range(N_Blocks)]
                )
            )

    def check_all():
        # TODO: check if all unit req and block req are met and if no overbooking and stuff
        pass

    def stats(self):
        scores = np.zeros(len(self.UNITS))
        blocks = np.zeros(len(self.UNITS))
        for i, unit in enumerate(self.UNITS):
            scores[i] = unit.score() 
            blocks[i] = len(unit.schedule.get_list())
        return scores, blocks
    
    def log_stats(self, path, runtime):
        s, b = self.stats() # scores, blocks assigned
        hist, c = np.unique(b, return_counts=True)
        with open(path, "a") as file:
            file.write(f"{self.seed:>10}, ")
            file.write(f"{s.sum():6.4f}, {s.min():5.4f}, {s.max():5.4f}, {s.std():5.4f}, ")
            file.write(f"{b.min():3.0f}, {b.max():3.0f}, {b.std():5.2f}, ")
            file.write(f"{str(c)}")
            file.write(f"{runtime:5.2f} s\n")


def str_from_block(block):

    if type(block) == dict:
        blockname = block["name"]
    elif type(block) == Block:
        blockname = block.name
    elif type(block) == str:
        blockname = block
    else:
        print("ERROR: Invalid Block type, expected Block(), dict[name] or string")
    return blockname

def test_random_seed():
    return random.random()