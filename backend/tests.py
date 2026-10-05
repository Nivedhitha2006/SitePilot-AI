from app.analyzers.seo import analyze

def test_seo_scoring():
    rows=[dict(url='https://example.com',title='A useful title for a page',meta_description='A useful description for the page',h1=1,h2=2,h3=1,images=2,missing_alt=0,internal_links=2,external_links=1,broken_links=0,canonical='https://example.com/',https=True,word_count=600,response_ms=100,error='')]
    x=analyze(rows,{'robots.txt':{'status':200},'sitemap.xml':{'status':200}})
    assert 0<=x['score']<=100
    assert x['stats']['pages']==1
