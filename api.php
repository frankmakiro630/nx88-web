<?php
// NX88 Casino API - PHP Backend
// Simple backend for Discord OAuth and game management

// Error handling - catch all errors and return as JSON
set_error_handler(function($errno, $errstr, $errfile, $errline) {
    http_response_code(500);
    echo json_encode([
        'error' => 'PHP Error: ' . $errstr,
        'file' => $errfile,
        'line' => $errline
    ]);
    exit;
});

// Set JSON header early
header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    echo json_encode(['status' => 'ok']);
    exit;
}

// Simple file-based storage (for testing)
$data_dir = __DIR__ . '/data';
if (!is_dir($data_dir)) {
    mkdir($data_dir, 0755, true);
}

// Constants
define('DISCORD_CLIENT_ID', '1501947066560020490');
define('DISCORD_CLIENT_SECRET', getenv('DISCORD_CLIENT_SECRET') ?: '_ug9k89AmA14dq63H_PuzPl0H5DKl3Qe');
define('DISCORD_REDIRECT_URI', 'https://nx88-web.frankcute2603.workers.dev/auth/discord/callback');
define('JWT_SECRET', getenv('JWT_SECRET') ?: 'CHANGE_THIS_TO_A_LONG_RANDOM_SECRET');

// Simple JWT handling
function createToken($user_id) {
    $header = base64_encode(json_encode(['typ' => 'JWT', 'alg' => 'HS256']));
    $payload = base64_encode(json_encode([
        'sub' => $user_id,
        'iat' => time(),
        'exp' => time() + (7 * 24 * 60 * 60)
    ]));
    $signature = base64_encode(hash_hmac('sha256', "$header.$payload", JWT_SECRET, true));
    return "$header.$payload.$signature";
}

function verifyToken($token) {
    if (strpos($token, 'Bearer ') === 0) {
        $token = substr($token, 7);
    }
    
    $parts = explode('.', $token);
    if (count($parts) !== 3) return null;
    
    list($header, $payload, $sig) = $parts;
    $check_sig = base64_encode(hash_hmac('sha256', "$header.$payload", JWT_SECRET, true));
    
    if (!hash_equals($sig, $check_sig)) return null;
    
    $data = json_decode(base64_decode($payload), true);
    if ($data['exp'] < time()) return null;
    
    return $data['sub'];
}

// Load user data
function getUser($user_id) {
    global $data_dir;
    $file = "$data_dir/user_$user_id.json";
    if (file_exists($file)) {
        return json_decode(file_get_contents($file), true);
    }
    return null;
}

function saveUser($user_id, $data) {
    global $data_dir;
    $file = "$data_dir/user_$user_id.json";
    file_put_contents($file, json_encode($data, JSON_PRETTY_PRINT));
}

// ════════════════════════════════════════════════════════════════════════════
// ROUTES
// ════════════════════════════════════════════════════════════════════════════

$request_uri = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
$request_method = $_SERVER['REQUEST_METHOD'];

