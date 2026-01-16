# step14_15_advanced_math.py
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
import math

@dataclass
class PotOddsResult:
    """ポットオッズ計算結果"""
    call_amount: float
    pot_size: float
    pot_odds: float
    pot_odds_percent: float
    required_equity: float
    breakeven_equity: float
    implied_odds_factor: float
    
    def format_ratio(self) -> str:
        """オッズを比率で表現 (例: 3:1)"""
        if self.pot_odds < 0.01:
            return "∞:1"
        ratio = 1 / self.pot_odds
        return f"{ratio:.1f}:1"

class AdvancedPotOddsEngine:
    """高度なポットオッズ計算エンジン"""
    
    @staticmethod
    def calculate_pot_odds(call_amount: float, pot_size: float,
                          effective_stack: float = None) -> PotOddsResult:
        """完全なポットオッズ計算"""
        if call_amount <= 0:
            call_amount = 0.01
        
        total_pot = pot_size + call_amount
        pot_odds = call_amount / total_pot
        required_equity = pot_odds
        
        # インプライドオッズファクター
        implied_factor = 1.0
        if effective_stack and effective_stack > call_amount:
            remaining_stack = effective_stack - call_amount
            potential_winnings = total_pot + remaining_stack
            implied_factor = potential_winnings / total_pot
        
        return PotOddsResult(
            call_amount=call_amount,
            pot_size=pot_size,
            pot_odds=pot_odds,
            pot_odds_percent=pot_odds * 100,
            required_equity=required_equity,
            breakeven_equity=required_equity,
            implied_odds_factor=implied_factor
        )
    
    @staticmethod
    def calculate_mdf(pot_before_bet: float, bet_size: float) -> float:
        """Minimum Defense Frequency (最小防御頻度)"""
        total_pot = pot_before_bet + bet_size
        return pot_before_bet / total_pot
    
    @staticmethod
    def calculate_optimal_bet_size(pot: float, equity: float,
                                  alpha: float = 1.0) -> float:
        """最適ベットサイズ (Geometric sizing)"""
        # alpha: アグレッションファクター (0.5-2.0)
        if equity < 0.5:
            return 0  # 弱い手でベットすべきでない
        
        # シンプルなジオメトリックサイジング
        optimal = pot * alpha * ((equity / (1 - equity)) ** 0.5)
        return min(optimal, pot * 1.5)  # 1.5x pot を上限
    
    @staticmethod
    def calculate_fold_equity(opponent_fold_percent: float, 
                             pot: float, bet_size: float) -> float:
        """フォールドエクイティ"""
        return opponent_fold_percent * (pot + bet_size)
    
    @staticmethod
    def calculate_ev_call(equity: float, pot: float, call_amount: float) -> float:
        """コールのEV"""
        return (equity * pot) - ((1 - equity) * call_amount)
    
    @staticmethod
    def calculate_ev_raise(equity: float, pot: float, raise_amount: float,
                          fold_equity: float) -> float:
        """レイズのEV"""
        win_by_fold = fold_equity
        win_by_showdown = (1 - fold_equity) * equity * (pot + raise_amount)
        cost = raise_amount
        return win_by_fold + win_by_showdown - cost
    
    @staticmethod
    def kelly_criterion(edge: float, odds: float) -> float:
        """ケリー基準（最適賭け金比率）"""
        if odds <= 0:
            return 0
        return edge / odds

@dataclass
class SPRAnalysis:
    """SPR分析結果"""
    spr: float
    category: str  # "committed", "short", "medium", "deep", "very_deep"
    recommended_strategy: str
    commitment_threshold: bool

class AdvancedSPRManager:
    """高度なSPR管理"""
    
    @staticmethod
    def calculate_spr(effective_stack: float, pot: float) -> float:
        """SPR計算"""
        if pot <= 0:
            return 100.0
        return effective_stack / pot
    
    @staticmethod
    def analyze_spr(effective_stack: float, pot: float,
                   hand_strength: str = "medium") -> SPRAnalysis:
        """SPR分析"""
        spr = AdvancedSPRManager.calculate_spr(effective_stack, pot)
        
        # カテゴリ分類
        if spr < 1.0:
            category = "committed"
            strategy = "Push/fold with any decent equity"
            committed = True
        elif spr < 3.0:
            category = "short"
            strategy = "Play straightforward, value-heavy"
            committed = spr < 1.5
        elif spr < 7.0:
            category = "medium"
            strategy = "Standard play, consider implied odds"
            committed = False
        elif spr < 13.0:
            category = "deep"
            strategy = "Focus on playability and position"
            committed = False
        else:
            category = "very_deep"
            strategy = "Speculative hands gain value, avoid marginal spots"
            committed = False
        
        # ハンド強度に基づく調整
        if hand_strength == "strong":
            if spr < 7.0:
                strategy = "Get all-in, maximize value"
            else:
                strategy = "Build pot on all streets"
        elif hand_strength == "weak":
            if spr < 3.0:
                strategy = "Fold or go all-in (no room for play)"
        
        return SPRAnalysis(
            spr=spr,
            category=category,
            recommended_strategy=strategy,
            commitment_threshold=committed
        )
    
    @staticmethod
    def calculate_commitment_threshold(spr: float) -> float:
        """コミットメント閾値（このエクイティがあればオールイン）"""
        if spr < 1.0:
            return 0.33  # 33%以上で突っ込む
        elif spr < 2.0:
            return 0.40
        elif spr < 3.0:
            return 0.45
        else:
            return 0.50

class CombinatoricsCalculator:
    """組み合わせ論計算"""
    
    @staticmethod
    def combinations(n: int, r: int) -> int:
        """nCr (組み合わせ)"""
        if r > n or r < 0:
            return 0
        return math.factorial(n) // (math.factorial(r) * math.factorial(n - r))
    
    @staticmethod
    def hand_combinations(hand_type: str) -> int:
        """ハンドタイプのコンボ数"""
        if hand_type.endswith('s'):  # Suited
            return 4
        elif hand_type.endswith('o'):  # Offsuit
            return 12
        elif len(hand_type) == 2 and hand_type[0] == hand_type[1]:  # Pair
            return 6
        return 0
    
    @staticmethod
    def blockers_effect(my_cards: List[str], opponent_range: List[str]) -> Dict:
        """ブロッカー効果の計算"""
        my_ranks = [c[0] for c in my_cards]
        my_suits = [c[1] for c in my_cards]
        
        blocked_combos = 0
        total_combos = 0
        
        for hand in opponent_range:
            combos = CombinatoricsCalculator.hand_combinations(hand)
            total_combos += combos
            
            # 自分のカードがブロックしているか
            if any(rank in hand for rank in my_ranks):
                blocked_combos += combos * 0.5  # 部分的にブロック
        
        return {
            'blocked_combos': blocked_combos,
            'total_combos': total_combos,
            'block_percent': blocked_combos / total_combos if total_combos > 0 else 0
        }
