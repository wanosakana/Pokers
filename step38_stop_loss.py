# step38_stop_loss.py
class StopLossManager:
    """ストップロス・テイクプロフィット管理"""
    
    def __init__(self, initial_bankroll: float):
        self.initial_bankroll = initial_bankroll
        self.session_start_bankroll = initial_bankroll
        self.current_bankroll = initial_bankroll
        
        # ストップロス設定
        self.stop_loss_amount = 200  # ドル
        self.stop_loss_percentage = 0.20  # 20%
        
        # テイクプロフィット設定
        self.take_profit_amount = 500
        self.take_profit_percentage = 0.50  # 50%
        
        # 時間制限
        self.max_session_hours = 6.0
        self.session_start_time = datetime.now()
        
        # 状態
        self.stop_loss_triggered = False
        self.take_profit_triggered = False
        self.time_limit_reached = False
    
    def update_bankroll(self, new_bankroll: float):
        """バンクロールを更新"""
        self.current_bankroll = new_bankroll
        self._check_conditions()
    
    def _check_conditions(self):
        """条件をチェック"""
        session_pl = self.current_bankroll - self.session_start_bankroll
        session_duration = (datetime.now() - self.session_start_time).total_seconds() / 3600
        
        # ストップロスチェック
        if (session_pl <= -self.stop_loss_amount or 
            session_pl / self.session_start_bankroll <= -self.stop_loss_percentage):
            self.stop_loss_triggered = True
        
        # テイクプロフィットチェック
        if (session_pl >= self.take_profit_amount or 
            session_pl / self.session_start_bankroll >= self.take_profit_percentage):
            self.take_profit_triggered = True
        
        # 時間制限チェック
        if session_duration >= self.max_session_hours:
            self.time_limit_reached = True
    
    def should_stop_session(self) -> Tuple[bool, str]:
        """セッションを停止すべきか"""
        if self.stop_loss_triggered:
            return True, f"Stop loss triggered: ${self.current_bankroll - self.session_start_bankroll:+.2f}"
        
        if self.take_profit_triggered:
            return True, f"Take profit triggered: ${self.current_bankroll - self.session_start_bankroll:+.2f}"
        
        if self.time_limit_reached:
            return True, f"Time limit reached: {self.max_session_hours} hours"
        
        return False, ""
    
    def reset_session(self):
        """新しいセッション開始"""
        self.session_start_bankroll = self.current_bankroll
        self.session_start_time = datetime.now()
        self.stop_loss_triggered = False
        self.take_profit_triggered = False
        self.time_limit_reached = False
    
    def get_status(self) -> Dict:
        """現在の状態を取得"""
        session_pl = self.current_bankroll - self.session_start_bankroll
        session_duration = (datetime.now() - self.session_start_time).total_seconds() / 3600
        
        return {
            'session_pl': session_pl,
            'session_duration': session_duration,
            'stop_loss_remaining': self.stop_loss_amount + session_pl,
            'take_profit_remaining': self.take_profit_amount - session_pl,
            'time_remaining': self.max_session_hours - session_duration,
            'stop_loss_triggered': self.stop_loss_triggered,
            'take_profit_triggered': self.take_profit_triggered,
            'time_limit_reached': self.time_limit_reached
        }