// Parse route
if (preg_match('/^\/api\/debug$/', $request_uri)) {
    // Debug endpoint - shows configuration (remove in production!)
    echo json_encode([
        'php_version' => phpversion(),
        'discord_client_id' => DISCORD_CLIENT_ID,
        'discord_configured' => (DISCORD_CLIENT_SECRET !== 'YOUR_DISCORD_CLIENT_SECRET_HERE'),
        'redirect_uri' => DISCORD_REDIRECT_URI,
        'data_dir_writable' => is_writable($data_dir),
        'note' => 'If discord_configured is false, login will fail!'
    ]);
    exit;
}
elseif (preg_match('/^\/api\/health$/', $request_uri)) {
    http_response_code(200);
    echo json_encode(['status' => 'healthy', 'timestamp' => date('c')]);
    exit;
}
elseif (preg_match('/^\/api\/auth\/discord$/', $request_uri)) {
    if ($request_method === 'POST') {
        handle_discord_auth();
    }
}
elseif (preg_match('/^\/api\/auth\/create-user$/', $request_uri)) {
    if ($request_method === 'POST') {
        handle_create_user();
    }
}
elseif (preg_match('/^\/api\/user\/profile$/', $request_uri)) {
    if ($request_method === 'GET') {
        handle_get_profile();
    }
}
elseif (preg_match('/^\/api\/baccarat\/result$/', $request_uri)) {
    if ($request_method === 'POST') {
        handle_baccarat_result();
    }
}
elseif (preg_match('/^\/api\/baccarat\/bet$/', $request_uri)) {
    if ($request_method === 'POST') {
        handle_baccarat_bet();
    }
}
elseif (preg_match('/^\/api\/baccarat\/reset$/', $request_uri)) {
    if ($request_method === 'POST') {
        handle_baccarat_reset();
    }
}
elseif (preg_match('/^\/api\/baccarat\/save$/', $request_uri)) {
    if ($request_method === 'POST') {
        handle_baccarat_save();
    }
}
elseif (preg_match('/^\/api\/baccarat\/history$/', $request_uri)) {
    if ($request_method === 'GET') {
        handle_baccarat_history();
    }
}
elseif (preg_match('/^\/api\/leaderboard$/', $request_uri)) {
    if ($request_method === 'GET') {
        handle_leaderboard();
    }
}
elseif (preg_match('/^\/api\/slot\/spin$/', $request_uri)) {
    if ($request_method === 'POST') {
        handle_slot_spin();
    }
}
elseif (preg_match('/^(?:\/auth\/me|\/api\/profile)$/', $request_uri)) {
    if ($request_method === 'GET') {
        handle_get_profile();
    }
}
elseif (preg_match('/^\/api\/stats$/', $request_uri)) {
    if ($request_method === 'GET') {
        handle_stats();
    }
}
elseif (preg_match('/^\/api\/hoantra$/', $request_uri)) {
    if ($request_method === 'GET') {
        handle_hoantra_info();
    }
}
elseif (preg_match('/^\/api\/hoantra\/claim$/', $request_uri)) {
    if ($request_method === 'POST') {
        handle_claim_hoantra();
    }
}
elseif (preg_match('/^\/api\/user\/claim-hoantra$/', $request_uri)) {
    if ($request_method === 'POST') {
        handle_claim_hoantra();
    }
}
else {
    http_response_code(404);
    echo json_encode(['error' => 'Not found']);
}

// ════════════════════════════════════════════════════════════════════════════
// HANDLERS
// ════════════════════════════════════════════════════════════════════════════

function discord_api_request($url, $method = 'GET', $headers = [], $body = null) {
    if (!function_exists('curl_init')) {
        return ['ok' => false, 'status' => 500, 'error' => 'PHP cURL is not enabled on this hosting'];
    }

    $ch = curl_init($url);
    $options = [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_CONNECTTIMEOUT => 10,
        CURLOPT_TIMEOUT => 20,
        CURLOPT_FOLLOWLOCATION => false,
        CURLOPT_USERAGENT => 'NX88-Auth/1.0',
        CURLOPT_HTTPHEADER => $headers,
        CURLOPT_SSL_VERIFYPEER => true,
        CURLOPT_SSL_VERIFYHOST => 2
    ];

    // Some shared hosts have broken IPv6 DNS/routing. Prefer IPv4 when available.
    if (defined('CURLOPT_IPRESOLVE') && defined('CURL_IPRESOLVE_V4')) {
        $options[CURLOPT_IPRESOLVE] = CURL_IPRESOLVE_V4;
    }

    if ($method === 'POST') {
        $options[CURLOPT_POST] = true;
        $options[CURLOPT_POSTFIELDS] = $body;
    }

    curl_setopt_array($ch, $options);
    $response = curl_exec($ch);
    $errno = curl_errno($ch);
    $error = curl_error($ch);
    $status = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($errno !== 0 || $response === false) {
        return [
            'ok' => false,
            'status' => 502,
            'error' => 'Discord API connection failed: ' . ($error ?: 'cURL error ' . $errno)
        ];
    }

    $data = json_decode($response, true);
    if (!is_array($data)) {
        return [
            'ok' => false,
            'status' => 502,
            'error' => 'Invalid response from Discord API (HTTP ' . $status . ')'
        ];
    }

    return [
        'ok' => $status >= 200 && $status < 300,
        'status' => $status,
        'data' => $data
    ];
}

