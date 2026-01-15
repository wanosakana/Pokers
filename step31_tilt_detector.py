# step31_tilt_detector.py
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import numpy as np

class TiltDetector:
    """ティルト（感情的プレイ）の検知と警告"""
    
    def __init__(self):
        self.action_history: List[Dict] = []
        self.emotional_indicators = {
            'rapid_decisions': 0,
            'variance_from_gto': 0,
            'aggression_spike': 0,
            'loss_chasing': 0,
            'bankroll_ignore': 0
        }
        self.tilt_threshold = 0.7
        self.warning_issued = False
    
    def record_action(self, action: Dict):
        """アクションを記録"""
        action['timestamp'] = datetime.now()
        self.action_history.append(action)
        
        # 古いデータを削除（直近50ハンドのみ保持）
        if len(self.action_history) > 50:
            self.action_history = self.action_history[-50:]
    
    def analyze_decision_time(self) -> float:
        """意思決定時間の分析"""
        if len(self.action_history) < 10:
            return 0.0
        
        recent = self.action_history[-10:]
        decision_times = []
        
        for i in range(1, len(recent)):
            time_diff = (recent[i]['timestamp'] - recent[i-1]['timestamp']).total_seconds()
            if time_diff < 60:  # 60秒以内のアクション
                decision_times.append(time_diff)
        
        if not decision_times:
            return 0.0
        
        avg_time = np.mean(decision_times)
        std_time = np.std(decision_times)
        
        # 極端に早い判断が多い場合（平均の半分以下）
        rapid_count = sum(1 for t in decision_times if t < avg_time * 0.5)
        return rapid_count / len(decision_times)
    
    def analyze_gto_deviation(self) -> float:
        """GTOからの逸脱度を分析"""
        if len(self.action_history) < 15:
            return 0.0
        
        recent = self.action_history[-15:]
        deviations = []
        
        for action in recent:
            if 'gto_recommendation' in action and 'actual_action' in action:
                gto = action['gto_recommendation']
                actual = action['actual_action']
                
                if gto != actual:
                    # EVの差を計算
                    ev_diff = abs(action.get('gto_ev', 0) - action.get('actual_ev', 0))
                    deviations.append(ev_diff)
        
        if not deviations:
            return 0.0
        
        # 平均逸脱度
        return min(1.0, np.mean(deviations) / 50)  # 50BBを基準に正規化
    
    def analyze_aggression_change(self) -> float:
        """アグレッションの急激な変化を検出"""
        if len(self.action_history) < 20:
            return 0.0
        
        # 前半10ハンドと後半10ハンドを比較
        first_half = self.action_history[-20:-10]
        second_half = self.action_history[-10:]
        
        def calculate_aggression(hands):
            aggressive = sum(1 for h in hands if h.get('action') in ['raise', 'bet', '3bet'])
            return aggressive / len(hands) if hands else 0
        
        aggression_1 = calculate_aggression(first_half)
        aggression_2 = calculate_aggression(second_half)
        
        # 急激な増加（2倍以上）をティルトの兆候とする
        if aggression_1 > 0:
            change_ratio = aggression_2 / aggression_1
            if change_ratio > 2.0:
                return min(1.0, (change_ratio - 1.0) / 2.0)
        
        return 0.0
    
    def analyze_loss_chasing(self) -> float:
        """負けを取り戻そうとする行動を検出"""
        if len(self.action_history) < 10:
            return 0.0
        
        recent = self.action_history[-10:]
        consecutive_losses = 0
        max_consecutive = 0
        risky_plays_after_loss = 0
        
        for i, action in enumerate(recent):
            result = action.get('result', 0)
            
            if result < 0:
                consecutive_losses += 1
                max_consecutive = max(max_consecutive, consecutive_losses)
                
                # 次のアクションがリスキーか確認
                if i < len(recent) - 1:
                    next_action = recent[i + 1]
                    if next_action.get('risk_level', 'normal') == 'high':
                        risky_plays_after_loss += 1
            else:
                consecutive_losses = 0
        
        # 3連敗以上 + その後のリスキープレイ
        if max_consecutive >= 3 and risky_plays_after_loss > 0:
            return min(1.0, (max_consecutive / 5.0 + risky_plays_after_loss / 3.0) / 2)
        
        return 0.0
    
    def analyze_bankroll_management(self) -> float:
        """バンクロール管理の逸脱を検出"""
        if len(self.action_history) < 5:
            return 0.0
        
        recent = self.action_history[-5:]
        oversized_bets = 0
        
        for action in recent:
            bet_size = action.get('bet_size', 0)
            bankroll = action.get('current_bankroll', float('inf'))
            recommended_max = action.get('recommended_max_bet', float('inf'))
            
            if bet_size > recommended_max * 1.5:
                oversized_bets += 1
        
        return oversized_bets / len(recent)
    
    def calculate_tilt_score(self) -> Dict[str, any]:
        """総合的なティルトスコアを計算"""
        self.emotional_indicators['rapid_decisions'] = self.analyze_decision_time()
        self.emotional_indicators['variance_from_gto'] = self.analyze_gto_deviation()
        self.emotional_indicators['aggression_spike'] = self.analyze_aggression_change()
        self.emotional_indicators['loss_chasing'] = self.analyze_loss_chasing()
        self.emotional_indicators['bankroll_ignore'] = self.analyze_bankroll_management()
        
        # 重み付け平均
        weights = {
            'rapid_decisions': 0.15,
            'variance_from_gto': 0.25,
            'aggression_spike': 0.20,
            'loss_chasing': 0.30,
            'bankroll_ignore': 0.10
        }
        
        tilt_score = sum(
            self.emotional_indicators[key] * weights[key]
            for key in weights
        )
        
        # レベル分類
        if tilt_score > 0.7:
            level = 'CRITICAL'
            recommendation = 'STOP PLAYING IMMEDIATELY'
        elif tilt_score > 0.5:
            level = 'HIGH'
            recommendation = 'Take a break, review recent hands'
        elif tilt_score > 0.3:
            level = 'MODERATE'
            recommendation = 'Be cautious, focus on GTO'
        else:
            level = 'LOW'
            recommendation = 'Continue playing'
        
        return {
            'tilt_score': tilt_score,
            'level': level,
            'recommendation': recommendation,
            'indicators': self.emotional_indicators.copy()
        }
    
    def should_stop_session(self) -> bool:
        """セッションを停止すべきか判定"""
        analysis = self.calculate_tilt_score()
        return analysis['tilt_score'] > self.tilt_threshold
    
    def get_cooling_off_period(self) -> timedelta:
        """推奨休憩時間を算出"""
        analysis = self.calculate_tilt_score()
        score = analysis['tilt_score']
        
        if score > 0.7:
            return timedelta(hours=24)
        elif score > 0.5:
            return timedelta(hours=4)
        elif score > 0.3:
            return timedelta(minutes=30)
        else:
            return timedelta(minutes=5)
