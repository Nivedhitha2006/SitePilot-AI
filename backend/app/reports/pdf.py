import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.platypus import BaseDocTemplate,Frame,PageTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,LongTable,KeepTogether
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.units import mm

PAGE_W,PAGE_H=A4

def P(text,style): return Paragraph(str(text if text is not None else '—').replace('&','&amp;').replace('<','&lt;').replace('>','&gt;'),style)

def make_pdf(path,data):
    os.makedirs(os.path.dirname(path),exist_ok=True)
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='KickerX',parent=styles['Normal'],fontSize=9,leading=11,fontName='Helvetica-Bold',textColor=colors.HexColor('#4f46e5'),spaceAfter=7))
    styles.add(ParagraphStyle(name='TitleX',parent=styles['Title'],fontSize=28,leading=33,fontName='Helvetica-Bold',textColor=colors.HexColor('#0f172a'),spaceAfter=12))
    styles.add(ParagraphStyle(name='H1X',parent=styles['Heading1'],fontSize=21,leading=25,fontName='Helvetica-Bold',textColor=colors.HexColor('#111827'),spaceBefore=4,spaceAfter=11))
    styles.add(ParagraphStyle(name='H2X',parent=styles['Heading2'],fontSize=13,leading=16,fontName='Helvetica-Bold',textColor=colors.HexColor('#334155'),spaceBefore=9,spaceAfter=6))
    styles.add(ParagraphStyle(name='BodyX',parent=styles['BodyText'],fontSize=9.5,leading=14,textColor=colors.HexColor('#475569')))
    styles.add(ParagraphStyle(name='SmallX',parent=styles['BodyText'],fontSize=7.5,leading=9.5,textColor=colors.HexColor('#64748b')))
    styles.add(ParagraphStyle(name='THX',parent=styles['BodyText'],fontSize=7.2,leading=8.5,fontName='Helvetica-Bold',textColor=colors.white))
    styles.add(ParagraphStyle(name='TDX',parent=styles['BodyText'],fontSize=7.1,leading=9,textColor=colors.HexColor('#334155')))
    styles.add(ParagraphStyle(name='TOCX',parent=styles['Normal'],fontSize=10,leading=15,textColor=colors.HexColor('#334155')))

    class Doc(BaseDocTemplate):
        def __init__(self,*a,**kw):
            super().__init__(*a,**kw); self._bookmark_count=0
        def afterFlowable(self,flowable):
            if isinstance(flowable,Paragraph) and flowable.style.name=='H1X':
                self._bookmark_count+=1; key=f'sec{self._bookmark_count}'; self.canv.bookmarkPage(key); self.canv.addOutlineEntry(flowable.getPlainText(),key,0,False); self.notify('TOCEntry',(0,flowable.getPlainText(),self.page,key))

    doc=Doc(path,pagesize=A4,leftMargin=16*mm,rightMargin=16*mm,topMargin=18*mm,bottomMargin=17*mm,title='SitePilot AI Website Intelligence Report',author='SitePilot AI')
    frame=Frame(doc.leftMargin,doc.bottomMargin,doc.width,doc.height,id='normal')
    doc.addPageTemplates([PageTemplate(id='main',frames=frame,onPage=lambda c,d: footer(c,d))])
    styles['BodyX'].spaceAfter=5
    url=data.get('url',''); o=data.get('overview') or {}; seo=data.get('seo') or {}; perf=data.get('performance') or {}; content=data.get('content') or {}; audience=data.get('analytics') or {}; leads=data.get('lead_intelligence') or {}; recs=data.get('recommendations') or []; pages=data.get('pages') or []
    story=[]
    # Cover
    story += [Spacer(1,34*mm),P('SITEPILOT AI',styles['KickerX']),P('Website Intelligence Report',styles['TitleX']),P('Optimization, SEO, performance, content, audience and conversion intelligence',styles['H2X']),Spacer(1,8*mm),P(url,styles['BodyX']),Spacer(1,6*mm),P(o.get('gist','Independent public website assessment.'),styles['BodyX']),Spacer(1,52*mm),P('Independent prototype • Public website signals • No fabricated metrics',styles['SmallX']),P(datetime.now().strftime('Generated %d %B %Y, %H:%M'),styles['SmallX']),PageBreak()]
    # TOC
    story += [P('Contents',styles['H1X']),Paragraph('Click a section in the PDF outline/bookmarks to jump directly to it.',styles['BodyX']),Spacer(1,4*mm),PageBreak()]
    # Executive
    story += [
        P('Executive Summary',styles['H1X']),
        Paragraph(
            f"<b>Verdict:</b> {o.get('verdict','Not assessed')} &nbsp; • &nbsp; <b>Overall score:</b> {seo.get('score','N/A')}/100",
            styles['BodyX']
        ),
        P(o.get('gist','The audit summarizes observable public website signals.'),styles['BodyX'])
    ]
    score_rows=[['Score area','Result'],['SEO',seo.get('score','N/A')],['Technical SEO',seo.get('technical_score','N/A')],['Content SEO',seo.get('content_score','N/A')]]
    story += [Spacer(1,4*mm),table(score_rows,[95,55])]
    metrics=[['Metric','Result'],['SEO score',seo.get('score','N/A')],['Technical score',seo.get('technical_score','N/A')],['Content score',seo.get('content_score','N/A')],['PageSpeed score',((perf.get('pagespeed') or {}).get('performance_score') if isinstance(perf.get('pagespeed'),dict) else perf.get('performance_score')) or 'N/A'],['Pages crawled',len(pages)],['Avg words / page',seo.get('stats',{}).get('avg_words','N/A')]]
    story += [Spacer(1,5*mm),table(metrics,[65,90]),PageBreak()]
    # Website
    story += [P('Website Analysis',styles['H1X']),P((data.get('website_analysis') or {}).get('profile',{}).get('purpose',o.get('gist','')),styles['BodyX'])]
    profile=(data.get('website_analysis') or {}).get('profile',{})
    story += [table([['Signal','Observed'],['Site type',profile.get('site_type','—')],['Domain',profile.get('domain','—')],['HTTPS coverage',f"{profile.get('https_coverage','—')}%"],['Page types',', '.join(f'{k}: {v}' for k,v in (profile.get('page_types') or {}).items()) or '—']], [45,110]),Spacer(1,5*mm)]
    if pages:
        rows=[['Page','Type','Status','Title','H1/H2/H3','Words','Images/ALT','Response']]
        for r in pages: rows.append([r.get('url',''),r.get('type','—'),r.get('status_code','—'),r.get('title') or 'Untitled',f"{r.get('h1',0)}/{r.get('h2',0)}/{r.get('h3',0)}",r.get('word_count',0),f"{r.get('images',0)}/{r.get('missing_alt',0)}",f"{round(r.get('response_ms') or 0)} ms"])
        story += [long_table(rows,[39,24,14,34,18,13,19,18]),PageBreak()]
    else: story += [P('No pages were returned by the crawl.',styles['BodyX']),PageBreak()]
    # SEO
    story += [P('SEO Intelligence',styles['H1X']),P('The SEO section explains the inspected scope and the findings produced from the crawl.',styles['BodyX'])]
    issues=seo.get('issues') or []
    rows=[['Severity','Category','Finding','Action','Impact']]
    for x in issues: rows.append([x.get('severity',''),x.get('category',''),x.get('issue',''),x.get('solution',''),x.get('expected_impact','')])
    if len(rows)>1: story += [long_table(rows,[18,25,42,61,18])]
    else: story += [P('No issues detected by the current rule set.',styles['BodyX'])]
    story += [PageBreak()]
    # Performance
    story += [P('Performance',styles['H1X']),P(perf.get('pagespeed',{}).get('message') if isinstance(perf.get('pagespeed'),dict) else perf.get('message') or 'Performance summary',styles['BodyX'])]
    ps=perf.get('pagespeed') if isinstance(perf.get('pagespeed'),dict) else {}
    rows=[['Measured factor','Value'],['Average crawl response',f"{perf.get('page_response_avg_ms','—')} ms"],['P95 crawl response',f"{perf.get('page_response_p95_ms','—')} ms"],['Average page size',f"{round((perf.get('avg_page_bytes') or 0)/1024)} KB" if perf.get('avg_page_bytes') else '—'],['Pages with errors',perf.get('pages_with_errors','—')],['HTTPS coverage',f"{perf.get('https_coverage','—')}%"],['PageSpeed',ps.get('performance_score','Unavailable')]]
    story += [table(rows,[70,85]),Spacer(1,5*mm)]
    if ps.get('available'): story += [P(f"LCP: {ps.get('lcp','—')} • CLS: {ps.get('cls','—')} • INP: {ps.get('inp','—')}",styles['BodyX'])]
    else: story += [P('PageSpeed field data/lab metrics were unavailable; the report does not invent LCP, CLS or INP.',styles['BodyX'])]
    story += [PageBreak()]
    # Content
    story += [P('Content & Keyword Intelligence',styles['H1X']),P('Keywords are extracted from the crawled public content. Coverage indicates how widely a term is distributed across the crawled pages.',styles['BodyX'])]
    kw=content.get('top_keywords') or seo.get('keywords') or []
    rows=[['Keyword','Count','Density','Pages','Coverage']]
    for k in kw[:40]: rows.append([k.get('phrase',''),k.get('count',0),f"{k.get('density',0)}%",k.get('pages','—'),f"{k.get('coverage','—')}%"])
    if len(rows)>1: story += [long_table(rows,[57,20,25,20,28])]
    story += [Spacer(1,5*mm),P('Repetitive terms',styles['H2X'])]
    rep=content.get('repetitive_sitewide') or []
    story += [P(', '.join(f"{k.get('phrase')} ({k.get('coverage')}% pages)" for k in rep) if rep else 'No strongly repetitive term signal was detected.',styles['BodyX']),P('Distinctive / niche terms',styles['H2X']),P(', '.join(f"{k.get('phrase')} ({k.get('coverage')}% pages)" for k in (content.get('distinctive_or_niche') or [])) or 'No distinctive cluster was detected by the current heuristic.',styles['BodyX']),PageBreak()]
    # Analytics + lead
    story += [P('Website Analytics & Audience Intelligence',styles['H1X']),P(audience.get('disclaimer','Public-site analytics are inferred, not actual visitor counts.'),styles['BodyX'])]
    rows=[['Audience segment','Signal','Relative interest']]
    for x in audience.get('audience_segments',[]): rows.append([x.get('segment',''),x.get('signal',0),f"{x.get('relative_interest',0)}%"])
    if len(rows)>1: story += [long_table(rows,[80,30,45])]
    story += [Spacer(1,5*mm),P(f"Imported analytics rows: {audience.get('imported_rows',0)}",styles['SmallX']),P('High-interest pages',styles['H2X'])]
    rows=[['Page','Likely audience','Page type','Signal']]
    for x in audience.get('most_interest_pages',[])[:15]: rows.append([x.get('title',''),x.get('likely_audience',''),x.get('page_type',''),x.get('interest_signal',0)])
    if len(rows)>1: story += [long_table(rows,[55,52,45,18])]
    story += [Spacer(1,4*mm),P('Important: actual page views, sessions, users and individual visitor behaviour cannot be observed from a public crawl. Upload a real GA4/Search Console export when available.',styles['SmallX']),PageBreak()]
    story += [P('Lead Intelligence',styles['H1X']),P('The lead section interprets the website’s likely conversion audiences and maps high-intent pages. It does not identify or score real individuals.',styles['BodyX']),P('Conversion opportunities',styles['H2X'])]
    for x in leads.get('conversion_opportunities',[]): story += [P('• '+x,styles['BodyX'])]
    story += [PageBreak()]
    # Recommendations
    story += [P('AI Recommendations',styles['H1X']),P('The recommendation engine combines observed SEO/technical findings with cross-area opportunities in content, performance, analytics and conversion.',styles['BodyX'])]
    rows=[['Priority','Area','Issue','What to do','Impact']]
    for r in recs: rows.append([r.get('priority',''),r.get('category',''),r.get('issue',''),r.get('solution',''),r.get('expected_impact','')])
    if len(rows)>1: story += [long_table(rows,[18,25,40,60,18])]
    story += [PageBreak(),P('Improvement Roadmap',styles['H1X'])]
    roadmap=[('Now','Fix critical security, metadata, heading and accessibility issues.'),('Next','Differentiate content topics, improve internal linking and strengthen high-intent landing pages.'),('Then','Improve measured response performance, caching/CDN and page weight where the crawl shows latency.'),('Measure','Connect GA4/Search Console and re-run the audit to replace inferred behaviour with real analytics.'),('Iterate','Re-audit after changes and compare scores, page coverage and issue counts.')]
    for a,b in roadmap: story += [KeepTogether([P(a,styles['H2X']),P(b,styles['BodyX'])])]
    story += [Spacer(1,8*mm),P('Final Assessment',styles['H1X']),P(f"{o.get('verdict','The website requires further review')}. This assessment is based on the public pages reachable during the crawl and configured external metrics only. Private traffic, conversion and individual visitor data are never fabricated.",styles['BodyX'])]
    doc.multiBuild(story)

