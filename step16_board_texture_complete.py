# step16_board_texture_complete.py
from typing import List, Dict, Set
from dataclasses import dataclass
from enum import Enum

class BoardType(Enum):
    DRY = "Dry"
    SEMI_WET = "Semi-Wet"
    WET = "Wet"
    ULTRA_WET = "Ultra-Wet"

class DrawType(Enum):
    FLUSH_DRAW = "Flush Draw"
    STRAIGHT_DRAW = "Straight Draw"
    GUTSHOT = "Gutshot"
    COMBO_DRAW = "Combo Draw"

@dataclass
class BoardAnalysis:
    """完全なボード分析結果"""
    texture: BoardType
    connectivity: float  # 0-1
    has_flush_draw: bool
    has_straight_draw: bool
    paired: bool
    trips: bool
    high_cards: int
    draw_types: List[DrawType]
    dangerous_turns: List[str]
    dangerous_rivers: List[str]
    equity_realization_factor: float
    recommended_cbet_frequency: float
    recommended_bet_size: float

class BoardTextureAnalyzer:
    """完全なボードテクスチャ分析"""
    
    def __init__(self):
        self.rank_values = {
            '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8,
            '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14
        }
    
    def analyze_board(self, board: List[str]) -> BoardAnalysis:
        """完全なボード分析"""
        if not board or len(board) < 3:
            return self._empty_analysis()
        
        ranks = [c[0] for c in board]
        suits = [c[1] for c in board]
        rank_values = [self.rank_values[r] for r in ranks]
        
        # 基本情報
        paired = len(ranks) != len(set(ranks))
        trips = any(ranks.count(r) >= 3 for r in ranks)
        high_cards = sum(1 for r in rank_values if r >= 10)
        
        # フラッシュドロー
        suit_counts = {s: suits.count(s) for s in set(suits)}
        has_flush_draw = max(suit_counts.values()) >= 2
        
        # ストレートドロー検出
        has_straight_draw, draw_types = self._analyze_straight_draws(rank_values)
        
        # コネクティビティ（連続性）
        connectivity = self._calculate_connectivity(rank_values)
        
        # テクスチャ分類
        texture = self._classify_texture(
            connectivity, has_flush_draw, has_straight_draw, paired
        )
        
        # 危険なカード
        dangerous_turns = self._calculate_dangerous_cards(board, len(board) == 3)
        dangerous_rivers = self._calculate_dangerous_cards(board, len(board) == 4)
        
        # EQR係数
        eqr_factor = self._calculate_eqr_factor(texture, paired)
        
        # 推奨戦略
        cbet_freq = self._recommend_cbet_frequency(texture, paired)
        bet_size = self._recommend_bet_size(texture, paired)
        
        return BoardAnalysis(
            texture=texture,
            connectivity=connectivity,
            has_flush_draw=has_flush_draw,
            has_straight_draw=has_straight_draw,
            paired=paired,
            trips=trips,
            high_cards=high_cards,
            draw_types=draw_types,
            dangerous_turns=dangerous_turns,
            dangerous_rivers=dangerous_rivers,
            equity_realization_factor=eqr_factor,
            recommended_cbet_frequency=cbet_freq,
            recommended_bet_size=bet_size
        )
    
    def _analyze_straight_draws(self, rank_values: List[int]) -> Tuple[bool, List[DrawType]]:
        """ストレートドロー分析"""
        sorted_ranks = sorted(set(rank_values))
        draw_types = []
        
        # OESD (Open-Ended Straight Draw)
        for i in range(len(sorted_ranks) - 1):
            if sorted_ranks[i+1] - sorted_ranks[i] <= 2:
                draw_types.append(DrawType.STRAIGHT_DRAW)
                break
        
        # ガットショット
        for i in range(len(sorted_ranks) - 1):
            if sorted_ranks[i+1] - sorted_ranks[i] == 3:
                draw_types.append(DrawType.GUTSHOT)
        
        return len(draw_types) > 0, draw_types
    
    def _calculate_connectivity(self, rank_values: List[int]) -> float:
        """連続性スコア (0-1)"""
        if len(rank_values) < 2:
            return 0.0
        
        sorted_ranks = sorted(rank_values)
        gaps = [sorted_ranks[i+1] - sorted_ranks[i] for i in range(len(sorted_ranks) - 1)]
        
        # ギャップが小さいほどコネクティビティが高い
        avg_gap = sum(gaps) / len(gaps)
        connectivity = 1.0 / (1.0 + avg_gap - 1.0)
        
        return min(1.0, connectivity)
    
    def _classify_texture(self, connectivity: float, has_flush: bool,
                         has_straight: bool, paired: bool) -> BoardType:
        """テクスチャ分類"""
        score = 0
        
        if connectivity > 0.7:
            score += 2
        elif connectivity > 0.5:
            score += 1
        
        if has_flush:
            score += 1
        if has_straight:
            score += 1
        if paired:
            score -= 1
        
        if score >= 3:
            return BoardType.ULTRA_WET
        elif score >= 2:
            return BoardType.WET
        elif score >= 1:
            return BoardType.SEMI_WET
        else:
            return BoardType.DRY
    
    def _calculate_dangerous_cards(self, board: List[str], 
                                   is_turn: bool) -> List[str]:
        """危険なカードを計算"""
        ranks = [c[0] for c in board]
        suits = [c[1] for c in board]
        
        dangerous = []
        
        # フラッシュ完成
        for suit in set(suits):
            if suits.count(suit) >= (2 if is_turn else 3):
                dangerous.append(f"Any {suit}")
        
        # ストレート完成の可能性
        rank_values = sorted([self.rank_values[r] for r in ranks])
        for r in range(2, 15):
            if self._completes_straight(rank_values, r):
                for rank_str, val in self.rank_values.items():
                    if val == r:
                        dangerous.append(rank_str)
        
        return dangerous
    
    def _completes_straight(self, rank_values: List[int], new_rank: int) -> bool:
        """ストレートが完成するか"""
        all_ranks = sorted(rank_values + [new_rank])
        for i in range(len(all_ranks) - 4):
            if all_ranks[i+4] - all_ranks[i] == 4:
                return True
        return False
    
    def _calculate_eqr_factor(self, texture: BoardType, paired: bool) -> float:
        """EQR係数"""
        base = {
            BoardType.DRY: 1.05,
            BoardType.SEMI_WET: 1.00,
            BoardType.WET: 0.95,
            BoardType.ULTRA_WET: 0.90
        }[texture]
        
        if paired:
            base *= 1.02
        
        return base
    
    def _recommend_cbet_frequency(self, texture: BoardType, paired: bool) -> float:
        """推奨CBet頻度"""
        base = {
            BoardType.DRY: 0.75,
            BoardType.SEMI_WET: 0.65,
            BoardType.WET: 0.55,
            BoardType.ULTRA_WET: 0.45
        }[texture]
        
        if paired:
            base += 0.05
        
        return base
    
    def _recommend_bet_size(self, texture: BoardType, paired: bool) -> float:
        """推奨ベットサイズ（ポット比）"""
        base = {
            BoardType.DRY: 0.33,
            BoardType.SEMI_WET: 0.50,
            BoardType.WET: 0.66,
            BoardType.ULTRA_WET: 0.75
        }[texture]
        
        return base
    
    def _empty_analysis(self) -> BoardAnalysis:
        """空のボード分析"""
        return BoardAnalysis(
            texture=BoardType.DRY,
            connectivity=0.0,
            has_flush_draw=False,
            has_straight_draw=False,
            paired=False,
            trips=False,
            high_cards=0,
            draw_types=[],
            dangerous_turns=[],
            dangerous_rivers=[],
            equity_realization_factor=1.0,
            recommended_cbet_frequency=0.66,
            recommended_bet_size=0.5
        )
