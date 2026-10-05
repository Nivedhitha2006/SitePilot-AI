import React from 'react';
export default function ScoreCard({label,value,sub}){return <section className="card score-card"><span className="muted text-xs">{label}</span><div className="score-number">{value==null?'N/A':value}</div>{sub&&<span className="muted text-xs">{sub}</span>}</section>}
