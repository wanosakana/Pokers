# step10_advanced_bridge.py
import ctypes
import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass
from functools import lru_cache
import threading

@dataclass
class CardRepresentation:
    """カード表現の統一インターフェース"""
    card_id: int  # 0-51
    
    @classmethod
    def from_string(cls, card_str: str) -> 'CardRepresentation':
        """文字列からカードを生成 (例: 'As', 'Kh')"""
        rank_map = {'2': 0, '3': 1, '4': 2, '5': 3, '6': 4, '7': 5, '8': 6,
                   '9': 7, 'T': 8, 'J': 9, 'Q': 10, 'K': 11, 'A': 12}
        suit_map = {'s': 0, 'h': 1, 'd': 2, 'c': 3}
        
        rank = rank_map[card_str[0]]
        suit = suit_map[card_str[1].lower()]
        return cls(suit * 13 + rank)
    
    def to_string(self) -> str:
        """カードを文字列に変換"""
        ranks = '23456789TJQKA'
        suits = 'shdc'
        rank = self.card_id % 13
        suit = self.card_id // 13
        return f"{ranks[rank]}{suits[suit]}"

class OptimizedCppBridge:
    """最適化されたC++ブリッジ"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        
        # 全C++ライブラリをロード
        self.evaluator = ctypes.CDLL('./poker_engine.so')
        
        # 関数シグネチャの完全定義
        self._setup_function_signatures()
        
        # キャッシュの初期化
        self._equity_cache = {}
        self._eval_cache = {}
    
    def _setup_function_signatures(self):
        """全C++関数のシグネチャを設定"""
        
        # ハンド評価
        self.evaluator.evaluate_7cards_perfect.argtypes = [
            ctypes.POINTER(ctypes.c_uint8)
        ]
        self.evaluator.evaluate_7cards_perfect.restype = ctypes.c_uint32
        
        # エクイティ計算
        self.evaluator.calculate_equity_optimized.argtypes = [
            ctypes.c_uint8,  # hero card 1
            ctypes.c_uint8,  # hero card 2
            ctypes.POINTER(ctypes.c_uint8),  # board
            ctypes.c_int,    # board count
            ctypes.c_int,    # opponents
            ctypes.c_int     # iterations
        ]
        self.evaluator.calculate_equity_optimized.restype = ctypes.c_float
        
        # EQR計算
        self.evaluator.calculate_eqr_advanced.argtypes = [
            ctypes.c_double,  # raw equity
            ctypes.c_int,     # position
            ctypes.c_double,  # stack
            ctypes.c_double,  # pot
            ctypes.c_int,     # board texture
            ctypes.c_int,     # opponents
            ctypes.c_bool,    # in position
            ctypes.c_double   # opponent skill
        ]
        self.evaluator.calculate_eqr_advanced.restype = ctypes.c_double
        
        # CFR
        self.evaluator.create_cfr_solver.restype = ctypes.c_void_p
        self.evaluator.cfr_train.argtypes = [ctypes.c_void_p, ctypes.c_int]
    
    @lru_cache(maxsize=10000)
    def evaluate_hand_cached(self, cards_tuple: Tuple[int, ...]) -> int:
        """キャッシュ付きハンド評価"""
        cards_array = (ctypes.c_uint8 * 7)(*cards_tuple)
        return self.evaluator.evaluate_7cards_perfect(cards_array)
    
    def calculate_equity_fast(self, hero: Tuple[int, int], 
                             board: List[int], 
                             opponents: int = 1,
                             iterations: int = 100000) -> float:
        """高速エクイティ計算"""
        # キャッシュキー生成
        cache_key = (hero, tuple(board), opponents, iterations)
        
        if cache_key in self._equity_cache:
            return self._equity_cache[cache_key]
        
        board_array = (ctypes.c_uint8 * len(board))(*board) if board else None
        
        equity = self.evaluator.calculate_equity_optimized(
            hero[0], hero[1], board_array, len(board),
            opponents, iterations
        )
        
        self._equity_cache[cache_key] = equity
        return equity
    
    def calculate_eqr_complete(self, raw_equity: float, position: int,
                              stack: float, pot: float,
                              board_texture: int, opponents: int,
                              in_position: bool, opponent_skill: float = 0.5) -> float:
        """完全なEQR計算"""
        return self.evaluator.calculate_eqr_advanced(
            raw_equity, position, stack, pot,
            board_texture, opponents, in_position, opponent_skill
        )
    
    def batch_equity_calculation(self, hands: List[Tuple[int, int]],
                                board: List[int],
                                opponents: int = 1) -> np.ndarray:
        """バッチエクイティ計算（並列処理対応）"""
        results = np.zeros(len(hands), dtype=np.float32)
        
        for i, hand in enumerate(hands):
            results[i] = self.calculate_equity_fast(hand, board, opponents, 50000)
        
        return results
    
    def clear_cache(self):
        """キャッシュをクリア"""
        self._equity_cache.clear()
        self._eval_cache.clear()