function handle_discord_auth() {
    $input = json_decode(file_get_contents('php://input'), true);
    if (!is_array($input)) {
        http_response_code(400);
        echo json_encode(['error' => 'Invalid JSON request']);
        return;
    }

    $code = trim((string)($input['code'] ?? ''));
    // Never trust an arbitrary redirect URI supplied by the browser.
    $redirect_uri = DISCORD_REDIRECT_URI;

    if ($code === '') {
        http_response_code(400);
        echo json_encode(['error' => 'Missing authorization code']);
        return;
    }

    if (DISCORD_CLIENT_SECRET === 'YOUR_DISCORD_CLIENT_SECRET_HERE') {
        http_response_code(500);
        echo json_encode(['error' => 'Server not configured: set DISCORD_CLIENT_SECRET on the server']);
        return;
    }

    $tokenResult = discord_api_request(
        'https://discord.com/api/v10/oauth2/token',
        'POST',
        [
            'Content-Type: application/x-www-form-urlencoded',
            'Accept: application/json'
        ],
        http_build_query([
            'client_id' => DISCORD_CLIENT_ID,
            'client_secret' => DISCORD_CLIENT_SECRET,
            'code' => $code,
            'grant_type' => 'authorization_code',
            'redirect_uri' => $redirect_uri
        ])
    );

    if (!$tokenResult['ok']) {
        http_response_code($tokenResult['status'] ?? 502);
        $detail = $tokenResult['data']['error_description'] ?? $tokenResult['data']['error'] ?? null;
        echo json_encode([
            'error' => $detail ?: ($tokenResult['error'] ?? 'Discord authentication failed')
        ]);
        return;
    }

    $token_data = $tokenResult['data'];
    $access_token = $token_data['access_token'] ?? '';
    if ($access_token === '') {
        http_response_code(502);
        echo json_encode(['error' => 'Discord did not return an access token']);
        return;
    }

    $userResult = discord_api_request(
        'https://discord.com/api/v10/users/@me',
        'GET',
        [
            'Authorization: Bearer ' . $access_token,
            'Accept: application/json'
        ]
    );

    if (!$userResult['ok']) {
        http_response_code($userResult['status'] ?? 502);
        $detail = $userResult['data']['message'] ?? $userResult['error'] ?? 'Failed to fetch Discord user';
        echo json_encode(['error' => $detail]);
        return;
    }

    $discord_user = $userResult['data'];
    if (empty($discord_user['id'])) {
        http_response_code(502);
        echo json_encode(['error' => 'Discord user response is missing an id']);
        return;
    }

    $user_id = (string)$discord_user['id'];
    $user = getUser($user_id);

    if (!$user) {
        $user = [
            'id' => $user_id,
            'username' => $discord_user['global_name'] ?? $discord_user['username'] ?? ('User' . substr($user_id, -4)),
            'email' => $discord_user['email'] ?? '',
            'avatar' => $discord_user['avatar'] ?? '',
            'balance' => 0,
            'vip_level' => 0,
            'xp' => 0,
            'total_bet' => 0,
            'total_win' => 0,
            'created_at' => date('Y-m-d H:i:s')
        ];
    } else {
        $user['username'] = $discord_user['global_name'] ?? $discord_user['username'] ?? $user['username'];
        $user['avatar'] = $discord_user['avatar'] ?? $user['avatar'];
        if (isset($discord_user['email'])) $user['email'] = $discord_user['email'];
    }

    $user['last_login'] = date('Y-m-d H:i:s');
    saveUser($user_id, $user);

    $jwt = createToken($user_id);

    http_response_code(200);
    echo json_encode([
        'token' => $jwt,
        'token_type' => 'Bearer',
        'user' => [
            'id' => $user['id'],
            'username' => $user['username'],
            'avatar' => $user['avatar'],
            'balance' => $user['balance'],
            'vip_level' => $user['vip_level'],
            'xp' => $user['xp']
        ]
    ]);
}

