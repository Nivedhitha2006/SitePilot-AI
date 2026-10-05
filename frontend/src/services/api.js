const API=import.meta.env.VITE_API_URL||'http://localhost:8000/api';
async function request(path,options={}){const r=await fetch(API+path,options);if(!r.ok){let msg='Request failed';try{const j=await r.json();msg=j.detail||msg}catch{try{msg=await r.text()}catch{}}throw new Error(msg)}return r}
export async function analyze(url,max_pages=25){const r=await request('/analyze',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url,max_pages})});return r.json()}
export async function resolveSite(q){const r=await request('/resolve-site?q='+encodeURIComponent(q));return r.json()}
export async function upload(path,file){const f=new FormData();f.append('file',file);const r=await request('/'+path,{method:'POST',body:f});return r.json()}
export async function report(id){const r=await request(`/report/${id}`,{method:'POST'});return r.blob()}
