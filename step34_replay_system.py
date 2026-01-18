# step34_replay_system.py
from typing import List, Dict, Optional
import time

class HandReplayer:
    """ハンドのリプレイと詳細分析"""
    
    def __init__(self, hand_history_db):
        self.db = hand_history_db
        self.replay_speed = 1.0  # 再生速度
    
    def replay_hand(self, hand_id: str, analyze: bool = True) -> Dict:
        """ハンドを再生"""
        hand_data = self.db.get_hand(hand_id)
        if not hand_data:
            return {'error': 'Hand not found'}
        
        replay_log = []
        analysis = {}
        
        # プリフロップ
        replay_log.append(f"\n{'='*60}")
        replay_log.append(f"Hand ID: {hand_id}")
        replay_log.append(f"Position: {hand_data['position']}")
        replay_log.append(f"Hole Cards: {hand_data['hole_cards']}")
        replay_log.append(f"{'='*60}\n")
        
        # 各ストリートを再生
        streets = ['preflop', 'flop', 'turn', 'river']
        for street in streets:
            street_actions = [a for a in hand_data.get('actions', []) if a['street'] == street]
            if not street_actions:
                continue
            
            replay_log.append(f"\n--- {street.upper()} ---")
            
            if street == 'flop' and len(hand_data['board']) >= 3:
                replay_log.append(f"Board: {hand_data['board'][:3]}")
            elif street == 'turn' and len(hand_data['board']) >= 4:
                replay_log.append(f"Board: {hand_data['board'][:4]}")
            elif street == 'river' and len(hand_data['board']) >= 5:
                replay_log.append(f"Board: {hand_data['board']}")
            
            for action in street_actions:
                action_str = f"{action['type']}"
                if action.get('amount', 0) > 0:
                    action_str += f" ${action['amount']:.2f}"
                action_str += f" (Pot: ${action['pot_after']:.2f})"
                replay_log.append(action_str)
                
                time.sleep(0.5 / self.replay_speed)  # アニメーション効果
            
            # 分析を追加
            if analyze:
                street_analysis = self._analyze_street(hand_data, street)
                if street_analysis:
                    replay_log.append(f"\n📊 Analysis:")
                    for key, value in street_analysis.items():
                        replay_log.append(f"  {key}: {value}")
        
        # 結果
        replay_log.append(f"\n{'='*60}")
        replay_log.append(f"Result: {'WON' if hand_data['won'] else 'LOST'}")
        replay_log.append(f"P/L: ${hand_data['profit_loss']:+.2f}")
        replay_log.append(f"{'='*60}\n")
        
        return {
            'replay_log': '\n'.join(replay_log),
            'hand_data': hand_data,
            'analysis': analysis
        }
    
    def _analyze_street(self, hand_data: Dict, street: str) -> Dict:
        """各ストリートの分析"""
        analysis = {}
        
        if street == 'preflop':
            analysis['Position'] = hand_data['position']
            analysis['Equity'] = f"{hand_data.get('equity', 0):.1%}"
        
        elif street == 'flop':
            analysis['Board Texture'] = self._analyze_board_texture(hand_data['board'][:3])
            analysis['EQR'] = f"{hand_data.get('eqr', 0):.1%}"
        
        return analysis
    
    def _analyze_board_texture(self, board: List) -> str:
        """ボードテクスチャの簡易分析"""
        if len(board) < 3:
            return "N/A"
        # 簡易的な判定
        return "Wet" if len(set(board)) == 3 else "Paired"
    
    def compare_hands(self, hand_ids: List[str]) -> Dict:
        """複数のハンドを比較"""
        hands = [self.db.get_hand(hid) for hid in hand_ids]
        hands = [h for h in hands if h]
        
        if not hands:
            return {}
        
        comparison = {
            'total_hands': len(hands),
            'avg_profit': sum(h['profit_loss'] for h in hands) / len(hands),
            'win_rate': sum(1 for h in hands if h['won']) / len(hands),
            'avg_equity': sum(h.get('equity', 0) for h in hands) / len(hands),
            'by_position': {}
        }
        
        # ポジション別
        from collections import defaultdict
        pos_stats = defaultdict(lambda: {'count': 0, 'profit': 0, 'wins': 0})
        
        for hand in hands:
            pos = hand['position']
            pos_stats[pos]['count'] += 1
            pos_stats[pos]['profit'] += hand['profit_loss']
            pos_stats[pos]['wins'] += 1 if hand['won'] else 0
        
        for pos, stats in pos_stats.items():
            comparison['by_position'][pos] = {
                'hands': stats['count'],
                'avg_profit': stats['profit'] / stats['count'],
                'win_rate': stats['wins'] / stats['count']
            }
        
        return comparison
    
    def find_mistakes(self, hand_id: str) -> List[Dict]:
        """ハンド内のミスを検出"""
        hand_data = self.db.get_hand(hand_id)
        if not hand_data:
            return []
        
        mistakes = []
        
        # GTOからの逸脱をチェック
        if hand_data.get('gto_action') and hand_data.get('actual_action'):
            if hand_data['gto_action'] != hand_data['actual_action']:
                ev_loss = hand_data.get('gto_ev', 0) - hand_data.get('actual_ev', 0)
                if ev_loss > 5:  # 5BB以上の損失
                    mistakes.append({
                        'type': 'GTO Deviation',
                        'severity': 'high' if ev_loss > 20 else 'medium',
                        'description': f"Chose {hand_data['actual_action']} instead of {hand_data['gto_action']}",
                        'cost': f"{ev_loss:.2f} BB"
                    })
        
        return mistakes