function handle_create_user() {
    // Create or update user from Discord info (used when frontend calls Discord directly)
    $input = json_decode(file_get_contents('php://input'), true);
    $discord_id = $input['discord_id'] ?? null;
    
    if (!$discord_id) {
        http_response_code(400);
        echo json_encode(['error' => 'Missing discord_id']);
        return;
    }
    
    $user_id = $discord_id;
    $user = getUser($user_id);
    
    if (!$user) {
        // Create new user
        $user = [
            'id' => $user_id,
            'username' => $input['username'] ?? 'User' . substr($user_id, -4),
            'email' => $input['email'] ?? '',
            'avatar' => $input['avatar'] ?? '',
            'balance' => 0,
            'vip_level' => 0,
            'xp' => 0,
            'total_bet' => 0,
            'total_win' => 0,
            'created_at' => date('Y-m-d H:i:s')
        ];
    } else {
        // Update existing user
        $user['username'] = $input['username'] ?? $user['username'];
        $user['email'] = $input['email'] ?? $user['email'];
        $user['avatar'] = $input['avatar'] ?? $user['avatar'];
    }
    
    $user['last_login'] = date('Y-m-d H:i:s');
    saveUser($user_id, $user);
    
    // Create JWT token
    $jwt = createToken($user_id);
    
    http_response_code(200);
    echo json_encode([
        'token' => $jwt,
        'token_type' => 'Bearer',
        'user' => [
            'id' => $user['id'],
            'username' => $user['username'],
            'avatar' => $user['avatar'],
            'balance' => $user['balance'],
            'vip_level' => $user['vip_level'],
            'xp' => $user['xp']
        ]
    ]);
}

function handle_get_profile() {
    $auth = $_SERVER['HTTP_AUTHORIZATION'] ?? '';
    $user_id = verifyToken($auth);
    
    if (!$user_id) {
        http_response_code(401);
        echo json_encode(['error' => 'Unauthorized']);
        return;
    }
    
    $user = getUser($user_id);
    if (!$user) {
        http_response_code(404);
        echo json_encode(['error' => 'User not found']);
        return;
    }
    
    http_response_code(200);
    echo json_encode($user);
}

function handle_baccarat_result() {
    $auth = $_SERVER['HTTP_AUTHORIZATION'] ?? '';
    $user_id = verifyToken($auth);
    
    if (!$user_id) {
        http_response_code(401);
        echo json_encode(['error' => 'Unauthorized']);
        return;
    }
    
    $input = json_decode(file_get_contents('php://input'), true);
    $user = getUser($user_id);
    
    if (!$user) {
        http_response_code(404);
        echo json_encode(['error' => 'User not found']);
        return;
    }
    
    $bet = $input['bet'] ?? 0;
    $payout = $input['payout'] ?? 0;
    $profit = $payout - $bet;
    
    $user['balance'] += $profit;
    $user['total_bet'] += $bet;
    $user['total_win'] += $payout;
    $user['xp'] += abs($bet);
    
    // Update VIP level based on total_win
    if ($user['total_win'] >= 100000) $user['vip_level'] = 5;
    elseif ($user['total_win'] >= 50000) $user['vip_level'] = 4;
    elseif ($user['total_win'] >= 10000) $user['vip_level'] = 3;
    elseif ($user['total_win'] >= 5000) $user['vip_level'] = 2;
    elseif ($user['total_win'] >= 1000) $user['vip_level'] = 1;
    
    saveUser($user_id, $user);
    
    http_response_code(200);
    echo json_encode([
        'success' => true,
        'new_balance' => $user['balance'],
        'profit' => $profit,
        'message' => $profit > 0 ? 'Win!' : 'Loss!'
    ]);
}

function handle_baccarat_history() {
    $auth = $_SERVER['HTTP_AUTHORIZATION'] ?? '';
    $user_id = verifyToken($auth);
    
    if (!$user_id) {
        http_response_code(401);
        echo json_encode(['error' => 'Unauthorized']);
        return;
    }
    
    global $data_dir;
    $history_file = "$data_dir/history_$user_id.json";
    $history = file_exists($history_file) ? json_decode(file_get_contents($history_file), true) : [];
    
    http_response_code(200);
    echo json_encode(['history' => $history]);
}

