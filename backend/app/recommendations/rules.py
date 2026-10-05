def build(issues):
    out=[]
    for i in issues: out.append({'priority':i['severity'].upper(),'category':i['category'],'issue':i['issue'],'explanation':f"Detected during the public-site crawl. Severity: {i['severity']}.",'solution':i['solution'],'expected_impact':i['expected_impact']})
    return out
