# step36_alert_system.py
from typing import List, Dict, Callable
from datetime import datetime
from enum import Enum
import threading
import time

class AlertPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class Alert:
    """アラートメッセージ"""
    
    def __init__(self, priority: AlertPriority, category: str, 
                 message: str, actionable: bool = False, 
                 action_recommendation: str = ""):
        self.priority = priority
        self.category = category
        self.message = message
        self.actionable = actionable
        self.action_recommendation = action_recommendation
        self.timestamp = datetime.now()
        self.acknowledged = False
    
    def __str__(self):
        priority_symbols = {
            AlertPriority.LOW: "ℹ️ ",
            AlertPriority.MEDIUM: "⚠️ ",
            AlertPriority.HIGH: "🔴",
            AlertPriority.CRITICAL: "🚨"
        }
        
        symbol = priority_symbols[self.priority]
        return f"{symbol} [{self.category}] {self.message}"

class AlertSystem:
    """リアルタイムアラートシステム"""
    
    def __init__(self):
        self.alerts: List[Alert] = []
        self.alert_history: List[Alert] = []
        self.callbacks: Dict[AlertPriority, List[Callable]] = {
            p: [] for p in AlertPriority
        }
        self.monitoring = False
        self.monitor_thread = None
        self.conditions = {
            'tilt_score': 0.0,
            'current_loss': 0.0,
            'session_duration': 0.0,
            'hands_per_hour': 0.0,
            'current_ev': 0.0,
            'bankroll_ratio': 1.0
        }
    
    def register_callback(self, priority: AlertPriority, callback: Callable):
        """コールバック関数を登録"""
        self.callbacks[priority].append(callback)
    
    def create_alert(self, priority: AlertPriority, category: str,
                    message: str, actionable: bool = False,
                    action_recommendation: str = "") -> Alert:
        """アラートを作成"""
        alert = Alert(priority, category, message, actionable, action_recommendation)
        self.alerts.append(alert)
        self.alert_history.append(alert)
        
        # コールバックを実行
        for callback in self.callbacks[priority]:
            try:
                callback(alert)
            except Exception as e:
                print(f"Alert callback error: {e}")
        
        # クリティカルアラートはログに記録
        if priority == AlertPriority.CRITICAL:
            self._log_critical_alert(alert)
        
        return alert
    
    def update_conditions(self, conditions: Dict):
        """監視条件を更新"""
        self.conditions.update(conditions)
        self._check_conditions()
    
    def _check_conditions(self):
        """条件をチェックしてアラートを生成"""
        # ティルトチェック
        if self.conditions['tilt_score'] > 0.7:
            self.create_alert(
                AlertPriority.CRITICAL,
                "Tilt Detection",
                f"Tilt score: {self.conditions['tilt_score']:.1%} - STOP PLAYING NOW",
                actionable=True,
                action_recommendation="End session immediately and take a break"
            )
        elif self.conditions['tilt_score'] > 0.5:
            self.create_alert(
                AlertPriority.HIGH,
                "Tilt Warning",
                f"Tilt score: {self.conditions['tilt_score']:.1%} - Be cautious",
                actionable=True,
                action_recommendation="Review recent decisions, consider taking a break"
            )
        
        # 損失チェック
        if self.conditions['current_loss'] < -200:
            self.create_alert(
                AlertPriority.HIGH,
                "Stop Loss",
                f"Loss: ${self.conditions['current_loss']:.2f} - Stop loss triggered",
                actionable=True,
                action_recommendation="End session to preserve bankroll"
            )
        elif self.conditions['current_loss'] < -100:
            self.create_alert(
                AlertPriority.MEDIUM,
                "Loss Warning",
                f"Loss: ${self.conditions['current_loss']:.2f}",
                actionable=False
            )
        
        # セッション時間チェック
        if self.conditions['session_duration'] > 4.0:
            self.create_alert(
                AlertPriority.MEDIUM,
                "Session Length",
                f"Playing for {self.conditions['session_duration']:.1f} hours - Consider break",
                actionable=True,
                action_recommendation="Take 15-minute break to refresh"
            )
        
        # ハンドレートチェック
        if self.conditions['hands_per_hour'] < 30:
            self.create_alert(
                AlertPriority.LOW,
                "Play Rate",
                f"Only {self.conditions['hands_per_hour']:.0f} hands/hour",
                actionable=False
            )
        
        # EVチェック
        if self.conditions['current_ev'] < -50:
            self.create_alert(
                AlertPriority.MEDIUM,
                "Negative EV",
                f"Session EV: ${self.conditions['current_ev']:.2f} - Review strategy",
                actionable=True,
                action_recommendation="Review hand history for leaks"
            )
        
        # バンクロールチェック
        if self.conditions['bankroll_ratio'] < 0.5:
            self.create_alert(
                AlertPriority.CRITICAL,
                "Bankroll Alert",
                "Bankroll down 50% - MOVE DOWN STAKES",
                actionable=True,
                action_recommendation="Drop to lower stakes immediately"
            )
    
    def _log_critical_alert(self, alert: Alert):
        """クリティカルアラートをログに記録"""
        with open('critical_alerts.log', 'a') as f:
            f.write(f"{alert.timestamp.isoformat()} | {alert.category} | {alert.message}\n")
    
    def get_active_alerts(self, priority: AlertPriority = None) -> List[Alert]:
        """アクティブなアラートを取得"""
        active = [a for a in self.alerts if not a.acknowledged]
        if priority:
            active = [a for a in active if a.priority == priority]
        return sorted(active, key=lambda a: a.priority.value, reverse=True)
    
    def acknowledge_alert(self, alert: Alert):
        """アラートを確認済みにする"""
        alert.acknowledged = True
        if alert in self.alerts:
            self.alerts.remove(alert)
    
    def start_monitoring(self, interval: float = 5.0):
        """バックグラウンド監視を開始"""
        self.monitoring = True
        
        def monitor_loop():
            while self.monitoring:
                self._check_conditions()
                time.sleep(interval)
        
        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """監視を停止"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
