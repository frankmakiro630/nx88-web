<?php
// Quick setup file - visit this once to initialize
echo "<h2>NX88 Casino Setup & Debug</h2>";

// Create data directory
$data_dir = __DIR__ . '/data';
if (!is_dir($data_dir)) {
    mkdir($data_dir, 0755, true);
    echo "✅ Created /data folder<br>";
} else {
    echo "✅ /data folder exists (writable: " . (is_writable($data_dir) ? 'YES' : 'NO') . ")<br>";
}

// Check if api.php exists
if (file_exists('api.php')) {
    echo "✅ api.php found<br>";
    
    // Read api.php and check configuration
    $api_content = file_get_contents('api.php');
    
    // Check Discord credentials
    preg_match("/define\('DISCORD_CLIENT_ID',\s*'([^']+)'\)/", $api_content, $client_id_match);
    preg_match("/define\('DISCORD_CLIENT_SECRET',\s*'([^']+)'\)/", $api_content, $secret_match);
    preg_match("/define\('DISCORD_REDIRECT_URI',\s*'([^']+)'\)/", $api_content, $redirect_match);
    
    echo "<h3>Discord Configuration Status:</h3>";
    echo "<ul>";
    echo "<li>CLIENT_ID: " . ($client_id_match[1] ?? 'NOT FOUND') . "</li>";
    echo "<li>CLIENT_SECRET: " . (isset($secret_match[1]) && $secret_match[1] !== 'YOUR_DISCORD_CLIENT_SECRET_HERE' ? 'CONFIGURED ✅' : 'NOT CONFIGURED ❌') . "</li>";
    echo "<li>REDIRECT_URI: " . ($redirect_match[1] ?? 'NOT FOUND') . "</li>";
    echo "</ul>";
    
    if (strpos($api_content, 'YOUR_DISCORD_CLIENT_SECRET_HERE') !== false) {
        echo "<h3 style='color:red'>⚠️ CRITICAL: Discord CLIENT_SECRET is NOT configured!</h3>";
        echo "<p>This is why authentication is failing.</p>";
        echo "<p><strong>How to fix:</strong></p>";
        echo "<ol>";
        echo "<li>Go to https://discord.com/developers/applications</li>";
        echo "<li>Select your app 'NX88 Casino'</li>";
        echo "<li>Go to OAuth2 tab → General</li>";
        echo "<li>Copy the <strong>CLIENT SECRET</strong></li>";
        echo "<li>Edit <code>api.php</code> line 20:</li>";
        echo "<pre>define('DISCORD_CLIENT_SECRET', 'PASTE_YOUR_SECRET_HERE');</pre>";
        echo "<li>Also verify REDIRECT_URI matches Discord settings</li>";
        echo "</ol>";
    }
} else {
    echo "❌ api.php not found!<br>";
}

// Check if .htaccess exists
if (file_exists('.htaccess')) {
    echo "✅ .htaccess configured<br>";
} else {
    echo "⚠️ .htaccess missing - API routing may not work<br>";
}

// Test API
echo "<h3>Test API Endpoints:</h3>";
echo "<pre>";
echo "GET  /api/health      - Check if API works\n";
echo "GET  /api/debug       - Show configuration\n";
echo "POST /api/auth/discord - Discord OAuth (this fails without CLIENT_SECRET)\n";
echo "</pre>";

echo "<h3 style='color:#d00'>Debugging Authentication Error:</h3>";
echo "<ol>";
echo "<li>First, verify Discord CLIENT_SECRET is set in api.php</li>";
echo "<li>Test this URL: <a href='/api/debug' target='_blank'>https://celebrated-fairy-a39883.netlify.app/api/debug</a></li>";
echo "<li>If 'discord_configured' shows false, the login will fail</li>";
echo "<li>Check browser console (F12) for detailed error message</li>";
echo "<li>The error will tell you exactly what went wrong</li>";
echo "</ol>";

echo "<h3>Common Issues:</h3>";
echo "<ul>";
echo "<li><strong>discord_configured: false</strong> → CLIENT_SECRET not set in api.php (line 20)</li>";
echo "<li><strong>data_dir: NOT writable</strong> → Check folder permissions (755)</li>";
echo "<li><strong>REDIRECT_URI mismatch</strong> → Must match Discord portal exactly</li>";
echo "<li><strong>404 on /api/auth/discord</strong> → .htaccess not working (ask host to enable mod_rewrite)</li>";
echo "</ul>";

echo "<hr>";
echo "<h3>✅ Setup Complete When:</h3>";
echo "<ol>";
echo "<li>Discord CLIENT_SECRET is configured</li>";
echo "<li>/api/debug shows 'discord_configured: true'</li>";
echo "<li>Discord login works without authentication error</li>";
echo "</ol>";

echo "<h3>⚠️ Security Note:</h3>";
echo "Delete setup.php after finishing setup for security.";
?>

