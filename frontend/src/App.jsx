import React, { useEffect, useState } from 'react';
import Sidebar from './components/Sidebar';

const API = import.meta.env.VITE_API_URL || '/api';
const NAV = ['Overview','Website Analysis','SEO','Performance','Content/Keywords','Analytics','Lead Intelligence','AI Recommendations','Reports'];

async function request(path, options={}) {
  const res = await fetch(API + path, options);
  const text = await res.text();
  let body = {};
  try { body = text ? JSON.parse(text) : {}; } catch { body = { detail: text }; }
  if (!res.ok) throw new Error(body.detail || body.message || `Request failed (${res.status})`);
  return body;
}

async function analyzeSite(url, maxPages=25) {
  return request('/analyze', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({url, max_pages:maxPages}) });
}
async function resolveSite(query) { return request('/resolve-site?q=' + encodeURIComponent(query)); }
async function createReport(id) {
  const res = await fetch(API + `/report/${id}`, {
    method: 'POST',
    headers: { Accept: 'application/pdf' }
  });

  const type = (res.headers.get('content-type') || '').toLowerCase();
  if (!res.ok) {
    const text = await res.text();
    let message = text;
    try {
      const body = text ? JSON.parse(text) : {};
      message = body.detail || body.message || text;
    } catch {}
    throw new Error(message || `Could not generate the PDF (${res.status}).`);
  }

  const blob = await res.blob();
  if (!blob.size || (!type.includes('pdf') && blob.type !== 'application/pdf')) {
    throw new Error('The server did not return a valid PDF file.');
  }
  return blob;
}

async function uploadCSV(path, websiteId, file) {
  const form = new FormData();
  form.append('file', file);
  return request(`${path}/${websiteId}`, { method: 'POST', body: form });
}

const n = (v, fallback='—') => v === null || v === undefined || Number.isNaN(Number(v)) ? fallback : v;
const pct = v => v === null || v === undefined ? 'N/A' : `${Math.round(Number(v))}/100`;
const tone = v => Number(v) >= 80 ? 'good' : Number(v) >= 60 ? 'warn' : 'bad';
const escText = s => String(s ?? '').replace(/\s+/g,' ').trim();

function Card({children,className=''}) { return <section className={`card ${className}`}>{children}</section>; }
function Header({title,desc}) { return <div className="page-header"><span className="eyebrow">SITEPILOT AI</span><h1>{title}</h1><p className="muted">{desc}</p></div>; }
function Badge({children,tone='info'}) { return <span className={`badge ${tone}`}>{children}</span>; }
function Empty({title,text}) { return <Card className="empty"><div className="empty-icon">◎</div><h3>{title}</h3><p className="muted">{text}</p></Card>; }
function Score({label,value,sub=''}) { return <Card className="score-card"><span className="muted text-xs">{label}</span><div className="score-number">{value === null || value === undefined ? 'N/A' : value}</div>{sub && <span className="muted text-xs">{sub}</span>}</Card>; }
function SectionTitle({children,right}) { return <div className="section-title"><h3>{children}</h3>{right}</div>; }

function speak(text) {
  if (!('speechSynthesis' in window)) return false;
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.lang = 'en-IN'; u.rate = 0.95; u.pitch = 1;
  window.speechSynthesis.speak(u); return true;
}

