import numpy as np
import pandas as pd
import json
import random
import os
from textwrap import dedent

SLOTS_PER_DAY = 5
DAYS = 14

NRANKS = 5

RED = "\033[31m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
BLUE = "\033[34m"
BOLD = "\033[1m"
RESET = "\033[0m"

KC_block = None
KC_unit = None

class Schedule: 
    def __init__(self, owner):
        self.calendar = [[[] for _ in range(SLOTS_PER_DAY)] for __ in range(DAYS)]
        self.owner = owner

    def __getitem__(self, ipt):
        day, time = Schedule.to_idx(ipt)
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

    def get_time_list(self):
        l = []
        for idd, day in enumerate(self.calendar):
            for it, time in enumerate(day):
                if time:
                    l.append({"slot": self.idx2str(idd, it), "elements": [e.ID for e in time]})
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

    @staticmethod
    def idx2str(day, time):
        return chr(day+65)+str(time)

    @staticmethod
    def next_N_slots(ipt, N=1):
        day, time = Schedule.to_idx(ipt)
        slots = []
        for i in range(1, N+1):
            time += 1
            if time >= SLOTS_PER_DAY:
                time = 0
                day += 1
            
            if day >= DAYS:
                print("ERROR: no next slots available")
            else:
                slots.append(Schedule.idx2str(day, time))
        return slots

    def set_entry(self, entry, slot):
        self[slot].append(entry)
  
    # sets block for unit
    def set_block(self, block, slot):
        self.set_entry(block, slot)
        block.schedule.set_entry(self.owner, slot)
        for kc_slot in Schedule.next_N_slots(slot, block.data["length"] -1):
            block.set_unit(KC_block, kc_slot)
        
        if hasattr(block, "twin_block") and block.twin_block:
            block.twin_block.schedule.set_entry(KC_unit, slot)

    # sets unit for block
    def set_unit(self, unit, slot):
        self.set_entry(unit, slot)
        unit.schedule.set_entry(self.owner, slot)
        for kc_slot in Schedule.next_N_slots(slot, self.owner.data["length"] -1):
            unit.set_block(KC_block, kc_slot)
        
        if hasattr(self.owner, "twin_block") and self.owner.twin_block:
            self.owner.twin_block.schedule.set_entry(KC_unit, slot)

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
        if not block:
            block = self[slot][0]
        self.remove_entry(block, slot)
        block.schedule.remove_entry(self.owner, slot)
    
    def remove_unit(self, unit=None, slot=None):
        if type(self.owner) == Unit: print("ERROR: cannot remove unit from Unit()")
        if not unit:
            unit = self[slot][0]
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
    def matching_slots(unit_slots, block_slots):
        if type(block_slots) == list:
            matching = []
            for slot in unit_slots:
                if slot in block_slots:
                    matching.append(slot)
            return matching
        elif type(block_slots) == dict:
            matching = []
            for block_id, slotlist in block_slots.items():
                for slot in slotlist:
                    if slot in unit_slots:
                        matching.append({"ID": block_id, "slot": slot})
            return matching
        else:
            print(f"{RED}{BOLD}: unit_slots must be 'list' and block_slots must be 'list' or dict of lists{RESET}")
    

def no_two_on_same_day(slot, self, blockdata):
    # if block["cat"] == "dusche":
    #     return True
    if "tags" in blockdata and "same_day" in blockdata["tags"]:
        return True
    for time in self.schedule.calendar[Schedule.to_idx(slot)[0]]:
        if time: # If there is something at this time
            for b in time: 
                # if b.data["cat"] != "dusche": # if it is not a shower block
                #     return False
                if "tags" in b.data and "same_day" not in b.data["tags"]:
                    return False
    return True  

def no_two_water_activities(slot, self, block_req):
    for idd, day in enumerate(self.schedule.calendar):
        for iss, time in enumerate(day):
            for block in time:
                if hasattr(block, "cat") and block.cat == "wasser":
                    return False
    return True 

