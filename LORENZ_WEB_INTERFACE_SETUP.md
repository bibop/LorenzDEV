# 🌐 LORENZ Web Management Interface - Complete Setup

**Data**: 10 Gennaio 2026
**Status**: 🚧 Pronto per deployment

---

## 📋 Panoramica

Sistema completo di gestione web per LORENZ composto da:

1. **Flask API Server** - Espone dati LORENZ via REST API
2. **Next.js Dashboard** - Interfaccia web per monitoring e gestione
3. **Real-time Updates** - Dati aggiornati in tempo reale

---

## 🏗️ Architettura

```
┌─────────────────┐
│   Next.js App   │  (Port 3000)
│   bibop.com     │
└────────┬────────┘
         │ HTTP
         ▼
┌─────────────────┐
│   Flask API     │  (Port 5001)
│   80.240.31.197 │
└────────┬────────┘
         │ SQLite
         ▼
┌─────────────────┐
│  lorenz_memory  │
│      .db        │
└─────────────────┘
```

---

## 📦 File Creati

### Backend (API Server)

1. **`lorenz-api.py`** - Flask REST API server
   - Endpoints per status, stats, conversations, analytics
   - Accesso diretto al database SQLite
   - CORS enabled per Next.js

2. **`lorenz-api.service`** - Systemd service
   - Auto-start al boot
   - Log management
   - Security hardening

3. **`lorenz-api-requirements.txt`** - Python dependencies
   - Flask 3.0.0
   - flask-cors 4.0.0
   - gunicorn 21.2.0

---

## 🚀 STEP 1: Deploy API Server

### A. Carica Files sul Server

```bash
# Dal tuo PC locale
scp lorenz-api.py linuxuser@80.240.31.197:/opt/lorenz-bot/
scp lorenz-api.service linuxuser@80.240.31.197:/tmp/
scp lorenz-api-requirements.txt linuxuser@80.240.31.197:/opt/lorenz-bot/
```

### B. Installa Dependencies

```bash
# SSH nel server
ssh linuxuser@80.240.31.197

# Installa Flask nel venv
cd /opt/lorenz-bot
./venv/bin/pip install -r lorenz-api-requirements.txt

# Verifica installazione
./venv/bin/python3 -c "import flask; print(flask.__version__)"
```

### C. Configura Systemd Service

```bash
# Copia service file
sudo cp /tmp/lorenz-api.service /etc/systemd/system/

# Ricarica systemd
sudo systemctl daemon-reload

# Abilita e avvia il servizio
sudo systemctl enable lorenz-api
sudo systemctl start lorenz-api

# Verifica status
sudo systemctl status lorenz-api
```

### D. Test API Endpoint

```bash
# Local test
curl http://localhost:5001/api/health

# Expected response:
# {"status":"healthy","service":"lorenz-api","timestamp":"..."}

# Test status endpoint
curl http://localhost:5001/api/status
```

### E. Configura Firewall (se necessario)

```bash
# Apri porta 5001 solo per connessioni locali
sudo ufw allow from 127.0.0.1 to any port 5001
```

---

## 🌐 STEP 2: Deploy Next.js Dashboard

### Opzione A: Next.js API Routes (Recommended)

Create API routes in your Next.js app to proxy requests to the Flask server.

#### 1. Create API Route Handler

**File**: `src/app/api/lorenz/[...endpoint]/route.ts`

```typescript
import { NextRequest, NextResponse } from 'next/server';

const LORENZ_API_URL = process.env.LORENZ_API_URL || 'http://80.240.31.197:5001';

export async function GET(
  request: NextRequest,
  { params }: { params: { endpoint: string[] } }
) {
  try {
    const endpoint = params.endpoint.join('/');
    const searchParams = request.nextUrl.searchParams;

    const url = `${LORENZ_API_URL}/api/${endpoint}?${searchParams}`;

    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
      },
      // Disable caching for real-time data
      cache: 'no-store',
    });

    if (!response.ok) {
      return NextResponse.json(
        { error: 'API request failed' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);

  } catch (error) {
    console.error('LORENZ API Error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
```

#### 2. Add Environment Variable

**File**: `.env.local`

```bash
LORENZ_API_URL=http://80.240.31.197:5001
```

#### 3. Create Dashboard Page

**File**: `src/app/[locale]/lorenz/page.tsx`

