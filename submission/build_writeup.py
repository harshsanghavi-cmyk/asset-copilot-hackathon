"""Build the local PDF from the same architecture and saved JSON as the live Doc.

The authoritative editable DOCX is exported from the linked Google Doc.
Run package_final_results.py first. Requires reportlab and pypdf.
"""
from pathlib import Path
import json, textwrap
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'submission'
FIGS=[('10','10-architecture-and-evidence-for-review.png'),('12','12-contextual-retrieval-operating-flow.png'),('13','13-memory-save-and-summary-flow.png'),('14','14-long-term-compression-and-retrieval.png')]
W,H=A4
c=canvas.Canvas(str(OUT/'asset-copilot-writeup.pdf'),pagesize=A4)
c.setTitle('Asset Intelligence Copilot - Architecture and all 11 saved results')
y=H-40; page=1

def newpage():
 global y,page
 c.setFont('Helvetica',7);c.drawRightString(W-36,20,str(page));c.showPage();page+=1;y=H-40

def line(text,font='Helvetica',size=9,leading=12):
 global y
 if y<40:newpage()
 c.setFont(font,size);c.drawString(36,y,text);y-=leading

architecture=(OUT/'ARCHITECTURE.md').read_text()
for raw in architecture.splitlines():
 for wrapped in textwrap.wrap(raw,105,replace_whitespace=False) or ['']:
  line(wrapped)
newpage()
for num,file in FIGS:
 line('Diagram '+num,'Helvetica-Bold',13,22)
 h=(W-72)*2/3
 c.drawImage(ImageReader(str(ROOT/'diagrams'/file)),36,y-h,width=W-72,height=h,preserveAspectRatio=True)
 y-=h+25
 newpage()
for part in json.loads((OUT/'google-doc-results-parts.json').read_text()):
 if part['style']=='heading':
  if y<H-80:newpage()
  line(part['text'].strip(),'Helvetica-Bold',14,22)
 else:
  code=part['style']=='code'
  for raw in part['text'].splitlines():
   for wrapped in textwrap.wrap(raw,118 if code else 105,replace_whitespace=False,break_long_words=True,break_on_hyphens=False) or ['']:
    line(wrapped,'Courier' if code else 'Helvetica',7 if code else 9,9 if code else 12)
c.setFont('Helvetica',7);c.drawRightString(W-36,20,str(page));c.save()
pdf=PdfReader(OUT/'asset-copilot-writeup.pdf')
print('PDF pages:',len(pdf.pages),'Original figures:',len(FIGS),'Result replies:',21)
