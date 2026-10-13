import re, collections
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.formatting.rule import CellIsRule, FormulaRule
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table

S = '/tmp/claude-0/-home-user-curly-octo-rotary-phone/e8ee6c75-57ee-5976-a7af-e8d9f787f16a/scratchpad'
OUT = '/home/user/curly-octo-rotary-phone/analysis/NCO2004_crosswalk_comparison.xlsx'

# ---------- inputs ----------
dge = pd.read_excel('/home/user/curly-octo-rotary-phone/analysis/NCO_Occupations.xlsx', dtype=str)
m15 = pd.read_csv('/home/user/curly-octo-rotary-phone/analysis/nco2015_ai_exposure_3digit.csv', dtype={'nco2015_3d': str})
wp = pd.read_csv('/home/user/kpmishra1998/nco2015-ai-exposure/ilo_wp140_tableA1.tsv', sep='\t', dtype={'code4': str})
ilo = pd.read_pickle(f'{S}/ilo_rows.pkl')

# DGE links: one row per (occupation, NCO-2004 code); occupations without a 2004 code kept once
dl = []
for _, r in dge.iterrows():
    codes = [c.strip() for c in re.split(r'[;,]', r['NCO 2004'])] if isinstance(r['NCO 2004'], str) else []
    codes = [c for c in codes if re.fullmatch(r'\d{4}\.\d{2}', c)]
    for c in codes or ['']:
        dl.append([int(r['S.No.']), r['Occupational Title'], r['NCO 2015'], c, r['Group Code'], r['Group']])
dl = pd.DataFrame(dl, columns=['sno', 'title', 'n15', 'n04', 'g15', 'g15name'])

# ILO links: titles. ISCO-08 from WP140 where available; ISCO-88 most common printed text per code
t08 = dict(zip(wp.code4, wp.occupation))
t88 = ilo.groupby('c88')['t88'].agg(lambda s: collections.Counter(s).most_common(1)[0][0])
ilo['t08c'] = [t08.get(c, t) for c, t in zip(ilo.c08, ilo.t08)]
ilo['t88c'] = ilo.c88.map(t88)
score08 = dict(zip(wp.code4, wp['mean'])); grad08 = dict(zip(wp.code4, wp.Exposure))

# group universe and lists (descriptive text columns)
dg = dl[dl.n04 != ''].assign(g04=lambda d: d.n04.str[:3])
ig = ilo.assign(g04=ilo.c88.str[:3])
groups = sorted(set(dg.g04) | set(ig.g04))
dge_sets = dg.groupby('g04').g15.apply(lambda s: sorted(set(s)))
ilo_sets = ig.groupby('g04').c08.apply(lambda s: sorted({c[:3] for c in s}))
main15 = dg.groupby('g04').apply(lambda t: t.g15.value_counts().idxmax())
name15 = dict(zip(dl.g15, dl.g15name))
name15.update(dict(zip(m15.nco2015_3d, m15.isco_label)))

# ---------- styles ----------
F = 'Arial'
base = Font(name=F, size=10)
bold = Font(name=F, size=10, bold=True)
white_bold = Font(name=F, size=10, bold=True, color='FFFFFF')
blue = Font(name=F, size=10, color='0000FF')
green = Font(name=F, size=10, color='008000')
title_font = Font(name=F, size=14, bold=True)
head_fill = PatternFill('solid', fgColor='1F3864')
yellow = PatternFill('solid', fgColor='FFFF00')
wrap = Alignment(wrap_text=True, vertical='top')

wb = Workbook()

def header(ws, row, cols, widths):
    for i, (c, w) in enumerate(zip(cols, widths), 1):
        cell = ws.cell(row=row, column=i, value=c)
        cell.font = white_bold; cell.fill = head_fill; cell.alignment = Alignment(wrap_text=True, vertical='center')
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[row].height = 42
    ws.freeze_panes = ws.cell(row=row + 1, column=2)

# ---------- NCO-2015 scores ----------
ws5 = wb.active; ws5.title = 'NCO-2015 scores'
header(ws5, 1, ['NCO-2015 group', 'Group title (ISCO-08)', 'ILO exposure score (0-1)', 'Share of jobs in ILO gradients 3-4'], [14, 55, 16, 18])
for i, r in enumerate(m15.itertuples(), 2):
    ws5.cell(i, 1, r.nco2015_3d); ws5.cell(i, 2, r.isco_label)
    ws5.cell(i, 3, None if pd.isna(r.ilo_score_uw) else r.ilo_score_uw).font = blue
    ws5.cell(i, 4, None if pd.isna(r.ilo_high_grad_share) else r.ilo_high_grad_share).font = blue
