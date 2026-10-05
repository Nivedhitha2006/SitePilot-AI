import {useState} from 'react';
import {BarChart,Bar,XAxis,YAxis,Tooltip,ResponsiveContainer,CartesianGrid} from 'recharts';
import ScoreCard from '../components/ScoreCard';
export default function Dashboard({data,loading,error,setError,onAnalyze}){
 const [url,setUrl]=useState(data?.url||'https://example.com');
 const issues=data?.seo?.issues||[];
 const sev=['critical','high','medium','low'].map(x=>({name:x[0].toUpperCase()+x.slice(1),value:issues.filter(i=>String(i.severity).toLowerCase()===x).length}));
 return <div>
  <div className="page-header hero"><div><span className="eyebrow">AI WEBSITE INTELLIGENCE</span><h2>Website Intelligence</h2><p className="muted">Audit public websites with measurable, explainable signals.</p></div></div>
  <div className="analyze-bar"><input value={url} onChange={e=>setUrl(e.target.value)} placeholder="https://yourwebsite.com"/><button className="btn primary" disabled={loading} onClick={()=>onAnalyze(url,25)}>{loading?'Analyzing…':'Analyze Website'}</button></div>
  {error&&<div className="global-error">{error}<button onClick={()=>setError('')}>×</button></div>}
  {!data&&!loading&&<div className="card empty"><h3>Ready for an audit</h3><p className="muted">Enter a public URL to crawl the site and generate real SEO, technical, content and performance signals.</p></div>}
  {loading&&<div className="card loading"><div className="spinner"/><h3>Analyzing website…</h3><p className="muted">Crawling pages and calculating measurable signals.</p></div>}
  {data&&<>
   <div className="score-grid five"><ScoreCard label="SEO" value={data.seo.score}/><ScoreCard label="Technical" value={data.seo.technical_score}/><ScoreCard label="Content" value={data.seo.content_score}/><ScoreCard label="Performance" value={data.performance?.performance_score}/><ScoreCard label="Pages" value={data.seo.stats.pages}/></div>
   <div className="grid-2">
    <section className="card"><div className="section-title"><h3>Issue severity</h3><span className="muted text-xs">Latest crawl</span></div><ResponsiveContainer width="100%" height={280}><BarChart data={sev}><CartesianGrid vertical={false}/><XAxis dataKey="name"/><YAxis allowDecimals={false}/><Tooltip/><Bar dataKey="value" radius={[6,6,0,0]}/></BarChart></ResponsiveContainer></section>
    <section className="card"><div className="section-title"><h3>Top keywords</h3><span className="muted text-xs">NLP signals</span></div>{(data.seo.keywords||[]).slice(0,10).map(k=><div className="keyword-row" key={k.phrase}><span>{k.phrase}</span><b>{k.count}</b></div>)}</section>
   </div>
   <section className="card mt"><div className="section-title"><h3>Priority recommendations</h3><span className="badge info">{data.recommendations?.length||0} findings</span></div><div className="rec-grid compact">{(data.recommendations||[]).slice(0,6).map((r,i)=><div className="recommendation" key={i}><span className={`badge ${r.priority==='HIGH'||r.priority==='CRITICAL'?'danger':'warning'}`}>{r.priority}</span><h4>{r.issue}</h4><p className="muted">{r.solution}</p></div>)}</div></section>
  </>}
 </div>
}
