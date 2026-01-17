# poker_master_complete.py - 全50ステップ完全統合版
import customtkinter as ctk
from tkinter import messagebox
import sys
import os
from datetime import datetime

# ===== 全モジュールインポート =====
# Layer 1 (Step 1-9): C++エンジン（自動ロード）
from step10_advanced_bridge import OptimizedCppBridge

# Layer 2 (Step 10-20): Python統合層
from step20_complete_integration import PokerMasterSystemComplete

# Layer 3 (Step 21-30): 高度な分析
# これらは既にPokerMasterSystemCompleteに統合済み

# Layer 4 (Step 31-40): 実戦機能
from step31_tilt_detector import TiltDetector
from step32_session_manager import SessionManager
from step33_hand_history import HandHistory
from step34_replay_system import HandReplayer
from step35_report_generator import ReportGenerator
from step36_alert_system import AlertSystem, AlertPriority
from step37_performance_tracker import PerformanceTracker
from step38_stop_loss import StopLossManager
from step39_visualization import DataVisualizer
from step40_dashboard import IntegratedDashboard

# Layer 5 (Step 41-50): 最適化とUI
from step41_parallel_optimizer import ParallelOptimizer
from step42_cache_system import PersistentCache
from gui.auto_capture_system import AutoCaptureSystem

