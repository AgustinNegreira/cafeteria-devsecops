"""Genera el PDF de entrega y un diagrama SVG desde las fuentes Markdown.
Requiere reportlab. Ejecutar desde cualquier carpeta: python docs/generar-informe.py
"""
from pathlib import Path
import re
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon
from reportlab.graphics import renderSVG
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/pdf/Entregable_3_DevSecOps_Agustin_Negreira.pdf'
NAVY = colors.HexColor('#18354B')
TEAL = colors.HexColor('#007E7A')
INK = colors.HexColor('#243D4E')
GRAY = colors.HexColor('#607785')
PALE = colors.HexColor('#EFF5F7')
WHITE = colors.white
FONT, BOLD = 'Helvetica', 'Helvetica-Bold'
if Path('C:/Windows/Fonts/arial.ttf').exists():
    pdfmetrics.registerFont(TTFont('Arial', 'C:/Windows/Fonts/arial.ttf'))
    pdfmetrics.registerFont(TTFont('Arial-Bold', 'C:/Windows/Fonts/arialbd.ttf'))
    pdfmetrics.registerFontFamily('Arial',normal='Arial',bold='Arial-Bold',italic='Arial',boldItalic='Arial-Bold')
    FONT, BOLD = 'Arial', 'Arial-Bold'


def architecture():
    d = Drawing(490, 425)
    def text(x,y,value,size=9,bold=False,col=INK):
        d.add(String(x,y,value,fontName=BOLD if bold else FONT,fontSize=size,fillColor=col))
    def box(x,y,w,h,title,lines=(),fill=WHITE):
        d.add(Rect(x,y,w,h,rx=6,ry=6,fillColor=fill,strokeColor=colors.HexColor('#B9CFD6'),strokeWidth=.8))
        text(x+9,y+h-17,title,10,True)
        for i,line in enumerate(lines):text(x+9,y+h-32-i*12,line,8.5)
    def arrow(points,col=TEAL):
        for (x1,y1),(x2,y2) in zip(points,points[1:]): d.add(Line(x1,y1,x2,y2,strokeColor=col,strokeWidth=1.2))
        x,y=points[-1];px,py=points[-2]
        if x>px:head=[x,y,x-5,y+3,x-5,y-3]
        elif x<px:head=[x,y,x+5,y+3,x+5,y-3]
        elif y>py:head=[x,y,x-3,y-5,x+3,y-5]
        else:head=[x,y,x-3,y+5,x+3,y+5]
        d.add(Polygon(head,fillColor=col,strokeColor=col))
    box(5,370,480,50,'Windows / navegador',['App: localhost:8081   |   Jenkins: localhost:8080   |   API local: 127.0.0.1:6445'])
    d.add(Rect(5,5,480,345,rx=9,ry=9,fillColor=PALE,strokeColor=colors.HexColor('#A7C3CF'),strokeWidth=1))
    text(17,332,'Docker Desktop / Linux WSL2',11,True)
    box(18,241,183,72,'Jenkins (contenedor)',['Tests y controles / build / deploy','Login + volumen de historial','Repo local montado de solo lectura'])
    box(18,144,183,68,'Motor Docker + herramientas',['Semgrep / npm / pip-audit / Trivy','KubeLinter: manifiestos renderizados','Imagen con tag y etiquetas OCI'])
    box(18,37,183,70,'Archivos del proyecto',['reports/ + JUnit + informe','GitHub: fuente y evidencias','.local/: credenciales privadas'])
    d.add(Rect(218,21,253,296,rx=8,ry=8,fillColor=WHITE,strokeColor=TEAL,strokeWidth=1))
    text(229,299,'Nodo kind / Kubernetes + containerd',10,True)
    box(229,238,104,44,'API K8s',['6443 interno'],PALE)
    box(347,238,113,44,'Kyverno',['3 políticas Enforce'],colors.HexColor('#E6F4EE'))
    box(229,162,231,47,'Service NodePort',['30080 -> Service:80 -> app:8000'],PALE)
    box(229,85,128,53,'App FastAPI',['UID/GID 10001','API + HTML/JS'],colors.HexColor('#E6F4EE'))
    box(373,85,87,53,'PVC',['SQLite /data','256Mi'],PALE)
    box(229,32,231,33,'Falco: syscalls / modern eBPF',[],colors.HexColor('#E6F4EE'))
    arrow([(90,370),(90,313)])
    text(96,355,'8080',8,col=GRAY)
    arrow([(480,370),(480,185),(460,185)])
    text(422,355,'8081',8,col=GRAY)
    arrow([(201,274),(229,261)])
    text(204,284,'RBAC',7.5,col=GRAY)
    arrow([(333,259),(347,259)])
    arrow([(110,241),(110,212)])
    arrow([(201,180),(218,180)])
    text(174,221,'kind load',7.5,col=GRAY)
    arrow([(292,162),(292,138)])
    arrow([(357,109),(373,109)])
    arrow([(286,65),(286,85)])
    text(337,69,'observa',7.5,col=GRAY)
    arrow([(110,144),(110,107)])
    return d


