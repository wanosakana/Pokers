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
