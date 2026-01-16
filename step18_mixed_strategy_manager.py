# step18_mixed_strategy_manager.py
import random
from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class ActionDistribution:
    """アクション分布"""
    fold: float = 0.0
    call: float = 0.0
    raise_: float = 0.0
    
    def normalize(self):
        """正規化"""
        total = self.fold + self.call + self.raise_
        if total > 0:
            self.fold /= total
            self.call /= total
            self.raise_ /= total
    
    def sample(self) -> str:
        """分布からサンプリング"""
        rand = random.random()
        if rand < self.fold:
            return 'fold'
        elif rand < self.fold + self.call:
            return 'call'
        else:
            return 'raise'

class MixedStrategyManager:
    """GTO/エクスプロイトバランス管理"""
    
    def __init__(self, exploit_engine, range_manager):
        self.exploit_engine = exploit_engine
        self.range_manager = range_manager
        self.exploitation_level = 0.7  # 0=純粋GTO, 1=最大エクスプロイト
    
    def get_mixed_strategy(self, situation: Dict) -> Dict:
        """混合戦略を計算"""
        # GTO戦略を取得
        gto_strategy = self._get_gto_strategy(situation)
        
        # エクスプロイト調整を取得
        opponent_id = situation.get('opponent_id')
        exploit_adjustments = {}
        
        if opponent_id:
            exploits = self.exploit_engine.detect_exploits(opponent_id)
            exploit_adjustments = self._calculate_exploit_adjustments(
                exploits, situation
            )
        
        # 混合
        mixed_strategy = self._blend_strategies(
            gto_strategy,
            exploit_adjustments,
            self.exploitation_level
        )
        
        return mixed_strategy
    
    def _get_gto_strategy(self, situation: Dict) -> Dict:
        """GTO戦略を取得"""
        position = situation.get('position', 'BTN')
        street = situation.get('street', 'preflop')
        equity = situation.get('equity', 0.5)
        
        # プリフロップ
        if street == 'preflop':
            hand = situation.get('hand_description', 'XX')
            optimal_range = self.range_manager.get_optimal_range(position, 'RFI')
            
            if hand in optimal_range:
                return {'action': 'raise', 'frequency': 1.0, 'size': 2.5}
            else:
                return {'action': 'fold', 'frequency': 1.0}
        
        # ポストフロップ（簡易GTO）
        else:
            if equity > 0.65:
                return {'action': 'bet', 'frequency': 0.85, 'size': 0.66}
            elif equity > 0.45:
                return {'action': 'check', 'frequency': 0.70}
            else:
                return {'action': 'fold', 'frequency': 0.60}
    
    def _calculate_exploit_adjustments(self, exploits: List, 
                                      situation: Dict) -> Dict:
        """エクスプロイト調整を計算"""
        adjustments = {}
        
        for exploit in exploits[:3]:  # トップ3のみ考慮
            if exploit.exploit_type.name == 'OVERFOLDING':
                # もっとブラフする
                adjustments['bluff_frequency'] = adjustments.get('bluff_frequency', 0) + 0.2
                adjustments['cbet_frequency'] = adjustments.get('cbet_frequency', 0) + 0.15
            
            elif exploit.exploit_type.name == 'OVERCALLING':
                # バリューベットを増やす
                adjustments['value_frequency'] = adjustments.get('value_frequency', 0) + 0.15
                adjustments['bluff_frequency'] = adjustments.get('bluff_frequency', 0) - 0.1
            
            elif exploit.exploit_type.name == 'OVERLY_AGGRESSIVE':
                # コールダウンを増やす
                adjustments['call_frequency'] = adjustments.get('call_frequency', 0) + 0.2
                adjustments['fold_frequency'] = adjustments.get('fold_frequency', 0) - 0.15
            
            elif exploit.exploit_type.name == 'PASSIVE':
                # もっとアグレッシブに
                adjustments['bet_frequency'] = adjustments.get('bet_frequency', 0) + 0.15
                adjustments['raise_frequency'] = adjustments.get('raise_frequency', 0) + 0.1
        
        return adjustments
    
    def _blend_strategies(self, gto: Dict, exploit: Dict, 
                         exploitation_level: float) -> Dict:
        """戦略をブレンド"""
        blended = gto.copy()
        
        # エクスプロイト調整を適用
        for key, adjustment in exploit.items():
            if key == 'bluff_frequency' and 'frequency' in blended:
                blended['frequency'] += adjustment * exploitation_level
            elif key == 'bet_frequency' and blended.get('action') == 'bet':
                blended['frequency'] = min(1.0, blended.get('frequency', 0.5) + adjustment * exploitation_level)
        
        return blended
    
    def get_action_distribution(self, situation: Dict) -> ActionDistribution:
        """アクション分布を取得"""
        strategy = self.get_mixed_strategy(situation)
        
        dist = ActionDistribution()
        action = strategy.get('action', 'fold')
        frequency = strategy.get('frequency', 1.0)
        
        if action == 'fold':
            dist.fold = frequency
            dist.call = (1 - frequency) / 2
            dist.raise_ = (1 - frequency) / 2
        elif action == 'call':
            dist.call = frequency
            dist.fold = (1 - frequency) / 2
            dist.raise_ = (1 - frequency) / 2
        elif action in ['raise', 'bet']:
            dist.raise_ = frequency
            dist.call = (1 - frequency) * 0.3
            dist.fold = (1 - frequency) * 0.7
        
        dist.normalize()
        return dist
    
    def recommend_sizing(self, situation: Dict, action: str) -> float:
        """推奨サイズを取得"""
        pot = situation.get('pot', 100)
        equity = situation.get('equity', 0.5)
        
        if action in ['bet', 'raise']:
            # エクスプロイトベースの調整
            opponent_id = situation.get('opponent_id')
            if opponent_id:
                exploits = self.exploit_engine.detect_exploits(opponent_id)
                for exploit in exploits:
                    if exploit.exploit_type.name == 'OVERFOLDING':
                        return pot * 0.33  # 小さめに
                    elif exploit.exploit_type.name == 'OVERCALLING':
                        return pot * 0.75  # 大きめに
            
            # デフォルト（ジオメトリック）
            if equity > 0.6:
                return pot * 0.66
            else:
                return pot * 0.50
        
        return pot * 0.5