n5 = len(m15) + 1
ws5.cell(n5 + 2, 1, 'Source: Mishra, nco2015-ai-exposure (github.com/Kpmishra1998/nco2015-ai-exposure), built from ILO WP140 (Gmyrek et al. 2025) Table A1. Blue = input values.').font = Font(name=F, size=9, italic=True)

# ---------- DGE links ----------
ws2 = wb.create_sheet('DGE links')
cols = ['S.No.', 'Occupational title', 'NCO-2015 code', 'NCO-2004 code', 'NCO-2015 group', 'NCO-2004 group',
        'Same 3-digit number?', 'Weight (1 / links of this 2004 code)', 'Exposure of NCO-2015 group', 'Has score (1/0)']
header(ws2, 1, cols, [7, 45, 13, 13, 11, 11, 11, 13, 13, 9])
for i, r in enumerate(dl.itertuples(), 2):
    ws2.cell(i, 1, r.sno); ws2.cell(i, 2, r.title); ws2.cell(i, 3, r.n15); ws2.cell(i, 4, r.n04 or None)
    ws2.cell(i, 5, f'=LEFT(C{i},3)')
    ws2.cell(i, 6, f'=IF(D{i}="","",LEFT(D{i},3))')
    ws2.cell(i, 7, f'=IF(F{i}="","",IF(E{i}=F{i},"Yes","No"))')
    ws2.cell(i, 8, f'=IF(D{i}="",0,1/COUNTIF($D$2:$D${len(dl)+1},D{i}))')
    ws2.cell(i, 9, f"=IFERROR(INDEX('NCO-2015 scores'!$C$2:$C${n5},MATCH(E{i},'NCO-2015 scores'!$A$2:$A${n5},0)),0)").font = green
    ws2.cell(i, 10, f"=IF(ISNUMBER(MATCH(E{i},'NCO-2015 scores'!$A$2:$A${n5},0)),IF(ISNUMBER(INDEX('NCO-2015 scores'!$C$2:$C${n5},MATCH(E{i},'NCO-2015 scores'!$A$2:$A${n5},0))),1,0),0)").font = green
nd = len(dl) + 1
ws2.auto_filter.ref = f'A1:J{nd}'
ws2.cell(nd + 2, 1, 'Source: Directorate General of Employment, National Classification of Occupations listing (dge.gov.in/nat), 3,447 occupations, printed 13 Oct 2026 (provided by the user). Rows with several NCO-2004 codes are split, one row per code.').font = Font(name=F, size=9, italic=True)

# ---------- ILO links ----------
ws3 = wb.create_sheet('ILO links')
cols = ['ISCO-08 code', 'ISCO-08 title', 'ISCO-88 code', 'ISCO-88 title', 'Partial match (p)', 'ILO comment (as printed; may be clipped)',
        'NCO-2004 group (= ISCO-88 first 3 digits)', 'ILO exposure score of ISCO-08 job', 'ILO exposure gradient', 'First link of this job to this group (1/0)']
header(ws3, 1, cols, [10, 40, 10, 45, 9, 30, 14, 13, 16, 12])
for i, r in enumerate(ilo.itertuples(), 2):
    ws3.cell(i, 1, r.c08); ws3.cell(i, 2, r.t08c); ws3.cell(i, 3, r.c88); ws3.cell(i, 4, r.t88c)
    ws3.cell(i, 5, r.part or None); ws3.cell(i, 6, r.com or None)
    ws3.cell(i, 7, f'=LEFT(C{i},3)')
    s = score08.get(r.c08)
    c = ws3.cell(i, 8, s); c.font = blue
    ws3.cell(i, 9, grad08.get(r.c08, 'Not scored by ILO'))
    ws3.cell(i, 10, f'=IF(COUNTIFS($G$2:G{i},G{i},$A$2:A{i},A{i})=1,1,0)')
ni = len(ilo) + 1
ws3.auto_filter.ref = f'A1:J{ni}'
ws3.cell(ni + 2, 1, 'Sources: ILO, Correspondence table ISCO-08 to ISCO-88 (wcms_306833.pdf, provided by the user); scores and gradients from ILO WP140 (Gmyrek et al. 2025) Table A1. ISCO-88 titles were read from the PDF, which clips some long titles. Blue = input values.').font = Font(name=F, size=9, italic=True)

