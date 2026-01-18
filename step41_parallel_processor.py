# step41_parallel_processor.py
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from multiprocessing import cpu_count
from typing import List, Dict, Callable
import queue
import threading

class ParallelProcessor:
    """複数テーブルの同時処理"""
    
    def __init__(self, max_tables: int = 4):
        self.max_tables = max_tables
        self.thread_pool = ThreadPoolExecutor(max_workers=max_tables)
        self.process_pool = ProcessPoolExecutor(max_workers=cpu_count())
        self.active_tables = {}
        self.result_queue = queue.Queue()
    
    def add_table(self, table_id: str, game_state: Dict) -> str:
        """テーブルを追加"""
        if len(self.active_tables) >= self.max_tables:
            return "MAX_TABLES_REACHED"
        
        self.active_tables[table_id] = {
            'state': game_state,
            'analyzing': False
        }
        return "SUCCESS"
    
    def analyze_all_tables(self, analysis_func: Callable) -> Dict[str, Dict]:
        """全テーブルを並列分析"""
        futures = {}
        
        for table_id, table_data in self.active_tables.items():
            if not table_data['analyzing']:
                table_data['analyzing'] = True
                future = self.thread_pool.submit(
                    analysis_func, 
                    table_data['state']
                )
                futures[table_id] = future
        
        results = {}
        for table_id, future in futures.items():
            try:
                results[table_id] = future.result(timeout=5)
                self.active_tables[table_id]['analyzing'] = False
            except Exception as e:
                results[table_id] = {'error': str(e)}
                self.active_tables[table_id]['analyzing'] = False
        
        return results
    
    def batch_equity_calculation(self, hands: List[tuple], 
                                 board: List[int], 
                                 iterations: int = 50000) -> List[float]:
        """複数ハンドのエクイティを並列計算"""
        chunk_size = len(hands) // cpu_count() + 1
        chunks = [hands[i:i+chunk_size] for i in range(0, len(hands), chunk_size)]
        
        def calc_chunk(chunk):
            from step10_python_bridge import PokerEngineBase
            engine = PokerEngineBase()
            return [engine.calculate_equity(h, board, 1, iterations) for h in chunk]
        
        futures = [self.process_pool.submit(calc_chunk, chunk) for chunk in chunks]
        results = []
        for future in futures:
            results.extend(future.result())
        
        return results
    
    def shutdown(self):
        """リソースを解放"""
        self.thread_pool.shutdown(wait=True)
        self.process_pool.shutdown(wait=True)

