from docx import Document
from docx.shared import RGBColor
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

import subprocess
import datetime
import os
import pandas as pd

from Wählbär import Schedule, Block, Unit, Allocation, SLOTS_PER_DAY, DAYS
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import xlsxwriter as xls

def slot_to_table_idx(slot):
    if type(slot) == str:
        idx = Schedule.to_idx(slot)
    elif type(slot) == tuple:
        idx = slot
    else:
        print(f"ERROR: invalid type {type(slot)} expected 'tuple' or 'str'")
        
    row = idx[1] +1
    if idx[0] <= 6:
        col = idx[0] 
        return 0, row, col
    else:
        col = idx[0] -6 
        return 2, row, col


def export_to_pdf(unit):

    doc = Document("templates/template_unit.docx")
    # TODO: define all replacements
    
    for placeholder, value in { # TODO
    "{name}": unit.data["fullname"],
    "{date}": datetime.datetime.now().date().strftime("%d.%m.%Y"),
    "{ID}": str(unit.ID),
    "{group}": unit.data["group"]}.items():
        replace_text_in_document(doc, placeholder, value)

    for block in unit.schedule.get_list(with_slot=True):
        tab, row, col = slot_to_table_idx(block["slot"])
        table = doc.tables[tab]

        # Access the cell (e.g., first row, first column)
        cell = table.cell(row, col)

        # Set the background color of the cell
        shading_elm = OxmlElement('w:shd')
        shading_elm.set(qn('w:fill'), "00b48f")  # green color
        cell._tc.get_or_add_tcPr().append(shading_elm)



    doc.save(f"exports/{unit.ID}.docx")

    subprocess.run([
        "libreoffice",
        "--headless",
        "--convert-to", "pdf",
        "--outdir", "exports",
        f"exports/{unit.ID}.docx"
    ])


def replace_text_in_paragraph(paragraph, placeholder, replacement):
    for run in paragraph.runs:
        if placeholder in run.text:
            # Split the text into parts before, after, and the placeholder
            split = run.text.split(placeholder)
            pre = split[0]  # Keep the text before the placeholder
            post = split[1]
            
            run.text = pre + replacement + post  # Keep the text before the placeholder
            # Add the replacement text with the same style
            # for part in parts[1:]:
            #     run = paragraph.add_run(replacement + part)
            #     # Copy the style from the previous run
            #     run.bold = paragraph.runs[-2].bold
            #     run.italic = paragraph.runs[-2].italic
            #     run.underline = paragraph.runs[-2].underline
            #     run.font.name = paragraph.runs[-2].font.name
            #     run.font.size = paragraph.runs[-2].font.size
            #     run.font.color.rgb = paragraph.runs[-2].font.color.rgb

def replace_text_in_document(doc, placeholder, replacement):
    for paragraph in doc.paragraphs:
        replace_text_in_paragraph(paragraph, placeholder, replacement)

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    replace_text_in_paragraph(paragraph, placeholder, replacement)
    
    for section in doc.sections:
        # Header
        if section.header is not None:
            for paragraph in section.header.paragraphs:
                replace_text_in_paragraph(paragraph, placeholder, replacement)
        # Footer
        if section.footer is not None:
            for paragraph in section.footer.paragraphs:
                replace_text_in_paragraph(paragraph, placeholder, replacement)


def load_unitlist(allocation, path="data", filename="Antworten Buchungstool.xlsx"):
    df = pd.read_excel(os.path.join(path, filename), sheet_name="Formularantworten 1", header=2)
    
    PRIOS = [
        ["Umbedingt", "Das wollen wir unbendingt machen"],
        ["Sehr Gerne", "Das würden wir sehr gerne machen"],
        ["Gerne", "Das würden wir gerne machen"],
        ["Neutral"],
        ["Lieber nicht", "Das wollen wir nicht machen"]
    ]
    for ip, p in enumerate(PRIOS):
        for pp in  p:
            df.replace(pp, str(ip+1), inplace=True)
    
    for column in df.columns:
        print(f"{column}: \033[1m{df.loc[0, column]}\033[0m")
    for index, row in df.iterrows():
        # Convert the row to a dictionary

        data = {col: row[col] for col in df.columns}
        data["n_people"] = 24
        allocation.append_unit(
            Unit(
                data["ID"],
                data=data
            )
        )

    # TODO: load unit list

