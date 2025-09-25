from Wählbär import Schedule, Unit, Block

# create units
attila = Unit("attila", 12, [{"name": "hund", "rank": 1}])
speicher = Unit("speicher", 12, [{"name": "hund", "rank": 1}])

# create blocks
bootlen = Block("bootlen", {"length": 1, "space": 24, "on_days": [0, 1, 2, 3, 4, 5, 6], "on_times": [1, 2]})

# set by unit
attila.set_block(bootlen, (0, 1))
speicher.set_block(bootlen, "a1")

# set by block
bootlen.set_unit(attila, "b2")

# print some stuff
print(attila.schedule["a1"])
print(attila.schedule["A1"])
print(attila.schedule[0, 1])
print(bootlen.get_space("A1"))
print(bootlen.get_space("b3"))

# get free slots
print(attila.schedule.free_slots())
print(bootlen.schedule.free_slots())

# rule for excluding days by block requirement)
bootlen.rules.append(lambda slot, bootlen, unit_req: Schedule.to_idx(slot)[0] in bootlen.requirements["on_days"]) # only on day 1, 2, 3
bootlen.rules.append(lambda slot, bootlen, unit_req: Schedule.to_idx(slot)[1] in bootlen.requirements["on_times"]) # slot 2 (afternoon2)

# example for block slot search rule
def dummy_rule(slot, block, unit_req):
    # decide if slot matches the block- or/and unit requirements
    return True

# rule for excluding days by unit requirements (for 2d hike or visit day)
def not_on_day(slot, block, unit_req):
    if "not_on_day" in unit_req and Schedule.to_idx(slot)[0] in unit_req["not_on_day"]: 
        return False
    return True

bootlen.rules.append(not_on_day)

# search slots with rules
print(bootlen.search_slots({"space": 13}))
print(bootlen.search_slots({"space": 13, "not_on_day": [2]}))