# ---------- Comparison ----------
ws = wb.create_sheet('Comparison', 0)
cols = ['NCO-2004 group', 'Main NCO-2015 group (DGE)', 'Main NCO-2015 group title', 'NCO-2015 groups reached via DGE',
        'ISCO-08 groups reached via ILO table', 'Groups reached by both', 'Overlap (shared / all groups reached)',
        'DGE occupations', 'ISCO-08 jobs linked', 'Exposure: DGE route', 'Exposure: ILO route', 'Difference (DGE - ILO)',
        'Absolute difference', 'Agreement', 'Score used in dataset', 'Source of score used']
header(ws, 1, cols, [10, 11, 34, 20, 20, 16, 12, 10, 10, 11, 11, 11, 11, 13, 11, 13])
D, I = "'DGE links'", "'ILO links'"
for i, g in enumerate(groups, 2):
    a = dge_sets.get(g, []); b = ilo_sets.get(g, [])
    both = sorted(set(a) & set(b)); allg = set(a) | set(b)
    ws.cell(i, 1, g)
    mg = main15.get(g)
    ws.cell(i, 2, mg); ws.cell(i, 3, name15.get(mg) if mg else None)
    ws.cell(i, 4, ' '.join(a) or None); ws.cell(i, 5, ' '.join(b) or None); ws.cell(i, 6, ' '.join(both) or None)
    ws.cell(i, 7, (len(both) / len(allg)) if (a and b) else None).number_format = '0%'
    ws.cell(i, 8, f'=SUMPRODUCT(({D}!$F$2:$F${nd}=A{i})*1)').font = green
    ws.cell(i, 9, f'=SUMPRODUCT(({I}!$G$2:$G${ni}=A{i})*{I}!$J$2:$J${ni})').font = green
    ws.cell(i, 10, f'=IFERROR(SUMPRODUCT(({D}!$F$2:$F${nd}=A{i})*{D}!$H$2:$H${nd}*{D}!$I$2:$I${nd}*{D}!$J$2:$J${nd})'
                   f'/SUMPRODUCT(({D}!$F$2:$F${nd}=A{i})*{D}!$H$2:$H${nd}*{D}!$J$2:$J${nd}),"")').font = green
    ws.cell(i, 11, f'=IFERROR(AVERAGEIFS({I}!$H$2:$H${ni},{I}!$G$2:$G${ni},A{i},{I}!$J$2:$J${ni},1),"")').font = green
    ws.cell(i, 12, f'=IF(AND(ISNUMBER(J{i}),ISNUMBER(K{i})),J{i}-K{i},"")')
    ws.cell(i, 13, f'=IF(ISNUMBER(L{i}),ABS(L{i}),"")')
    ws.cell(i, 14, f'=IF(ISNUMBER(M{i}),IF(M{i}<=Summary!$B$4,"Agree","Check"),IF(ISNUMBER(J{i}),"DGE only",IF(ISNUMBER(K{i}),"ILO only","Not scored")))')
    ws.cell(i, 15, f'=IF(ISNUMBER(J{i}),J{i},IF(ISNUMBER(K{i}),K{i},""))')
    ws.cell(i, 16, f'=IF(ISNUMBER(J{i}),"DGE",IF(ISNUMBER(K{i}),"ILO table",""))')
    for c in (10, 11, 12, 13, 15):
        ws.cell(i, c).number_format = '0.000'
nc = len(groups) + 1
ws.auto_filter.ref = f'A1:P{nc}'
ws.conditional_formatting.add(f'N2:N{nc}', CellIsRule(operator='equal', formula=['"Check"'], fill=PatternFill('solid', fgColor='F8CBAD')))
ws.conditional_formatting.add(f'N2:N{nc}', CellIsRule(operator='equal', formula=['"Agree"'], fill=PatternFill('solid', fgColor='C6EFCE')))
ws.cell(nc + 2, 1, 'Each row is one NCO-2004 3-digit group (the codes PLFS used from 2017-18 to 2020-21). Columns J-P are formulas over the DGE links, ILO links and NCO-2015 scores sheets; columns B-G are text summaries computed when the workbook was built.').font = Font(name=F, size=9, italic=True)

