

# step40_dashboard.py
class IntegratedDashboard:
    """統合ダッシュボード - 全機能へのアクセスポイント"""
    
    def __init__(self, poker_system):
        self.system = poker_system
        self.alert_system = AlertSystem()
        self.performance_tracker = PerformanceTracker()
        self.stop_loss_manager = StopLossManager(poker_system.bankroll_mgr.current_bankroll)
        self.visualizer = DataVisualizer()
        
        # アラートシステムにコールバックを登録
        self.alert_system.register_callback(
            AlertPriority.CRITICAL,
            self._handle_critical_alert
        )
    
    def _handle_critical_alert(self, alert: Alert):
        """クリティカルアラートのハンドラ"""
        print(f"\n{'='*80}")
        print(f"🚨 CRITICAL ALERT 🚨")
        print(f"{alert}")
        print(f"Action Required: {alert.action_recommendation}")
        print(f"{'='*80}\n")
    
    def process_hand(self, game_state: Dict) -> Dict:
        """ハンドを処理して全システムを更新"""
        # メイン分析
        analysis = self.system.analyze_situation(game_state)
        
        # パフォーマンス追跡に追加
        self.performance_tracker.add_result({
            'profit_loss': game_state.get('result', 0),
            'ev': analysis.get('ev', 0),
            'equity': analysis.get('raw_equity', 0),
            'position': game_state['position'],
            'won': game_state.get('won', False)
        })
        
        # バンクロール更新
        new_bankroll = self.system.bankroll_mgr.current_bankroll + game_state.get('result', 0)
        self.system.bankroll_mgr.current_bankroll = new_bankroll
        self.stop_loss_manager.update_bankroll(new_bankroll)
        
        # ティルト検知
        tilt_analysis = self.system.tilt_detector.calculate_tilt_score() if hasattr(self.system, 'tilt_detector') else {'tilt_score': 0}
        
        # アラートシステム更新
        self.alert_system.update_conditions({
            'tilt_score': tilt_analysis.get('tilt_score', 0),
            'current_loss': new_bankroll - self.stop_loss_manager.session_start_bankroll,
            'session_duration': (datetime.now() - self.stop_loss_manager.session_start_time).total_seconds() / 3600,
            'current_ev': analysis.get('ev', 0),
            'bankroll_ratio': new_bankroll / self.stop_loss_manager.initial_bankroll
        })
        
        # ストップロスチェック
        should_stop, reason = self.stop_loss_manager.should_stop_session()
        
        return {
            'analysis': analysis,
            'alerts': self.alert_system.get_active_alerts(),
            'should_stop': should_stop,
            'stop_reason': reason,
            'performance': self.performance_tracker.get_position_performance(),
            'trend': self.performance_tracker.detect_trend()
        }
    
    def generate_full_report(self) -> str:
        """完全なダッシュボードレポート"""
        report = []
        report.append("=" * 80)
        report.append("🎰 POKER MASTER SYSTEM - DASHBOARD")
        report.append("=" * 80)
        
        # バンクロール状況
        report.append("\n💰 BANKROLL STATUS")
        stop_loss_status = self.stop_loss_manager.get_status()
        report.append(f"Current: ${self.system.bankroll_mgr.current_bankroll:,.2f}")
        report.append(f"Session P/L: ${stop_loss_status['session_pl']:+.2f}")
        report.append(f"Session Duration: {stop_loss_status['session_duration']:.1f} hours")
        
        # アクティブアラート
        active_alerts = self.alert_system.get_active_alerts()
        if active_alerts:
            report.append("\n🚨 ACTIVE ALERTS")
            for alert in active_alerts[:5]:
                report.append(f"  {alert}")
        
        # パフォーマンストレンド
        trend = self.performance_tracker.detect_trend()
        report.append(f"\n📈 TREND ANALYSIS")
        report.append(f"Current Trend: {trend.get('trend', 'N/A')}")
        
        # 連勝/連敗
        streak = self.performance_tracker.calculate_streak()
        report.append(f"\n🎲 STREAKS")
        report.append(f"Current: {streak['current_streak']} {streak['type']} hands")
        
        report.append("\n" + "=" * 80)
        return '\n'.join(report)
    
    def export_visualizations(self, prefix: str = ''):
        """全ビジュアライゼーションをエクスポート"""
        self.visualizer.plot_profit_graph(
            self.performance_tracker.performance_data,
            f'{prefix}profit_graph.png'
        )
        
        if self.performance_tracker.performance_data:
            equities = [d['equity'] for d in self.performance_tracker.performance_data]
            self.visualizer.plot_equity_distribution(equities, f'{prefix}equity_dist.png')
        
        position_perf = self.performance_tracker.get_position_performance()
        if position_perf:
            self.visualizer.plot_position_performance(position_perf, f'{prefix}position_perf.png')
