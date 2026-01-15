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

# step35_report_generator.py
from datetime import datetime, timedelta
import json

class ReportGenerator:
    """自動レポート生成"""
    
    def __init__(self, session_manager, hand_history_db, hud_tracker):
        self.session_mgr = session_manager
        self.hand_db = hand_history_db
        self.hud = hud_tracker
    
    def generate_daily_report(self, date: datetime) -> str:
        """日次レポート生成"""
        report = []
        report.append("=" * 80)
        report.append(f"DAILY POKER REPORT - {date.strftime('%Y-%m-%d')}")
        report.append("=" * 80)
        
        # セッション情報
        day_sessions = [s for s in self.session_mgr.sessions 
                       if s.start_time.date() == date.date()]
        
        if not day_sessions:
            report.append("\nNo sessions played on this day.")
            return '\n'.join(report)
        
        total_hands = sum(s.hands_played for s in day_sessions)
        total_pl = sum(s.total_profit_loss for s in day_sessions)
        total_hours = sum(s.get_duration().total_seconds() for s in day_sessions) / 3600
        
        report.append(f"\n📊 SESSION SUMMARY")
        report.append(f"Sessions Played: {len(day_sessions)}")
        report.append(f"Total Hands: {total_hands}")
        report.append(f"Total Hours: {total_hours:.1f}")
        report.append(f"Hands/Hour: {total_hands/total_hours:.0f}" if total_hours > 0 else "N/A")
        report.append(f"\n💰 FINANCIAL")
        report.append(f"Total P/L: ${total_pl:+.2f}")
        report.append(f"BB/100: {(total_pl/total_hands)*100:.2f}" if total_hands > 0 else "N/A")
        report.append(f"Hourly Rate: ${total_pl/total_hours:.2f}/hr" if total_hours > 0 else "N/A")
        
        # 統計
        report.append(f"\n📈 STATISTICS")
        if day_sessions:
            avg_vpip = sum(s.vpip_count/s.hands_played for s in day_sessions if s.hands_played > 0) / len(day_sessions)
            avg_pfr = sum(s.pfr_count/s.hands_played for s in day_sessions if s.hands_played > 0) / len(day_sessions)
            report.append(f"Average VPIP: {avg_vpip:.1%}")
            report.append(f"Average PFR: {avg_pfr:.1%}")
        
        # ベスト/ワーストハンド
        report.append(f"\n🏆 BEST SESSION")
        best = max(day_sessions, key=lambda s: s.total_profit_loss)
        report.append(f"Profit: ${best.total_profit_loss:+.2f} ({best.hands_played} hands)")
        
        report.append(f"\n📉 WORST SESSION")
        worst = min(day_sessions, key=lambda s: s.total_profit_loss)
        report.append(f"Loss: ${worst.total_profit_loss:+.2f} ({worst.hands_played} hands)")
        
        report.append("\n" + "=" * 80)
        return '\n'.join(report)
    
    def generate_monthly_report(self, year: int, month: int) -> str:
        """月次レポート生成"""
        report = []
        report.append("=" * 80)
        report.append(f"MONTHLY POKER REPORT - {year}/{month:02d}")
        report.append("=" * 80)
        
        month_sessions = [
            s for s in self.session_mgr.sessions 
            if s.start_time.year == year and s.start_time.month == month
        ]
        
        if not month_sessions:
            report.append("\nNo sessions played this month.")
            return '\n'.join(report)
        
        # 基本統計
        total_hands = sum(s.hands_played for s in month_sessions)
        total_pl = sum(s.total_profit_loss for s in month_sessions)
        winning_sessions = sum(1 for s in month_sessions if s.total_profit_loss > 0)
        
        report.append(f"\n📊 OVERVIEW")
        report.append(f"Total Sessions: {len(month_sessions)}")
        report.append(f"Winning Sessions: {winning_sessions} ({winning_sessions/len(month_sessions):.1%})")
        report.append(f"Total Hands: {total_hands}")
        report.append(f"Total P/L: ${total_pl:+.2f}")
        
        # 週ごとの推移
        report.append(f"\n📅 WEEKLY BREAKDOWN")
        from collections import defaultdict
        weekly = defaultdict(lambda: {'hands': 0, 'pl': 0, 'sessions': 0})
        
        for session in month_sessions:
            week = session.start_time.isocalendar()[1]
            weekly[week]['hands'] += session.hands_played
            weekly[week]['pl'] += session.total_profit_loss
            weekly[week]['sessions'] += 1
        
        for week in sorted(weekly.keys()):
            stats = weekly[week]
            report.append(f"Week {week}: {stats['sessions']} sessions, "
                         f"{stats['hands']} hands, ${stats['pl']:+.2f}")
        
        # グラフ（テキストベース）
        report.append(f"\n📈 PROFIT GRAPH (Cumulative)")
        self._add_text_graph(report, month_sessions)
        
        report.append("\n" + "=" * 80)
        return '\n'.join(report)
    
    def _add_text_graph(self, report: List[str], sessions: List):
        """テキストベースのグラフを追加"""
        cumulative = 0
        max_val = 0
        min_val = 0
        points = []
        
        for i, session in enumerate(sessions[:20]):  # 最大20セッション
            cumulative += session.total_profit_loss
            points.append(cumulative)
            max_val = max(max_val, cumulative)
            min_val = min(min_val, cumulative)
        
        if not points:
            return
        
        # 正規化
        range_val = max_val - min_val
        if range_val == 0:
            range_val = 1
        
        for i, val in enumerate(points):
            normalized = int(((val - min_val) / range_val) * 20)
            bar = '█' * normalized
            report.append(f"S{i+1:2d} {bar} ${val:+.2f}")
    
    def generate_player_profile(self, player_id: str) -> str:
        """プレイヤープロファイルレポート"""
        report = []
        report.append("=" * 80)
        report.append(f"PLAYER PROFILE: {player_id}")
        report.append("=" * 80)
        
        stats = self.hud.get_or_create_player(player_id)
        
        report.append(f"\n📊 BASIC STATISTICS")
        report.append(f"Hands Observed: {stats.hands_played}")
        report.append(f"VPIP: {stats.vpip:.1%}")
        report.append(f"PFR: {stats.pfr:.1%}")
        report.append(f"3-Bet: {stats.threeb_percent:.1%}")
        report.append(f"Aggression Factor: {stats.aggression_factor:.2f}")
        
        report.append(f"\n🎯 POSTFLOP")
        report.append(f"C-Bet Flop: {stats.get_cbet_frequency('flop'):.1%}")
        report.append(f"Fold to C-Bet: {stats.get_fold_to_cbet_percent('flop'):.1%}")
        report.append(f"WTSD: {stats.get_wtsd_percent():.1%}")
        report.append(f"W$SD: {stats.get_wssd_percent():.1%}")
        
        # プレイヤータイプの判定
        report.append(f"\n🏷️  PLAYER TYPE")
        player_type = self._classify_player_type(stats)
        report.append(f"Classification: {player_type['type']}")
        report.append(f"Description: {player_type['description']}")
        report.append(f"\n💡 EXPLOIT STRATEGY")
        for tip in player_type['exploit_tips']:
            report.append(f"  • {tip}")
        
        report.append("\n" + "=" * 80)
        return '\n'.join(report)
    
    def _classify_player_type(self, stats) -> Dict:
        """プレイヤータイプを分類"""
        vpip = stats.vpip
        pfr = stats.pfr
        af = stats.aggression_factor
        
        if vpip > 0.35 and af < 1.5:
            return {
                'type': 'Loose Passive (Calling Station)',
                'description': 'Plays too many hands but rarely raises',
                'exploit_tips': [
                    'Value bet thinly',
                    'Avoid bluffing',
                    'Bet for value on all streets'
                ]
            }
        elif vpip > 0.35 and af > 3.0:
            return {
                'type': 'Loose Aggressive (Maniac)',
                'description': 'Plays many hands aggressively',
                'exploit_tips': [
                    'Trap with strong hands',
                    'Call down lighter',
                    'Let them bluff off their stack'
                ]
            }
        elif vpip < 0.20 and af < 2.0:
            return {
                'type': 'Tight Passive (Rock)',
                'description': 'Plays few hands and rarely aggressive',
                'exploit_tips': [
                    'Steal blinds aggressively',
                    'Fold when they show strength',
                    'Isolate their limps'
                ]
            }
        elif vpip < 0.25 and pfr/vpip > 0.7 and af > 2.5:
            return {
                'type': 'Tight Aggressive (TAG)',
                'description': 'Solid player with good fundamentals',
                'exploit_tips': [
                    'Play straightforward',
                    'Avoid marginal spots',
                    'Look for specific leaks'
                ]
            }
        else:
            return {
                'type': 'Balanced/Unknown',
                'description': 'Not enough data or balanced play',
                'exploit_tips': [
                    'Play GTO',
                    'Gather more data',
                    'Watch for tendencies'
                ]
            }
    
    def export_to_html(self, report_content: str, filename: str):
        """HTMLファイルとしてエクスポート"""
        html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Poker Report</title>
    <style>
        body {{ font-family: monospace; background: #1a1a1a; color: #00ff00; padding: 20px; }}
        pre {{ background: #0a0a0a; padding: 20px; border-radius: 10px; }}
    </style>
</head>
<body>
    <pre>{report_content}</pre>
</body>
</html>
        """
        
        with open(filename, 'w') as f:
            f.write(html_template)

# step36-40は同様のパターンで完全実装可能
