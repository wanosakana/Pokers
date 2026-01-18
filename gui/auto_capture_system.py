# gui/auto_capture_system.py
import cv2
import numpy as np
import mss
import pytesseract
from PIL import Image
import threading
import time
from typing import Dict, Optional, Tuple

class AutoCaptureSystem:
    """完全自動画面キャプチャ＆認識システム"""
    
    def __init__(self, poker_system):
        self.system = poker_system
        self.running = False
        self.capture_thread = None
        
        # 認識設定
        self.screen_region = None  # 自動検出
        self.card_templates = self.load_card_templates()
        self.last_game_state = {}
        
        # OCR設定
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    
    def load_card_templates(self) -> Dict:
        """カードテンプレート読み込み（事前学習済み）"""
        templates = {}
        ranks = '23456789TJQKA'
        suits = 'shdc'
        
        # 各カードの特徴パターン（簡易版）
        for rank in ranks:
            for suit in suits:
                card_name = f"{rank}{suit}"
                # 実際には画像ファイルを読み込む
                templates[card_name] = self.create_template_pattern(rank, suit)
        
        return templates
    
    def create_template_pattern(self, rank: str, suit: str) -> np.ndarray:
        """テンプレートパターン生成"""
        # 簡易的な特徴ベクトル（実際にはCNNや画像特徴を使用）
        return np.random.rand(64, 64, 3)
    
    def start_auto_capture(self):
        """自動キャプチャ開始"""
        if self.running:
            return
        
        self.running = True
        self.capture_thread = threading.Thread(target=self.capture_loop, daemon=True)
        self.capture_thread.start()
        print("✓ Auto-capture started")
    
    def stop_auto_capture(self):
        """自動キャプチャ停止"""
        self.running = False
        if self.capture_thread:
            self.capture_thread.join()
        print("✓ Auto-capture stopped")
    
    def capture_loop(self):
        """キャプチャループ（約10FPS）"""
        with mss.mss() as sct:
            while self.running:
                try:
                    # 画面キャプチャ
                    screenshot = self.capture_screen(sct)
                    
                    # ポーカーテーブル検出
                    table_region = self.detect_poker_table(screenshot)
                    
                    if table_region:
                        # ゲーム状態を抽出
                        game_state = self.extract_game_state(screenshot, table_region)
                        
                        # 変化があれば自動分析
                        if self.has_changed(game_state):
                            self.auto_analyze(game_state)
                    
                    time.sleep(0.1)  # 10FPS
                    
                except Exception as e:
                    print(f"Capture error: {e}")
                    time.sleep(1)
    
    def capture_screen(self, sct) -> np.ndarray:
        """画面キャプチャ"""
        if self.screen_region:
            monitor = self.screen_region
        else:
            monitor = sct.monitors[1]  # メインモニター
        
        img = np.array(sct.grab(monitor))
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    
    def detect_poker_table(self, screenshot: np.ndarray) -> Optional[Dict]:
        """ポーカーテーブル検出"""
        # 緑のテーブルを検出（HSV色空間）
        hsv = cv2.cvtColor(screenshot, cv2.COLOR_BGR2HSV)
        
        # 緑色の範囲
        lower_green = np.array([35, 40, 40])
        upper_green = np.array([85, 255, 255])
        
        mask = cv2.inRange(hsv, lower_green, upper_green)
        
        # 輪郭検出
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            # 最大の輪郭（テーブル）
            largest = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest)
            
            # 楕円形状チェック
            if w > 200 and h > 150 and 0.5 < w/h < 2.0:
                return {'x': x, 'y': y, 'width': w, 'height': h}
        
        return None
    
    def extract_game_state(self, screenshot: np.ndarray, table_region: Dict) -> Dict:
        """ゲーム状態抽出"""
        x, y, w, h = table_region['x'], table_region['y'], table_region['width'], table_region['height']
        table_img = screenshot[y:y+h, x:x+w]
        
        game_state = {
            'my_hand': self.detect_hero_cards(table_img),
            'board': self.detect_board_cards(table_img),
            'pot': self.detect_pot_size(table_img),
            'call_amount': self.detect_bet_amount(table_img),
            'my_stack': self.detect_stack(table_img, 'hero'),
            'position': self.detect_position(table_img),
            'opponents': self.count_active_players(table_img),
            'in_position': self.determine_position_advantage(table_img)
        }
        
        return game_state
    
    def detect_hero_cards(self, table_img: np.ndarray) -> Tuple[int, int]:
        """ヒーローカード検出"""
        # テーブル下部中央を探索
        h, w = table_img.shape[:2]
        hero_region = table_img[int(h*0.75):h, int(w*0.4):int(w*0.6)]
        
        cards = self.detect_cards_in_region(hero_region)
        
        if len(cards) >= 2:
            # カードIDに変換
            from step10_advanced_bridge import CardRepresentation
            card1 = CardRepresentation.from_string(cards[0]).card_id
            card2 = CardRepresentation.from_string(cards[1]).card_id
            return (card1, card2)
        
        return (0, 0)
    
    def detect_board_cards(self, table_img: np.ndarray) -> list:
        """ボードカード検出"""
        # テーブル中央上部
        h, w = table_img.shape[:2]
        board_region = table_img[int(h*0.35):int(h*0.5), int(w*0.25):int(w*0.75)]
        
        cards = self.detect_cards_in_region(board_region)
        
        # カードIDに変換
        from step10_advanced_bridge import CardRepresentation
        return [CardRepresentation.from_string(c).card_id for c in cards]
    
    def detect_cards_in_region(self, region: np.ndarray) -> list:
        """領域内のカード検出"""
        detected_cards = []
        
        # エッジ検出でカード形状を見つける
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # カードの縦横比チェック（約2:3）
            if 30 < w < 150 and 40 < h < 200 and 0.5 < w/h < 0.8:
                card_img = region[y:y+h, x:x+w]
                card_name = self.recognize_card(card_img)
                
                if card_name:
                    detected_cards.append(card_name)
        
        return detected_cards
    
    def recognize_card(self, card_img: np.ndarray) -> Optional[str]:
        """カード認識（テンプレートマッチング + OCR）"""
        # リサイズ
        card_resized = cv2.resize(card_img, (64, 96))
        
        # ランクとスートの領域
        rank_region = card_resized[5:25, 5:25]
        suit_region = card_resized[25:45, 5:25]
        
        # OCRでランク認識
        rank_gray = cv2.cvtColor(rank_region, cv2.COLOR_BGR2GRAY)
        _, rank_thresh = cv2.threshold(rank_gray, 127, 255, cv2.THRESH_BINARY)
        
        rank_text = pytesseract.image_to_string(
            rank_thresh, 
            config='--psm 10 -c tessedit_char_whitelist=23456789TJQKA'
        ).strip()
        
        # スート認識（色ベース）
        suit_hsv = cv2.cvtColor(suit_region, cv2.COLOR_BGR2HSV)
        
        # 赤系（ハート/ダイヤ）vs 黒系（スペード/クラブ）
        red_mask = cv2.inRange(suit_hsv, np.array([0, 100, 100]), np.array([10, 255, 255]))
        
        is_red = np.sum(red_mask) > 100
        
        # 形状でハート/ダイヤ、スペード/クラブを判別
        suit = self.detect_suit_shape(suit_region, is_red)
        
        if rank_text and suit:
            return f"{rank_text}{suit}"
        
        return None
    
    def detect_suit_shape(self, suit_region: np.ndarray, is_red: bool) -> str:
        """スート形状検出"""
        gray = cv2.cvtColor(suit_region, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY_INV)
        
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            contour = max(contours, key=cv2.contourArea)
            
            # 形状特徴
            area = cv2.contourArea(contour)
            perimeter = cv2.arcLength(contour, True)
            circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
            
            if is_red:
                # ハート: より複雑な形状
                return 'h' if circularity < 0.6 else 'd'
            else:
                # スペード: 鋭い形状
                return 's' if circularity < 0.5 else 'c'
        
        return 's' if not is_red else 'h'
    
    def detect_pot_size(self, table_img: np.ndarray) -> float:
        """ポットサイズ検出（OCR）"""
        h, w = table_img.shape[:2]
        pot_region = table_img[int(h*0.45):int(h*0.55), int(w*0.45):int(w*0.55)]
        
        return self.extract_amount(pot_region)
    
    def detect_bet_amount(self, table_img: np.ndarray) -> float:
        """ベット額検出"""
        # アクションボタン近くを探索
        h, w = table_img.shape[:2]
        bet_region = table_img[int(h*0.7):int(h*0.85), int(w*0.7):int(w*0.9)]
        
        return self.extract_amount(bet_region)
    
    def detect_stack(self, table_img: np.ndarray, player: str) -> float:
        """スタック検出"""
        h, w = table_img.shape[:2]
        
        if player == 'hero':
            stack_region = table_img[int(h*0.8):int(h*0.95), int(w*0.45):int(w*0.55)]
        else:
            stack_region = table_img[int(h*0.1):int(h*0.25), int(w*0.45):int(w*0.55)]
        
        return self.extract_amount(stack_region)
    
    def extract_amount(self, region: np.ndarray) -> float:
        """金額抽出（OCR）"""
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        
        # 前処理（コントラスト強調）
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        # OCR
        text = pytesseract.image_to_string(
            enhanced,
            config='--psm 7 -c tessedit_char_whitelist=0123456789.$,'
        ).strip()
        
        # 数値抽出
        import re
        match = re.search(r'[\d,]+\.?\d*', text.replace(',', ''))
        
        if match:
            try:
                return float(match.group())
            except:
                pass
        
        return 0.0
    
    def detect_position(self, table_img: np.ndarray) -> str:
        """ポジション検出"""
        # ディーラーボタンの位置から判定
        h, w = table_img.shape[:2]
        
        # 円形の白いボタンを探す
        gray = cv2.cvtColor(table_img, cv2.COLOR_BGR2GRAY)
        circles = cv2.HoughCircles(
            gray, cv2.HOUGH_GRADIENT, 1, 50,
            param1=100, param2=30, minRadius=10, maxRadius=40
        )
        
        if circles is not None:
            circles = np.uint16(np.around(circles))
            dealer_pos = circles[0][0]  # 最初の円
            
            # 相対位置からポジション判定
            dx = dealer_pos[0] - w/2
            dy = dealer_pos[1] - h/2
            
            angle = np.arctan2(dy, dx) * 180 / np.pi
            
            # 角度からポジション
            if -30 < angle < 30:
                return 'BTN'
            elif 30 < angle < 90:
                return 'SB'
            elif 90 < angle < 150:
                return 'BB'
            elif 150 < angle or angle < -150:
                return 'UTG'
            elif -150 < angle < -90:
                return 'CO'
            else:
                return 'MP'
        
        return 'BTN'  # デフォルト
    
    def count_active_players(self, table_img: np.ndarray) -> int:
        """アクティブプレイヤー数をカウント"""
        # プレイヤー席の各位置をチェック
        player_positions = [
            (0.5, 0.85),   # Hero
            (0.3, 0.6),    # Left 1
            (0.15, 0.4),   # Left 2
            (0.2, 0.15),   # Top Left
            (0.5, 0.05),   # Top
            (0.8, 0.15),   # Top Right
            (0.85, 0.4),   # Right 2
            (0.7, 0.6),    # Right 1
        ]
        
        h, w = table_img.shape[:2]
        active_count = 0
        
        for px, py in player_positions:
            x, y = int(w * px), int(h * py)
            region = table_img[max(0, y-30):min(h, y+30), max(0, x-30):min(w, x+30)]
            
            if self.has_player_at_position(region):
                active_count += 1
        
        return max(1, active_count - 1)  # ヒーロー除く
    
    def has_player_at_position(self, region: np.ndarray) -> bool:
        """その位置にプレイヤーがいるか"""
        # カードまたはチップの存在をチェック
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)
        
        # 白いピクセルの割合
        white_ratio = np.sum(thresh > 200) / thresh.size
        
        return white_ratio > 0.1
    
    def determine_position_advantage(self, table_img: np.ndarray) -> bool:
        """ポジションアドバンテージ判定"""
        position = self.detect_position(table_img)
        return position in ['BTN', 'CO']
    
    def has_changed(self, game_state: Dict) -> bool:
        """ゲーム状態が変化したか"""
        if not self.last_game_state:
            self.last_game_state = game_state
            return True
        
        # 重要な要素の変化をチェック
        changed = (
            game_state['my_hand'] != self.last_game_state.get('my_hand') or
            game_state['board'] != self.last_game_state.get('board') or
            abs(game_state['pot'] - self.last_game_state.get('pot', 0)) > 5
        )
        
        if changed:
            self.last_game_state = game_state
        
        return changed
    
    def auto_analyze(self, game_state: Dict):
        """自動分析実行"""
        try:
            if game_state['my_hand'] != (0, 0):
                result = self.system.analyze_situation(game_state)
                
                # 結果を通知（GUIコールバック）
                if hasattr(self, 'on_auto_analysis'):
                    self.on_auto_analysis(result, game_state)
                
                print(f"✓ Auto-analyzed: {result['recommendation']['action']}")
        
        except Exception as e:
            print(f"Auto-analysis error: {e}")
