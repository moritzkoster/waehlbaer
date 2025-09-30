from Wählbär import Schedule, Unit, Block, Allocation, random, test_random_seed

from Utils import print_schedule

import json

# import random
random.seed(42) # change seed here affects it for Wählbär
print(random.random())
print(test_random_seed())

allocation = Allocation(42)
# create units
attila = Unit("attila", 12, [{"name": "hund", "rank": 1}])
speicher = Unit("speicher", 12, [{"name": "hund", "rank": 1}])

# create blocks
bootlen = Block("bootlen", {"length": 1, "space": 24, "on_days": [0, 1, 2, 3, 4, 5, 6], "on_times": [1, 2]})
fischen = Block("fischen", {"length": 2, "space": 24, "on_days": [0, 1, 2, 3, 4, 5, 6], "on_times": [1, 2]})

# set by unit
attila.set_block(bootlen, (0, 1))
attila.set_block(fischen, "f2")
speicher.set_block(bootlen, "a1")

# set by block
bootlen.set_unit(attila, "b2")

# print some stuff
print(attila.schedule.get_block("A1"))
print(attila.schedule["A1"])
print(attila.schedule["a1"])
print(attila.schedule[0, 1])
print(bootlen.get_space("A1"))
print(bootlen.get_space("b3"))

# get free slots
print(attila.schedule.free_slots())
print(bootlen.schedule.free_slots())

# rule for excluding days by block requirement)
bootlen.rules.append(lambda slot, self, unit_req: Schedule.to_idx(slot)[0] in self.requirements["on_days"]) # only on day 1, 2, 3
bootlen.rules.append(lambda slot, self, unit_req: Schedule.to_idx(slot)[1] in self.requirements["on_times"]) # slot 2 (afternoon2)

# example for block slot search rule
def dummy_rule(slot, self, unit_req):
    # decide if slot matches the block- or/and unit requirements
    return True

# rule for excluding days by unit requirements (for 2d hike or visit day)
def not_on_day(slot, self, unit_req):
    if "not_on_day" in unit_req and Schedule.to_idx(slot)[0] in unit_req["not_on_day"]: 
        return False
    return True

bootlen.rules.append(not_on_day)

# search slots with rules
print(bootlen.search_slots({"space": 13}))
print(bootlen.search_slots({"space": 13, "not_on_day": [2]}))

print_schedule(attila)

allocation.append_block(bootlen)
allocation.append_block(fischen)

allocation.append_unit(attila)
allocation.append_unit(speicher)

allocation.save("test.json")
allocation.clear_schedules()
allocation.load("test.json")

print(bootlen.schedule.get_list(names_only=True, with_slot=True))
print(fischen.schedule.get_list(names_only=True, with_slot=True))


allocation.clear_lists()
allocation.load_example_blocklist()
allocation.load_example_unitlist()

# print(json.dumps(UNITS[0].prios, indent=4))
# print(json.dumps(BLOCKS[0].requirements, indent=4))

# print(allocation.BLOCKS[0].search_slots({"space": 12, "on_days": [1, 2, 3], "on_times": [2]}))