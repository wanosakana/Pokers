# step13_advanced_hud.py
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from collections import deque
from enum import Enum
import statistics

class PlayerType(Enum):
    UNKNOWN = "Unknown"
    TAG = "Tight-Aggressive"
    LAG = "Loose-Aggressive"
    ROCK = "Tight-Passive (Rock)"
    FISH = "Loose-Passive (Calling Station)"
    MANIAC = "Hyper-Aggressive"
    NIT = "Ultra-Tight"

@dataclass
class AdvancedPlayerStats:
    """高度なプレイヤー統計"""
    
    # 基本スタッツ
    hands_played: int = 0
    vpip_count: int = 0
    pfr_count: int = 0
    threeb_count: int = 0
    threeb_opportunities: int = 0
    fourb_count: int = 0
    
    # ポジション別VPIP
    vpip_by_position: Dict[str, List[bool]] = field(default_factory=lambda: {
        'UTG': [], 'MP': [], 'CO': [], 'BTN': [], 'SB': [], 'BB': []
    })
    
    # アグレッション
    preflop_raises: int = 0
    postflop_bets: int = 0
    postflop_raises: int = 0
    postflop_calls: int = 0
    postflop_folds: int = 0
    
    # CBet統計（詳細）
    cbet_opportunities: Dict[str, int] = field(default_factory=lambda: {
        'flop': 0, 'turn': 0, 'river': 0
    })
    cbet_made: Dict[str, int] = field(default_factory=lambda: {
        'flop': 0, 'turn': 0, 'river': 0
    })
    
    # Fold to CBet
    faced_cbet: Dict[str, int] = field(default_factory=lambda: {
        'flop': 0, 'turn': 0, 'river': 0
    })
    folded_to_cbet: Dict[str, int] = field(default_factory=lambda: {
        'flop': 0, 'turn': 0, 'river': 0
    })
    
    # ショーダウン
    showdowns: int = 0
    showdowns_won: int = 0
    went_to_showdown: int = 0
    
    # ベットサイジング
    bet_sizes: deque = field(default_factory=lambda: deque(maxlen=100))
    raise_sizes: deque = field(default_factory=lambda: deque(maxlen=100))
    
    # レンジ推定用
    shown_hands: List[str] = field(default_factory=list)
    
    # タイミングテル
    fast_actions: int = 0
    slow_actions: int = 0
    action_times: deque = field(default_factory=lambda: deque(maxlen=100))
    
    @property
    def vpip(self) -> float:
        return self.vpip_count / self.hands_played if self.hands_played > 0 else 0
    
    @property
    def pfr(self) -> float:
        return self.pfr_count / self.hands_played if self.hands_played > 0 else 0
    
    @property
    def threeb_percent(self) -> float:
        return self.threeb_count / self.threeb_opportunities if self.threeb_opportunities > 0 else 0
    
    @property
    def aggression_factor(self) -> float:
        """アグレッションファクター: (Bet+Raise)/Call"""
        aggressive = self.postflop_bets + self.postflop_raises
        if self.postflop_calls == 0:
            return aggressive if aggressive > 0 else 0
        return aggressive / self.postflop_calls
    
    @property
    def aggression_frequency(self) -> float:
        """アグレッション頻度: (Bet+Raise)/(Bet+Raise+Call+Fold)"""
        total = self.postflop_bets + self.postflop_raises + self.postflop_calls + self.postflop_folds
        if total == 0:
            return 0
        return (self.postflop_bets + self.postflop_raises) / total
    
    def get_cbet_frequency(self, street: str) -> float:
        """CBet頻度"""
        if self.cbet_opportunities[street] == 0:
            return 0
        return self.cbet_made[street] / self.cbet_opportunities[street]
    
    def get_fold_to_cbet(self, street: str) -> float:
        """CBetへのフォールド率"""
        if self.faced_cbet[street] == 0:
            return 0
        return self.folded_to_cbet[street] / self.faced_cbet[street]
    
    def get_wtsd(self) -> float:
        """Went To ShowDown"""
        if self.vpip_count == 0:
            return 0
        return self.went_to_showdown / self.vpip_count
    
    def get_wssd(self) -> float:
        """Won $ at ShowDown"""
        if self.showdowns == 0:
            return 0
        return self.showdowns_won / self.showdowns
    
    def get_average_bet_size(self) -> float:
        """平均ベットサイズ（ポット比）"""
        if not self.bet_sizes:
            return 0
        return statistics.mean(self.bet_sizes)
    
    def get_position_vpip(self, position: str) -> float:
        """ポジション別VPIP"""
        if position not in self.vpip_by_position:
            return 0
        actions = self.vpip_by_position[position]
        if not actions:
            return 0
        return sum(actions) / len(actions)
    
    def classify_player_type(self) -> PlayerType:
        """プレイヤータイプの分類"""
        if self.hands_played < 30:
            return PlayerType.UNKNOWN
        
        vpip = self.vpip
        pfr = self.pfr
        af = self.aggression_factor
        
        # 分類ロジック
        if vpip < 0.15:
            return PlayerType.NIT
        elif vpip < 0.20 and pfr / vpip > 0.7 and af > 2.5:
            return PlayerType.TAG
        elif vpip > 0.35 and af > 3.5:
            return PlayerType.MANIAC
        elif vpip > 0.35 and af < 1.5:
            return PlayerType.FISH
        elif vpip > 0.28 and pfr / vpip > 0.65 and af > 2.0:
            return PlayerType.LAG
        elif vpip < 0.25 and af < 1.5:
            return PlayerType.ROCK
        else:
            return PlayerType.UNKNOWN