function Overview({data,onAnalyze,loading,error,setError}) {
  const [input,setInput] = useState(data?.url || '');
  const [listening,setListening] = useState(false);
  const [resolving,setResolving] = useState(false);
  const [voiceMsg,setVoiceMsg] = useState('');
  useEffect(()=>{ if(data?.url) setInput(data.url); },[data?.url]);

  const submitQuery = async (raw) => {
    const query = escText(raw);
    if (!query) return;
    setInput(query);
    setResolving(true); setError('');
    try {
      let url = query;
      if (!/^https?:\/\//i.test(url)) {
        const r = await resolveSite(url);
        url = r.url;
      }
      setInput(url);
      await onAnalyze(url);
    } catch(e) {
      setError(e.message);
    } finally {
      setResolving(false);
    }
  };

  const listen = () => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { setVoiceMsg('Voice input needs Chrome or Edge.'); return; }
    const r = new SR(); r.lang='en-IN'; r.interimResults=false; r.maxAlternatives=1;
    setListening(true); setVoiceMsg('Listening… say a website name or URL.');
    r.onresult = e => {
      const t = escText(e.results[0][0].transcript);
      setInput(t);
      setVoiceMsg(`Heard: ${t}. Finding the public website…`);
      submitQuery(t);
    };
    r.onerror = () => setVoiceMsg('I could not hear that. Please try again.');
    r.onend = () => setListening(false); r.start();
  };

  const submit = async () => submitQuery(input);

  const readSummary = () => {
    if(!data) return;
    const o=data.overview||{};
    const text=`${o.site_name || 'This website'} is a ${o.site_type || 'public website'}. Overall score ${Math.round(o.score||0)} out of 100. ${o.verdict || ''}. ${o.top_opportunity ? `Main improvement: ${o.top_opportunity}.` : ''}`;
    speak(text);
  };

  return <>
    <div className="hero-row"><Header title="Website Intelligence" desc="A crystal-clear gist first. The dedicated pages contain the evidence and improvement plan."/><div className="hero-actions"><Badge>Public data only</Badge>{data&&<button className="icon-btn" onClick={readSummary} title="Read overview aloud">🔊</button>}</div></div>
    <Card className="analyzer"><div className="input-wrap"><span>⌕</span><input value={input} onChange={e=>setInput(e.target.value)} onKeyDown={e=>e.key==='Enter'&&submit()} placeholder="Type a public URL or say a website name…"/><button className={`voice-btn ${listening?'listening':''}`} onClick={listen}>{listening?'■':'🎙'}</button></div><button className="btn primary" disabled={loading||resolving} onClick={submit}>{resolving?'Finding website…':loading?'Analyzing…':'Analyze Website'}</button></Card>
    {voiceMsg&&<div className="voice-msg">🎙 {voiceMsg}</div>}
    {error&&<div className="global-error">⚠ {error}<button onClick={()=>setError('')}>×</button></div>}
    {!data&&!loading&&<Empty title="Ready for an audit" text="Enter a public URL or speak a website name. SitePilot will discover, crawl and interpret the public website."/>}
    {loading&&<Card className="loading"><div className="spinner"/><h3>Analyzing the website…</h3><p className="muted">Crawling public pages and calculating measurable signals.</p></Card>}
    {data&&<div className="overview-content">
      <Card className="gist"><div><span className="eyebrow">CRYSTAL GIST</span><h2>{data.overview?.gist}</h2><p className="muted">{data.url}</p></div><div className={`verdict ${tone(data.overview?.score)}`}><strong>{Math.round(data.overview?.score||0)}</strong><span>/100</span><small>{data.overview?.verdict}</small></div></Card>
      <div className="overview-grid"><Card><SectionTitle right={<Badge>Observed</Badge>}>What this website is</SectionTitle><p className="big-copy">{data.overview?.gist}</p><div className="mini-grid"><div><span className="muted">Type</span><b>{data.overview?.site_type}</b></div><div><span className="muted">Pages</span><b>{data.overview?.pages_crawled}</b></div></div></Card><Card><SectionTitle right={<span>→</span>}>Best next action</SectionTitle><h4>{data.overview?.top_opportunity || 'No major issue detected'}</h4><p className="muted">Use the dedicated pages for the full evidence, not here.</p><button className="text-btn" onClick={()=>window.dispatchEvent(new CustomEvent('sitepilot-nav',{detail:'AI Recommendations'}))}>Open recommendations →</button></Card></div>
    </div>}
  </>;
}

