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


def load_unitlist(allocation, path="data", filename="Antworten Buchungstool.xlsx", print_enabled=False):
    full_labels = pd.read_excel(os.path.join(path, filename), sheet_name="Formularantworten 1", header=1).columns.tolist()
    df = pd.read_excel(os.path.join(path, filename), sheet_name="Formularantworten 1", header=2)

    df.dropna(subset=["ID_all_int"], inplace=True)

    for ic, col in enumerate(df.columns):
        new = col
        display_full_label = full_labels[ic].replace("\n", " ")
        if len(display_full_label) > 80:
            display_full_label = display_full_label[:77] + "..."
        if col.startswith("Unnamed") and full_labels[ic].startswith("Unnamed"):
            if print_enabled: print(f"\033[31m{new:>20}\033[0m: {display_full_label} (will get removed)")
        elif col.startswith("Unnamed") and not full_labels[ic].startswith("Unnamed"):
            try:
                ID = full_labels[ic].split("[")[2].split("]")[0]  
                group = full_labels[ic].split(" - ")[1].split(" ")[0][:2].lower()
                if group == "wö":
                    group = "wo"
                new = f"{ID}_{group}_m3"
                df.rename(columns={col: new}, inplace=True)
                if print_enabled: print(f"\033[32m{new:>20}\033[0m: {display_full_label}")
            except:
                if print_enabled: print(f"\033[31m{new:>20}\033[0m: '{display_full_label}' will get removed for no parsing")
                new = full_labels[ic]
        elif not col.startswith("Unnamed") and not full_labels[ic].startswith("Unnamed"):
            if print_enabled: print(f"\033[32m{new:>20}\033[0m: {display_full_label}")
        else:
            print(f"\033[31mERROR Label with no fullname \033[0m: '{display_full_label}' will get removed")
            # new = full_labels[ic]

    
    for col in df.columns:
        if col.startswith("Unnamed"):
            df.drop(columns=[col], inplace=True)

    if print_enabled:
        print("\033[32mFinal columns:\033[0m")
        for col in df.columns:
            print(f"{col:>20}") 

    group_df = []
    for group in ["Pios", "Pfadis", "Wölfe"]:
        df_group = df[df["group_all_tx"] == group].reset_index(drop=True)
        df_group = df_group[[c for c in df.columns if f"_{group[:2].lower().replace('ö', 'o')}_" in c or "_all" in c]]

        for ic, col in enumerate(df_group.columns):
            # print(f"{'_'.join(col.split('_')[:-2]):>20}") 
            if col.endswith("_m3") or col.endswith("_02") or col.endswith("_03")  or col.endswith("_05") or col.endswith("_int"):
                df_group = df_group.astype({col:"int32"})
            if col.endswith("_tx"):
                df_group = df_group.astype({col:"string"})
            if col.endswith("_jn"):
                df_group[col] = df_group[col].map({"Ja": True, "Nein": False})
                df_group = df_group.astype({col:"bool"})
            df_group.rename(columns={col: '_'.join(col.split('_')[:-2])}, inplace=True)
        group_df.append(df_group)

    df_pi, df_pf, df_wo = group_df

    unclassified = [c for c in df.columns if ("_pi_" not in c) and ("_pf_" not in c) and ("_wo_" not in c) and ("_all_" not in c) and ("ID" not in c)]
    if print_enabled:
        if len(unclassified) >0:
            print("\033[31mUnclassified columns (not assigned to any group):\033[0m")
            for col in unclassified:
                print(f"{col:>20}")
        else:
            print("\033[32mAll columns classified into groups.\033[0m")


    if print_enabled:
        for df_, name in zip([df_pi, df_pf, df_wo], ["Pios", "Pfadis", "Wölfe"]):
            print(f"\033[32m{name} Final columns:\033[0m")
            for col in df_.columns:
                print(f"{col:>20}: {df_.dtypes[col]}")
       

    for df_ in [df_pi, df_pf, df_wo]:
        for i in range(df_.shape[0]):
            allocation.append_unit(
                Unit(
                    str(int(df_.loc[i, "ID"])),
                    data={col: df_.loc[i, col] for col in df_.columns[1:]}
            )
        )

    print(f"Loaded {len(allocation.UNITS)} units.")
    
    
def load_blocklist(allocation, path="data", filename="PRG_Blockliste.xlsx"):

    # TODO: load unit list
    df = pd.read_excel(os.path.join(path, filename), sheet_name="On-Site Buchbar")
    df = df[[
        'Block Nr.',
        'Kategorie', 
        'Titel',
        'Programmstruktur', 
        'Dauer', 
        'J+S', 
        'Stufe', 
        'Gruppengrösse', 
        'Partizipation',
        'max. Anzahl Durchführungen (wie viele Einheiten können diesen Block besuchen?)',
        'geschätzte Anzahl Durchführungen'
    ]]

    df.columns = [
        'ID',
        'cat', 
        'fullname',
        'betr_unbetr', 
        'dauer', 
        'blockart_J_S', 
        'stufen', 
        'gruppengroesse', 
        'mix_units',
        'max_durchfuhrungen',
        'est_durchfuhrungen'
    ]

    df_offsite = pd.read_excel(os.path.join(path, filename), sheet_name="Off Site & Wasser")
    df_offsite = df_offsite[[
        'Block Nr.',
        'Off-Site', 
        'Block- Titel',
        'Programmstruktur', 
        'Blockdauer', 
        'Blockart J+S', 
        'Stufe', 
        'Gruppengrösse', 
        'Partizipation',
        'max. Anzahl Durchführungen (wie viele Einheiten können diesen Block besuchen?)',
        'geschätzte Anzahl Durchführungen'
    ]]

    df_offsite.columns = [
        'ID',
        'cat', 
        'fullname',
        'betr_unbetr', 
        'dauer', 
        'blockart_J_S', 
        'stufen', 
        'gruppengroesse', 
        'mix_units',
        'max_durchfuhrungen',
        'est_durchfuhrungen'
    ]

    df = pd.concat([df, df_offsite], ignore_index=True)
    df = df.dropna(subset=["ID"])
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
                    "cat": bd.cat,
                    "group": bd.stufen.split(", ") if type(bd.stufen) == str else bd.stufen,
                    # "group": random.choice([["wo"],["pf"], ["pi"], ["wo", "pf"], ["pf", "pi"], ["wo", "pf", "pi"]]),
                    "length": length,
                    # "on_days": [0, 1, 2, 3, 4, 5, 6],
                    "on_times": on_times
                    
                }
            )
        )
    
    allocation.find_block_cats()
    print(f"Loaded {len(allocation.BLOCKS)} blocks.")

 
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