function handle_leaderboard() {
    global $data_dir;
    $auth = $_SERVER['HTTP_AUTHORIZATION'] ?? '';
    $user_id = verifyToken($auth);
    
    $mode = $_GET['mode'] ?? 'balance';
    
    // Scan all users
    $leaderboard = [];
    foreach (glob("$data_dir/user_*.json") as $file) {
        $user = json_decode(file_get_contents($file), true);
        $leaderboard[] = [
            'id' => $user['id'],
            'username' => $user['username'],
            'vip_level' => $user['vip_level'],
            'balance' => $user['balance'],
            'total_win' => $user['total_win']
        ];
    }
    
    // Sort by mode
    if ($mode === 'vip') {
        usort($leaderboard, fn($a, $b) => $b['vip_level'] <=> $a['vip_level']);
    } else {
        usort($leaderboard, fn($a, $b) => $b['balance'] <=> $a['balance']);
    }
    
    http_response_code(200);
    echo json_encode([
        'entries' => array_slice($leaderboard, 0, 100),
        'total_players' => count($leaderboard),
        'current_user_rank' => $user_id ? array_search($user_id, array_column($leaderboard, 'id')) + 1 : null
    ]);
}

function handle_stats() {
    $auth = $_SERVER['HTTP_AUTHORIZATION'] ?? '';
    $user_id = verifyToken($auth);
    if (!$user_id) {
        http_response_code(401);
        echo json_encode(['error' => 'Unauthorized']);
        return;
    }

    $user = getUser($user_id);
    if (!$user) {
        http_response_code(404);
        echo json_encode(['error' => 'User not found']);
        return;
    }

    $total_bet = (float)($user['total_bet'] ?? 0);
    $total_win = (float)($user['total_win'] ?? 0);
    echo json_encode([
        'balance' => (float)($user['balance'] ?? 0),
        'total_bet' => $total_bet,
        'total_win' => $total_win,
        'net' => $total_win - $total_bet,
        'vip_level' => (int)($user['vip_level'] ?? 0),
        'xp' => (int)($user['xp'] ?? 0)
    ]);
}

function handle_hoantra_info() {
    $auth = $_SERVER['HTTP_AUTHORIZATION'] ?? '';
    $user_id = verifyToken($auth);
    if (!$user_id) {
        http_response_code(401);
        echo json_encode(['error' => 'Unauthorized']);
        return;
    }

    $user = getUser($user_id);
    if (!$user) {
        http_response_code(404);
        echo json_encode(['error' => 'User not found']);
        return;
    }

    $losses = max(0, (float)($user['total_bet'] ?? 0) - (float)($user['total_win'] ?? 0));
    echo json_encode([
        'losses' => $losses,
        'refund_rate' => 0.02,
        'available_refund' => floor($losses * 0.02)
    ]);
}

function handle_claim_hoantra() {
    $auth = $_SERVER['HTTP_AUTHORIZATION'] ?? '';
    $user_id = verifyToken($auth);
    
    if (!$user_id) {
        http_response_code(401);
        echo json_encode(['error' => 'Unauthorized']);
        return;
    }
    
    $user = getUser($user_id);
    if (!$user) {
        http_response_code(404);
        echo json_encode(['error' => 'User not found']);
        return;
    }
    
    // Calculate refund (2% of losses)
    $losses = $user['total_bet'] - $user['total_win'];
    $refund = floor($losses * 0.02);
    
    $user['balance'] += $refund;
    $user['total_win'] += $refund;
    saveUser($user_id, $user);
    
    http_response_code(200);
    echo json_encode([
        'success' => true,
        'amount' => $refund,
        'new_balance' => $user['balance'],
        'message' => "Claimed $refund đồng!"
    ]);
}

