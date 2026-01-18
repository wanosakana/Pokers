# gui/auto_input_panel.py
import customtkinter as ctk
from gui.auto_capture_system import AutoCaptureSystem

class AutoInputPanel(ctk.CTkFrame):
    """自動入力パネル"""
    
    def __init__(self, parent, poker_system, analysis_panel):
        super().__init__(parent)
        self.system = poker_system
        self.analysis_panel = analysis_panel
        
        # 自動キャプチャシステム
        self.auto_capture = AutoCaptureSystem(poker_system)
        self.auto_capture.on_auto_analysis = self.on_analysis_complete
        
        self.pack(fill="both", expand=True, padx=10, pady=10)
        self.create_widgets()
    
    def create_widgets(self):
        """ウィジェット作成"""
        # タイトル
        title = ctk.CTkLabel(
            self, text="🤖 Auto-Capture Mode",
            font=("Arial Bold", 20)
        )
        title.pack(pady=(0, 20))
        
        # ステータス表示
        self.status_frame = ctk.CTkFrame(self)
        self.status_frame.pack(fill="x", pady=10)
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Status: Inactive",
            font=("Arial", 14)
        )
        self.status_label.pack(pady=10)
        
        # プレビュー
        self.preview_label = ctk.CTkLabel(
            self, text="Detected Hand: --",
            font=("Courier", 12)
        )
        self.preview_label.pack(pady=5)
        
        self.board_label = ctk.CTkLabel(
            self, text="Board: --",
            font=("Courier", 12)
        )
        self.board_label.pack(pady=5)
        
        self.pot_label = ctk.CTkLabel(
            self, text="Pot: $0.00",
            font=("Courier", 12)
        )
        self.pot_label.pack(pady=5)
        
        # コントロールボタン
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=20)
        
        self.start_btn = ctk.CTkButton(
            button_frame, text="🚀 Start Auto-Capture",
            command=self.start_capture,
            height=50, width=200,
            fg_color="#00aa00", hover_color="#00cc00"
        )
        self.start_btn.pack(side="left", padx=5)
        
        self.stop_btn = ctk.CTkButton(
            button_frame, text="⏸️ Stop",
            command=self.stop_capture,
            height=50, width=200,
            fg_color="#aa0000", hover_color="#cc0000",
            state="disabled"
        )
        self.stop_btn.pack(side="left", padx=5)
        
        # 設定
        settings_frame = ctk.CTkFrame(self)
        settings_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(settings_frame, text="Screen Region:").pack(anchor="w", padx=10)
        
        self.region_btn = ctk.CTkButton(
            settings_frame, text="📐 Select Region",
            command=self.select_region,
            height=35
        )
        self.region_btn.pack(padx=10, pady=5, fill="x")
    
    def start_capture(self):
        """キャプチャ開始"""
        self.auto_capture.start_auto_capture()
        
        self.status_label.configure(text="Status: 🟢 Active - Monitoring screen...")
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        
        # ステータス更新ループ
        self.update_status()
    
    def stop_capture(self):
        """キャプチャ停止"""
        self.auto_capture.stop_auto_capture()
        
        self.status_label.configure(text="Status: 🔴 Inactive")
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
    
    def select_region(self):
        """画面領域選択"""
        # 画面選択ウィンドウを表示
        from gui.region_selector import RegionSelector
        selector = RegionSelector(self, self.auto_capture)
    
    def update_status(self):
        """ステータス更新"""
        if self.auto_capture.running:
            # 最新のゲーム状態を表示
            state = self.auto_capture.last_game_state
            
            if state:
                # カード表示
                hero = state.get('my_hand', (0, 0))
                if hero != (0, 0):
                    from step10_advanced_bridge import CardRepresentation
                    card1_str = CardRepresentation(hero[0]).to_string()
                    card2_str = CardRepresentation(hero[1]).to_string()
                    self.preview_label.configure(text=f"Detected Hand: {card1_str} {card2_str}")
                
                # ボード表示
                board = state.get('board', [])
                if board:
                    board_str = ' '.join(CardRepresentation(c).to_string() for c in board)
                    self.board_label.configure(text=f"Board: {board_str}")
                
                # ポット表示
                pot = state.get('pot', 0)
                self.pot_label.configure(text=f"Pot: ${pot:.2f}")
            
            # 0.5秒後に再更新
            self.after(500, self.update_status)
    
    def on_analysis_complete(self, result: dict, game_state: dict):
        """分析完了時のコールバック"""
        # 分析結果を表示パネルに送る
        self.analysis_panel.display_results(result)
