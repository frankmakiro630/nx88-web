const DB_URL_DEFAULT = 'https://wueazxozrcxjnhivqqwu.supabase.co';
const DB_KEY_DEFAULT = 'sb_publishable_tKVsV1cLkyNS_A4oJKoANw_0iZLKeHP';

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    try {
      if (url.pathname === '/api/discord-auth' && request.method === 'POST') return discordAuth(request, env, url);
      if (url.pathname === '/auth/me' && request.method === 'GET') return authMe(request, env);
      if (url.pathname === '/api/slot/spin' && request.method === 'POST') return slotSpin(request, env);
      if (url.pathname === '/api/jackpot' && request.method === 'GET') return jackpotInfo(env);
      if (url.pathname === '/api/stats' && request.method === 'GET') return statsInfo(env);
      if (url.pathname === '/api/leaderboard' && request.method === 'GET') return leaderboardInfo(env);
      if (url.pathname === '/api/baccarat/bet' && request.method === 'POST') return baccaratBet(request, env);
      if (url.pathname === '/api/baccarat/result' && request.method === 'POST') return baccaratResult(request, env);
      if (url.pathname === '/auth/discord/callback') return env.ASSETS.fetch(new URL('/', url));
      return env.ASSETS.fetch(request);
    } catch (err) { return json(500,{error:'Server error',detail:err?.message||String(err)}); }
  }
};
function json(status, body){return new Response(JSON.stringify(body),{status,headers:{'Content-Type':'application/json','Cache-Control':'no-store'}})}
function cfg(env){return {url:env.SUPABASE_URL||DB_URL_DEFAULT,key:env.SUPABASE_PUBLISHABLE_KEY||DB_KEY_DEFAULT}}
function makeToken(id){return btoa(JSON.stringify({id:String(id),iat:Date.now()})).replaceAll('+','-').replaceAll('/','_').replaceAll('=','')}
function readToken(req){const h=req.headers.get('Authorization')||'';const t=h.replace(/^Bearer\s+/i,'');if(!t)return null;try{const p=t.replaceAll('-','+').replaceAll('_','/');const pad=p+'='.repeat((4-p.length%4)%4);const o=JSON.parse(atob(pad));return o?.id?String(o.id):null}catch{return null}}
async function db(env,path,opts={}){const c=cfg(env);return fetch(c.url+'/rest/v1/'+path,{...opts,headers:{apikey:c.key,Authorization:'Bearer '+c.key,'Content-Type':'application/json',...(opts.headers||{})}})}
async function getUser(env,id){const r=await db(env,'users?user_id=eq.'+encodeURIComponent(id)+'&select=*');const a=await r.json();return Array.isArray(a)?a[0]:null}
function publicUser(r){return {id:String(r.user_id),username:r.username||'User',avatar:r.avatar||'',avatarUrl:r.avatar||'',balance:Number(r.balance??0),vipLevel:Number(r.vip_level??0),vipName:r.vip_name||'Member',vipProgress:Number(r.vip_progress??0),gamesPlayed:Number(r.games_played??0),wins:Number(r.wins??0),losses:Number(r.losses??0)}}
async function authMe(request,env){const id=readToken(request);if(!id)return json(401,{error:'Unauthorized'});const u=await getUser(env,id);if(!u)return json(401,{error:'User not found'});return json(200,publicUser(u))}
async function discordAuth(request,env,url){const input=await request.json().catch(()=>({}));if(!input.code)return json(400,{error:'Missing OAuth code'});const redirectUri=url.origin+'/auth/discord/callback';if(input.redirect_uri&&input.redirect_uri!==redirectUri)return json(400,{error:'Invalid redirect URI'});const clientId=env.DISCORD_CLIENT_ID||'1501947066560020490',secret=env.DISCORD_CLIENT_SECRET;if(!secret)return json(500,{error:'Discord client secret is not configured'});const form=new URLSearchParams({client_id:clientId,client_secret:secret,grant_type:'authorization_code',code:input.code,redirect_uri:redirectUri});const tr=await fetch('https://discord.com/api/v10/oauth2/token',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:form.toString()});const td=await tr.json().catch(()=>({}));if(!tr.ok||!td.access_token)return json(401,{error:td.error_description||'Discord token exchange failed'});const ur=await fetch('https://discord.com/api/v10/users/@me',{headers:{Authorization:'Bearer '+td.access_token}});const du=await ur.json().catch(()=>({}));if(!ur.ok||!du.id)return json(401,{error:du.message||'Failed to fetch Discord user'});const id=String(du.id),username=du.global_name||du.username||('User'+id.slice(-4)),hash=du.avatar||'';const avatar=hash?`https://cdn.discordapp.com/avatars/${id}/${hash}.${hash.startsWith('a_')?'gif':'png'}?size=128`:'';const row={user_id:id,username,avatar,updated_at:new Date().toISOString()};const r=await db(env,'users?on_conflict=user_id',{method:'POST',headers:{Prefer:'resolution=merge-duplicates,return=representation'},body:JSON.stringify(row)});const txt=await r.text();let data=[];try{data=txt?JSON.parse(txt):[]}catch{}if(!r.ok)return json(500,{error:'Supabase upsert failed',detail:data.message||data.hint||txt});const u=Array.isArray(data)&&data[0]?data[0]:await getUser(env,id);return json(200,{token:makeToken(id),user:publicUser(u||{...row,balance:0})})}
async function slotSpin(request,env){const id=readToken(request);if(!id)return json(401,{error:'Unauthorized'});const body=await request.json().catch(()=>({}));const amount=Math.floor(Number(body.amount||0));if(!Number.isFinite(amount)||amount<=0)return json(400,{error:'Invalid bet'});const u=await getUser(env,id);if(!u)return json(404,{error:'User not found'});const bal=Number(u.balance??0);if(bal<amount)return json(400,{error:'Không đủ tiền'});const syms=['🍒','🍋','🔔','7️⃣','💎','👑'];const slot=Array.from({length:5},()=>syms[Math.floor(Math.random()*syms.length)]);const counts={};slot.forEach(x=>counts[x]=(counts[x]||0)+1);const max=Math.max(...Object.values(counts));let mult=max===5?80:max===4?10:max===3?3:0;const jackpot=max===5;const reward=Math.floor(amount*mult);const newBalance=bal-amount+reward;const games=Number(u.games_played??0)+1,wins=Number(u.wins??0)+(reward>0?1:0),losses=Number(u.losses??0)+(reward>0?0:1);const r=await db(env,'users?user_id=eq.'+encodeURIComponent(id),{method:'PATCH',headers:{Prefer:'return=representation'},body:JSON.stringify({balance:newBalance,games_played:games,wins,losses,updated_at:new Date().toISOString()})});if(!r.ok)return json(500,{error:'Không thể cập nhật balance'});return json(200,{slot,reward,jackpot,newBalance,newBal:newBalance,newBalanceFormatted:newBalance.toLocaleString('vi-VN'),newBalFmt:newBalance.toLocaleString('vi-VN'),vipLevel:Number(u.vip_level??0),vipName:u.vip_name||'Member',vipProgress:Number(u.vip_progress??0)})}
async function jackpotInfo(env){const r=await db(env,'users?select=balance');const a=await r.json().catch(()=>[]);const total=(Array.isArray(a)?a:[]).reduce((s,x)=>s+Number(x.balance||0),0);return json(200,{jackpot:Math.max(1000000000,Math.floor(total*.01)),rtp:96,players:Array.isArray(a)?a.length:0})}

