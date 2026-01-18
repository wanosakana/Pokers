# step37_performance_tracker.py
import numpy as np
from scipy import stats
from typing import List, Tuple
import matplotlib.pyplot as plt

class PerformanceTracker:
    """パフォーマンス追跡とトレンド分析"""
    
    def __init__(self):
        self.performance_data = []
        self.rolling_window = 100  # 直近100ハンド
    
    def add_result(self, hand_result: Dict):
        """ハンド結果を追加"""
        self.performance_data.append({
            'timestamp': datetime.now(),
            'profit_loss': hand_result.get('profit_loss', 0),
            'ev': hand_result.get('ev', 0),
            'equity': hand_result.get('equity', 0),
            'position': hand_result.get('position', ''),
            'won': hand_result.get('won', False)
        })
    
    def calculate_rolling_average(self, window: int = None) -> List[float]:
        """移動平均を計算"""
        if not self.performance_data:
            return []
        
        window = window or self.rolling_window
        profits = [d['profit_loss'] for d in self.performance_data]
        
        if len(profits) < window:
            return [np.mean(profits[:i+1]) for i in range(len(profits))]
        
        rolling_avg = []
        for i in range(len(profits)):
            if i < window:
                rolling_avg.append(np.mean(profits[:i+1]))
            else:
                rolling_avg.append(np.mean(profits[i-window+1:i+1]))
        
        return rolling_avg
    
    def detect_trend(self) -> Dict:
        """トレンドを検出"""
        if len(self.performance_data) < 30:
            return {'trend': 'insufficient_data'}
        
        recent = self.performance_data[-100:]
        profits = [d['profit_loss'] for d in recent]
        x = np.arange(len(profits))
        
        # 線形回帰
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, profits)
        
        if p_value < 0.05:  # 統計的に有意
            if slope > 0.5:
                trend = 'strong_upward'
            elif slope > 0:
                trend = 'upward'
            elif slope < -0.5:
                trend = 'strong_downward'
            else:
                trend = 'downward'
        else:
            trend = 'flat'
        
        return {
            'trend': trend,
            'slope': slope,
            'r_squared': r_value ** 2,
            'confidence': 1 - p_value
        }
    
    def calculate_streak(self) -> Dict:
        """連勝・連敗を計算"""
        if not self.performance_data:
            return {'current_streak': 0, 'type': 'none'}
        
        current_streak = 0
        streak_type = None
        
        for result in reversed(self.performance_data):
            if result['won']:
                if streak_type is None:
                    streak_type = 'winning'
                if streak_type == 'winning':
                    current_streak += 1
                else:
                    break
            else:
                if streak_type is None:
                    streak_type = 'losing'
                if streak_type == 'losing':
                    current_streak += 1
                else:
                    break
        
        # 最大連勝/連敗も計算
        max_winning = 0
        max_losing = 0
        current = 0
        current_type = None
        
        for result in self.performance_data:
            if result['won']:
                if current_type == 'winning':
                    current += 1
                else:
                    max_losing = max(max_losing, current)
                    current = 1
                    current_type = 'winning'
            else:
                if current_type == 'losing':
                    current += 1
                else:
                    max_winning = max(max_winning, current)
                    current = 1
                    current_type = 'losing'
        
        return {
            'current_streak': current_streak,
            'type': streak_type,
            'max_winning_streak': max_winning,
            'max_losing_streak': max_losing
        }
    
    def calculate_consistency(self) -> float:
        """一貫性スコアを計算 (0-1)"""
        if len(self.performance_data) < 50:
            return 0.5
        
        profits = [d['profit_loss'] for d in self.performance_data[-100:]]
        
        # 標準偏差が小さく、平均がプラスなら一貫性が高い
        mean = np.mean(profits)
        std = np.std(profits)
        
        if std == 0:
            return 1.0 if mean > 0 else 0.0
        
        # シャープレシオ的な計算
        consistency = (mean / std) if std > 0 else 0
        # 0-1の範囲に正規化
        consistency_score = 1 / (1 + np.exp(-consistency))
        
        return consistency_score
    
    def get_position_performance(self) -> Dict:
        """ポジション別パフォーマンス"""
        position_stats = {}
        
        for data in self.performance_data:
            pos = data['position']
            if pos not in position_stats:
                position_stats[pos] = {
                    'hands': 0,
                    'profit': 0,
                    'wins': 0
                }
            
            position_stats[pos]['hands'] += 1
            position_stats[pos]['profit'] += data['profit_loss']
            position_stats[pos]['wins'] += 1 if data['won'] else 0
        
        for pos in position_stats:
            stats = position_stats[pos]
            stats['avg_profit'] = stats['profit'] / stats['hands']
            stats['win_rate'] = stats['wins'] / stats['hands']
        
        return position_stats
    
    def calculate_variance(self) -> Dict:
        """分散分析"""
        if len(self.performance_data) < 30:
            return {}
        
        profits = [d['profit_loss'] for d in self.performance_data]
        
        return {
            'mean': np.mean(profits),
            'std_dev': np.std(profits),
            'variance': np.var(profits),
            'min': min(profits),
            'max': max(profits),
            'median': np.median(profits),
            'q1': np.percentile(profits, 25),
            'q3': np.percentile(profits, 75)
        }
