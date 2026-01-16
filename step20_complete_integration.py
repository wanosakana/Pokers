# step20_complete_integration.py
from typing import Dict, Optional
from step10_advanced_bridge import OptimizedCppBridge
from step11_12_advanced_range import AdvancedRangeManager
from step13_advanced_hud import AdvancedHUDTracker
from step14_15_advanced_math import AdvancedPotOddsEngine, AdvancedSPRManager
from step16_board_texture_complete import BoardTextureAnalyzer
from step17_exploit_engine_complete import AdvancedExploitEngine
from step18_mixed_strategy_manager import MixedStrategyManager
from step19_realtime_advisor import RealtimeAdvisor

class PokerMasterSystemComplete:
    """完全統合ポーカーシステム"""
    
    def __init__(self, bankroll: float = 10000):
        # コアコンポーネント
        self.cpp_bridge = OptimizedCppBridge()
        self.range_manager = AdvancedRangeManager()
        self.hud_tracker = AdvancedHUDTracker()
        self.board_analyzer = BoardTextureAnalyzer()
        
        # 数学エンジン
        self.pot_odds_engine = AdvancedPotOddsEngine()
        self.spr_manager = AdvancedSPRManager()
        
        # 戦略コンポーネント
        self.exploit_engine = AdvancedExploitEngine(self.hud_tracker)
        self.strategy_manager = MixedStrategyManager(
            self.exploit_engine, 
            self.range_manager
        )
        
        # アドバイザー
        self.advisor = RealtimeAdvisor(self)
        
        # 状態管理
        self.bankroll = bankroll
        self.session_hands = 0
    
    def analyze_situation(self, game_state: Dict) -> Dict:
        """完全な状況分析 - システムの中核"""
        
        # 1. 基本計算（C++エンジン）
        hero_hand = tuple(game_state['my_hand'])
        board = game_state.get('board', [])
        opponents = game_state.get('opponents', 1)
        
        # エクイティ計算
        raw_equity = self.cpp_bridge.calculate_equity_fast(
            hero_hand, board, opponents, 100000
        )
        
        # EQR計算
        position_idx = self._position_to_index(game_state.get('position', 'BTN'))
        opponent_skill = self._estimate_opponent_skill(game_state.get('opponent_id'))
        board_texture_score = self._board_to_texture_score(board)
        
        eqr = self.cpp_bridge.calculate_eqr_complete(
            raw_equity,
            position_idx,
            game_state.get('my_stack', 1000),
            game_state.get('pot', 100),
            board_texture_score,
            opponents,
            game_state.get('in_position', True),
            opponent_skill
        )
        
        # 2. ボード分析
        board_strings = self._cards_to_strings(board)
        board_analysis = self.board_analyzer.analyze_board(board_strings)
        
        # 3. ポットオッズ/SPR
        call_amount = game_state.get('call_amount', 0)
        pot = game_state.get('pot', 100)
        
        pot_odds_result = self.pot_odds_engine.calculate_pot_odds(
            call_amount, pot, game_state.get('my_stack', 1000)
        )
        
        spr_analysis = self.spr_manager.analyze_spr(
            game_state.get('my_stack', 1000),
            pot
        )
        
        # 4. 混合戦略
        situation = {
            'position': game_state.get('position'),
            'equity': eqr,
            'opponent_id': game_state.get('opponent_id'),
            'street': 'flop' if len(board) >= 3 else 'preflop',
            'pot': pot
        }
        
        mixed_strategy = self.strategy_manager.get_mixed_strategy(situation)
        action_dist = self.strategy_manager.get_action_distribution(situation)
        
        # 5. EV計算
        ev_fold = 0
        ev_call = self.pot_odds_engine.calculate_ev_call(
            eqr, pot, call_amount
        )
        ev_raise = self.pot_odds_engine.calculate_ev_raise(
            eqr, pot, call_amount * 3, 
            self._estimate_fold_equity(game_state)
        )
        
        # 最良アクション決定
        evs = {'fold': ev_fold, 'call': ev_call, 'raise': ev_raise}
        best_action = max(evs, key=evs.get)
        best_ev = evs[best_action]
        
        # 6. 推奨サイズ
        recommended_size = self.strategy_manager.recommend_sizing(
            situation, best_action
        )
        
        # 7. エクスプロイト検出
        exploits = []
        if game_state.get('opponent_id'):
            exploits = self.exploit_engine.detect_exploits(game_state['opponent_id'])
        
        # 結果をまとめる
        return {
            'raw_equity': raw_equity,
            'eqr': eqr,
            'pot_odds': pot_odds_result,
            'spr': spr_analysis,
            'board_analysis': board_analysis,
            'mixed_strategy': mixed_strategy,
            'action_distribution': action_dist,
            'ev': {
                'fold': ev_fold,
                'call': ev_call,
                'raise': ev_raise,
                'best': best_ev
            },
            'recommendation': {
                'action': best_action,
                'size': recommended_size,
                'confidence': self._calculate_confidence(evs),
                'exploitative': len(exploits) > 0
            },
            'exploits': exploits[:3],
            'advice': self.advisor.get_comprehensive_advice(game_state)
        }
    
    def _position_to_index(self, position: str) -> int:
        """ポジション文字列をインデックスに"""
        mapping = {
            'UTG': 0, 'UTG+1': 1, 'MP': 3, 'CO': 5, 
            'BTN': 6, 'SB': 7, 'BB': 8
        }
        return mapping.get(position, 6)
    
    def _estimate_opponent_skill(self, opponent_id: Optional[str]) -> float:
        """相手のスキルを推定 (0-1)"""
        if not opponent_id or opponent_id not in self.hud_tracker.players:
            return 0.5
        
        stats = self.hud_tracker.players[opponent_id]
        player_type = stats.classify_player_type()
        
        skill_map = {
            'TAG': 0.8,
            'LAG': 0.75,
            'ROCK': 0.4,
            'FISH': 0.2,
            'MANIAC': 0.3,
            'NIT': 0.35
        }
        
        return skill_map.get(player_type.name, 0.5)
    
    def _board_to_texture_score(self, board: list) -> int:
        """ボードをテクスチャスコアに (0-2)"""
        if len(board) < 3:
            return 0
        
        board_strings = self._cards_to_strings(board)
        analysis = self.board_analyzer.analyze_board(board_strings)
        
        texture_map = {
            'DRY': 0,
            'SEMI_WET': 1,
            'WET': 2,
            'ULTRA_WET': 2
        }
        
        return texture_map.get(analysis.texture.name, 1)
    
    def _cards_to_strings(self, cards: list) -> list:
        """カードIDを文字列に変換"""
        if not cards:
            return []
        
        from step10_advanced_bridge import CardRepresentation
        return [CardRepresentation(c).to_string() for c in cards]
    
    def _estimate_fold_equity(self, game_state: Dict) -> float:
        """フォールドエクイティ推定"""
        opponent_id = game_state.get('opponent_id')
        
        if opponent_id and opponent_id in self.hud_tracker.players:
            stats = self.hud_tracker.players[opponent_id]
            fold_to_cbet = stats.get_fold_to_cbet('flop')
            return fold_to_cbet
        
        return 0.5  # デフォルト
    
    def _calculate_confidence(self, evs: Dict) -> float:
        """判断の信頼度 (0-1)"""
        values = list(evs.values())
        best = max(values)
        second_best = sorted(values, reverse=True)[1]
        
        if second_best == 0:
            return 1.0
        
        return min(1.0, (best - second_best) / abs(best))
    
    def get_formatted_output(self, game_state: Dict) -> str:
        """見やすい出力"""
        analysis = self.analyze_situation(game_state)
        
        lines = []
        lines.append("\n" + "="*80)
        lines.append("🎰 POKER MASTER SYSTEM - COMPLETE ANALYSIS")
        lines.append("="*80)
        
        # エクイティ
        lines.append(f"\n📊 EQUITY ANALYSIS")
        lines.append(f"Raw Equity: {analysis['raw_equity']:.1%}")
        lines.append(f"EQR (Realized): {analysis['eqr']:.1%}")
        
        # EV
        lines.append(f"\n💰 EXPECTED VALUE")
        for action, ev in analysis['ev'].items():
            symbol = "✓" if ev == analysis['ev']['best'] else " "
            lines.append(f"{symbol} {action.capitalize()}: ${ev:+.2f}")
        
        # 推奨アクション
        rec = analysis['recommendation']
        lines.append(f"\n⚡ RECOMMENDATION")
        lines.append(f"Action: {rec['action'].upper()}")
        lines.append(f"Size: ${rec['size']:.2f}")
        lines.append(f"Confidence: {rec['confidence']:.0%}")
        
        # エクスプロイト
        if analysis['exploits']:
            lines.append(f"\n🎯 EXPLOITS DETECTED")
            for exploit in analysis['exploits']:
                lines.append(f"• {exploit.description}")
                lines.append(f"  → {exploit.strategy_adjustment}")
        
        lines.append("\n" + "="*80 + "\n")
        
        return "\n".join(lines)
