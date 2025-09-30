from Wählbär import Schedule, Block, Unit, random, SLOTS_PER_DAY
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
 
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

    ax.set_xticks(np.linspace(0.5, 13.5, 14))
    # TODO: Labels for days
    
    if save:
        plt.savefig(save)
    else:
        plt.show()
