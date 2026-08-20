export async function onRequestPost(context) {
  const json = (status, body) => new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' }
  });

  try {
    const input = await context.request.json().catch(() => ({}));
    if (!input.code || typeof input.code !== 'string') return json(400, { error: 'Missing OAuth code' });

    const url = new URL(context.request.url);
    const redirectUri = `${url.origin}/auth/discord/callback`;
    if (input.redirect_uri && input.redirect_uri !== redirectUri) {
      return json(400, { error: 'Invalid redirect URI' });
    }

    const CLIENT_ID = context.env.DISCORD_CLIENT_ID || '1501947066560020490';
    const CLIENT_SECRET = context.env.DISCORD_CLIENT_SECRET;
    const SUPABASE_URL = context.env.SUPABASE_URL || 'https://wueazxozrcxjnhivqqwu.supabase.co';
    const SUPABASE_KEY = context.env.SUPABASE_PUBLISHABLE_KEY || 'sb_publishable_tKVsV1cLkyNS_A4oJKoANw_0iZLKeHP';

    if (!CLIENT_SECRET) return json(500, { error: 'Discord client secret is not configured' });

    const form = new URLSearchParams({
      client_id: CLIENT_ID,
      client_secret: CLIENT_SECRET,
      grant_type: 'authorization_code',
      code: input.code,
      redirect_uri: redirectUri
    });

    const tokenRes = await fetch('https://discord.com/api/v10/oauth2/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: form.toString()
    });
    const tokenData = await tokenRes.json().catch(() => ({}));
    if (!tokenRes.ok || !tokenData.access_token) {
      return json(401, { error: tokenData.error_description || tokenData.message || 'Discord token exchange failed' });
    }

    const userRes = await fetch('https://discord.com/api/v10/users/@me', {
      headers: { Authorization: `Bearer ${tokenData.access_token}` }
    });
    const du = await userRes.json().catch(() => ({}));
    if (!userRes.ok || !du.id) return json(401, { error: du.message || 'Failed to fetch Discord user' });

    const id = String(du.id);
    const username = du.global_name || du.username || `User${id.slice(-4)}`;
    const hash = du.avatar || '';
    const avatarUrl = hash
      ? `https://cdn.discordapp.com/avatars/${id}/${hash}.${String(hash).startsWith('a_') ? 'gif' : 'png'}?size=128`
      : `https://cdn.discordapp.com/embed/avatars/${Number((BigInt(id) >> 22n) % 6n)}.png`;

    const row = { user_id: id, username, avatar: avatarUrl, updated_at: new Date().toISOString() };
    const dbRes = await fetch(`${SUPABASE_URL}/rest/v1/users?on_conflict=user_id`, {
      method: 'POST',
      headers: {
        apikey: SUPABASE_KEY,
        Authorization: `Bearer ${SUPABASE_KEY}`,
        'Content-Type': 'application/json',
        Prefer: 'resolution=merge-duplicates,return=representation'
      },
      body: JSON.stringify(row)
    });
    const dbText = await dbRes.text();
    let dbData = [];
    try { dbData = dbText ? JSON.parse(dbText) : []; } catch {}
    if (!dbRes.ok) return json(500, { error: 'Supabase upsert failed', detail: dbData.message || dbData.hint || dbText });
    const dbUser = Array.isArray(dbData) && dbData[0] ? dbData[0] : row;

    const tokenBytes = crypto.getRandomValues(new Uint8Array(32));
    const sessionToken = Array.from(tokenBytes, b => b.toString(16).padStart(2, '0')).join('');
    return json(200, {
      token: sessionToken,
      user: {
        id, username, email: du.email || '', avatar: hash, avatarUrl,
        balance: Number(dbUser.balance || 1000), vipLevel: 0, vipName: 'Member', vipProgress: 0
      }
    });
  } catch (err) {
    console.error('Discord auth failed:', err);
    return json(500, { error: 'Authentication server error', detail: err?.message || String(err) });
  }
}