```typescript
import { Metadata } from 'next';
import LorenzDashboard from '@/components/LorenzDashboard';

export const metadata: Metadata = {
  title: 'LORENZ Dashboard',
  description: 'Monitor and manage LORENZ AI bot',
};

export default function LorenzPage() {
  return <LorenzDashboard />;
}
```

#### 4. Create Dashboard Component

**File**: `src/components/LorenzDashboard.tsx`

```typescript
'use client';

import { useState, useEffect } from 'react';

interface LorenzStatus {
  status: string;
  total_conversations: number;
  recent_activity_24h: number;
  last_interaction: string;
}

interface LorenzStats {
  command_stats: Record<string, number>;
  activity_by_day: Array<{ date: string; count: number }>;
}

export default function LorenzDashboard() {
  const [status, setStatus] = useState<LorenzStatus | null>(null);
  const [stats, setStats] = useState<LorenzStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  async function fetchData() {
    try {
      const [statusRes, statsRes] = await Promise.all([
        fetch('/api/lorenz/status'),
        fetch('/api/lorenz/stats?days=7'),
      ]);

      if (statusRes.ok && statsRes.ok) {
        setStatus(await statusRes.json());
        setStats(await statsRes.json());
      }
    } catch (error) {
      console.error('Error fetching LORENZ data:', error);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-4">Loading LORENZ Dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-4xl font-bold mb-8">LORENZ Dashboard</h1>

      {/* Status Card */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Status</h3>
          <p className={`text-2xl font-bold mt-2 ${
            status?.status === 'online' ? 'text-green-600' : 'text-red-600'
          }`}>
            {status?.status === 'online' ? '🟢 Online' : '🔴 Offline'}
          </p>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Total Conversations</h3>
          <p className="text-2xl font-bold mt-2">{status?.total_conversations || 0}</p>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Activity (24h)</h3>
          <p className="text-2xl font-bold mt-2">{status?.recent_activity_24h || 0}</p>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Last Interaction</h3>
          <p className="text-sm mt-2">
            {status?.last_interaction ?
              new Date(status.last_interaction).toLocaleString() :
              'N/A'
            }
          </p>
        </div>
      </div>

      {/* Command Stats */}
      <div className="bg-white p-6 rounded-lg shadow mb-8">
        <h2 className="text-2xl font-bold mb-4">Command Usage (7 days)</h2>
        <div className="space-y-2">
          {stats && Object.entries(stats.command_stats).map(([cmd, count]) => (
            <div key={cmd} className="flex items-center">
              <span className="w-32 font-medium">{cmd}</span>
              <div className="flex-1 bg-gray-200 rounded-full h-4 mr-4">
                <div
                  className="bg-blue-600 h-4 rounded-full"
                  style={{
                    width: `${(count / Math.max(...Object.values(stats.command_stats))) * 100}%`
                  }}
                ></div>
              </div>
              <span className="w-16 text-right">{count}x</span>
            </div>
          ))}
        </div>
      </div>

      {/* Activity Chart */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-2xl font-bold mb-4">Activity by Day</h2>
        <div className="flex items-end justify-between h-48 gap-2">
          {stats?.activity_by_day.map((day) => (
            <div key={day.date} className="flex-1 flex flex-col items-center">
              <div className="w-full bg-blue-600 rounded-t"
                style={{
                  height: `${(day.count / Math.max(...stats.activity_by_day.map(d => d.count))) * 100}%`
                }}
              ></div>
              <span className="text-xs mt-2">{new Date(day.date).getDate()}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
```

---

## 📊 API Endpoints Reference

### GET `/api/status`
Returns general LORENZ status

**Response**:
```json
{
  "status": "online",
  "total_conversations": 42,
  "recent_activity_24h": 5,
  "last_interaction": "2026-01-10T12:30:00",
  "timestamp": "2026-01-10T14:00:00"
}
```

### GET `/api/stats?days=7`
Returns usage statistics

**Parameters**:
- `days` (optional): Number of days to analyze (default: 7)

**Response**:
```json
{
  "command_stats": {
    "ask": 15,
    "chat": 12,
    "email": 8
  },
  "activity_by_day": [
    {"date": "2026-01-10", "count": 10},
    {"date": "2026-01-09", "count": 8}
  ],
  "period_days": 7
}
```

### GET `/api/profile`
Returns user profile

