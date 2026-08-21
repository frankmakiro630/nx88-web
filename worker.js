export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === '/api/discord-auth' && request.method === 'POST') {
      return discordAuth(request, env, url);
    }
    // SPA callback: Discord redirects here, serve index.html so the frontend can read ?code=...
    if (url.pathname === '/auth/discord/callback') {
      return env.ASSETS.fetch(new URL('/', url));
    }
    return env.ASSETS.fetch(request);
  }
};

function json(status, body) {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' } });
}

async function discordAuth(request, env, url) {
  try {
    const input = await request.json().catch(() => ({}));
    if (!input.code || typeof input.code !== 'string') return json(400, { error: 'Missing OAuth code' });
    const redirectUri = `${url.origin}/auth/discord/callback`;
    if (input.redirect_uri && input.redirect_uri !== redirectUri) return json(400, { error: 'Invalid redirect URI' });

    const clientId = env.DISCORD_CLIENT_ID || '1501947066560020490';
    const clientSecret = env.DISCORD_CLIENT_SECRET;
    const supabaseUrl = env.SUPABASE_URL || 'https://wueazxozrcxjnhivqqwu.supabase.co';
    const supabaseKey = env.SUPABASE_PUBLISHABLE_KEY || 'sb_publishable_tKVsV1cLkyNS_A4oJKoANw_0iZLKeHP';
    if (!clientSecret) return json(500, { error: 'Discord client secret is not configured' });

    const form = new URLSearchParams({ client_id: clientId, client_secret: clientSecret, grant_type: 'authorization_code', code: input.code, redirect_uri: redirectUri });
    const tokenRes = await fetch('https://discord.com/api/v10/oauth2/token', { method: 'POST', headers: {'Content-Type':'application/x-www-form-urlencoded'}, body: form.toString() });
    const tokenData = await tokenRes.json().catch(() => ({}));
    if (!tokenRes.ok || !tokenData.access_token) return json(401, { error: tokenData.error_description || tokenData.message || 'Discord token exchange failed' });

    const userRes = await fetch('https://discord.com/api/v10/users/@me', { headers: { Authorization: `Bearer ${tokenData.access_token}` } });
    const du = await userRes.json().catch(() => ({}));
    if (!userRes.ok || !du.id) return json(401, { error: du.message || 'Failed to fetch Discord user' });

    const id = String(du.id), username = du.global_name || du.username || `User${id.slice(-4)}`;
    const hash = du.avatar || '';
    const avatarUrl = hash ? `https://cdn.discordapp.com/avatars/${id}/${hash}.${String(hash).startsWith('a_') ? 'gif':'png'}?size=128` : `https://cdn.discordapp.com/embed/avatars/${Number((BigInt(id)>>22n)%6n)}.png`;
    const row = { user_id:id, username, avatar:avatarUrl, updated_at:new Date().toISOString() };
    const dbRes = await fetch(`${supabaseUrl}/rest/v1/users?on_conflict=user_id`, { method:'POST', headers:{apikey:supabaseKey,Authorization:`Bearer ${supabaseKey}`,'Content-Type':'application/json',Prefer:'resolution=merge-duplicates,return=representation'}, body:JSON.stringify(row) });
    const dbText = await dbRes.text(); let dbData=[]; try { dbData=dbText?JSON.parse(dbText):[] } catch {}
    if (!dbRes.ok) return json(500, { error:'Supabase upsert failed', detail:dbData.message || dbData.hint || dbText });
    const dbUser = Array.isArray(dbData)&&dbData[0]?dbData[0]:row;
    const bytes=crypto.getRandomValues(new Uint8Array(32)); const token=Array.from(bytes,b=>b.toString(16).padStart(2,'0')).join('');
    return json(200,{token,user:{id,username,email:du.email||'',avatar:hash,avatarUrl,balance:Number(dbUser.balance||1000),vipLevel:0,vipName:'Member',vipProgress:0}});
  } catch (err) { return json(500,{error:'Authentication server error',detail:err?.message||String(err)}); }
}