def no_two_water_in_same_week(slot, self, block_req):
    if block_req["cat"] != "wasser": return True

    if Schedule.to_idx(slot)[0] < 7:
        test_days = range(0, 7)
    else:
        test_days = range(7, 14)
    for idd in test_days:
        day = self.schedule.calendar[idd]
        for iss, time in enumerate(day):
            for block in time:
                if block.data["cat"] == "wasser":
                    return False 
    return True   
    
def no_two_workshops_in_same_week(slot, self, block_req):
    if block_req["cat"] != "workshop": return True

    if Schedule.to_idx(slot)[0] < 7:
        test_days = range(0, 7)
    else:
        test_days = range(7, 14)
    for idd in test_days:
        day = self.schedule.calendar[idd]
        for iss, time in enumerate(day):
            for block in time:
                if block.data["cat"] == "workshop":
                    return False 
    return True 

# def no_two_shower_in_same_week(slot, self, block_req):
#     if block_req["cat"] != "dusche": return True

#     if Schedule.to_idx(slot)[0] < 7:
#         test_days = range(1, 6+1)
#     else:
#         test_days = range(8, 12+1)
#     for idd in test_days:
#         day = self.schedule.calendar[idd]
#         for iss, time in enumerate(day):
#             for block in time:
#                 if block.data["cat"] == "dusche":
#                     return False 
#     return True 

def max_per_week(slot, self, block_req):
    if block_req["cat"] not in ["wald", "nacht" , "dusche"]: return True

    if Schedule.to_idx(slot)[0] < 7:
        test_days = range(1, 6+1)
    else:
        test_days = range(8, 12+1)
    count = 0
    for idd in test_days:
        day = self.schedule.calendar[idd]
        for iss, time in enumerate(day):
            for block in time:
                if block.data["cat"] == block_req["cat"]:
                    count += 1

    max_counts_per_week = {
        "wald": 3,
        "nacht": 2,
        "dusche": 1
    }

    return count < max_counts_per_week[block_req["cat"]]

def max_per_day(slot, self, block_req):
    if block_req["cat"] not in ["wald"]: return True
    count = 0
    for time in self.schedule.calendar[Schedule.to_idx(slot)[0]]:
        for block in time:
            if block.data["cat"] == block_req["cat"]:
                count += 1

    max_counts_per_day = {
        "wald": 1
    }

    return count < max_counts_per_day[block_req["cat"]]
    

def is_present(slot, self, blockdata):
    return Schedule.to_idx(slot)[0] in self.present_on

def long_blocks(slot, self, blockdata):
    next_slots = Schedule.next_N_slots(slot, N=blockdata["length"]-1)
    # print(last_6_slots, slot)
    for i, slot in enumerate(next_slots):
        if self.schedule[slot]:
            if blockdata["ID"] in ["OFF-17", "OFF-18", "OFF-19", "OFF-20", "OFF-24", "OFF-25"] and  self.schedule[slot][0].ID == "ON-39":  # OVERRIDE zweitageswanderung darf während freizeit sein
                continue
            if blockdata["cat"] == "ausflug" and self.schedule[slot][0].ID == "ON-39": # override ausflüge wärend freizeit
                continue
            return False
    return True