class PokerMasterCompleteApp:
    """全50ステップ完全統合アプリケーション"""
    
    def __init__(self):
        print("="*70)
        print("🎰 POKER MASTER SYSTEM - COMPLETE EDITION")
        print("   All 50 Steps Integrated")
        print("="*70)
        
        # ===== コアシステム初期化 =====
        print("\n[1/10] Initializing Core Engine...")
        self.poker_system = PokerMasterSystemComplete(bankroll=10000)
        print("✓ Core engine ready")
        
        # ===== Layer 4機能統合 =====
        print("\n[2/10] Integrating Session Management...")
        self.session_manager = SessionManager()
        self.hand_history = HandHistory(db_path='poker_hands.db')
        self.hand_replayer = HandReplayer(self.hand_history)
        print("✓ Session & history systems ready")
        
        print("\n[3/10] Initializing Tilt Detection...")
        self.tilt_detector = TiltDetector()
        print("✓ Tilt detector active")
        
        print("\n[4/10] Setting up Alert System...")
        self.alert_system = AlertSystem()
        self.alert_system.start_monitoring(interval=5.0)
        # アラートコールバック登録
        self.alert_system.register_callback(AlertPriority.CRITICAL, self.on_critical_alert)
        self.alert_system.register_callback(AlertPriority.HIGH, self.on_high_alert)
        print("✓ Alert system monitoring")
        
        print("\n[5/10] Initializing Performance Tracker...")
        self.performance_tracker = PerformanceTracker()
        print("✓ Performance tracking active")
        
        print("\n[6/10] Setting up Stop-Loss Manager...")
        self.stop_loss_manager = StopLossManager(initial_bankroll=10000)
        print("✓ Stop-loss protection enabled")
        
        print("\n[7/10] Initializing Visualizer...")
        self.visualizer = DataVisualizer()
        print("✓ Data visualization ready")
        
        print("\n[8/10] Creating Integrated Dashboard...")
        self.integrated_dashboard = IntegratedDashboard(self.poker_system)
        # Layer 4コンポーネントを接続
        self.integrated_dashboard.alert_system = self.alert_system
        self.integrated_dashboard.performance_tracker = self.performance_tracker
        self.integrated_dashboard.stop_loss_manager = self.stop_loss_manager
        self.integrated_dashboard.visualizer = self.visualizer
        print("✓ Dashboard integrated")
        
        # ===== Layer 5最適化 =====
        print("\n[9/10] Optimizing Performance...")
        self.parallel_optimizer = ParallelOptimizer()
        self.cache_system = PersistentCache()
        print("✓ Optimization layer active")
        
        # ===== GUI構築 =====
        print("\n[10/10] Building GUI...")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")
        
        self.root = ctk.CTk()
        self.root.title("🎰 Poker Master System - Complete Edition (All 50 Steps)")
        self.root.geometry("1600x1000")
        
        self.build_complete_ui()
        print("✓ GUI ready")
        
        print("\n" + "="*70)
        print("🚀 ALL SYSTEMS OPERATIONAL!")
        print("="*70 + "\n")
    
    def build_complete_ui(self):
        """完全なUI構築"""
        # トップバー（拡張版）
        self.create_enhanced_top_bar()
        
        # メインコンテナ（3カラムレイアウト）
        self.main_container = ctk.CTkFrame(self.root)
        self.main_container.pack(fill="both", expand=True)
        
        # 左パネル（入力 + コントロール）
        self.left_panel = ctk.CTkFrame(self.main_container, width=400)
        self.left_panel.pack(side="left", fill="y", padx=(10, 5), pady=10)
        self.left_panel.pack_propagate(False)
        
        # 中央パネル（メイン表示）
        self.center_panel = ctk.CTkFrame(self.main_container)
        self.center_panel.pack(side="left", fill="both", expand=True, padx=5, pady=10)
        
        # 右パネル（リアルタイム情報）
        self.right_panel = ctk.CTkFrame(self.main_container, width=350)
        self.right_panel.pack(side="right", fill="y", padx=(5, 10), pady=10)
        self.right_panel.pack_propagate(False)
        
        # 各パネルの初期化
        self.setup_left_panel()
        self.setup_center_panel()
        self.setup_right_panel()
        
        # ステータスバー（拡張版）
        self.create_enhanced_status_bar()
        
        # 自動更新開始
        self.start_auto_updates()
    
    def create_enhanced_top_bar(self):
        """拡張トップバー"""
        top_bar = ctk.CTkFrame(self.root, height=60, corner_radius=0)
        top_bar.pack(fill="x")
        
        # ロゴ
        logo_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        logo_frame.pack(side="left", padx=20)
        
        ctk.CTkLabel(
            logo_frame,
            text="🎰 POKER MASTER",
            font=("Arial Black", 24),
            text_color="#00ff00"
        ).pack(side="left")
        
        ctk.CTkLabel(
            logo_frame,
            text="Complete Edition | All 50 Steps",
            font=("Arial", 10),
            text_color="#888888"
        ).pack(side="left", padx=(10, 0))
        
        # メニューボタン
        menu_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        menu_frame.pack(side="right", padx=20)
        
        buttons = [
            ("🤖 Auto", self.show_auto_mode, "#00aa00"),
            ("✋ Manual", self.show_manual_mode, "#0066cc"),
            ("📊 Stats", self.show_stats_mode, "#cc6600"),
            ("📈 Graphs", self.show_graph_mode, "#cc00cc"),
            ("🔄 Replay", self.show_replay_mode, "#00cccc"),
            ("🎓 Train", self.show_training_mode, "#6600cc"),
            ("👁️ HUD", self.toggle_hud, "#aa00aa"),
            ("🚨 Alerts", self.show_alerts, "#cc0000"),
            ("⚙️", self.show_settings, "#666666"),
        ]
        
        for text, cmd, color in buttons:
            ctk.CTkButton(
                menu_frame, text=text, command=cmd,
                width=70 if len(text) > 2 else 40, height=40,
                fg_color=color, font=("Arial Bold", 11)
            ).pack(side="left", padx=2)
    
    def setup_left_panel(self):
        """左パネル（入力コントロール）"""
        # タイトル
        ctk.CTkLabel(
            self.left_panel,
            text="🎮 Control Panel",
            font=("Arial Bold", 18)
        ).pack(pady=10)
        
        # 自動キャプチャパネル（デフォルト）
        from gui.auto_input_panel import AutoInputPanel
        from gui.analysis_panel import AnalysisPanel
        
        # 分析パネル用の一時変数
        self.temp_analysis_panel = AnalysisPanel(self.center_panel)
        
        self.auto_panel = AutoInputPanel(
            self.left_panel,
            self.poker_system,
            self.temp_analysis_panel
        )
    
    def setup_center_panel(self):
        """中央パネル（メイン表示）"""
        from gui.analysis_panel import AnalysisPanel
        self.analysis_panel = AnalysisPanel(self.center_panel)
    
    def setup_right_panel(self):
        """右パネル（リアルタイム情報）"""
        # タイトル
        ctk.CTkLabel(
            self.right_panel,
            text="📡 Live Info",
            font=("Arial Bold", 18)
        ).pack(pady=10)
        
        # ティルトメーター
        tilt_frame = ctk.CTkFrame(self.right_panel)
        tilt_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(tilt_frame, text="🎭 Tilt Level", font=("Arial Bold", 12)).pack(anchor="w", padx=10, pady=5)
        self.tilt_progress = ctk.CTkProgressBar(tilt_frame)
        self.tilt_progress.pack(fill="x", padx=10, pady=5)
        self.tilt_progress.set(0)
        
        self.tilt_label = ctk.CTkLabel(tilt_frame, text="LOW", text_color="#00ff00")
        self.tilt_label.pack(pady=5)
        
        # セッション情報
        session_frame = ctk.CTkFrame(self.right_panel)
        session_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(session_frame, text="📊 Session Stats", font=("Arial Bold", 12)).pack(anchor="w", padx=10, pady=5)
        
        self.session_info = ctk.CTkTextbox(session_frame, height=150, font=("Consolas", 10))
        self.session_info.pack(fill="x", padx=10, pady=5)
        
        # アクティブアラート
        alert_frame = ctk.CTkFrame(self.right_panel)
        alert_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(alert_frame, text="🚨 Active Alerts", font=("Arial Bold", 12)).pack(anchor="w", padx=10, pady=5)
        
        self.alerts_text = ctk.CTkTextbox(alert_frame, height=200, font=("Consolas", 9))
        self.alerts_text.pack(fill="x", padx=10, pady=5)
        
        # パフォーマンスグラフ（ミニ）
        perf_frame = ctk.CTkFrame(self.right_panel)
        perf_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        ctk.CTkLabel(perf_frame, text="📈 Performance", font=("Arial Bold", 12)).pack(anchor="w", padx=10, pady=5)
        
        self.perf_canvas = ctk.CTkCanvas(perf_frame, height=150, bg="#1a1a1a", highlightthickness=0)
        self.perf_canvas.pack(fill="both", expand=True, padx=10, pady=5)
    
    def create_enhanced_status_bar(self):
        """拡張ステータスバー"""
        self.status_frame = ctk.CTkFrame(self.root, height=40, corner_radius=0)
        self.status_frame.pack(fill="x", side="bottom")
        
        # 左側：システムステータス
        left_status = ctk.CTkFrame(self.status_frame, fg_color="transparent")
        left_status.pack(side="left", fill="both", expand=True)
        
        self.status_label = ctk.CTkLabel(
            left_status,
            text="🟢 All Systems Operational",
            font=("Consolas", 11),
            anchor="w"
        )
        self.status_label.pack(side="left", padx=15, pady=10)
        
        # 中央：バンクロール & セッション
        center_status = ctk.CTkFrame(self.status_frame, fg_color="transparent")
        center_status.pack(side="left")
        
        self.bankroll_label = ctk.CTkLabel(
            center_status,
            text="💰 $10,000.00",
            font=("Consolas Bold", 12),
            text_color="#00ff00"
        )
        self.bankroll_label.pack(side="left", padx=10)
        
        self.session_label = ctk.CTkLabel(
            center_status,
            text="📊 Session: 0 hands",
            font=("Consolas", 11)
        )
        self.session_label.pack(side="left", padx=10)
        
        # 右側：パフォーマンス指標
        right_status = ctk.CTkFrame(self.status_frame, fg_color="transparent")
        right_status.pack(side="right", padx=15)
        
        self.fps_label = ctk.CTkLabel(
            right_status,
            text="FPS: 0",
            font=("Consolas", 10),
            text_color="#888888"
        )
        self.fps_label.pack(side="right", padx=5)
        
        self.cpu_label = ctk.CTkLabel(
            right_status,
            text="CPU: 0%",
            font=("Consolas", 10),
            text_color="#888888"
        )
        self.cpu_label.pack(side="right", padx=5)
    
    def start_auto_updates(self):
        """自動更新開始"""
        self.update_realtime_info()
        self.update_performance_graph()
    
    def update_realtime_info(self):
        """リアルタイム情報更新"""
        # ティルト検知更新
        tilt_analysis = self.tilt_detector.calculate_tilt_score()
        tilt_score = tilt_analysis.get('tilt_score', 0)
        
        self.tilt_progress.set(tilt_score)
        
        if tilt_score > 0.7:
            self.tilt_label.configure(text="CRITICAL", text_color="#ff0000")
        elif tilt_score > 0.5:
            self.tilt_label.configure(text="HIGH", text_color="#ff8800")
        elif tilt_score > 0.3:
            self.tilt_label.configure(text="MODERATE", text_color="#ffff00")
        else:
            self.tilt_label.configure(text="LOW", text_color="#00ff00")
        
        # セッション情報更新
        current_session = self.session_manager.current_session
        if current_session:
            stats = current_session.get_statistics()
            session_text = f"""
Hands: {stats['hands_played']}
Win Rate: {stats['win_rate']:.1%}
P/L: ${stats['profit_loss']:+.2f}
VPIP: {stats['vpip']:.1%}
PFR: {stats['pfr']:.1%}
Duration: {stats['duration']}
            """.strip()
            self.session_info.delete("1.0", "end")
            self.session_info.insert("1.0", session_text)
        
        # アラート更新
        active_alerts = self.alert_system.get_active_alerts()
        if active_alerts:
            alerts_text = "\n".join([str(a) for a in active_alerts[:5]])
            self.alerts_text.delete("1.0", "end")
            self.alerts_text.insert("1.0", alerts_text)
        
        # バンクロール更新
        bankroll = self.stop_loss_manager.current_bankroll
        self.bankroll_label.configure(text=f"💰 ${bankroll:,.2f}")
        
        color = "#00ff00" if bankroll >= 10000 else "#ff0000"
        self.bankroll_label.configure(text_color=color)
        
        # 0.5秒後に再実行
        self.root.after(500, self.update_realtime_info)
    
    def update_performance_graph(self):
        """パフォーマンスグラフ更新"""
        if not self.performance_tracker.performance_data:
            self.root.after(1000, self.update_performance_graph)
            return
        
        # 簡易グラフ描画
        self.perf_canvas.delete("all")
        
        data = self.performance_tracker.performance_data[-50:]  # 最新50ハンド
        if len(data) < 2:
            self.root.after(1000, self.update_performance_graph)
            return
        
        width = self.perf_canvas.winfo_width()
        height = self.perf_canvas.winfo_height()
        
        profits = [d['profit_loss'] for d in data]
        cumulative = []
        total = 0
        for p in profits:
            total += p
            cumulative.append(total)
        
        if not cumulative:
            self.root.after(1000, self.update_performance_graph)
            return
        
        max_val = max(cumulative) if max(cumulative) > 0 else 1
        min_val = min(cumulative) if min(cumulative) < 0 else -1
        
        range_val = max_val - min_val
        if range_val == 0:
            range_val = 1
        
        # グラフ描画
        points = []
        for i, val in enumerate(cumulative):
            x = (i / len(cumulative)) * width
            y = height - ((val - min_val) / range_val) * height
            points.append((x, y))
        
        # ライン描画
        for i in range(len(points) - 1):
            color = "#00ff00" if cumulative[i+1] >= 0 else "#ff0000"
            self.perf_canvas.create_line(
                points[i][0], points[i][1],
                points[i+1][0], points[i+1][1],
                fill=color, width=2
            )
        
        # ゼロライン
        zero_y = height - ((0 - min_val) / range_val) * height
        self.perf_canvas.create_line(0, zero_y, width, zero_y, fill="#666666", dash=(2, 2))
        
        self.root.after(1000, self.update_performance_graph)
    
    def on_critical_alert(self, alert):
        """クリティカルアラート処理"""
        messagebox.showwarning(
            "🚨 CRITICAL ALERT",
            f"{alert.message}\n\nRecommended Action:\n{alert.action_recommendation}"
        )
    
    def on_high_alert(self, alert):
        """高優先度アラート処理"""
        print(f"⚠️ HIGH ALERT: {alert.message}")
    
    # モード切り替えメソッド（省略 - 既存のメソッドを使用）
    def show_auto_mode(self): pass
    def show_manual_mode(self): pass
    def show_stats_mode(self): pass
    def show_graph_mode(self): pass
    def show_replay_mode(self): pass
    def show_training_mode(self): pass
    def toggle_hud(self): pass
    def show_alerts(self): pass
    def show_settings(self): pass
    
    def run(self):
        """アプリケーション実行"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def on_closing(self):
        """終了処理"""
        # 全システム停止
        self.alert_system.stop_monitoring()
        if hasattr(self, 'auto_panel'):
            self.auto_panel.auto_capture.stop_auto_capture()
        
        self.root.destroy()

def main():
    """メイン関数"""
    app = PokerMasterCompleteApp()
    app.run()

if __name__ == "__main__":
    main()
