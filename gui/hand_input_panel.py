# gui/hand_input_panel.py
import customtkinter as ctk
from typing import Callable
from step10_advanced_bridge import CardRepresentation

class HandInputPanel(ctk.CTkFrame):
    """ハンド入力パネル"""
    
    def __init__(self, parent, system, on_analyze_callback: Callable):
        super().__init__(parent)
        self.system = system
        self.on_analyze = on_analyze_callback
        
        self.pack(fill="both", expand=True, padx=10, pady=10)
        self.create_widgets()
    
    def create_widgets(self):
        """ウィジェット作成"""
        # タイトル
        title = ctk.CTkLabel(
            self, text="🃏 Hand Input",
            font=("Arial Bold", 20)
        )
        title.pack(pady=(0, 20))
        
        # ヒーローカード
        self.create_card_input("Your Cards (e.g. AsKh):", "hero_cards")
        
        # ボード
        self.create_card_input("Board (e.g. QdJhTs):", "board")
        
        # ポジション
        self.create_position_selector()
        
        # 数値入力
        self.create_number_input("Pot Size ($):", "pot", 100)
        self.create_number_input("To Call ($):", "call_amount", 50)
        self.create_number_input("Your Stack ($):", "stack", 1000)
        self.create_number_input("Opponents:", "opponents", 1)
        
        # 相手ID（オプション）
        self.create_text_input("Opponent ID (optional):", "opponent_id")
        
        # 分析ボタン
        analyze_btn = ctk.CTkButton(
            self, text="⚡ ANALYZE",
            command=self.execute_analysis,
            height=50, font=("Arial Bold", 16),
            fg_color="#00aa00", hover_color="#00cc00"
        )
        analyze_btn.pack(pady=20, fill="x")
        
        # クリアボタン
        clear_btn = ctk.CTkButton(
            self, text="🗑️ Clear",
            command=self.clear_inputs,
            height=35, fg_color="#aa0000"
        )
        clear_btn.pack(fill="x")
    
    def create_card_input(self, label: str, key: str):
        """カード入力"""
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(frame, text=label, anchor="w").pack(anchor="w")
        
        entry = ctk.CTkEntry(frame, height=35, font=("Courier", 14))
        entry.pack(fill="x", pady=5)
        setattr(self, f"{key}_entry", entry)
    
    def create_position_selector(self):
        """ポジション選択"""
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(frame, text="Position:", anchor="w").pack(anchor="w")
        
        self.position_var = ctk.StringVar(value="BTN")
        positions = ["UTG", "UTG+1", "MP", "CO", "BTN", "SB", "BB"]
        
        pos_frame = ctk.CTkFrame(frame, fg_color="transparent")
        pos_frame.pack(fill="x", pady=5)
        
        for pos in positions:
            btn = ctk.CTkRadioButton(
                pos_frame, text=pos, 
                variable=self.position_var, value=pos
            )
            btn.pack(side="left", padx=5)
    
    def create_number_input(self, label: str, key: str, default: float):
        """数値入力"""
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(frame, text=label, anchor="w").pack(anchor="w")
        
        entry = ctk.CTkEntry(frame, height=35)
        entry.insert(0, str(default))
        entry.pack(fill="x", pady=5)
        setattr(self, f"{key}_entry", entry)
    
    def create_text_input(self, label: str, key: str):
        """テキスト入力"""
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(frame, text=label, anchor="w").pack(anchor="w")
        
        entry = ctk.CTkEntry(frame, height=35)
        entry.pack(fill="x", pady=5)
        setattr(self, f"{key}_entry", entry)
    
    def execute_analysis(self):
        """分析実行"""
        try:
            # 入力取得
            hero_str = self.hero_cards_entry.get().strip()
            board_str = self.board_entry.get().strip()
            
            # カード変換
            hero_cards = self.parse_cards(hero_str)
            board_cards = self.parse_cards(board_str) if board_str else []