UNIT_RULES = [
    # soft_assign_musthave_blocks,/
    no_two_on_same_day,
    is_present,
    # no_two_shower_in_same_week,
    max_per_week,
    max_per_day,
    long_blocks
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

def on_slot(slot, self, unit_req):
    if "on_slots" in self.data:
        return slot in self.data["on_slots"]
    return True

def only_single_unit(slot, self, unit_req):
    if self.schedule[slot] and not self.data["mix_units"]:
        return False
    return True

def is_blocked(slot, self, unit_req):
    if "state" in self.data and self.data["state"] == "Gesperrt":
        return False
    else:
        return True

BLOCK_RULES = [
    # has_space,
    # is_for_group,
    on_slot,
    is_blocked,
    has_space_for_group,
    # on_days_block,
    # on_times_block,
    # not_in_slot_block,
    # on_days_unit,
    # on_times_unit,
    only_single_unit
]

class Block:
    def __init__(self, ID, data):
        self.ID = ID
        self.data = data
        self.schedule = Schedule(self)

        self.rules = BLOCK_RULES

        if self.data["cat"] in ["wasser", "si-mo", "flussbaden", "dusche"]:
            self.data["tags"].add("nass")
        if self.data["cat"] in ["wasser", "dusche"]:
            self.data["tags"].add("sauber")

        self.is_active = data["state"] != "Gesperrt"

    def get_space(self, slot):
        taken = 0
        for unit in self.schedule[slot]:
            taken += unit.n_people
        return self.data["space"] - taken

    def get_group_space(self, slot):
        if not self.schedule[slot]: 
            if "hard_limit" in self.data and self.data["hard_limit"] == "Ja":
                return self.data["space"], ["wo", "pf", "pi"]
            else:
                return 99, ["wo", "pf", "pi"] # returns 99 for first units, so that is only relevant when there are already units in the block
    
        taken=0
        group = self.schedule[slot][0].group
        for unit in self.schedule[slot]:
            taken += unit.n_people
            if unit.group != group:
                print(f"{RED}ERROR: two different groups assigned to block {self.ID}{RESET}")
                print(self.schedule[slot]); exit()
        return self.data["space"] - taken, [group]
        
    
    def set_unit(self, unit, slot):
        if type(slot) == dict:
            self.schedule.set_unit(unit, slot["slot"])
        elif type(slot) == str:
            self.schedule.set_unit(unit, slot)
        else:
            print("ERROR: slot must be str 'A0' or dict {'slot': 'A0', ...}"); return 

    def remove_unit(self, unit=None, slot=None):
        self.schedule.remove_unit(unit, slot)
  
    # returns free slots of block
    # accounts for other units, block requirements
    # groups slots per day, so that days are filled first
    # returns [[best1, best2], [sec1, ...]]

    def search_slots(self, requirements, return_reason=False):
        slots = []
        search_result = SearchResult(self, requirements)
        free_slots = self.schedule.free_slots()
        if not free_slots:
            if return_reason:
                search_result.reason.add("Block free slots available")
                return search_result
            return []
        for iss, slot in enumerate(free_slots):
            matching = True
            for rule in self.rules:
                if not rule(slot["slot"], self, requirements):
                    matching = False
                    if return_reason:
                        search_result.reason.add(f"Block-Rule '{rule.__name__}' not fulfilled")
                    break
            if matching:
                slots.append(slot["slot"])
        if return_reason:
            search_result.slots = slots
            return search_result
        return slots

    def to_dict(self):
        unit_list = self.schedule.get_list(with_slot=True, id_only=True)
        self.data["tags"] = list(self.data["tags"])
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
            \033[1m\033[34m{self.ID}: {data["fullname"]} ({data["verteilungsprio"]})\033[0m
            {data["js_type"]}: {data["cat"]} 
            space: {data["space"]} | duration: {data["length"]} | mix: {data['mix_units']}
            for: {", ".join(data["group"])} | tags: {YELLOW}{', '.join(data['tags'])}{RESET}"""
        )
        return s

class MetaBlock(Block):
    def __init__(self, ID, data):
        super().__init__(ID, data)
        self.sub_blocks = []

    def add_subblock(self, block):
        if type(block) != Block:
            print(f"ERROR: type is not block but '{type(block)}'"); return 0
        self.sub_blocks.append(block)
    
    def search_slots(self, requirements, return_reason=False):
        search_result = SearchResult(self, requirements)
        search_result.found = False
        slots = {}
        for sub_block in self.sub_blocks:
            if return_reason:
                sb_search_result = sub_block.search_slots(requirements, return_reason)
                slots[sub_block.ID] = sb_search_result.slots
                if sb_search_result.slots:
                    search_result.found = True
                for reason in sb_search_result.reason:
                    search_result.reason.add(reason)
        if return_reason:
            search_result.slots = slots
            return search_result
        return slots

    def set_unit(self, unit, slot):
        if type(slot) != dict:
            print("ERROR: MetaBlock expects slot as dict of '{ID:OFF-12: slot:A1}'"); return 
        for sub_block in self.sub_blocks:
            if sub_block.ID == slot["ID"]:
                sub_block.set_unit(unit, slot["slot"])
                return
        print(f"ERROR: could not find sub_block with ID '{slot['ID']}' in MetaBlock '{self.ID}'")
    
    def remove_unit(self, unit=None, slot=None):
        if type(slot) != dict:
            print("ERROR: MetaBlock expects slot as dict of '{ID:OFF-12: slot:A1}'"); return 
        for sub_block in self.sub_blocks:
            if sub_block.ID == slot["ID"]:
                sub_block.remove_unit(unit, slot["slot"])
                return
        print(f"ERROR: could not find sub_block with ID '{slot['ID']}' in MetaBlock '{self.ID}'")
        
    def __repr__(self):
        s = f"\n{BOLD}{GREEN}Meta {self.ID}: {self.data['fullname']}{RESET}"
        s += "\n  Sub-Blocks:\n"
        for sb in self.sub_blocks:
            s += "    - " + sb.ID + ": " + sb.data["fullname"] + "\n"
        return s

class Unit: 
    def __init__(self, ID, data):
        self.ID = ID
        self.fullname = data["fullname"]; del data["fullname"]
        self.n_people = data["n_people"]; del data["n_people"]

        
        self.contact = data["contact"]; del data["contact"]
        self.email = data["email"]; del data["email"]
        self.group = data["group"].lower().replace("ö", "o"); del data["group"]
        self.more_or_less = data["more_or_less"]; del data["more_or_less"]
        self.wasser_anerk = data["wasser_anerk"]; del data["wasser_anerk"]
        self.present_on = data["present_on"]; del data["present_on"]

        self.prios = data
        self.prios_sorted = None
        self.general = None

        self.tags = set()
        if self.n_people > 30: self.tags.add("large_unit")
        # self.sort_prios_by_cat() is called while appending the unit
        
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
    
    def is_nacht_satisfied(self):
        count = 0
        for block in self.schedule.get_list():
            if block.data["cat"] == "nacht":
                count += 1
        return count >= self.general["nacht"] * (1 if self.group == "wo" else 2)

    def is_wald_satisfied(self):
        count = 0
        for block in self.schedule.get_list():
            if block.data["cat"] == "wald":
                count += 1
        return count >= self.general["wald"] * (1 if self.group == "wo" else 2)
    
    # define how the score is calculated 
    # TODO: Is this the Way???
    def score(self):
        return self.score_advanced()
    
    def score_advanced(self):
        allowed_numbers = {
            "pf": {
                "wasser": 2,
                "si-mo": 1,
                "flussbaden": 2,
                "ausflug": 1,
                "wanderung": 1,
                "workshop": 2,
                "sportaktivitat": 2,
                "programmflache": 2,
                "nacht": 4,
                "wald": 6
            },
            "pi": {
                "wasser": 2,
                "si-mo": 1,
                "flussbaden": 2,
                "ausflug": 1,
                "wanderung": 1,
                "workshop": 2,
                "sportaktivitat": 2,
                "programmflache": 2,
                "nacht": 4,
                "wald": 6
            },
            "wo": {
                "wasser": 1,
                "si-mo": 0,
                "flussbaden": 2,
                "ausflug": 1,
                "wanderung": 1,
                "workshop": 1,
                "sportaktivitat": 2,
                "programmflache": 2,
                "nacht": 2,
                "wald": 3
            }
        }
        score = 0
        cf = 0
        for cat in self.prios_sorted:
            for ip, prio in enumerate(self.prios_sorted[cat]):
                if ip < allowed_numbers[self.group][cat]:
                    cf += prio["value"]
                if self.has_block(prio["ID"]):
                    score += prio["value"]
        return score / max(cf, 1)

    def score_sum_prios(self): 
        score = 0     
        for block in self.schedule.get_list():
            score += NRANKS - (self.rank(block)) # is this the way???
        return score
   
    def score_top_N(self, N, p=False): 
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
    def search_slots(self, block_req={}, return_reason=False):
        slots = []
        search_result = SearchResult(self, block_req)
        free_slots = self.schedule.free_slots()
        if free_slots:
            for iss, slot in enumerate(self.schedule.free_slots()):
                matching = True
                for rule in self.rules:
                    if not rule(slot, self, block_req):
                        matching = False
                        if return_reason:
                            search_result.reason.add(f"Unit-rule '{rule.__name__}' not fulfilled")
                        break
                if matching: slots.append(slot)
            if return_reason:
                search_result.slots = slots
                return search_result
            else:
                return slots
        else:
            if return_reason:
                search_result.reason.add("Unit has free slots available")
                return search_result
            return None

    def get_unmatched_prios(self):
        prios = []
        for cat, prio_list in self.prios.items():
            for prio in prio_list:
                if not self.has_block(prio):
                    prio["cat"] = cat 
                    prios.append(prio)
        return prios
    
    def highest_unmatched_prios(self, N=5): # TODO
        print("\033[31m'highest_unmatched_prios()' IS DEPRECATED, USE 'get_highest_unmatched_by_cat()' INSTEAD\033[0m]")
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
    
    # assumes prios are sorted by rank
    def get_highest_unmatched_by_cat(self, cat): 
        if not cat in self.prios_sorted:
            return None
        for prio in self.prios_sorted[cat]:
            if not self.has_block(prio["ID"]):
                return prio
        return None
    
    def get_all_unmatched_by_cat(self, cat):
        if not cat in self.prios_sorted:
            return None
        prios = []
        for prio in self.prios_sorted[cat]:
            if not self.has_block(prio) and prio["value"] >= 0:
                prios.append(prio)
        return prios

    # Monte Carlo sampling a priority according to the rank
    def mc_prio(self): 
        print("\033[31m'mc_prio()' IS DEPRECATED, NO REPLACEMENT SO FAR\033[0m]")
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
        print("\033[31m'sample_top_N_prios()' IS DEPRECATED, NO REPLACEMENT SO FAR\033[0m]")
        prios = self.get_unmatched_prios()
        if len(prios) >= N:
            return random.choice(prios[:N])
        else:
            return random.choice(prios)

    def set_block(self, block, slot):
        self.schedule.set_block(block, slot)
    
    def check_possibility(self, p, slot):
        for rule in self.rules:
            block = self.allocation.get_block_by_ID(p["ID"])
            if not rule(self, block, slot):
                return False
        return True


    def sort_prios_by_cat(self):
        if not hasattr(self.allocation, "block_cats"): print("\033[1m\033[31mERR: call 'find_block_cats()' first\033[0m")
        prios = {}
        general = {}
        wish = 0
        total = 0
        for ID, value in self.prios.items():
            if len(ID.split("-"))== 2:
                cat = self.allocation.cat_map[ID]
                
                if ID == "AUX-FL":
                    general["flussbaden"] = value
                    if value:
                        if self.group == "wo":
                            prios[cat] = [{"ID": "OFF-21", "value": 3}, {"ID": "OFF-22", "value": -1}, {"ID": "OFF-23", "value": -1}]
                        else:
                            prios[cat] = [{"ID": "OFF-21", "value": 3}, {"ID": "OFF-22", "value": 3}, {"ID": "OFF-23", "value": 3}]
                    else:
                        prios[cat] = [{"ID": "OFF-21", "value": -1}, {"ID": "OFF-22", "value": -1}, {"ID": "OFF-23", "value": -1}]
                    continue

                if cat in prios:
                    prios[cat].append({"ID": ID, "value": value})
                else:
                    prios[cat] = [{"ID": ID, "value": value}]

                
                wish += max(0, value)
                total += 3

            else:
                general[ID] = value
                if ID == "wasser":
                    general["si-mo"] = value
                
        for cat in prios.keys():
            prios[cat] = sorted(prios[cat], key=lambda d : d["value"], reverse=True)
        
        self.prios_sorted = prios
        self.general = general
        
        self.score_data = {
            "wish": wish,
            "total": total,
            }

        if self.group == "pi":
            self.score_cf = total / 124  * self.more_or_less / 5
            if total < 50: 
                self.tags.add("frechdachs")
        if self.group == "pf":
            self.score_cf = total / 149  * self.more_or_less / 5
            if  total < 60:
                self.tags.add("frechdachs")
        if self.group == "wo":
            self.score_cf = total / 89  * self.more_or_less / 5
            if total < 30:
                self.tags.add("frechdachs")
            

    def __repr__(self):
        s = dedent(f"""
            \033[1m\033[34m{self.ID}: {self.fullname} {self.group}\033[0m 
            n_people: {self.n_people} | email: {self.email}
            contact: {self.contact} | wasser_anerk: {self.wasser_anerk}
            more_or_less: {self.more_or_less} | cf: {self.score_cf:.3f} | tags: {YELLOW}{BOLD} {', '.join(self.tags)} {RESET}
            """
        )
        s += f"  \033[1mGeneral:\033[0m\n"
        i = 0
        for key, val in self.general.items():
            s += f"  {GREEN if val else RED}{key:>18}: {val:<5}{RESET}"
            if i % 4 == 3 or i == len(self.general) -1:
                s+= "\n"
            i+=1

        for cat, prio_list in self.prios_sorted.items():
            if self.general[cat]:
                s += f"  \033[1m{cat}:\033[0m\n"
                for ip, prio in enumerate(prio_list):
                    s += f"  {prio['ID']:>18}: {prio['value']:>2} {'(A)' if self.has_block(prio) else ''}"
                    if ip % 4 == 3 or ip == len(prio_list) -1:
                        s+= "\n"
        
        return s
    
class SearchResult:
    def __init__(self, author, additional_data):
        self.author = author
        self.additional_data = additional_data
        self.slots = []
        self.reason = set()
        

class Allocation:
    def __init__(self, seed):

        self.BLOCKS = []
        self.UNITS = []
        self.seed = seed
        self.random = np.random

        global KC_block
        KC_block = Block("AUX-KC", {"fullname": "KEEP CLEAR", "cat": "AUX", "js_type": "None", "space": 9999, "length": 1, "group": ["wo", "pf", "pi"], "state": True, "tags": set(), "verteilungsprio": 6, "mix_units":False})

        global KC_unit
        KC_unit = Unit("KC", {"fullname": "KEEP CLEAR", "n_people": 0, "group":"wo", "contact": "X", "email": "X", "wasser_anerk": "X", "more_or_less": 5, "present_on": list(range(14)), "prios": []})


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
        if not self.UNITS or not self.BLOCKS:
            print(f"{RED}{BOLD}Load units and blocklists first with 'load_unitlist(a)' and 'load_blocklist(a)'{RESET}")
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
        print(f"ERROR: could not find Block with ID '{ID}'")
        return None

    def remve_KC_from_all_blocks(self):
        for unit in self.UNITS:
            for day in unit.schedule.calendar:
                for time in day:
                    if KC_block in time:
                        time.remove(KC_block)
        
        for block in self.BLOCKS:
            for day in block.schedule.calendar:
                for time in day:
                    if KC_unit in time:
                        time.remove(KC_unit)

    def get_unit_by_ID(self, ID, print_error=True):
        for unit in self.UNITS:
            if unit.ID == ID:
                return unit
        if print_error:
            print(f"ERROR: could not find Unit with ID '{ID}'")
        return None
    
    def append_block(self, block, index=None):
        if type(block) != Block and type(block) != MetaBlock: print(f"ERROR: type is not block but '{type(block)}'"); return 0
        if index is not None:
            self.BLOCKS.insert(index, block)
        else:
            self.BLOCKS.append(block)
        block.allocation = self
    
    def append_unit(self, unit):
        if type(unit) != Unit: print(f"ERROR: type is not block but '{type(unit)}'"); return 0
        if self.get_unit_by_ID(unit.ID, print_error=False): 
            print(f"{YELLOW}WARN: unit with ID '{unit.ID}' already exists and is replaced{RESET}")
            input("Press Enter to continue...")
            self.UNITS.remove(self.get_unit_by_ID(unit.ID, print_error=False))
        self.UNITS.append(unit)
        unit.allocation = self
        unit.sort_prios_by_cat()
    
    def search_blocks(self, slot, requirements={}):
        open_blocks = []
        for block in self.BLOCKS:
            if slot in block.search_slots(requirements):
                open_blocks.append(block)
        return open_blocks

    def find_block_cats(self):
        cats = []
        cat_map = {}
        for b in self.BLOCKS:
            cat_map[b.ID] = b.data["cat"]
            if b.data["cat"] not in cats:
                cats.append(b.data["cat"])
        
        cat_map["AUX-FL"] = "flussbaden"
        cat_map["AUX-FR"] = "wasser"
        cat_map["AUX-HB"] = "wasser"
            
        self.block_cats = cats
        self.cat_map = cat_map

    def generate_block_series(self, base_id, count, data, index = None):
        mb = MetaBlock(base_id, data)
        for i in range(count):

            if base_id[-1] in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]: 
                block_id = f"{base_id}_{chr(i+65)}"
            else:
                block_id = f"{base_id}_{i+1}"
                
            b = Block(
                    block_id,
                    data
                )
            if index is not None:
                self.append_block(b, index=index+i)
            else:   
                self.append_block(b)
            mb.add_subblock(b)
        self.append_block(mb)
    
    def print_blocklist(self):
        for b in self.BLOCKS:
            print(b)
    
    def print_unitlist(self):
        for u in self.UNITS:
            print(u)


 

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
    #                     "cat": bd.typ,
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
                        "cat": random.choice(["wasser", "workshop", "none", "none", "none", "none", "none", "none", "none", "none"]),
                        "group": ["wo", "pf", "pi"],
                        # "group": random.choice([["wo"],["pf"], ["pi"], ["wo", "pf"], ["pf", "pi"], ["wo", "pf", "pi"]]),
                        "length": length,
                        # "on_days": [0, 1, 2, 3, 4, 5, 6],
                        "on_times": on_times
                        
                    }
                )
            )
        self.find_block_cats()
        

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
    def print_stats(self):
        s, b = self.stats() # scores, blocks assigned
        hist, c = np.unique(b, return_counts=True)
        for unit in self.UNITS:
            print(f"{BLUE}{unit.ID:3}{RESET}: score={unit.score():6.4f}, blocks={len(unit.schedule.get_list()):3.0f}, tags={YELLOW}{', '.join(unit.tags)}{RESET}")
        print(f"Scores: sum={s.sum():6.4f}, min={s.min():5.4f}, max={s.max():5.4f}, std={s.std():5.4f}")
        print(f"Blocks assigned: min={b.min():3.0f}, max={b.max():3.0f}, std={b.std():5.2f}")
        print("Block assignment histogram:")
        for hi, h in enumerate(hist):
            print(f"  {h:2.0f} blocks: {c[hi]:3.0f} units")

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