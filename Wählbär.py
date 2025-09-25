import numpy as np
import pandas as pd
import random


SLOTS_PER_DAY = 4
DAYS = 14

NRANKS = 5
SEED = 42

random.seed(SEED)

class Schedule: 
    def __init__(self, owner):
        self.blocks = [[[] for _ in range(SLOTS_PER_DAY)] for __ in range(DAYS)]
        self.owner = owner

    def __getitem__(self, ipt):
        day, slot = self.to_idx(ipt)
        return self.blocks[day][slot]


    def get_block(self, ipt):
        # day, slot = self.ipt_to_idx(ipt)
        return self[ipt]
    
    @staticmethod
    def to_idx(ipt):
        if type(ipt) == tuple or type(ipt) == str:
            if len(ipt) > 2:
                print("ERROR: WIERD INPUT")
            day, slot = ipt
        else:
            print("ERROR: WIERD INPUT")

        if type(day) == str:
            if ord(day) >=97:
                day = ord(day) - 97
            else:
                day = ord(day) - 65
        slot = int(slot)
        
        if day >= DAYS:
            print("INDEX OF DAY TOO LARGE")
            return None
        if slot >= SLOTS_PER_DAY:
            print("INDEX OF SLOT TOO LARGE")
            return None
        return day, slot
    
    def idx2str(self, day, slot):
        return chr(day+65)+str(slot)
    
    
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
    
    def free_slots(self):
        slot_list = []
        for idd, day in enumerate(self.blocks):
            for iss, slot in enumerate(day):
                if type(self.owner) == Block:

                    if self.owner.get_space((idd, iss)) > 0:
                        slot_list.append({"slot":self.idx2str(idd, iss), "space": self.owner.get_space((idd, iss))})
                else:
                    if slot == []:
                        slot_list.append(self.idx2str(idd, iss))
        return slot_list
    

class Block:
    def __init__(self, name, requirements):
        self.name = name
        self.requirements = requirements
        self.schedule = Schedule(self)

        self.rules = [lambda slot, self, unit_req : self.get_space(slot) >= unit_req["space"]]

    def get_space(self, slot):
        taken = 0
        for unit in self.schedule[slot]:
            taken += unit.nPeople
        return self.requirements["space"] - taken
    
    def set_unit(self, unit, slot):
        self.schedule.set_unit(unit, slot)    

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

        

class Unit:
    
    def __init__(self, name, nPeople, prios):
        self.name = name
        self.nPeople = nPeople
        self.prios = sorted(prios, key=lambda d: d['rank'])
        
        self.schedule = Schedule(self)

    def set_block(self, block, slot):
        self.schedule.set_block(block, slot)

    

    def rank(self, block):
        if type(block) == Block:
            blockname = block.name
        else:
            blockname = block

        for prio in self.prios:
            if blockname == prio["name"]:
                return prio["rank"]
        print("ERROR: block not in Prio")
        return NRANKS

    def score(self):  
        score = 0     
        for block in self.schedule.blocks:
            NRANKS - self.rank(block)
        return score
    
    
    def has_block(self, name):
        if type(name) == dict:
            name = name["name"]
        for block in self.schedule.blocks:
            if block.name == name:
                return True
        return False

    # returns free slots for blocks
    # accounts for: need for visit day, 1d/2d hike, ...
    # accounts for block requirements (1 slot, 2 slots, ...)
    
    # might use the function self.schedule.free_slots() which lists all free slots
    def suitable_slots(self, requirements):
        pass

    
    def highest_unmatched_prio(self):
        possibilities = []
        for prio in self.prios:
            if not self.has_block(prio):
                if len(possibilities)==0:
                    possibilities.append(prio) 
                elif possibilities[0]["rank"] == prio["rank"]:
                    possibilities.append(prio) 
                else:
                    break
        
        if possibilities:
            return random.choice(possibilities)

        return None
    
    def set_block(self, block, slot):
        self.schedule.set_block(block, slot)



# def main():
#     while True:
#         reset_and_sort_by_score(units)
#         placed_block
#         for unit in units:
#             unit.place_block()
#             unit.update_score()
#             units.remove(unit)
            

            
            
            
        