function WebsiteAnalysis({data}) {
  if(!data) return <Empty title="No website analysis yet" text="Run an audit from Overview first."/>;
  const p=data.website_analysis?.profile||{}; const rows=data.pages||[]; const types=p.page_types||{};
  return <><Header title="Website Analysis" desc="A full public-site inventory: what pages exist, what they contain, who they appear to serve, and how the structure is organized."/>
    <div className="stat-grid four"><Score label="Pages crawled" value={rows.length} sub="public pages"/><Score label="HTTPS" value={`${n(p.https_coverage,0)}%`} sub="crawled pages"/><Score label="Page groups" value={Object.keys(types).length} sub="inferred types"/><Score label="Site type" value={p.site_type||'—'} sub="classification"/></div>
    <div className="grid-2"><Card><SectionTitle right={<Badge tone="success">Observed</Badge>}>Website profile</SectionTitle><dl className="definition"><div><dt>Purpose</dt><dd>{p.purpose}</dd></div><div><dt>Domain</dt><dd>{p.domain}</dd></div><div><dt>Coverage</dt><dd>{p.pages_crawled} pages in this crawl</dd></div></dl></Card><Card><SectionTitle>Page-type distribution</SectionTitle><div className="bar-list">{Object.entries(types).sort((a,b)=>b[1]-a[1]).map(([k,v])=><div className="bar-item" key={k}><div><span>{k}</span><b>{v}</b></div><i style={{width:`${Math.max(5,(v/Math.max(1,...Object.values(types)))*100)}%`}}/></div>)}</div></Card></div>
    <Card><SectionTitle right={<span className="muted text-xs">Page-by-page evidence</span>}>Page inventory</SectionTitle><div className="table-wrap"><table><thead><tr><th>Page</th><th>Status</th><th>Title</th><th>H1/H2/H3</th><th>Words</th><th>Images</th><th>Links</th><th>Response</th></tr></thead><tbody>{rows.map((r,i)=><tr key={i}><td className="url-cell">{r.url}</td><td><Badge tone={r.status_code===200?'success':'danger'}>{r.status_code||'ERR'}</Badge></td><td>{r.title||'Untitled'}</td><td>{r.h1}/{r.h2}/{r.h3}</td><td>{r.word_count||0}</td><td>{r.images||0} / {r.missing_alt||0} missing ALT</td><td>{r.internal_links||0} internal / {r.external_links||0} external</td><td>{Math.round(r.response_ms||0)} ms</td></tr>)}</tbody></table></div></Card>
  </>;
}

function SEOPage({data}) {
  if(!data) return <Empty title="No SEO data" text="Run an audit first."/>;
  const s=data.seo||{}; const issues=s.issues||[];
  const checks=['Titles and title length','Meta descriptions','Duplicate titles/meta','H1/H2 structure','Image ALT coverage','Canonical URLs','HTTPS','robots.txt','sitemap.xml','Content depth'];
  return <><Header title="SEO Intelligence" desc="The SEO scope found on this public website, the current strength, the actual findings, and what should improve."/><div className="stat-grid three"><Score label="Overall SEO" value={pct(s.score)}/><Score label="Technical SEO" value={pct(s.technical_score)}/><Score label="Content SEO" value={pct(s.content_score)}/></div><div className="grid-2"><Card><SectionTitle>SEO scope inspected</SectionTitle><div className="check-grid">{checks.map(x=><div key={x}>✓ <span>{x}</span></div>)}</div></Card><Card><SectionTitle right={<Badge tone={issues.length?'warning':'success'}>{issues.length} findings</Badge>}>Diagnosis</SectionTitle>{issues.slice(0,12).map((x,i)=><div className="issue-line" key={i}><Badge tone={x.severity==='critical'||x.severity==='high'?'danger':x.severity==='medium'?'warning':'info'}>{x.severity}</Badge><div><b>{x.issue}</b><p>{x.solution}</p></div></div>)}</Card></div><Card><SectionTitle>SEO improvement plan</SectionTitle><div className="rec-grid compact">{issues.map((x,i)=><div className="recommendation" key={i}><Badge tone={x.severity==='critical'||x.severity==='high'?'danger':'warning'}>{x.severity}</Badge><h4>{x.issue}</h4><p>{x.explanation}</p><div className="solution"><b>Do this</b><p>{x.solution}</p></div></div>)}</div></Card></>;
}

