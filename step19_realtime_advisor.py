# step19_realtime_advisor.py
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class AdviceItem:
    """アドバイス項目"""
    priority: int  # 1=highest
    category: str
    message: str
    reasoning: str
    ev_impact: float

class RealtimeAdvisor:
    """リアルタイム意思決定アドバイザー"""
    
    def __init__(self, poker_system):
        self.system = poker_system
    
    def get_comprehensive_advice(self, game_state: Dict) -> List[AdviceItem]:
        """包括的なアドバイスを生成"""
        advice = []
        
        # 基本分析を実行
        analysis = self.system.analyze_situation(game_state)
        
        # 1. アクション推奨
        advice.append(self._generate_action_advice(analysis, game_state))
        
        # 2. サイジング推奨
        if analysis['recommendation']['action'] in ['raise', 'bet']:
            advice.append(self._generate_sizing_advice(analysis, game_state))
        
        # 3. エクスプロイト機会
        if game_state.get('opponent_id'):
            advice.extend(self._generate_exploit_advice(game_state))
        
        # 4. リスク警告
        advice.extend(self._generate_risk_warnings(analysis, game_state))
        
        # 5. ポジションアドバイス
        advice.append(self._generate_position_advice(game_state))
        
        # 優先度でソート
        advice.sort(key=lambda x: x.priority)
        
        return advice
    
    def _generate_action_advice(self, analysis: Dict, 
                                game_state: Dict) -> AdviceItem:
        """アクション推奨"""
        rec = analysis['recommendation']
        action = rec['action']
        confidence = rec.get('confidence', 0.5)
        
        reasoning = []
        
        # エクイティベース
        equity = analysis.get('raw_equity', 0)
        reasoning.append(f"Equity: {equity:.1%}")
        
        # EVベース
        ev = analysis.get('ev', 0)
        reasoning.append(f"EV: ${ev:+.2f}")
        
        # 戦略タイプ
        if rec.get('exploitative'):
            reasoning.append("Exploiting opponent weakness")
        else:
            reasoning.append("GTO-based decision")
        
        message = f"{'⚡ ' if confidence > 0.8 else ''}RECOMMENDED: {action.upper()}"
        
        return AdviceItem(
            priority=1,
            category="Action",
            message=message,
            reasoning=" | ".join(reasoning),
            ev_impact=ev
        )
    
    def _generate_sizing_advice(self, analysis: Dict, 
                                game_state: Dict) -> AdviceItem:
        """サイジング推奨"""
        rec = analysis['recommendation']
        size = rec.get('size', game_state['pot'] * 0.66)
        pot = game_state['pot']
        
        pot_percent = (size / pot) * 100
        
        reasoning = []
        
        # サイズの理由
        if pot_percent < 40:
            reasoning.append("Small sizing for thin value/inducing")
        elif pot_percent < 70:
            reasoning.append("Standard sizing for balanced range")
        else:
            reasoning.append("Large sizing for polarized/protection")
        
        # ボードテクスチャ
        board_texture = analysis.get('board_texture', {})
        if board_texture.get('texture') == 'wet':
            reasoning.append("Wet board - larger size recommended")
        
        return AdviceItem(
            priority=2,
            category="Sizing",
            message=f"Size: ${size:.2f} ({pot_percent:.0f}% pot)",
            reasoning=" | ".join(reasoning),
            ev_impact=0
        )
    
    def _generate_exploit_advice(self, game_state: Dict) -> List[AdviceItem]:
        """エクスプロイトアドバイス"""
        advice = []
        opponent_id = game_state['opponent_id']
        
        exploits = self.system.exploit_engine.detect_exploits(opponent_id)
        
        for i, exploit in enumerate(exploits[:2]):
            advice.append(AdviceItem(
                priority=3 + i,
                category="Exploit",
                message=f"🎯 {exploit.exploit_type.value}",
                reasoning=exploit.strategy_adjustment,
                ev_impact=exploit.expected_ev_gain
            ))
        
        return advice
    
    def _generate_risk_warnings(self, analysis: Dict, 
                               game_state: Dict) -> List[AdviceItem]:
        """リスク警告"""
        warnings = []
        
        # バンクロールリスク
        bankroll = game_state.get('bankroll', float('inf'))
        pot = game_state.get('pot', 0)
        
        if pot > bankroll * 0.1:
            warnings.append(AdviceItem(
                priority=5,
                category="Risk",
                message="⚠️ Pot is >10% of bankroll",
                reasoning="Consider folding marginal hands to protect bankroll",
                ev_impact=-10.0
            ))
        
        # ティルトリスク
        if hasattr(self.system, 'tilt_detector'):
            tilt_score = self.system.tilt_detector.calculate_tilt_score()
            if tilt_score.get('tilt_score', 0) > 0.5:
                warnings.append(AdviceItem(
                    priority=1,
                    category="Risk",
                    message=f"🚨 TILT WARNING: {tilt_score['level']}",
                    reasoning=tilt_score['recommendation'],
                    ev_impact=-20.0
                ))
        
        return warnings
    
    def _generate_position_advice(self, game_state: Dict) -> AdviceItem:
        """ポジションアドバイス"""
        position = game_state.get('position', 'BTN')
        
        advice_map = {
            'UTG': "Early position - Play tight, strong hands only",
            'MP': "Middle position - Standard ranges",
            'CO': "Late position - Widen ranges slightly",
            'BTN': "Button - Maximum position advantage, play wide",
            'SB': "Small blind - Difficult position, play carefully",
            'BB': "Big blind - Already invested, defend wide vs steals"
        }
        
        return AdviceItem(
            priority=6,
            category="Position",
            message=f"Position: {position}",
            reasoning=advice_map.get(position, "Standard play"),
            ev_impact=0
        )
    
    def format_advice_display(self, advice: List[AdviceItem]) -> str:
        """アドバイスを見やすくフォーマット"""
        lines = []
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("🎯 POKER MASTER ADVISOR")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        for item in advice:
            lines.append(f"\n[{item.category}] {item.message}")
            lines.append(f"  → {item.reasoning}")
            if item.ev_impact != 0:
                lines.append(f"  💰 EV Impact: ${item.ev_impact:+.2f}")
        
        lines.append("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        return "\n".join(lines)
