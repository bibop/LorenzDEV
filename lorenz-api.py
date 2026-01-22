#!/usr/bin/env python3
"""
🌐 LORENZ API Server
====================

REST API per accedere ai dati di LORENZ dal web dashboard

Endpoints:
- GET  /api/status      - Status generale LORENZ
- GET  /api/stats       - Statistiche utilizzo
- GET  /api/profile     - Profilo utente
- GET  /api/conversations - Storia conversazioni
- GET  /api/analytics   - Analytics dettagliati
- POST /api/command     - Esegui comando server

Autore: Claude Code
Data: 2026-01-10
"""

import os
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List
from flask import Flask, jsonify, request
from flask_cors import CORS

# Configurazione
MEMORY_DB_PATH = '/opt/lorenz-bot/lorenz_memory.db'
API_PORT = 5001
API_HOST = '0.0.0.0'

# Crea Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for Next.js

# ============================================================================
# DATABASE HELPERS
# ============================================================================

def get_db_connection():
    """Connessione al database SQLite"""
    try:
        conn = sqlite3.connect(MEMORY_DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/status', methods=['GET'])
def get_status():
    """Status generale LORENZ"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500

        cursor = conn.cursor()

        # Total conversations
        cursor.execute('SELECT COUNT(*) as total FROM conversations')
        total_conversations = cursor.fetchone()['total']

        # Recent activity (last 24h)
        yesterday = (datetime.now() - timedelta(days=1)).isoformat()
        cursor.execute(
            'SELECT COUNT(*) as recent FROM conversations WHERE timestamp >= ?',
            (yesterday,)
        )
        recent_activity = cursor.fetchone()['recent']

        # Last interaction
        cursor.execute('SELECT MAX(timestamp) as last FROM conversations')
        last_interaction = cursor.fetchone()['last']

        # Bot status (check if service is running)
        import subprocess
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', 'lorenz-bot'],
                capture_output=True,
                text=True
            )
            bot_running = result.stdout.strip() == 'active'
        except:
            bot_running = False

        conn.close()

        return jsonify({
            'status': 'online' if bot_running else 'offline',
            'total_conversations': total_conversations,
            'recent_activity_24h': recent_activity,
            'last_interaction': last_interaction,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Statistiche utilizzo"""
    try:
        days = request.args.get('days', 7, type=int)

        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500

        cursor = conn.cursor()

        # Usage stats per command type
        cutoff_date = (datetime.now() - timedelta(days=days)).date().isoformat()
        cursor.execute('''
            SELECT command_type, SUM(count) as total
            FROM usage_stats
            WHERE stat_date >= ?
            GROUP BY command_type
            ORDER BY total DESC
        ''', (cutoff_date,))

        command_stats = {}
        for row in cursor.fetchall():
            command_stats[row['command_type']] = row['total']

        # Activity by day
        cursor.execute('''
            SELECT stat_date, SUM(count) as total
            FROM usage_stats
            WHERE stat_date >= ?
            GROUP BY stat_date
            ORDER BY stat_date
        ''', (cutoff_date,))

        activity_by_day = []
        for row in cursor.fetchall():
            activity_by_day.append({
                'date': row['stat_date'],
                'count': row['total']
            })

        conn.close()

        return jsonify({
            'command_stats': command_stats,
            'activity_by_day': activity_by_day,
            'period_days': days
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/profile', methods=['GET'])
def get_profile():
    """Profilo utente"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500

        cursor = conn.cursor()

        # Total conversations
        cursor.execute('SELECT COUNT(*) as total FROM conversations')
        total = cursor.fetchone()['total']

        # First and last interaction
        cursor.execute('SELECT MIN(timestamp) as first, MAX(timestamp) as last FROM conversations')
        row = cursor.fetchone()
        first_interaction = row['first']
        last_interaction = row['last']

        # Top activities
        cursor.execute('''
            SELECT message_type, COUNT(*) as count
            FROM conversations
            GROUP BY message_type
            ORDER BY count DESC
            LIMIT 5
        ''')

        top_activities = []
        for row in cursor.fetchall():
            top_activities.append({
                'type': row['message_type'],
                'count': row['count']
            })

        # Preferences
        cursor.execute('SELECT preference_key, preference_value FROM user_preferences ORDER BY updated_at DESC')
        preferences = {}
        for row in cursor.fetchall():
            preferences[row['preference_key']] = row['preference_value']

        conn.close()

        return jsonify({
            'total_conversations': total,
            'first_interaction': first_interaction,
            'last_interaction': last_interaction,
            'top_activities': top_activities,
            'preferences': preferences
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/conversations', methods=['GET'])
def get_conversations():
    """Storia conversazioni"""
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        message_type = request.args.get('type', None)

        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500

        cursor = conn.cursor()

        # Build query
        if message_type:
            cursor.execute('''
                SELECT id, timestamp, user_message, bot_response, message_type
                FROM conversations
                WHERE message_type = ?
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
            ''', (message_type, limit, offset))
        else:
            cursor.execute('''
                SELECT id, timestamp, user_message, bot_response, message_type
                FROM conversations
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
            ''', (limit, offset))

        conversations = []
        for row in cursor.fetchall():
            conversations.append({
                'id': row['id'],
                'timestamp': row['timestamp'],
                'user_message': row['user_message'],
                'bot_response': row['bot_response'],
                'message_type': row['message_type']
            })

        # Total count
        if message_type:
            cursor.execute('SELECT COUNT(*) as total FROM conversations WHERE message_type = ?', (message_type,))
        else:
            cursor.execute('SELECT COUNT(*) as total FROM conversations')

        total = cursor.fetchone()['total']

        conn.close()

        return jsonify({
            'conversations': conversations,
            'total': total,
            'limit': limit,
            'offset': offset
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    """Analytics dettagliati"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500

        cursor = conn.cursor()

        # Conversations by type
        cursor.execute('''
            SELECT message_type, COUNT(*) as count
            FROM conversations
            GROUP BY message_type
        ''')

        by_type = {}
        for row in cursor.fetchall():
            by_type[row['message_type']] = row['count']

        # Conversations per hour of day
        cursor.execute('''
            SELECT strftime('%H', timestamp) as hour, COUNT(*) as count
            FROM conversations
            GROUP BY hour
            ORDER BY hour
        ''')

        by_hour = {}
        for row in cursor.fetchall():
            by_hour[row['hour']] = row['count']

        # Average response length
        cursor.execute('SELECT AVG(LENGTH(bot_response)) as avg_length FROM conversations')
        avg_response_length = cursor.fetchone()['avg_length']

        conn.close()

        return jsonify({
            'conversations_by_type': by_type,
            'conversations_by_hour': by_hour,
            'avg_response_length': int(avg_response_length) if avg_response_length else 0
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'lorenz-api',
        'timestamp': datetime.now().isoformat()
    })

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print(f"🚀 Starting LORENZ API Server on {API_HOST}:{API_PORT}")
    print(f"📊 Database: {MEMORY_DB_PATH}")
    print(f"🌐 API endpoints available at http://{API_HOST}:{API_PORT}/api/")

    app.run(
        host=API_HOST,
        port=API_PORT,
        debug=False
    )