function PerformancePage({data}) {
  if(!data) return <Empty title="No performance data" text="Run an audit first."/>;
  const p=data.performance||{}; const ps=p.pagespeed||{}; const available=ps?.available;
  return <><Header title="Performance" desc="Performance is based on real crawl response measurements. Lighthouse/PageSpeed values appear only when the API is configured and returns them."/>
    <div className="stat-grid four"><Score label="PageSpeed" value={available&&ps.performance_score!=null?Math.round(ps.performance_score):'N/A'} sub={available?'real PageSpeed score':'not configured / unavailable'}/><Score label="Avg response" value={p.page_response_avg_ms!=null?`${Math.round(p.page_response_avg_ms)} ms`:'N/A'}/><Score label="P95 response" value={p.page_response_p95_ms!=null?`${Math.round(p.page_response_p95_ms)} ms`:'N/A'}/><Score label="Error pages" value={n(p.pages_with_errors,0)} sub="observed in crawl"/></div>
    <div className="grid-2"><Card><SectionTitle>Real measurements</SectionTitle><div className="metric-list"><div><span>Average page response</span><b>{p.page_response_avg_ms==null?'N/A':`${p.page_response_avg_ms} ms`}</b></div><div><span>P95 page response</span><b>{p.page_response_p95_ms==null?'N/A':`${p.page_response_p95_ms} ms`}</b></div><div><span>Average page bytes</span><b>{p.avg_page_bytes==null?'N/A':`${Math.round(p.avg_page_bytes/1024)} KB`}</b></div><div><span>HTTPS coverage</span><b>{p.https_coverage}%</b></div></div>{!available&&<p className="muted text-sm">{ps?.message||'No PageSpeed result was returned, so no synthetic performance score is shown.'}</p>}</Card><Card><SectionTitle>Slowest crawled pages</SectionTitle><div className="simple-list">{(p.slow_pages||[]).map((x,i)=><div key={i}><span>{x.url}</span><b>{Math.round(x.response_ms)} ms</b></div>)}{!(p.slow_pages||[]).length&&<p className="muted">No response-time records available.</p>}</div></Card></div>
    {available&&<Card><SectionTitle>Core Web Vitals / PageSpeed evidence</SectionTitle><div className="metric-list"><div><span>LCP</span><b>{ps.lcp ?? 'N/A'}</b></div><div><span>CLS</span><b>{ps.cls ?? 'N/A'}</b></div><div><span>INP</span><b>{ps.inp ?? 'N/A'}</b></div></div></Card>}
  </>;
}