function handle_baccarat_bet() {
    $auth = $_SERVER['HTTP_AUTHORIZATION'] ?? '';
    $user_id = verifyToken($auth);
    
    if (!$user_id) {
        http_response_code(401);
        echo json_encode(['error' => 'Unauthorized']);
        return;
    }
    
    $input = json_decode(file_get_contents('php://input'), true);
    $user = getUser($user_id);
    
    if (!$user) {
        http_response_code(404);
        echo json_encode(['error' => 'User not found']);
        return;
    }
    
    $bet = $input['bet'] ?? 0;
    
    // Check balance
    if ($user['balance'] < $bet) {
        http_response_code(400);
        echo json_encode(['error' => 'Insufficient balance']);
        return;
    }
    
    http_response_code(200);
    echo json_encode([
        'success' => true,
        'balance' => $user['balance'],
        'bet_accepted' => $bet
    ]);
}

function handle_baccarat_reset() {
    $auth = $_SERVER['HTTP_AUTHORIZATION'] ?? '';
    $user_id = verifyToken($auth);
    
    if (!$user_id) {
        http_response_code(401);
        echo json_encode(['error' => 'Unauthorized']);
        return;
    }
    
    http_response_code(200);
    echo json_encode(['success' => true, 'message' => 'Game reset']);
}

function handle_baccarat_save() {
    $auth = $_SERVER['HTTP_AUTHORIZATION'] ?? '';
    $user_id = verifyToken($auth);
    
    if (!$user_id) {
        http_response_code(401);
        echo json_encode(['error' => 'Unauthorized']);
        return;
    }
    
    $input = json_decode(file_get_contents('php://input'), true);
    global $data_dir;
    
    // Save game history
    $history_file = "$data_dir/history_$user_id.json";
    $history = file_exists($history_file) ? json_decode(file_get_contents($history_file), true) : [];
    
    $history[] = [
        'timestamp' => date('c'),
        'type' => 'baccarat',
        'bet' => $input['bet'] ?? 0,
        'payout' => $input['payout'] ?? 0,
        'result' => $input['result'] ?? null
    ];
    
    file_put_contents($history_file, json_encode($history, JSON_PRETTY_PRINT));
    
    http_response_code(200);
    echo json_encode(['success' => true, 'message' => 'Game saved']);
}

function handle_slot_spin() {
    $auth = $_SERVER['HTTP_AUTHORIZATION'] ?? '';
    $user_id = verifyToken($auth);
    
    if (!$user_id) {
        http_response_code(401);
        echo json_encode(['error' => 'Unauthorized']);
        return;
    }
    
    $input = json_decode(file_get_contents('php://input'), true);
    $user = getUser($user_id);
    
    if (!$user) {
        http_response_code(404);
        echo json_encode(['error' => 'User not found']);
        return;
    }
    
    $bet = $input['bet'] ?? 0;
    
    // Check balance
    if ($user['balance'] < $bet) {
        http_response_code(400);
        echo json_encode(['error' => 'Insufficient balance']);
        return;
    }
    
    // Simple random result
    $spin_results = [
        ['id' => 1, 'name' => 'Cherry'],
        ['id' => 2, 'name' => 'Bell'],
        ['id' => 3, 'name' => 'Seven'],
        ['id' => 4, 'name' => 'Gold']
    ];
    
    $reel1 = $spin_results[array_rand($spin_results)];
    $reel2 = $spin_results[array_rand($spin_results)];
    $reel3 = $spin_results[array_rand($spin_results)];
    
    // Calculate payout (simplistic)
    $payout = 0;
    if ($reel1['id'] === $reel2['id'] && $reel2['id'] === $reel3['id']) {
        $payout = $bet * 10; // 3 match = 10x
    } elseif ($reel1['id'] === $reel2['id'] || $reel2['id'] === $reel3['id']) {
        $payout = $bet * 3; // 2 match = 3x
    }
    
    $profit = $payout - $bet;
    $user['balance'] += $profit;
    $user['total_bet'] += $bet;
    $user['total_win'] += $payout;
    $user['xp'] += $bet;
    
    saveUser($user_id, $user);
    
    http_response_code(200);
    echo json_encode([
        'success' => true,
        'reels' => [$reel1, $reel2, $reel3],
        'bet' => $bet,
        'payout' => $payout,
        'profit' => $profit,
        'new_balance' => $user['balance'],
        'message' => $payout > 0 ? 'Win!' : 'Loss!'
    ]);
}

?>