# ---------- Summary ----------
sm = wb.create_sheet('Summary', 0)
sm.column_dimensions['A'].width = 62; sm.column_dimensions['B'].width = 14; sm.column_dimensions['C'].width = 60
sm['A1'] = 'NCO-2004 to exposure: DGE concordance vs ILO correspondence table'; sm['A1'].font = title_font
sm['A3'] = 'Setting'; sm['A3'].font = bold
sm['A4'] = 'Agreement threshold (absolute difference in exposure score)'; sm['B4'] = 0.05
sm['B4'].font = blue; sm['B4'].fill = yellow
sm['C4'] = 'Edit this cell. Groups whose two scores differ by more than this are marked "Check".'
C = 'Comparison'
rows = [
    ('Coverage', None, None),
    ('NCO-2004 groups in either source', f'=COUNTA({C}!A2:A{nc})', '0'),
    ('Groups scored via DGE concordance', f'=COUNT({C}!J2:J{nc})', '0'),
    ('Groups scored via ILO table', f'=COUNT({C}!K2:K{nc})', '0'),
    ('Groups scored by both', f'=COUNT({C}!L2:L{nc})', '0'),
    ('Groups only in DGE', f'=COUNTIF({C}!N2:N{nc},"DGE only")', '0'),
    ('Groups only in ILO table', f'=COUNTIF({C}!N2:N{nc},"ILO only")', '0'),
    ('Agreement (groups scored by both)', None, None),
    ('Correlation of the two scores', f'=CORREL({C}!J2:J{nc},{C}!K2:K{nc})', '0.000'),
    ('Mean absolute difference', f'=AVERAGE({C}!M2:M{nc})', '0.000'),
    ('Largest absolute difference', f'=MAX({C}!M2:M{nc})', '0.000'),
    ('Groups that agree (within threshold)', f'=COUNTIF({C}!N2:N{nc},"Agree")', '0'),
    ('Groups to check (beyond threshold)', f'=COUNTIF({C}!N2:N{nc},"Check")', '0'),
    ('Share that agree', f'=IFERROR(B17/B9,0)', '0%'),
    ('Code numbering', None, None),
    ("DGE occupations with an NCO-2004 code", f"=COUNTIF('DGE links'!F2:F{nd},\"?*\")", '#,##0'),
    ('...of which keep the same 3-digit number in NCO-2015', f"=COUNTIF('DGE links'!G2:G{nd},\"Yes\")", '#,##0'),
    ('Share keeping the same 3-digit number', '=IFERROR(B22/B21,0)', '0%'),
]
r0 = 6
for k, (lab, f, fmt) in enumerate(rows):
    r = r0 + k
    sm.cell(r, 1, lab)
    if f is None:
        sm.cell(r, 1).font = bold
    else:
        sm.cell(r, 1).font = base
        c = sm.cell(r, 2, f); c.number_format = fmt; c.font = green
sm.cell(r0 + len(rows) + 1, 1, 'How to read this workbook').font = bold
notes = [
    'Comparison: one row per NCO-2004 group. "Exposure: DGE route" averages the NCO-2015 group scores of the occupations DGE lists under that old group (each old occupation counts once). "Exposure: ILO route" averages the ILO scores of the ISCO-08 jobs the ILO table links to that ISCO-88 group.',
    'DGE links: India\'s own concordance, one row per occupation and NCO-2004 code. ILO links: the ILO ISCO-08 to ISCO-88 table, one row per link.',
    'Why both: NCO-2004 is based on ISCO-88 but departs from it in places (e.g. farm labourers are 920 in NCO-2004 and 921 in ISCO-88; general managers are 130). "DGE only" and "ILO only" rows are often these renumbered groups.',
    'Colour key: blue = input values from the sources; green = formulas pulling from another sheet; yellow = setting you can change.',
]
for k, t in enumerate(notes):
    c = sm.cell(r0 + len(rows) + 2 + k, 1, t); c.alignment = wrap; c.font = base
    sm.merge_cells(start_row=c.row, end_row=c.row, start_column=1, end_column=3)
    sm.row_dimensions[c.row].height = 42

for wsx in wb.worksheets:
    for row in wsx.iter_rows():
        for cell in row:
            if cell.font is None or cell.font.name != F:
                cell.font = Font(name=F, size=cell.font.size or 10, bold=cell.font.bold, italic=cell.font.italic, color=cell.font.color)
wb.save(OUT)
print('saved', OUT, len(groups), 'groups', nd, ni)