function ContentPage({data}) {
  if(!data) return <Empty title="No content intelligence" text="Run an audit first."/>;
  const c=data.content||{}; const kws=c.top_keywords||[];
  return <><Header title="Content & Keywords" desc="What topics the website emphasizes, which terms repeat heavily, which topics are distinctive, and where content depth can improve."/><div className="stat-grid three"><Score label="Avg words/page" value={Math.round(c.avg_words||0)}/><Score label="Duplicate titles" value={c.duplicate_titles||0}/><Score label="Duplicate meta" value={c.duplicate_meta||0}/></div><div className="grid-2"><Card><SectionTitle>Top keywords / phrases</SectionTitle>{kws.slice(0,20).map((k,i)=><div className="keyword-row" key={i}><div><b>{k.phrase}</b><small>{k.count} occurrences · {k.coverage!=null?`${k.coverage}% page coverage`:''}</small></div><Badge>{k.density!=null?`${k.density}%`:''}</Badge></div>)}{!kws.length&&<p className="muted">No keyword signals were extracted.</p>}</Card><Card><SectionTitle>Repetition & uniqueness</SectionTitle><h4>Repeated site-wide</h4>{(c.repetitive_sitewide||[]).map((k,i)=><div className="keyword-row" key={i}><span>{k.phrase}</span><b>{k.coverage}%</b></div>)}<h4 className="subhead">Distinctive / niche</h4>{(c.distinctive_or_niche||[]).map((k,i)=><div className="keyword-row" key={i}><span>{k.phrase}</span><b>{k.count}</b></div>)}<p className="muted text-sm">These are public-site content signals, not a fabricated competitor ranking.</p></Card></div><Card><SectionTitle>Content improvement opportunities</SectionTitle><div className="action-list">{(c.improvements||[]).map((x,i)=><div key={i}><span>{i+1}</span><p>{x}</p></div>)}</div></Card><Card><SectionTitle>Page content map</SectionTitle><div className="table-wrap"><table><thead><tr><th>Page</th><th>Type</th><th>Words</th><th>H1</th><th>H2</th></tr></thead><tbody>{(c.page_content_map||[]).map((r,i)=><tr key={i}><td className="url-cell">{r.url}</td><td>{r.type}</td><td>{r.words}</td><td>{r.h1}</td><td>{r.h2}</td></tr>)}</tbody></table></div></Card></>;
}

function AnalyticsPage({data}) {
  const [uploading,setUploading]=useState(false);
  const [uploadMsg,setUploadMsg]=useState('');
  const [uploaded,setUploaded]=useState(null);
  if(!data) return <Empty title="No website analytics yet" text="Run an audit first. SitePilot will infer audience interest from public page structure; it will not invent visitor counts."/>;
  const a=data.analytics||{}; const seg=a.audience_segments||[]; const pages=a.most_interest_pages||[];
  const upload=async(file)=>{
    if(!file) return;
    setUploading(true); setUploadMsg('');
    try{
      const result=await uploadCSV('/analytics',data.website_id,file);
      setUploaded(result);
      setUploadMsg(`Imported ${result.rows} analytics rows successfully.`);
    }catch(e){setUploadMsg(`Upload error: ${e.message}`)}
    finally{setUploading(false)}
  };
  return <><Header title="Website Analytics" desc="Public-site intent signals plus optional real analytics CSV import. Actual traffic numbers are shown only when you provide the source data."/>
    <Card className="notice"><div>ⓘ</div><div><b>Inference mode</b><p>{a.disclaimer}</p></div></Card>
    <Card><SectionTitle right={<label className="upload"><input type="file" accept=".csv,text/csv" disabled={uploading} onChange={e=>upload(e.target.files?.[0])}/>{uploading?'Uploading…':'Upload GA4 / analytics CSV'}</label>}>Optional real analytics</SectionTitle><p className="muted text-sm">Upload a CSV export when you have it. SitePilot stores up to 10,000 rows for this website and previews the first 10 rows. It never fabricates traffic.</p>{uploadMsg&&<div className={uploadMsg.startsWith('Upload error')?'global-error':'success-box'}>{uploadMsg}</div>}{uploaded&&uploaded.preview?.length>0&&<div className="table-wrap"><table><thead><tr>{uploaded.columns.map(c=><th key={c}>{c}</th>)}</tr></thead><tbody>{uploaded.preview.map((row,i)=><tr key={i}>{uploaded.columns.map(c=><td key={c}>{String(row[c]??'')}</td>)}</tr>)}</tbody></table></div>}</Card>
    <div className="grid-2"><Card><SectionTitle>Likely visitor groups</SectionTitle>{seg.length?seg.map((s,i)=><div className="audience" key={i}><div><span>{s.segment}</span><b>{s.relative_interest}%</b></div><div className="interest-bar"><i style={{width:`${s.relative_interest}%`}}/></div></div>):<p className="muted">Not enough public signals to infer a segment.</p>}</Card><Card><SectionTitle>Pages with strongest interest signals</SectionTitle>{pages.map((p,i)=><div className="intent-card" key={i}><span className="intent-rank">{i+1}</span><div><b>{p.title}</b><p>{p.page_type} · {p.likely_audience}</p></div><span className="intent-score">{p.interest_signal}</span></div>)}</Card></div><Card><SectionTitle>Visitor journey / funnel</SectionTitle><div className="rec-grid compact">{(a.funnel||[]).map((f,i)=><div className="recommendation" key={i}><Badge>{f.stage}</Badge><h4>{f.page_type}</h4><p>{f.url}</p><small>Likely audience: {f.likely_audience}</small></div>)}</div></Card></>;
}