async function statsInfo(env){
  const r=await db(env,'users?select=balance,games_played,wins,losses');
  const a=await r.json().catch(()=>[]);
  const users=Array.isArray(a)?a:[];
  const totalBal=users.reduce((s,x)=>s+Number(x.balance||0),0);
  const players=users.length;
  const games=users.reduce((s,x)=>s+Number(x.games_played||0),0);
  const wins=users.reduce((s,x)=>s+Number(x.wins||0),0);
  // Approximate RTP until a dedicated game ledger is added.
  const rtp=games?Math.max(85,Math.min(99,Math.round(94+(wins/games)*4))):96;
  return json(200,{jackpot:Math.max(1000000000,Math.floor(totalBal*.01)),players,online:players,rtp});
}
async function leaderboardInfo(env){
  const r=await db(env,'users?select=user_id,username,avatar,balance,vip_level,vip_name&order=balance.desc&limit=100');
  const a=await r.json().catch(()=>[]);
  const list=(Array.isArray(a)?a:[]).map((u,i)=>({id:String(u.user_id),username:u.username||'User',avatar:u.avatar||'',balance:Number(u.balance||0),vipLevel:Number(u.vip_level||0),vipName:u.vip_name||'Member',rank:i+1}));
  return json(200,{byBal:list,byVip:[...list].sort((a,b)=>b.vipLevel-a.vipLevel||b.balance-a.balance)});
}
async function patchUser(env,id,body){
  const r=await db(env,'users?user_id=eq.'+encodeURIComponent(id),{method:'PATCH',headers:{Prefer:'return=representation'},body:JSON.stringify(body)});
  const a=await r.json().catch(()=>[]);
  if(!r.ok) throw new Error((a&&a.message)||'Database update failed');
  return Array.isArray(a)&&a[0]?a[0]:await getUser(env,id);
}
async function baccaratBet(request,env){
  const id=readToken(request); if(!id)return json(401,{error:'Unauthorized'});
  const b=await request.json().catch(()=>({}));
  const amount=Math.floor(Number(b.amount||0));
  if(!Number.isFinite(amount)||amount<=0)return json(400,{error:'Invalid bet'});
  const u=await getUser(env,id); if(!u)return json(404,{error:'User not found'});
  const bal=Number(u.balance??0); if(bal<amount)return json(400,{error:'Không đủ tiền'});
  const row=await patchUser(env,id,{balance:bal-amount,updated_at:new Date().toISOString()});
  return json(200,{newBalance:Number(row.balance??bal-amount)});
}
async function baccaratResult(request,env){
  const id=readToken(request); if(!id)return json(401,{error:'Unauthorized'});
  const b=await request.json().catch(()=>({}));
  const bet=Math.max(0,Math.floor(Number(b.bet||0))), payout=Math.max(0,Math.floor(Number(b.payout||0)));
  const u=await getUser(env,id); if(!u)return json(404,{error:'User not found'});
  const bal=Number(u.balance??0), games=Number(u.games_played??0)+1;
  const won=payout>bet;
  const row=await patchUser(env,id,{
    balance:bal+payout,games_played:games,
    wins:Number(u.wins??0)+(won?1:0),losses:Number(u.losses??0)+(won?0:1),
    updated_at:new Date().toISOString()
  });
  return json(200,{newBalance:Number(row.balance??bal+payout)});
}
