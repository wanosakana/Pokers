# step32_session_manager.py
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import uuid

class Session:
    """個別セッションの管理"""
    
    def __init__(self, stake_level: str, table_type: str, buyin: float):
        self.session_id = str(uuid.uuid4())
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.stake_level = stake_level
        self.table_type = table_type
        self.buyin = buyin
        self.current_stack = buyin
        self.hands_played = 0
        self.hands_won = 0
        self.total_profit_loss = 0
        self.max_stack = buyin
        self.min_stack = buyin
        self.vpip_count = 0
        self.pfr_count = 0
        self.showdowns = 0
        self.showdowns_won = 0
        self.hand_history: List[Dict] = []
    
    def update_stack(self, new_stack: float):
        """スタックを更新"""
        self.current_stack = new_stack
        self.max_stack = max(self.max_stack, new_stack)
        self.min_stack = min(self.min_stack, new_stack)
        self.total_profit_loss = new_stack - self.buyin
    
    def record_hand(self, hand_data: Dict):
        """ハンドを記録"""
        self.hands_played += 1
        self.hand_history.append(hand_data)
        
        if hand_data.get('won', False):
            self.hands_won += 1
        
        if hand_data.get('vpip', False):
            self.vpip_count += 1
        
        if hand_data.get('pfr', False):
            self.pfr_count += 1
        
        if hand_data.get('showdown', False):
            self.showdowns += 1
            if hand_data.get('won', False):
                self.showdowns_won += 1
    
    def end_session(self):
        """セッションを終了"""
        self.end_time = datetime.now()
    
    def get_duration(self) -> timedelta:
        """セッション時間を取得"""
        end = self.end_time or datetime.now()
        return end - self.start_time
    
    def get_bb_per_hour(self, big_blind: float) -> float:
        """BB/100を計算"""
        if self.hands_played == 0:
            return 0
        
        duration_hours = self.get_duration().total_seconds() / 3600
        if duration_hours == 0:
            return 0
        
        hands_per_hour = self.hands_played / duration_hours
        bb_won = self.total_profit_loss / big_blind
        
        return (bb_won / self.hands_played) * 100 if self.hands_played > 0 else 0
    
    def get_statistics(self) -> Dict:
        """統計情報を取得"""
        return {
            'session_id': self.session_id,
            'duration': str(self.get_duration()),
            'hands_played': self.hands_played,
            'profit_loss': self.total_profit_loss,
            'profit_loss_bb': self.total_profit_loss / 2,  # 仮定: BB=2
            'win_rate': self.hands_won / self.hands_played if self.hands_played > 0 else 0,
            'vpip': self.vpip_count / self.hands_played if self.hands_played > 0 else 0,
            'pfr': self.pfr_count / self.hands_played if self.hands_played > 0 else 0,
            'wtsd': self.showdowns / self.hands_played if self.hands_played > 0 else 0,
            'wssd': self.showdowns_won / self.showdowns if self.showdowns > 0 else 0,
            'max_stack': self.max_stack,
            'min_stack': self.min_stack,
        }

class SessionManager:
    """複数セッションの管理"""
    
    def __init__(self):
        self.sessions: List[Session] = []
        self.current_session: Optional[Session] = None
        self.total_profit_loss = 0
        self.total_hands = 0
    
    def start_session(self, stake_level: str, table_type: str, 
                     buyin: float) -> Session:
        """新しいセッションを開始"""
        if self.current_session and not self.current_session.end_time:
            self.current_session.end_session()
        
        session = Session(stake_level, table_type, buyin)
        self.sessions.append(session)
        self.current_session = session
        return session
    
    def end_current_session(self):
        """現在のセッションを終了"""
        if self.current_session:
            self.current_session.end_session()
            self.total_profit_loss += self.current_session.total_profit_loss
            self.total_hands += self.current_session.hands_played
    
    def get_session_summary(self, session_id: Optional[str] = None) -> Dict:
        """セッションのサマリーを取得"""
        if session_id:
            session = next((s for s in self.sessions if s.session_id == session_id), None)
        else:
            session = self.current_session
        
        if not session:
            return {}
        
        return session.get_statistics()
    
    def get_all_time_stats(self) -> Dict:
        """全期間の統計"""
        if not self.sessions:
            return {}
        
        total_hands = sum(s.hands_played for s in self.sessions)
        total_pl = sum(s.total_profit_loss for s in self.sessions)
        total_duration = sum((s.get_duration().total_seconds() for s in self.sessions), 0)
        
        return {
            'total_sessions': len(self.sessions),
            'total_hands': total_hands,
            'total_profit_loss': total_pl,
            'total_hours': total_duration / 3600,
            'avg_session_length': (total_duration / len(self.sessions)) / 3600,
            'overall_winrate': total_pl / total_hands if total_hands > 0 else 0,
        }
    
    def get_best_session(self) -> Optional[Session]:
        """最も利益の多いセッション"""
        if not self.sessions:
            return None
        return max(self.sessions, key=lambda s: s.total_profit_loss)
    
    def get_worst_session(self) -> Optional[Session]:
        """最も損失の多いセッション"""
        if not self.sessions:
            return None
        return min(self.sessions, key=lambda s: s.total_profit_loss)
    
    def export_sessions(self, filename: str):
        """セッションデータをエクスポート"""
        data = {
            'sessions': [s.get_statistics() for s in self.sessions],
            'all_time': self.get_all_time_stats()
        }
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
