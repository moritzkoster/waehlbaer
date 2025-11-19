import numpy as np
import pandas as pd
import json
import random
import os
from textwrap import dedent

SLOTS_PER_DAY = 5
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

    def get_list(self, with_slot=False, id_only=False):
        l = []
        for idd, day in enumerate(self.calendar):
            for it, time in enumerate(day):
                for entry in time:
                    if with_slot:
                        if id_only:
                            l.append({"slot": self.idx2str(idd, it), "ID": entry.ID})
                        else:
                            l.append({"slot": self.idx2str(idd, it), "element": entry})
                    else:
                        if id_only:
                            l.append(entry.ID)
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
            if entry in self[slot]:
                self[slot].remove(entry)
                return 0
        
        if entry:
            for idd, day in enumerate(self.calendar):
                for itt, time in enumerate(day):
                    if entry in time:
                        self[(idd, itt)].remove(entry)
                        return 0
            print(f"ERROR: couldnt find entry with ID {entry.ID}  in schedule"); return 0
        
        if slot:
            if len(self[slot]) == 1:
                self[slot].clear()
                return 0
            if len(self[slot]) == 0:
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
                if hasattr(block, "cath") and block.cath == "wasser":
                    return False
    return True 

def no_two_water_in_same_week(slot, self, block_req):
    if block_req["cath"] != "wasser": return True

    if Schedule.to_idx(slot)[0] < 7:
        test_days = range(0, 7)
    else:
        test_days = range(7, 14)
    for idd in test_days:
        day = self.schedule.calendar[idd]
        for iss, time in enumerate(day):
            for block in time:
                if block.data["cath"] == "wasser":
                    return False 
        return True   
    
def no_two_workshops_in_same_week(slot, self, block_req):
    if block_req["cath"] != "workshop": return True

    if Schedule.to_idx(slot)[0] < 7:
        test_days = range(0, 7)
    else:
        test_days = range(7, 14)
    for idd in test_days:
        day = self.schedule.calendar[idd]
        for iss, time in enumerate(day):
            for block in time:
                if block.data["cath"] == "workshop":
                    return False 
        return True 

UNIT_RULES = [
    soft_assign_musthave_blocks,
    no_two_on_same_day#,
    # no_two_water_in_same_week,
    # no_two_workshops_in_same_week
]
def has_space(slot, self, unit_req):
    return unit_req["space"] <= self.get_space(slot)

def is_for_group(slot, self, unit_req):
    return unit_req["group"] in self.data["group"]

# also tests for group
def has_space_for_group(slot, self, unit_req):
    if unit_req["group"] in self.data["group"]:
        space, groups = self.get_group_space(slot)
        return unit_req["space"] <= space and unit_req["group"] in groups
    return False

def on_times_block(slot, self, unit_req):
    return False if "on_times"    in self.data and Schedule.to_idx(slot)[1] not in self.data["on_times"] else True

def on_days_block(slot, self, unit_req):
    return False if "on_days"     in self.data and Schedule.to_idx(slot)[0] not in self.data["on_days"]  else True

def not_in_slot_block(slot, self, unit_req):
    return False if "not_in_slot" in self.data and slot in self.data["not_in_slot"] else True

def on_days_unit(slot, self, unit_req):
    return False if "on_days"  in unit_req and Schedule.to_idx(slot)[0] not in unit_req["on_days"]  else True

def on_times_unit(slot, self, unit_req):
    return False if "on_times" in unit_req and Schedule.to_idx(slot)[1] not in unit_req["on_times"] else True

BLOCK_RULES = [
    # has_space,
    # is_for_group,
    has_space_for_group,
    on_days_block,
    on_times_block,
    not_in_slot_block,
    on_days_unit,
    on_times_unit,
]

class Block:
    def __init__(self, ID, data):
        self.ID = ID
        self.data = data
        self.schedule = Schedule(self)

        self.rules = BLOCK_RULES

    def get_space(self, slot):
        taken = 0
        for unit in self.schedule[slot]:
            taken += unit.n_people
        return self.data["space"] - taken

    def get_group_space(self, slot):
        if not self.schedule[slot]: 
            return self.data["space"], ["wo", "pf", "pi"]
        if "mix_groups" in self.data and self.data["mix_groups"]: 
            return self.get_space(slot), ["wo", "pf", "pi"]
        
        taken=0
        group = self.schedule[slot][0].data["group"]
        for unit in self.schedule[slot]:
            taken += unit.n_people
            if unit.data["group"] != group:
                print(f"ERROR: two different groups assigned to block {self.ID}")
                print(self.schedule[slot]); exit()
        return self.data["space"] - taken, [group]
        
    
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
        unit_list = self.schedule.get_list(with_slot=True, id_only=True)
        d = {
            "type": "block",
            "ID": self.ID,
            "data": self.data,
            "schedule": unit_list
            }
        return d
    
    def __repr__(self):
        data = self.data
        s = dedent(f"""
            \033[1m{data["fullname"]}\033[0m
            {self.ID}: {data["js_type"]} : {data["cath"]} 
            space: {data["space"]} : on times {data["on_times"]} : duration {data["length"]}
            for: {data["group"]}"""
        )
        return s