function LeadsPage({data}) {
  const [uploading,setUploading]=useState(false);
  const [uploadMsg,setUploadMsg]=useState('');
  const [result,setResult]=useState(null);
  if(!data) return <Empty title="No lead intelligence yet" text="Run an audit first. You can then upload a lead CSV to train the conversion model."/>;
  const a=data.lead_intelligence||{}; const seg=a.audience_segments||[]; const pages=a.most_interest_pages||[];
  const upload=async(file)=>{
    if(!file) return;
    setUploading(true); setUploadMsg('');
    try{
      const r=await uploadCSV('/leads',data.website_id,file);
      setResult(r);
      setUploadMsg(`Processed ${r.rows} lead rows successfully.`);
    }catch(e){setUploadMsg(`Upload error: ${e.message}`)}
    finally{setUploading(false)}
  };
  return <><Header title="Lead Intelligence" desc="Public intent signals plus an optional Random Forest model trained on your own lead CSV."/>
    <Card className="notice"><div>◎</div><div><b>Public intent model</b><p>This is an inferred model based on page titles, URLs, metadata and site structure. It is not a claim about real individual visitors.</p></div></Card>
    <Card><SectionTitle right={<label className="upload"><input type="file" accept=".csv,text/csv" disabled={uploading} onChange={e=>upload(e.target.files?.[0])}/>{uploading?'Training…':'Upload lead CSV'}</label>}>Optional real lead model</SectionTitle><p className="muted text-sm">For ML scoring, the CSV needs a <b>converted</b> target column plus the features documented in the README. The model is trained only on the uploaded data.</p>{uploadMsg&&<div className={uploadMsg.startsWith('Upload error')?'global-error':'success-box'}>{uploadMsg}</div>}{result&&<><div className="stat-grid three"><Score label="Rows" value={result.rows}/><Score label="Validation accuracy" value={result.metrics?.accuracy!=null?`${Math.round(result.metrics.accuracy*100)}%`:'N/A'}/><Score label="Validation AUC" value={result.metrics?.roc_auc!=null?result.metrics.roc_auc.toFixed(3):'N/A'}/></div><div className="table-wrap"><table><thead><tr><th>Lead</th><th>Score</th><th>Probability</th><th>Intent</th></tr></thead><tbody>{(result.predictions||[]).map((p,i)=><tr key={i}><td>{p.lead_id}</td><td>{p.score}</td><td>{Math.round(Number(p.probability||0)*100)}%</td><td><Badge tone={String(p.intent).toLowerCase().includes('high')?'danger':'warning'}>{p.intent}</Badge></td></tr>)}</tbody></table></div></>}</Card>
    <div className="grid-2"><Card><SectionTitle>Potential audience / lead categories</SectionTitle>{seg.map((s,i)=><div className="audience" key={i}><div><span>{s.segment}</span><b>{s.relative_interest}% signal</b></div><div className="interest-bar"><i style={{width:`${s.relative_interest}%`}}/></div></div>)}</Card><Card><SectionTitle>High-intent pages</SectionTitle>{pages.slice(0,10).map((p,i)=><div className="intent-card" key={i}><span className="intent-rank">{i+1}</span><div><b>{p.title}</b><p>{p.likely_audience} · {p.page_type}</p></div><span className="intent-score">{p.interest_signal}</span></div>)}</Card></div><Card><SectionTitle>How to drive more qualified visitors</SectionTitle><div className="action-list">{(a.conversion_opportunities||[]).map((x,i)=><div key={i}><span>{i+1}</span><p>{x}</p></div>)}</div></Card></>;
}

