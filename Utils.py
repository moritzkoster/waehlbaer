from Wählbär import Schedule, Block, Unit, Allocation, SLOTS_PER_DAY, DAYS
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os
import xlsxwriter as xls
 
def plot_block(ax, slot, block):
    day, slot = Schedule.to_idx(slot)
    x = day
    y = SLOTS_PER_DAY - slot 
    ax.add_patch(patches.Rectangle((x, y), 1, -block.requirements["length"], linewidth=1, edgecolor='none', facecolor='teal'))
    ax.text(x + 0.1, y-0.3, block.name, fontweight="bold")
    ax.text(x + 0.1, y-0.5, "ORT")


def print_schedule(thing, save=False):
    if type(thing) == Block or type(thing) == Unit:
        schedule = thing.schedule
    elif type(thing) == Schedule:
        schedule = thing
    else:
        print("ERROR: unknown schedule type. expected 'Block', 'Unit' or 'Schedule'")

    fig = plt.figure(figsize=(16, 5))
    ax = plt.subplot(111)
    for idd, day in enumerate(schedule.calendar):
        for iss, slot in enumerate(day):
            if len(slot) == 1:
                block = slot[0]
                plot_block(ax, (idd, iss), block)
            if len(slot) > 1:
                print("ERROR: MORE THAN ONE BLOCK PER SLOT")
    ax.set_xlim(-1, 15)
    ax.set_ylim(-1, 5)

    ax.set_xticks([i + 0.5 for i in range(14)])
    # TODO: Labels for days
    
    if save:
        plt.savefig(save)
    else:
        plt.show()

def slot_to_xlsx_cell(slot):
    day, time = ord(slot[0]) - 65, int(slot[1])
    return f"{chr(day+1+65) + str(time+1 +2)}"


def write_to_xlsx(allocation, fname="allocation.xlsx", path="saves"):
    workbook = xls.Workbook(os.path.join(path,fname))

    merge_format = workbook.add_format(
    {
        "bold": 1,
        "border": 0,
        "align": "center",
        "valign": "vcenter",
        # "fg_color": "yellow",
    }
)

    for iu, unit in enumerate(allocation.UNITS):
        # unit = allocation.UNITS[0]
        worksheet = workbook.add_worksheet(unit.name)
        worksheet.merge_range("B1:O1", unit.name, merge_format)
        for i in range(1, SLOTS_PER_DAY +1):
            worksheet.write(f"A{i+2}", f"slot {i}")
        for i in range(DAYS):
            worksheet.write(f"{chr(i+1+65)}2", f"day {i+1}")

        for block in unit.schedule.get_list(names_only=True, with_slot=True):
            worksheet.write(slot_to_xlsx_cell(block["slot"]), block["name"])

    worksheet = workbook.add_worksheet("Freie Blöcke")
    worksheet.merge_range("B1:O1", "Freie Blöcke", merge_format)
    for i in range(1, SLOTS_PER_DAY +1):
        worksheet.write(f"A{i+2}", f"slot {i}")
    for i in range(DAYS):
        worksheet.write(f"{chr(i+1+65)}2", f"day {i+1}")

    for idd in range(DAYS):
        for itt in range(SLOTS_PER_DAY):
            cell = chr(idd + 1+65) + str(itt +3)
            string = "=CONCATENATE(CONCATENATE("
            for ib, block in enumerate(allocation.BLOCKS):
                string += f'IF(${block.name}.{cell} ="";CONCATENATE(${block.name}.B1; CHAR(10));"");'
                if ib == 63:
                    string = string[:-1] + "); CONCATENATE("
            
            string = string[:-1]+"))"
            worksheet.write(cell, string)   
    
    
    for ib, block in enumerate(allocation.BLOCKS):
        # unit = allocation.UNITS[0]
        worksheet = workbook.add_worksheet(block.name)
        worksheet.merge_range("B1:O1", block.name, merge_format)
        for i in range(1, SLOTS_PER_DAY +1):
            worksheet.write(f"A{i+2}", f"slot {i}")
        for i in range(DAYS):
            worksheet.write(f"{chr(i+1+65)}2", f"day {i+1}")

        for block in block.schedule.get_list(names_only=True, with_slot=True):
            worksheet.write(slot_to_xlsx_cell(block["slot"]), block["name"])

    workbook.close()
