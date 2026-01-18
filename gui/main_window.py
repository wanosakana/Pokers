# gui/main_window.py
import customtkinter as ctk
from tkinter import messagebox
from gui.hand_input_panel import HandInputPanel
from gui.analysis_panel import AnalysisPanel
from gui.stats_panel import StatsPanel
from gui.graph_panel import GraphPanel
from gui.hud_overlay import HUDOverlay
from gui.training_mode import TrainingMode

class MainWindow:
    """メインウィンドウ"""
    
    def __init__(self, root, poker_system):
        self.root = root
        self.system = poker_system
        
        # メニューバー
        self.create_menu_bar()
        
        # レイアウト
        self.create_layout()
        
        # ステータスバー
        self.create_status_bar()
        
    def create_menu_bar(self):
        """メニューバー作成"""
        menu_frame = ctk.CTkFrame(self.root, height=40, fg_color="#1a1a1a")
        menu_frame.pack(fill="x", padx=0, pady=0)
        
        # メニューボタン
        buttons = [
            ("📊 Analyze", self.show_analyze),
            ("📈 Stats", self.show_stats),
            ("📉 Graphs", self.show_graphs),
            ("👁️ HUD", self.toggle_hud),
            ("🎓 Training", self.show_training),
            ("⚙️ Settings", self.show_settings),
        ]
        
        for text, command in buttons:
            btn = ctk.CTkButton(
                menu_frame, text=text, command=command,
                width=100, height=35,
                fg_color="#2a2a2a", hover_color="#3a3a3a"
            )
            btn.pack(side="left", padx=5, pady=2)
    
    def create_layout(self):
        """レイアウト作成"""
        # メインコンテナ
        self.main_container = ctk.CTkFrame(self.root)
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 左パネル（入力）
        left_panel = ctk.CTkFrame(self.main_container, width=400)
        left_panel.pack(side="left", fill="both", padx=(0, 5))
        
        self.hand_input = HandInputPanel(left_panel, self.system, self.on_analyze)
        
        # 右パネル（分析結果）
        right_panel = ctk.CTkFrame(self.main_container)
        right_panel.pack(side="right", fill="both", expand=True)
        
        self.analysis_panel = AnalysisPanel(right_panel)
        
        # その他のパネル（初期は非表示）
        self.stats_panel = None
        self.graph_panel = None
        self.hud_overlay = None
        self.training_mode = None
    
    def create_status_bar(self):
        """ステータスバー"""
        self.status_bar = ctk.CTkFrame(self.root, height=30, fg_color="#1a1a1a")
        self.status_bar.pack(fill="x", side="bottom")
        
        self.status_label = ctk.CTkLabel(
            self.status_bar, 
            text="🟢 Ready | Bankroll: $10,000.00 | Session: 0 hands",
            anchor="w"
        )
        self.status_label.pack(fill="x", padx=10, pady=5)
    
    def on_analyze(self, game_state):
        """分析実行"""
        try:
            # 分析
            result = self.system.analyze_situation(game_state)
            
            # 結果表示
            self.analysis_panel.display_results(result)
            
            # ステータス更新
            self.update_status(f"✓ Analysis complete | EV: ${result['ev']['best']:+.2f}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Analysis failed: {str(e)}")
    
    def show_analyze(self):
        """分析画面表示"""
        self.hide_all_panels()
        self.hand_input.show()
        self.analysis_panel.show()
    
    def show_stats(self):
        """統計画面表示"""
        self.hide_all_panels()
        if not self.stats_panel:
            self.stats_panel = StatsPanel(self.main_container, self.system)
        self.stats_panel.pack(fill="both", expand=True)
        self.stats_panel.refresh()
    
    def show_graphs(self):
        """グラフ画面表示"""
        self.hide_all_panels()
        if not self.graph_panel:
            self.graph_panel = GraphPanel(self.main_container, self.system)
        self.graph_panel.pack(fill="both", expand=True)
        self.graph_panel.refresh()
    
    def toggle_hud(self):
        """HUDトグル"""
        if not self.hud_overlay:
            self.hud_overlay = HUDOverlay(self.root, self.system)
        self.hud_overlay.toggle()
    
    def show_training(self):
        """トレーニングモード"""
        self.hide_all_panels()
        if not self.training_mode:
            self.training_mode = TrainingMode(self.main_container, self.system)
        self.training_mode.pack(fill="both", expand=True)
        self.training_mode.new_scenario()
    
    def show_settings(self):
        """設定ダイアログ"""
        from gui.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self.root, self.system)
    
    def hide_all_panels(self):
        """全パネル非表示"""
        for widget in self.main_container.winfo_children():
            widget.pack_forget()
    
    def update_status(self, message: str):
        """ステータス更新"""
        bankroll = self.system.bankroll
        hands = self.system.session_hands
        self.status_label.configure(
            text=f"{message} | Bankroll: ${bankroll:,.2f} | Session: {hands} hands"
        )
