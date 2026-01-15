# step33_hand_history.py
from datetime import datetime
from typing import List, Dict, Optional
import json
import sqlite3

class HandHistory:
    """ハンド履歴の詳細記録"""
    
    def __init__(self, db_path: str = 'poker_hands.db'):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """データベースを初期化"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hands (
                hand_id TEXT PRIMARY KEY,
                timestamp TEXT,
                session_id TEXT,
                position TEXT,
                hole_cards TEXT,
                board TEXT,
                pot_size REAL,
                won BOOLEAN,
                profit_loss REAL,
                action_preflop TEXT,
                action_flop TEXT,
                action_turn TEXT,
                action_river TEXT,
                showdown BOOLEAN,
                hand_strength TEXT,
                equity REAL,
                eqr REAL,
                ev REAL,
                gto_action TEXT,
                actual_action TEXT,
                opponents TEXT,
                notes TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS actions (
                action_id INTEGER PRIMARY KEY AUTOINCREMENT,
                hand_id TEXT,
                street TEXT,
                action_type TEXT,
                amount REAL,
                pot_before REAL,
                pot_after REAL,
                timestamp TEXT,
                FOREIGN KEY (hand_id) REFERENCES hands (hand_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def record_hand(self, hand_data: Dict) -> str:
        """ハンドを記録"""
        hand_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{hand_data.get('position', 'UNK')}"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO hands VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            hand_id,
            datetime.now().isoformat(),
            hand_data.get('session_id', ''),
            hand_data.get('position', ''),
            json.dumps(hand_data.get('hole_cards', [])),
            json.dumps(hand_data.get('board', [])),
            hand_data.get('pot_size', 0),
            hand_data.get('won', False),
            hand_data.get('profit_loss', 0),
            hand_data.get('action_preflop', ''),
            hand_data.get('action_flop', ''),
            hand_data.get('action_turn', ''),
            hand_data.get('action_river', ''),
            hand_data.get('showdown', False),
            hand_data.get('hand_strength', ''),
            hand_data.get('equity', 0),
            hand_data.get('eqr', 0),
            hand_data.get('ev', 0),
            hand_data.get('gto_action', ''),
            hand_data.get('actual_action', ''),
            json.dumps(hand_data.get('opponents', [])),
            hand_data.get('notes', '')
        ))
        
        # アクションを記録
        for action in hand_data.get('actions', []):
            cursor.execute('''
                INSERT INTO actions (hand_id, street, action_type, amount, pot_before, pot_after, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                hand_id,
                action.get('street', ''),
                action.get('type', ''),
                action.get('amount', 0),
                action.get('pot_before', 0),
                action.get('pot_after', 0),
                action.get('timestamp', datetime.now().isoformat())
            ))
        
        conn.commit()
        conn.close()
        
        return hand_id
    
    def get_hand(self, hand_id: str) -> Optional[Dict]:
        """特定のハンドを取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM hands WHERE hand_id = ?', (hand_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
        
        # アクションも取得
        cursor.execute('SELECT * FROM actions WHERE hand_id = ?', (hand_id,))
        actions = cursor.fetchall()
        
        conn.close()
        
        return self._row_to_dict(row, actions)
    
    def _row_to_dict(self, row, actions) -> Dict:
        """データベース行を辞書に変換"""
        return {
            'hand_id': row[0],
            'timestamp': row[1],
            'session_id': row[2],
            'position': row[3],
            'hole_cards': json.loads(row[4]),
            'board': json.loads(row[5]),
            'pot_size': row[6],
            'won': bool(row[7]),
            'profit_loss': row[8],
            'actions': [{
                'street': a[2],
                'type': a[3],
                'amount': a[4],
                'pot_before': a[5],
                'pot_after': a[6]
            } for a in actions]
        }
    
    def search_hands(self, filters: Dict) -> List[Dict]:
        """フィルタ条件でハンドを検索"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = 'SELECT * FROM hands WHERE 1=1'
        params = []
        
        if 'position' in filters:
            query += ' AND position = ?'
            params.append(filters['position'])
        
        if 'won' in filters:
            query += ' AND won = ?'
            params.append(filters['won'])
        
        if 'min_pot' in filters:
            query += ' AND pot_size >= ?'
            params.append(filters['min_pot'])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_dict(row, []) for row in rows]
    
    def get_statistics_by_position(self) -> Dict:
        """ポジション別統計"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT position, COUNT(*), SUM(profit_loss), AVG(equity)
            FROM hands
            GROUP BY position
        ''')
        
        results = {}
        for row in cursor.fetchall():
            results[row[0]] = {
                'hands': row[1],
                'profit_loss': row[2],
                'avg_equity': row[3]
            }
        
        conn.close()
        return results
