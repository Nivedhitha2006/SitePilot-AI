import React from 'react';
const items=['Overview','Website Analysis','SEO','Performance','Content/Keywords','Analytics','Lead Intelligence','AI Recommendations','Reports'];
const icons={'Overview':'▦','Website Analysis':'◎','SEO':'⌕','Performance':'⌁','Content/Keywords':'▤','Analytics':'⌁','Lead Intelligence':'♙','AI Recommendations':'✦','Reports':'⇩'};
export default function Sidebar({page,setPage}){return <aside className="sidebar"><div className="logo"><div className="logo-dot">S</div><div><b>SitePilot AI</b><small>Website Intelligence</small></div></div><nav>{items.map(x=><button key={x} className={page===x?'active':''} onClick={()=>setPage(x)}><span>{icons[x]}</span>{x}</button>)}</nav><div className="side-footer">Independent prototype<br/>Public data only</div></aside>}
