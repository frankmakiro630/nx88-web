# NX88 - Cloudflare Pages

## Deploy
Upload this project to GitHub, then in Cloudflare Dashboard:
1. Workers & Pages -> Create application -> Pages -> Connect to Git.
2. Select this repository.
3. Build command: leave empty.
4. Build output directory: `.`
5. Deploy.

## Environment variables / secrets
In Pages -> Settings -> Variables and Secrets add:
- `DISCORD_CLIENT_SECRET` = Discord OAuth Client Secret (SECRET)
- `DISCORD_CLIENT_ID` = 1501947066560020490
- `SUPABASE_URL` = https://wueazxozrcxjnhivqqwu.supabase.co
- `SUPABASE_PUBLISHABLE_KEY` = your Supabase publishable key

## Discord redirect URI
After Pages gives you a domain, add exactly:
`https://YOUR-DOMAIN/auth/discord/callback`
in Discord Developer Portal -> OAuth2 -> Redirects.

If you later attach a custom domain, add that exact callback URL too.