def load_blocklist(allocation, path="data", filename="PRG_Blockliste.xlsx"):

    # TODO: load unit list
    df = pd.read_excel(os.path.join(path, filename), sheet_name="On-Site Buchbar")
    df = df[[
        'Block Nr.',
        'Off-Site', 
        'Block- Titel',
        'Ort', 
        'Programmstruktur', 
        'On-Site', 'Off-Site.1',
        'Blockdauer', 
        'Blockart J+S', 
        'Stufe', 
        'Gruppengrösse', 
        'Partizipation',
        'max. Anzahl Durchführungen (wie viele Einheiten können diesen Block besuchen?)',
        'geschätzte Anzahl Durchführungen'
    ]]

    df.columns = [
        'ID',
        'typ', 
        'fullname',
        'ort', 
        'betr_unbetr', 
        'tags_onsite', 'tags_offsite',
        'dauer', 
        'blockart_J_S', 
        'stufen', 
        'gruppengroesse', 
        'mix_units',
        'max_durchführungen',
        'est_durchführungen'
    ]
    df = df.dropna(subset=["ID"])

    print(df["stufen"])
    for bd in df.itertuples():
        
        length = 1
        on_times = [0, 1, 2]
        if bd.dauer == "4h": 
            length = 2
            on_times = [1]
        if bd.dauer == "8h":
            length = 4
            on_times = [0]
        if bd.dauer == "2 Tage":
            length = 7
            on_times = [0]
        
        allocation.append_block(

            Block(
                bd.ID,
                {   "fullname": bd.fullname,
                    "space": bd.gruppengroesse,
                    "js_type": bd.blockart_J_S,
                    "cath": bd.typ,
                    "group": bd.stufen.split(", ") if type(bd.stufen) == str else bd.stufen,
                    # "group": random.choice([["wo"],["pf"], ["pi"], ["wo", "pf"], ["pf", "pi"], ["wo", "pf", "pi"]]),
                    "length": length,
                    # "on_days": [0, 1, 2, 3, 4, 5, 6],
                    "on_times": on_times
                    
                }
            )
        )
 
def plot_block(ax, slot, block):
    day, slot = Schedule.to_idx(slot)
    x = day
    y = SLOTS_PER_DAY - slot 
    ax.add_patch(patches.Rectangle((x, y), 1, -block.requirements["length"], linewidth=1, edgecolor='none', facecolor='teal'))
    ax.text(x + 0.1, y-0.3, block.ID, fontweight="bold")
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
        worksheet = workbook.add_worksheet(unit.ID)
        worksheet.merge_range("B1:O1", unit.ID, merge_format)
        for i in range(1, SLOTS_PER_DAY +1):
            worksheet.write(f"A{i+2}", f"slot {i}")
        for i in range(DAYS):
            worksheet.write(f"{chr(i+1+65)}2", f"day {i+1}")

        for block in unit.schedule.get_list(id_only=True, with_slot=True):
            worksheet.write(slot_to_xlsx_cell(block["slot"]), block["ID"])

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
                string += f'IF(${block.ID}.{cell} ="";CONCATENATE(${block.ID}.B1; CHAR(10));"");'
                if ib == 63:
                    string = string[:-1] + "); CONCATENATE("
            
            string = string[:-1]+"))"
            worksheet.write(cell, string)   
    
    
    for ib, block in enumerate(allocation.BLOCKS):
        # unit = allocation.UNITS[0]
        worksheet = workbook.add_worksheet(block.ID)
        worksheet.merge_range("B1:O1", block.ID, merge_format)
        for i in range(1, SLOTS_PER_DAY +1):
            worksheet.write(f"A{i+2}", f"slot {i}")
        for i in range(DAYS):
            worksheet.write(f"{chr(i+1+65)}2", f"day {i+1}")

        for block in block.schedule.get_list(id_only=True, with_slot=True):
            worksheet.write(slot_to_xlsx_cell(block["slot"]), block["ID"])

    workbook.close()