function RecommendationsPage({data}) {
  if(!data) return <Empty title="No recommendations yet" text="Run an audit first."/>;
  const recs=data.recommendations||[]; const groups={}; recs.forEach(r=>{const k=r.category||'General'; if(!groups[k]) groups[k]=[]; groups[k].push(r);});
  return <><Header title="AI Recommendations" desc="One improvement layer across website structure, SEO, performance, content, analytics, lead intent and additional opportunities."/><div className="rec-summary"><div><b>{recs.length}</b><span>Total findings</span></div><div><b>{recs.filter(r=>['CRITICAL','HIGH'].includes(String(r.priority).toUpperCase())).length}</b><span>High priority</span></div><div><b>{Object.keys(groups).length}</b><span>Improvement areas</span></div></div>{Object.entries(groups).map(([cat,items])=><Card key={cat}><SectionTitle>{cat}</SectionTitle><div className="rec-grid">{items.map((r,i)=><div className="recommendation" key={i}><Badge tone={String(r.priority).toUpperCase()==='CRITICAL'||String(r.priority).toUpperCase()==='HIGH'?'danger':'warning'}>{r.priority}</Badge><span className="issue-cat">{cat}</span><h4>{r.issue}</h4><p>{r.explanation}</p><div className="solution"><b>Recommended action</b><p>{r.solution}</p><small>Impact: {r.expected_impact}</small></div></div>)}</div></Card>)}</>;
}

function ReportsPage({data}) {
  const [generating,setGenerating]=useState(false);
  const [msg,setMsg]=useState('');
  const [reportUrl,setReportUrl]=useState('');
  useEffect(()=>()=>{if(reportUrl) URL.revokeObjectURL(reportUrl)},[reportUrl]);
  if(!data) return <Empty title="No report yet" text="Run an audit first, then generate the complete report here."/>;
  const generate=async()=>{
    setGenerating(true); setMsg('');
    try{
      const blob=await createReport(data.website_id);
      const url=URL.createObjectURL(blob);
      setReportUrl(old=>{if(old) URL.revokeObjectURL(old); return url;});
      const a=document.createElement('a');
      a.href=url; a.download=`SitePilot_Report_${data.website_id}.pdf`; a.style.display='none';
      document.body.appendChild(a); a.click(); a.remove();
      setMsg('Full report generated successfully. If Chrome did not start the download, click Open PDF or Download PDF below.');
      const o=data.overview||{};
      speak(`${o.site_name||'The analyzed website'} has an overall score of ${Math.round(o.score||0)} out of 100. ${o.verdict||''}. ${o.top_opportunity?`Main improvement: ${o.top_opportunity}.`:''}`);
    }catch(e){setMsg(`Report error: ${e.message}`)}
    finally{setGenerating(false)}
  };
  const o=data.overview||{};
  return <><Header title="Reports" desc="Generate the complete evidence-based PDF report with website analysis, SEO, performance, content, analytics, lead intelligence, recommendations, roadmap and final assessment."/>
    <Card className="report-card"><div className="report-icon">▣</div><div><h2>Complete website intelligence report</h2><p className="muted">The report uses the current audit result and does not fabricate traffic, revenue, conversions or PageSpeed metrics.</p><div className="tag-row"><Badge>{o.verdict}</Badge><Badge tone="success">Score {Math.round(o.score||0)}/100</Badge></div></div><button className="btn primary" onClick={generate} disabled={generating}>{generating?'Generating full report…':'Generate Full PDF Report'}</button></Card>
    {msg&&<div className={msg.startsWith('Report error')?'global-error':'success-box'}>{msg}</div>}
    {reportUrl&&<Card className="notice"><div>📄</div><div><b>PDF is ready</b><p className="muted">Use either button. Open PDF is also a reliable fallback if browser download permissions block automatic downloads.</p></div><a className="btn" href={reportUrl} target="_blank" rel="noreferrer">Open PDF</a><a className="btn primary" href={reportUrl} download={`SitePilot_Report_${data.website_id}.pdf`}>Download PDF</a></Card>}
    <Card className="notice"><div>🔊</div><div><b>Final voice assessment</b><p>SitePilot speaks a short verdict based only on the analyzed public website.</p></div><button className="btn" onClick={()=>speak(`${o.site_name||'This website'} has a score of ${Math.round(o.score||0)} out of 100. ${o.verdict||''}. ${o.top_opportunity?`The most important improvement is ${o.top_opportunity}.`:''}`)}>Speak now</button></Card>
  </>;
}

