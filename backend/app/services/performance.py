import requests
from app.config import settings
def run(url):
    if not settings.pagespeed_api_key:return {'available':False,'performance_score':None,'message':'Performance API unavailable (no API key configured).'}
    try:
        r=requests.get('https://www.googleapis.com/pagespeedonline/v5/runPagespeed',params={'url':url,'key':settings.pagespeed_api_key,'category':'performance'},timeout=30); r.raise_for_status(); d=r.json(); lh=d.get('lighthouseResult',{}); score=lh.get('categories',{}).get('performance',{}).get('score'); a=lh.get('audits',{}); return {'available':True,'performance_score':round(score*100,1) if score is not None else None,'lcp':a.get('largest-contentful-paint',{}).get('numericValue'),'cls':a.get('cumulative-layout-shift',{}).get('numericValue'),'inp':a.get('interaction-to-next-paint',{}).get('numericValue'),'message':'','raw_json':d}
    except Exception as e:return {'available':False,'performance_score':None,'message':f'Performance API unavailable: {e}'}
