# NX88 Casino - PHP Backend Setup Guide

## Files Added

- **api.php** - Main API backend (replace Python FastAPI)
- **.htaccess** - URL routing for API endpoints
- **setup.php** - Quick setup verification

## Setup Steps

### 1. Get Discord Client Secret
- Go to https://discord.com/developers/applications
- Select your app "NX88 Casino"
- Copy **CLIENT SECRET** (⚠️ Keep it private!)

### 2. Configure api.php
Edit `api.php` and update these lines:

```php
// Line 19-23
define('DISCORD_CLIENT_ID', '1501947066560020490');          // Already set
define('DISCORD_CLIENT_SECRET', 'YOUR_SECRET_HERE');          // ⬅️ PASTE YOUR SECRET
define('DISCORD_REDIRECT_URI', 'https://celebrated-fairy-a39883.netlify.app/auth/discord/callback');
define('JWT_SECRET', 'your-secret-key-change-this');         // ⬅️ Change to random string
```

### 3. Upload to InfinityFree

1. Download these files:
   - `index.html`
   - `api.php` (updated)
   - `.htaccess` (new)
   - Any CSS/JS files needed

2. Upload via **FTP** or **File Manager**:
   ```
   /public_html/
   ├── index.html
   ├── api.php
   ├── .htaccess
   ├── style.css (if exists)
   └── data/          (will be auto-created)
   ```

3. Create `/data/` folder (if not auto-created):
   - Right-click → New Folder → Name: `data`
   - Set permissions: 755

### 4. Verify Setup

Visit these URLs:
- `https://celebrated-fairy-a39883.netlify.app/setup.php` - Should show setup guide ✅
- `https://celebrated-fairy-a39883.netlify.app/api/health` - Should return `{"status":"healthy"}`

### 5. Test Discord Login

1. Go to https://celebrated-fairy-a39883.netlify.app
2. Click "Login with Discord"
3. Approve permissions
4. Should redirect back and show your profile ✅

## Discord Configuration

Make sure in **Discord Developer Portal**:

**OAuth2** → **Redirects**
```
https://celebrated-fairy-a39883.netlify.app/auth/discord/callback
```

(No other URLs needed)

## API Endpoints

| Endpoint | Method | Requires Auth | Description |
|----------|--------|---------------|-------------|
| `/api/health` | GET | No | Health check |
| `/api/auth/discord` | POST | No | Discord OAuth login |
| `/api/user/profile` | GET | Yes | Get user profile |
| `/api/baccarat/result` | POST | Yes | Log game result |
| `/api/baccarat/history` | GET | Yes | Get game history |
| `/api/leaderboard` | GET | No | Get rankings |
| `/api/user/claim-hoantra` | POST | Yes | Claim refund bonus |

## Troubleshooting

### 404 Error on API calls
- Make sure `.htaccess` is uploaded
- Check server supports mod_rewrite
- Ask InfinityFree support to enable mod_rewrite

### Discord login fails
- Verify CLIENT_SECRET is correct and private
- Check REDIRECT_URI matches exactly in Discord portal
- Test `https://celebrated-fairy-a39883.netlify.app/api/health` first

### Data not saving
- Check `/data/` folder exists and is writable
- FTP into it, create a test file to verify

## Security Notes

⚠️ **IMPORTANT:**
1. **Delete setup.php** after verification
2. Never commit api.php with real Discord secret to git
3. Change JWT_SECRET to random value
4. Keep DISCORD_CLIENT_SECRET private

## Data Storage

User data is stored in `/data/user_[ID].json`:
```
/data/
├── user_1234567890.json
├── user_0987654321.json
└── history_1234567890.json
```

## Need Help?

Check these:
1. Browser console (F12) for frontend errors
2. InfinityFree file manager for `/data/` folder
3. Verify files uploaded successfully
4. Test endpoints with curl:
   ```bash
   curl https://celebrated-fairy-a39883.netlify.app/api/health
   ```