export default function App(){
  const [page,setPage]=useState('Overview');
  const [data,setData]=useState(()=>{
    try { return JSON.parse(localStorage.getItem('sitepilot-last-analysis') || 'null'); }
    catch { return null; }
  });
  const [loading,setLoading]=useState(false);
  const [error,setError]=useState('');
  const [theme,setTheme]=useState(localStorage.getItem('sitepilot-theme')||'light');
  useEffect(()=>{const h=e=>setPage(e.detail);window.addEventListener('sitepilot-nav',h);return()=>window.removeEventListener('sitepilot-nav',h)},[]);
  useEffect(()=>{const t=theme==='system'?(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'):theme;document.documentElement.dataset.theme=t;localStorage.setItem('sitepilot-theme',theme)},[theme]);
  useEffect(()=>{
    try {
      if(data) localStorage.setItem('sitepilot-last-analysis',JSON.stringify(data));
      else localStorage.removeItem('sitepilot-last-analysis');
    } catch {}
  },[data]);
  const analyze=async(url)=>{
    setLoading(true);
    setError('');
    setData(null);
    try{
      const d=await analyzeSite(url,25);
      setData(d);
      setPage('Overview');
    }catch(e){
      setError(e.message || 'Website analysis failed.');
    }finally{
      setLoading(false);
    }
  };
  const common={data,setData};
  let content=<Overview data={data} onAnalyze={analyze} loading={loading} error={error} setError={setError}/>;
  if(page==='Website Analysis') content=<WebsiteAnalysis {...common}/>;
  if(page==='SEO') content=<SEOPage {...common}/>;
  if(page==='Performance') content=<PerformancePage {...common}/>;
  if(page==='Content/Keywords') content=<ContentPage {...common}/>;
  if(page==='Analytics') content=<AnalyticsPage {...common}/>;
  if(page==='Lead Intelligence') content=<LeadsPage {...common}/>;
  if(page==='AI Recommendations') content=<RecommendationsPage {...common}/>;
  if(page==='Reports') content=<ReportsPage {...common}/>;
  return <><Sidebar page={page} setPage={setPage}/><main className="main"><header className="topbar"><span className="mobile-brand">SitePilot AI</span><div className="theme-controls"><button className={theme==='light'?'active':''} onClick={()=>setTheme('light')}>☀</button><button className={theme==='dark'?'active':''} onClick={()=>setTheme('dark')}>☾</button><button className={theme==='system'?'active':''} onClick={()=>setTheme('system')}>▣</button></div></header>{error&&page!=='Overview'&&<div className="global-error">⚠ {error}<button onClick={()=>setError('')}>×</button></div>}{content}</main></>;
}