def markup(s):
    s=s.replace('\u2011','-').replace('\u2013','-').replace('\u2014','-')
    s=escape(s)
    s=re.sub(r'`([^`]+)`',r'<font name="Courier" size="8.3">\1</font>',s)
    s=re.sub(r'\*\*([^*]+)\*\*',r'<b>\1</b>',s)
    s=re.sub(r'https://[^\s<]+',lambda m:'<link href="'+m.group(0)+'" color="#007E7A">'+m.group(0)+'</link>',s)
    return s

styles=getSampleStyleSheet()
styles.add(ParagraphStyle('BodyCustom',fontName=FONT,fontSize=9.3,leading=13.6,textColor=INK,spaceAfter=7))
styles.add(ParagraphStyle('H1Custom',fontName=BOLD,fontSize=22,leading=27,textColor=NAVY,spaceAfter=14))
styles.add(ParagraphStyle('H2Custom',fontName=BOLD,fontSize=12,leading=16,textColor=TEAL,spaceBefore=10,spaceAfter=7))
styles.add(ParagraphStyle('CellCustom',fontName=FONT,fontSize=8.5,leading=11.5,textColor=INK))
styles.add(ParagraphStyle('HeadCustom',fontName=BOLD,fontSize=8.7,leading=11.5,textColor=WHITE))


def decorate(c,doc):
    w,h=A4
    c.setFillColor(NAVY);c.rect(0,h-9,w,9,stroke=0,fill=1)
    c.setFont(BOLD,8);c.setFillColor(TEAL);c.drawString(46,h-34,'CAFETERIA  /  DEVSECOPS')
    c.setFont(FONT,8);c.setFillColor(GRAY);c.drawRightString(w-46,h-34,'AGUSTIN NEGREIRA  |  2026')
    c.setStrokeColor(colors.HexColor('#D1DFE4'));c.line(46,37,w-46,37)
    c.setFont(FONT,7.5);c.drawString(46,25,'Laboratorio local - evidencias de ejecucion, configuracion y pruebas')
    c.drawRightString(w-46,25,str(doc.page))


def main():
    diagram=architecture()
    renderSVG.drawToFile(diagram,str(ROOT/'docs/arquitectura-devsecops.svg'))
    lines=(ROOT/'ENTREGABLE_3.md').read_text(encoding='utf-8-sig').splitlines()
    story=[];i=0
    while i<len(lines):
        line=lines[i].strip()
        if not line:i+=1;continue
        if line=='<!-- pagebreak -->':story.append(PageBreak());i+=1;continue
        if line.startswith('!['):
            story.extend([diagram,Spacer(1,10)]);i+=1;continue
        if line.startswith('# '):story.append(Paragraph(markup(line[2:]),styles['H1Custom']));i+=1;continue
        if line.startswith('## '):story.append(Paragraph(markup(line[3:]),styles['H2Custom']));i+=1;continue
        if line.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                cells=[x.strip() for x in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r'[:\- ]+',x) for x in cells):rows.append(cells)
                i+=1
            count=len(rows[0]);widths=[135,368] if count==2 else [121,207,175]
            if count==2 and 'CVE' in rows[0][0]:widths=[130,373]
            data=[[Paragraph(markup(cell),styles['HeadCustom'] if ri==0 else styles['CellCustom']) for cell in row] for ri,row in enumerate(rows)]
            table=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
            table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),NAVY),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('ROWBACKGROUNDS',(0,1),(-1,-1),[PALE,WHITE]),('LINEBELOW',(0,0),(-1,0),.5,NAVY)]))
            story.extend([table,Spacer(1,10)]);continue
        paragraph=[line];i+=1
        while i<len(lines) and lines[i].strip() and not lines[i].startswith(('#','|','<!--','![')):
            if re.match(r'^(- |\d+\. )',lines[i].strip()):break
            paragraph.append(lines[i].strip());i+=1
        story.append(Paragraph(markup(' '.join(paragraph)),styles['BodyCustom']))
    OUT.parent.mkdir(parents=True,exist_ok=True)
    SimpleDocTemplate(str(OUT),pagesize=A4,leftMargin=46,rightMargin=46,topMargin=60,bottomMargin=51,
        title='Entregable 3 - DevSecOps - Cafeteria',author='Agustin Negreira').build(story,onFirstPage=decorate,onLaterPages=decorate)
    print(OUT)

if __name__=='__main__':main()