def _fit_widths(widths,max_width_mm=176):
    total=sum(widths)
    if total <= max_width_mm: return widths
    scale=max_width_mm/total
    return [round(w*scale,2) for w in widths]

def table(rows,widths):
    widths=_fit_widths(widths)
    data=[[Paragraph(str(c),getSampleStyleSheet()['BodyText']) for c in row] for row in rows]
    data[0]=[Paragraph(str(c),getSampleStyleSheet()['BodyText']) for c in rows[0]]
    return Table(data,colWidths=[w*mm for w in widths],repeatRows=1,style=[('BACKGROUND',(0,0),(-1,0),colors.HexColor('#4f46e5')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('GRID',(0,0),(-1,-1),.3,colors.HexColor('#cbd5e1')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)])

def long_table(rows,widths):
    widths=_fit_widths(widths)
    styles=getSampleStyleSheet(); th=ParagraphStyle('pdfth',parent=styles['BodyText'],fontSize=7.1,leading=8.4,fontName='Helvetica-Bold',textColor=colors.white); td=ParagraphStyle('pdftd',parent=styles['BodyText'],fontSize=6.9,leading=8.8,textColor=colors.HexColor('#334155'))
    data=[[Paragraph(str(c),th) for c in rows[0]]]+[[Paragraph(str(c if c is not None else '—'),td) for c in row] for row in rows[1:]]
    return LongTable(data,colWidths=[w*mm for w in widths],repeatRows=1,splitByRow=1,style=[('BACKGROUND',(0,0),(-1,0),colors.HexColor('#334155')),('GRID',(0,0),(-1,-1),.25,colors.HexColor('#d7dee8')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),4),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)])

def footer(canvas,doc):
    canvas.saveState(); canvas.setFont('Helvetica',7.5); canvas.setFillColor(colors.HexColor('#64748b')); canvas.drawString(16*mm,8*mm,'SitePilot AI • Independent public-data prototype'); canvas.drawRightString(PAGE_W-16*mm,8*mm,f'Page {doc.page}'); canvas.restoreState()