**Response**:
```json
{
  "total_conversations": 42,
  "first_interaction": "2026-01-10T10:17:31",
  "last_interaction": "2026-01-10T14:00:00",
  "top_activities": [
    {"type": "ask", "count": 15}
  ],
  "preferences": {
    "preferred_email": "info@bibop.com"
  }
}
```

### GET `/api/conversations?limit=50&offset=0&type=ask`
Returns conversation history

**Parameters**:
- `limit` (optional): Number of conversations (default: 50)
- `offset` (optional): Pagination offset (default: 0)
- `type` (optional): Filter by message_type

**Response**:
```json
{
  "conversations": [
    {
      "id": 1,
      "timestamp": "2026-01-10T14:00:00",
      "user_message": "How is the server?",
      "bot_response": "Server is stable...",
      "message_type": "ask"
    }
  ],
  "total": 42,
  "limit": 50,
  "offset": 0
}
```

### GET `/api/analytics`
Returns detailed analytics

**Response**:
```json
{
  "conversations_by_type": {
    "ask": 15,
    "chat": 12
  },
  "conversations_by_hour": {
    "14": 5,
    "15": 3
  },
  "avg_response_length": 250
}
```

---

## 🎨 UI Enhancements (Optional)

### Add Chart Library

```bash
npm install recharts
```

### Enhanced Activity Chart with Recharts

```typescript
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

<ResponsiveContainer width="100%" height={300}>
  <BarChart data={stats?.activity_by_day}>
    <XAxis dataKey="date" />
    <YAxis />
    <Tooltip />
    <Bar dataKey="count" fill="#3b82f6" />
  </BarChart>
</ResponsiveContainer>
```

---

## 🔐 Security Considerations

1. **API Authentication** - Add API key auth:
```python
# In lorenz-api.py
from functools import wraps

API_KEY = os.getenv('LORENZ_API_KEY', 'change-me')

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get('X-API-Key')
        if key != API_KEY:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/api/status')
@require_api_key
def get_status():
    ...
```

2. **HTTPS Only** - Sempre usare HTTPS in produzione

3. **Rate Limiting** - Add Flask-Limiter:
```python
from flask_limiter import Limiter

limiter = Limiter(app, key_func=lambda: request.remote_addr)

@app.route('/api/stats')
@limiter.limit("10 per minute")
def get_stats():
    ...
```

---

## 📝 Monitoring & Logs

### View API Logs

```bash
# Real-time logs
sudo tail -f /var/log/lorenz-api.log

# Error logs
sudo tail -f /var/log/lorenz-api-error.log

# Service status
sudo systemctl status lorenz-api
```

### Restart API Server

```bash
sudo systemctl restart lorenz-api
```

---

## 🚀 Production Deployment

### Use Gunicorn (Production WSGI)

Update `lorenz-api.service`:

```ini
ExecStart=/opt/lorenz-bot/venv/bin/gunicorn \
    --bind 0.0.0.0:5001 \
    --workers 2 \
    --timeout 30 \
    --access-logfile /var/log/lorenz-api-access.log \
    --error-logfile /var/log/lorenz-api-error.log \
    lorenz-api:app
```

### Add Nginx Reverse Proxy (Optional)

```nginx
# /etc/nginx/sites-available/lorenz-api
server {
    listen 80;
    server_name api.bibop.com;

    location /api/ {
        proxy_pass http://localhost:5001/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## ✅ Testing Checklist

- [ ] Flask API server running (`systemctl status lorenz-api`)
- [ ] Health endpoint responds (`curl http://localhost:5001/api/health`)
- [ ] Status endpoint returns data (`curl http://localhost:5001/api/status`)
- [ ] Next.js API route proxies correctly
- [ ] Dashboard page loads
- [ ] Real-time data updates work
- [ ] Charts and visualizations display

---

## 🎯 Future Enhancements

1. **WebSocket Support** - Real-time updates via WebSockets
2. **Advanced Analytics** - More detailed charts and insights
3. **Configuration Panel** - Edit LORENZ settings from web
4. **Email Management** - View and manage emails from dashboard
5. **Command Execution** - Execute LORENZ commands from web
6. **Alert System** - Browser notifications for important events

---

**Creato da**: Claude Code
**Data**: 2026-01-10
**Version**: 1.0 - Complete Web Interface Setup
