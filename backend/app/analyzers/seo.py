import re
from collections import Counter
from urllib.parse import urlparse

STOP = set('''the and for are but not you your with this that from have has was were into about our their they them then than a an of to in on is it as at by or be we can will what which when where who how why while with without from this these those its it's www com edu org net college university engineering institute school department admissions admission students student campus home about contact more page click learn new best top get use used using based also than all any each per via one two three four five six seven eight nine ten'''.split())


def _tokens(text):
    return [w.lower() for w in re.findall(r"[A-Za-z][A-Za-z0-9'-]{2,}", text or '') if w.lower() not in STOP and len(w) >= 3]


def keywords(rows):
    counter = Counter(); page_sets = {}
    total_words = sum(int(r.get('word_count') or 0) for r in rows)
    for r in rows:
        text = r.get('text','') or ''
        title = r.get('title','') or ''
        meta = r.get('meta_description','') or ''
        toks = _tokens(text)
        weighted = _tokens(title) * 4 + _tokens(meta) * 2 + toks
        counter.update(weighted)
        page_sets[r.get('url','')] = set(toks)
    result=[]
    for phrase,count in counter.most_common(40):
        pages = sum(1 for s in page_sets.values() if phrase in s)
        density = round(counter[phrase] / max(total_words,1) * 100, 3)
        result.append({'phrase':phrase,'count':int(count),'density':density,'pages':pages,'coverage':round(pages/max(len(rows),1)*100,1)})
    return result


def analyze(rows, files):
    n=max(len(rows),1); checks=[]; score=100
    def issue(cond,sev,cat,msg,fix,impact,pen):
        nonlocal score
        if cond:
            checks.append({'severity':sev,'category':cat,'issue':msg,'solution':fix,'expected_impact':impact})
            score -= pen
    titles=[(r.get('title') or '').strip() for r in rows]
    metas=[(r.get('meta_description') or '').strip() for r in rows]
    title_dupes=len(titles)-len(set(t for t in titles if t))
    meta_dupes=len(metas)-len(set(m for m in metas if m))
    avg_words=sum(int(r.get('word_count') or 0) for r in rows)/n
    avg_h1=sum(int(r.get('h1') or 0) for r in rows)/n
    issue(any(not t for t in titles),'high','SEO','Missing page title','Add a unique descriptive title of about 30–60 characters.','High',12)
    issue(any(t and (len(t)<30 or len(t)>60) for t in titles),'medium','SEO','Title length outside recommended range','Rewrite titles to be concise and descriptive.','Medium',5)
    issue(title_dupes>0,'medium','SEO',f'Duplicate page titles detected ({title_dupes})','Give each important page a unique search-focused title.','Medium',6)
    issue(any(not m for m in metas),'high','SEO','Missing meta description','Add a unique, useful description around 120–160 characters.','High',10)
    issue(meta_dupes>0,'medium','SEO',f'Duplicate meta descriptions detected ({meta_dupes})','Write page-specific descriptions that match search intent.','Medium',5)
    issue(any(int(r.get('h1') or 0)!=1 for r in rows),'high','Content','H1 structure is inconsistent','Use one clear H1 per important page.','High',8)
    issue(any(int(r.get('h2') or 0)==0 for r in rows),'medium','Content','Some pages lack H2 structure','Break long content into descriptive sections.','Medium',4)
    issue(any(int(r.get('missing_alt') or 0)>0 for r in rows),'high','Accessibility','Images missing ALT text','Add meaningful alt text; use empty alt only for decorative images.','High',8)
    issue(any(not r.get('canonical') for r in rows),'medium','Technical','Canonical tag missing','Add a self-referencing or intentionally canonical URL.','Medium',5)
    issue(not all(bool(r.get('https')) for r in rows),'critical','Security','HTTPS is not consistent','Serve all pages over HTTPS and redirect HTTP to HTTPS.','Critical',15)
    issue(files.get('robots.txt',{}).get('status')!=200,'medium','Technical','robots.txt unavailable','Publish a valid robots.txt at the domain root.','Medium',4)
    issue(files.get('sitemap.xml',{}).get('status')!=200,'medium','Technical','sitemap.xml unavailable','Publish an XML sitemap and reference it from robots.txt.','Medium',4)
    issue(avg_words<300,'medium','Content','Average crawled content is thin','Expand useful original content where search intent requires depth.','Medium',5)
    return {
      'score':round(max(0,min(100,score)),1),
      'technical_score':round(max(0,100-6*sum(1 for i in checks if i['category'] in ('Technical','Security'))-4*sum(1 for i in checks if i['category']=='Accessibility')),1),
      'content_score':round(max(0,100-(8 if avg_h1!=1 else 0)-(10 if avg_words<300 else 0)-(6 if title_dupes else 0)),1),
      'issues':checks,
      'keywords':keywords(rows),
      'stats':{'pages':len(rows),'avg_words':round(avg_words,1),'duplicate_titles':title_dupes,'duplicate_meta':meta_dupes},
    }