class Unit: 
    def __init__(self, ID, data):
        self.ID = ID
        self.fullname = data["fullname"]
        self.n_people = data["n_people"]
        # self.data["prios"] = sorted(data["prios"], key=lambda d: d['rank']) # redo
        self.data = data
        
        self.schedule = Schedule(self)
        self.rules = UNIT_RULES

    def set_block(self, block, slot):
        self.schedule.set_block(block, slot)
    
    def remove_block(self, block=None, slot=None):
        self.schedule.remove_block(block, slot)
    
    
    def rank(self, block): # TODO
        id_ = id_from_block(block)

        for prio in self.data["prios"]:
            if id_ == prio["ID"]:
                return prio["rank"]
        print("ERROR: block not in Prio")
        return NRANKS
    
    # define how the score is calculated 
    # TODO: Is this the Way???
    def score(self):
        return self.score_top_N_norm()
    
    def score_sum_prios(self):  # TODO 
        score = 0     
        for block in self.schedule.get_list():
            score += NRANKS - (self.rank(block)) # TODO: is this the way???
        return score
   
    def score_top_N(self, N, p=False): # TODO
        score = 0
        sorter = lambda d: d["rank"] - 0.1 * self.has_block(d)
        top_N = sorted(self.data["prios"], key=sorter)[:N]

        if p:
            for p in top_N:
                print(f"{p['rank']}: {self.has_block(p)} ", end="")
            print("")

        for block in top_N:
            if self.has_block(block):
                score += 1 
        return score

    def score_sum_norm(self): # TODO
        if not hasattr(self, "norm_const"):
            self.norm_const = np.array([NRANKS - p["rank"] for p in self.data["prios"]]).sum()
            if self.norm_const == 0: 
                print("WARNING: all prios are 5")
                return 1
        sum_ = 0
        for prio in self.data["prios"]:
            sum_ += self.has_block(prio) * (NRANKS - prio["rank"])
        return sum_ / self.norm_const

    def score_top_N_norm(self, N=11): # TODO
        sorter = lambda d: d["rank"] - 0.1 * self.has_block(d)
        sorted_prios = sorted(self.data["prios"], key=sorter)
        norm_const = 0
        total = 0
        for ip, prio in enumerate(sorted_prios):
            if ip < N:
                norm_const += (NRANKS - prio["rank"])
            total += self.has_block(prio) * (NRANKS - prio["rank"])
        return total / norm_const

    
    def has_block(self, block):
        id_ = id_from_block(block)

        for block in self.schedule.get_list():
            if block.ID == id_:
                return True
        return False
    
    # returns free slots for blocks
    # accounts for: need for visit day, 1d/2d hike, ...
    # accounts for block requirements (1 slot, 2 slots, ...)
    def search_slots(self, block_req={}):
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


    def get_unmatched_prios(self): # TODO
        prios = []
        for prio in self.data["prios"]:
            if not self.has_block(prio):
                prios.append(prio)
        return sorted(prios, key=lambda d: d["rank"])
    
    def highest_unmatched_prios(self, N=5): # TODO
        prios = self.get_unmatched_prios()
        if prios:
            rank_min = prios[0]["rank"]
            highest_prios = [prios[0]]
            for p in prios:
                if p["rank"] == rank_min:
                    highest_prios.append(p)
                    continue
                if N and len(highest_prios) < N: # if not N: strictly highest prios
                    highest_prios.append(p)
                    rank_min = p["rank"]
                else:  
                    break
            return highest_prios
        return []
      

        
    # Monte Carlo sampling a priority according to the rank
    def mc_prio(self): # TODO
        blocks = [] 
        block_map = [0]
        for prio in self.data["prios"]:
            if not self.has_block(prio):
                blocks.append(prio["ID"])
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
            block = self.allocation.get_block_by_ID(p["ID"])
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
                block = self.get_block_by_ID(d["ID"])
                for entry in d["schedule"]:
                    block.set_unit(self.get_unit_by_ID(entry["ID"]), entry["slot"] )
            # should not be necessary
            # if d["type"] == "unit":
            #     unit = get_unit_by_ID(d["ID"])
            #     for entry in d["schedule"]:
            #         unit.set_block(get_unit_by_ID(entry["unit"]), entry["slot"] )

    def clear_schedules(self):
        for block in self.BLOCKS:
            block.schedule.clear()
        for unit in self.BLOCKS:
            unit.schedule.clear()

    def clear_lists(self):
        self.BLOCKS.clear()
        self.UNITS.clear()

    def get_block_by_ID(self, ID):
        for block in self.BLOCKS:
            if block.ID == ID:
                return block
        return None

    def get_unit_by_ID(self, ID):
        for unit in self.UNITS:
            if unit.ID == ID:
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
    
    def search_blocks(self, slot, requirements={}):
        open_blocks = []
        for block in self.BLOCKS:
            if slot in block.search_slots(requirements):
                open_blocks.append(block)
        return open_blocks


 

    # def load_unitlist(self, path="data", filename="Antworten Buchungstool.xlsx"):
    #     df = pd.read_excel(os.path.join(path, filename), sheet_name="Formularantworten 1", header=1)
        
    #     PRIOS = [
    #         ["Umbedingt", "Das wollen wir unbendingt machen"],
    #         ["Sehr Gerne", "Das würden wir sehr gerne machen"],
    #         ["Gerne", "Das würden wir gerne machen"],
    #         ["Neutral"],
    #         ["Lieber nicht", "Das wollen wir nicht machen"]
    #     ]
    #     for ip, p in enumerate(PRIOS):
    #         for pp in  p:
    #             df.replace(pp, str(ip+1), inplace=True)
        
    #     for column in df.columns:
    #         print(f"{column}: \033[1m{df.loc[0, column]}\033[0m")

    # def load_blocklist(self, path="data", filename="PRG_Blockliste.xlsx"):
    #     df = pd.read_excel(os.path.join(path, filename), sheet_name="On-Site Buchbar")
    #     df = df[[
    #         'Block Nr.',
    #         'Off-Site', 
    #         'Block- Titel',
    #         'Ort', 
    #         'Programmstruktur', 
    #         'On-Site', 'Off-Site.1',
    #         'Blockdauer', 
    #         'Blockart J+S', 
    #         'Stufe', 
    #         'Gruppengrösse', 
    #         'Partizipation',
    #         'max. Anzahl Durchführungen (wie viele Einheiten können diesen Block besuchen?)',
    #         'geschätzte Anzahl Durchführungen'
    #     ]]

    #     df.columns = [
    #         'ID',
    #         'typ', 
    #         'name',
    #         'ort', 
    #         'betr_unbetr', 
    #         'tags_onsite', 'tags_offsite',
    #         'dauer', 
    #         'blockart_J_S', 
    #         'stufen', 
    #         'gruppengroesse', 
    #         'mix_units',
    #         'max_durchführungen',
    #         'est_durchführungen'
    #     ]
    #     df = df.dropna(subset=["ID"])

    #     print(df["stufen"])
    #     for bd in df.itertuples():
            
    #         length = 1
    #         on_times = [0, 1, 2]
    #         if bd.dauer == "4h": 
    #             length = 2
    #             on_times = [1]
    #         if bd.dauer == "8h":
    #             length = 4
    #             on_times = [0]
    #         if bd.dauer == "2 Tage":
    #             length = 7
    #             on_times = [0]
            
    #         self.append_block(

    #             Block(
    #                 bd.ID,
    #                 {   "fullname": bd.name,
    #                     "space": bd.gruppengroesse,
    #                     "js_type": bd.blockart_J_S,
    #                     "cath": bd.typ,
    #                     "group": bd.stufen.split(", ") if type(bd.stufen) == str else bd.stufen,
    #                     # "group": random.choice([["wo"],["pf"], ["pi"], ["wo", "pf"], ["pf", "pi"], ["wo", "pf", "pi"]]),
    #                     "length": length,
    #                     # "on_days": [0, 1, 2, 3, 4, 5, 6],
    #                     "on_times": on_times
                        
    #                 }
    #             )
    #         )




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
                        "js_type": random.choice(["LS", "LA", "LP"]),
                        "cath": random.choice(["wasser", "workshop", "none", "none", "none", "none", "none", "none", "none", "none"]),
                        "group": ["wo", "pf", "pi"],
                        # "group": random.choice([["wo"],["pf"], ["pi"], ["wo", "pf"], ["pf", "pi"], ["wo", "pf", "pi"]]),
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
                    ID="unit"+str(i+1),
                    data={
                        "fullname": "Unit " + str(i+1),
                        "n_people": random.randint(12,24),
                        "group": random.choice(["wo", "pf", "pi"]),
                        "hike": random.randint(0, 2),
                        "total_blocks": random.randint(7,11),
                        "free_slots": random.choice(["A1", "B2", "C3", ]),
                        "prios": [{"ID": "block"+str(ii+1), "rank": min(5, random.randint(1, 20))} for ii in range(N_Blocks)]
                    }
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

    def print_blocklist(self):
        for b in self.BLOCKS:
            print(b)
    
    def log_stats(self, path, runtime):
        s, b = self.stats() # scores, blocks assigned
        hist, c = np.unique(b, return_counts=True)
        with open(path, "a") as file:
            file.write(f"{self.seed:>10}, ")
            file.write(f"{s.sum():6.4f}, {s.min():5.4f}, {s.max():5.4f}, {s.std():5.4f}, ")
            file.write(f"{b.min():3.0f}, {b.max():3.0f}, {b.std():5.2f}, ")
            file.write(f"{str(c)}")
            file.write(f"{runtime:5.2f} s\n")


def id_from_block(block):

    if type(block) == dict:
        id_ = block["ID"]
    elif type(block) == Block:
        id_ = block.ID
    elif type(block) == str:
        id_ = block
    else:
        print("ERROR: Invalid Block type, expected Block(), dict['ID'] or string")
    return id_

def test_random_seed():
    return random.random()