class AdvancedHUDTracker:
    """高度なHUDトラッキングシステム"""
    
    def __init__(self):
        self.players: Dict[str, AdvancedPlayerStats] = {}
        self.session_hands = 0
    
    def get_or_create_player(self, player_id: str) -> AdvancedPlayerStats:
        if player_id not in self.players:
            self.players[player_id] = AdvancedPlayerStats()
        return self.players[player_id]
    
    def record_preflop_action(self, player_id: str, action: str, 
                             position: str, facing_raise: bool = False):
        """プリフロップアクションを記録"""
        stats = self.get_or_create_player(player_id)
        stats.hands_played += 1
        
        vpip_action = action in ['call', 'raise', 'bet']
        
        if vpip_action:
            stats.vpip_count += 1
            stats.vpip_by_position[position].append(True)
        else:
            stats.vpip_by_position[position].append(False)
        
        if action in ['raise', 'bet']:
            stats.pfr_count += 1
            stats.preflop_raises += 1
        
        if facing_raise:
            stats.threeb_opportunities += 1
            if action == 'raise':
                stats.threeb_count += 1
    
    def record_postflop_action(self, player_id: str, action: str, 
                              street: str, amount: float = 0, 
                              pot: float = 1, is_aggressor: bool = False):
        """ポストフロップアクションを記録"""
        stats = self.get_or_create_player(player_id)
        
        if action == 'bet':
            stats.postflop_bets += 1
            if amount > 0 and pot > 0:
                stats.bet_sizes.append(amount / pot)
        elif action == 'raise':
            stats.postflop_raises += 1
            if amount > 0 and pot > 0:
                stats.raise_sizes.append(amount / pot)
        elif action == 'call':
            stats.postflop_calls += 1
        elif action == 'fold':
            stats.postflop_folds += 1
    
    def record_cbet(self, player_id: str, street: str, made_cbet: bool):
        """CBetを記録"""
        stats = self.get_or_create_player(player_id)
        stats.cbet_opportunities[street] += 1
        if made_cbet:
            stats.cbet_made[street] += 1
    
    def record_faced_cbet(self, player_id: str, street: str, folded: bool):
        """CBetに直面した際の行動を記録"""
        stats = self.get_or_create_player(player_id)
        stats.faced_cbet[street] += 1
        if folded:
            stats.folded_to_cbet[street] += 1
    
    def record_showdown(self, player_id: str, won: bool, hand: str = None):
        """ショーダウンを記録"""
        stats = self.get_or_create_player(player_id)
        stats.showdowns += 1
        stats.went_to_showdown += 1
        if won:
            stats.showdowns_won += 1
        if hand:
            stats.shown_hands.append(hand)
    
    def record_action_timing(self, player_id: str, time_seconds: float):
        """アクション時間を記録"""
        stats = self.get_or_create_player(player_id)
        stats.action_times.append(time_seconds)
        
        if time_seconds < 2.0:
            stats.fast_actions += 1
        elif time_seconds > 10.0:
            stats.slow_actions += 1
    
    def get_player_summary(self, player_id: str) -> Dict:
        """プレイヤーサマリーを取得"""
        if player_id not in self.players:
            return {'error': 'Player not found'}
        
        stats = self.players[player_id]
        player_type = stats.classify_player_type()
        
        return {
            'player_id': player_id,
            'hands': stats.hands_played,
            'type': player_type.value,
            'vpip': f"{stats.vpip:.1%}",
            'pfr': f"{stats.pfr:.1%}",
            '3bet': f"{stats.threeb_percent:.1%}",
            'af': f"{stats.aggression_factor:.2f}",
            'agg_freq': f"{stats.aggression_frequency:.1%}",
            'cbet_flop': f"{stats.get_cbet_frequency('flop'):.1%}",
            'fold_to_cbet_flop': f"{stats.get_fold_to_cbet('flop'):.1%}",
            'wtsd': f"{stats.get_wtsd():.1%}",
            'wssd': f"{stats.get_wssd():.1%}",
            'avg_bet_size': f"{stats.get_average_bet_size():.2f}x pot"
        }
    
    def detect_patterns(self, player_id: str) -> List[str]:
        """プレイパターンを検出"""
        if player_id not in self.players:
            return []
        
        stats = self.players[player_id]
        patterns = []
        
        # ポジション別の傾向
        btn_vpip = stats.get_position_vpip('BTN')
        utg_vpip = stats.get_position_vpip('UTG')
        if btn_vpip > utg_vpip * 2:
            patterns.append("Position-aware (Steals from button)")
        
        # CBet傾向
        if stats.get_cbet_frequency('flop') > 0.8:
            patterns.append("High CBet frequency (exploitable with check-raises)")
        elif stats.get_cbet_frequency('flop') < 0.5:
            patterns.append("Low CBet frequency (can float more)")
        
        # Fold to CBet
        if stats.get_fold_to_cbet('flop') > 0.7:
            patterns.append("Overfolds to CBets (CBet 100%)")
        
        # タイミングテル
        if stats.action_times:
            avg_time = statistics.mean(stats.action_times)
            if stats.fast_actions / len(stats.action_times) > 0.7:
                patterns.append("Fast player (likely auto-actions)")
        
        # アグレッション
        if stats.aggression_factor > 4.0:
            patterns.append("Hyper-aggressive (trap with strong hands)")
        elif stats.aggression_factor < 1.0:
            patterns.append("Passive (can bluff more)")
        
        return patterns
