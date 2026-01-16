# step11_12_advanced_range.py
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass
from enum import Enum

class HandStrength(Enum):
    PREMIUM = 5    # AA, KK
    STRONG = 4     # QQ-TT, AK
    MEDIUM = 3     # 99-77, AQ, AJ
    MARGINAL = 2   # 小ペア, suited連続
    WEAK = 1       # その他

@dataclass
class HandDescriptor:
    """ハンドの詳細記述"""
    name: str
    strength: HandStrength
    playability: float  # 0-1: ポストフロップでのプレイしやすさ
    equity_vs_random: float
    blockers_value: float  # ブロッカー価値
    
class AdvancedRangeManager:
    """高度なレンジ管理システム"""
    
    def __init__(self):
        self.cpp_bridge = OptimizedCppBridge()
        self.hand_matrix = self._build_hand_matrix()
        self.gto_ranges = self._load_gto_ranges()
        
    def _build_hand_matrix(self) -> Dict[str, HandDescriptor]:
        """169種類のハンドマトリクスを構築"""
        matrix = {}
        ranks = '23456789TJQKA'
        
        # ペア
        for i, r in enumerate(ranks):
            pair = r + r
            strength = HandStrength.PREMIUM if i >= 11 else \
                      HandStrength.STRONG if i >= 8 else \
                      HandStrength.MEDIUM if i >= 5 else HandStrength.MARGINAL
            
            matrix[pair] = HandDescriptor(
                name=pair,
                strength=strength,
                playability=0.85 if i >= 8 else 0.7,
                equity_vs_random=self._calculate_pair_equity(i),
                blockers_value=0.9 if i >= 11 else 0.6
            )
        
        # スーテッド/オフスート
        for i in range(len(ranks)):
            for j in range(i + 1, len(ranks)):
                high = ranks[j]
                low = ranks[i]
                
                # スーテッド
                suited = high + low + 's'
                matrix[suited] = self._create_descriptor(suited, j, i, True)
                
                # オフスート
                offsuit = high + low + 'o'
                matrix[offsuit] = self._create_descriptor(offsuit, j, i, False)
        
        return matrix
    
    def _create_descriptor(self, name: str, high: int, low: int, 
                          suited: bool) -> HandDescriptor:
        """ハンド記述子を作成"""
        gap = high - low
        
        # 強度判定
        if high >= 12 and low >= 11:  # AK, AQ
            strength = HandStrength.STRONG
        elif high >= 12 and low >= 9:  # AJ, AT
            strength = HandStrength.MEDIUM
        elif gap <= 1 and suited:  # 連続スーテッド
            strength = HandStrength.MEDIUM
        else:
            strength = HandStrength.MARGINAL
        
        # プレイアビリティ
        playability = 0.8 if suited else 0.6
        if gap <= 1:
            playability += 0.1  # 連続性ボーナス
        if high >= 11:
            playability += 0.05  # ハイカードボーナス
        
        return HandDescriptor(
            name=name,
            strength=strength,
            playability=min(1.0, playability),
            equity_vs_random=self._estimate_equity(high, low, suited),
            blockers_value=0.8 if high >= 12 else 0.5
        )
    
    def _calculate_pair_equity(self, rank: int) -> float:
        """ペアのエクイティ推定"""
        base = 0.50
        return min(0.85, base + (rank * 0.027))
    
    def _estimate_equity(self, high: int, low: int, suited: bool) -> float:
        """エクイティの推定"""
        base = 0.35 + (high * 0.02) + (low * 0.01)
        if suited:
            base += 0.03
        return min(0.70, base)
    
    def _load_gto_ranges(self) -> Dict:
        """GTOレンジのロード（ポジション×シチュエーション）"""
        return {
            ('UTG', 'RFI'): self._create_range('AA-77,AKs-ATs,AKo-AJo,KQs-KJs'),
            ('MP', 'RFI'): self._create_range('AA-66,AKs-A9s,AKo-ATo,KQs-KTs,KQo'),
            ('CO', 'RFI'): self._create_range('AA-22,AKs-A5s,AKo-A9o,KQs-K9s,KQo-KTo,QJs-Q9s,QJo,JTs-J9s,T9s-T8s,98s'),
            ('BTN', 'RFI'): self._create_range('AA-22,AXs,KXs,QXs,JXs,TXs,9Xs,8Xs,7Xs,6Xs,5Xs,AXo,KXo,QXo'),
            ('SB', 'RFI'): self._create_range('AA-22,AKs-A2s,AKo-A8o,KQs-K7s,KQo-K9o,QJs-Q8s,QJo-QTo,JTs-J9s,T9s-T8s,98s-97s,87s'),
            ('BB', 'vs_SB'): self._create_range('AA-22,AXs,AXo,KXs,KXo,QXs,QXo,JXs,JXo,TXs,9Xs,8Xs,7Xs,6Xs,5Xs'),
            ('BTN', 'vs_3bet'): self._create_range('AA-QQ,AKs,AKo'),
            ('BB', 'vs_steal'): self._create_range('AA-22,AXs,AXo,KXs,KXo,QXs,Q9o+,JXs,J9o+,TXs,T9o,9Xs,8Xs,7Xs,6Xs,5Xs,4Xs'),
        }
    
    def _create_range(self, range_string: str) -> Set[str]:
        """レンジ文字列を展開"""
        hands = set()
        parts = range_string.split(',')
        
        for part in parts:
            part = part.strip()
            
            if '-' in part and len(part) == 5:  # AA-TT
                self._expand_pair_range(part, hands)
            elif '+' in part:  # A9s+
                self._expand_plus_range(part, hands)
            elif 'X' in part:  # AXs (全てのスート付き)
                self._expand_x_range(part, hands)
            else:
                hands.add(part)
        
        return hands
    
    def _expand_pair_range(self, range_str: str, hands: Set):
        """ペアレンジを展開 (AA-TT)"""
        start, end = range_str.split('-')
        ranks = '23456789TJQKA'
        start_idx = ranks.index(start[0])
        end_idx = ranks.index(end[0])
        
        for i in range(end_idx, start_idx + 1):
            hands.add(ranks[i] * 2)
    
    def _expand_plus_range(self, range_str: str, hands: Set):
        """プラスレンジを展開 (A9s+)"""
        range_str = range_str.rstrip('+')
        high = range_str[0]
        low = range_str[1]
        suited = 's' in range_str
        
        ranks = '23456789TJQKA'
        low_idx = ranks.index(low)
        high_idx = ranks.index(high)
        
        for i in range(low_idx, high_idx):
            suffix = 's' if suited else 'o'
            hands.add(high + ranks[i] + suffix)
    
    def _expand_x_range(self, range_str: str, hands: Set):
        """Xレンジを展開 (AXs)"""
        high = range_str[0]
        suited = 's' in range_str
        ranks = '23456789TJQK'
        
        for low in ranks:
            if low != high:
                suffix = 's' if suited else 'o'
                hands.add(high + low + suffix)
    
    def get_optimal_range(self, position: str, situation: str) -> Set[str]:
        """最適レンジを取得"""
        return self.gto_ranges.get((position, situation), set())
    
    def should_play(self, hand: str, position: str, situation: str) -> Dict:
        """ハンドをプレイすべきか判定"""
        optimal_range = self.get_optimal_range(position, situation)
        in_range = hand in optimal_range
        
        descriptor = self.hand_matrix.get(hand)
        
        return {
            'should_play': in_range,
            'strength': descriptor.strength.name if descriptor else 'UNKNOWN',
            'playability': descriptor.playability if descriptor else 0,
            'equity': descriptor.equity_vs_random if descriptor else 0,
            'recommendation': 'PLAY' if in_range else 'FOLD'
        }
    
    def calculate_range_equity(self, my_range: Set[str], 
                              opponent_range: Set[str],
                              board: List[int] = None) -> float:
        """レンジ対レンジのエクイティ"""
        total_equity = 0
        count = 0
        
        for my_hand in my_range:
            for opp_hand in opponent_range:
                # カードの重複チェック
                if self._hands_overlap(my_hand, opp_hand):
                    continue
                
                # 簡易エクイティ計算（実際にはC++呼び出し）
                my_desc = self.hand_matrix.get(my_hand)
                opp_desc = self.hand_matrix.get(opp_hand)
                
                if my_desc and opp_desc:
                    equity = my_desc.equity_vs_random / (my_desc.equity_vs_random + opp_desc.equity_vs_random)
                    total_equity += equity
                    count += 1
        
        return total_equity / count if count > 0 else 0.5
    
    def _hands_overlap(self, hand1: str, hand2: str) -> bool:
        """2つのハンドがカードを共有しているか"""
        # 簡易実装
        return hand1[0] == hand2[0] or hand1[1] == hand2[1]
