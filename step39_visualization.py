# step39_visualization.py
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

class DataVisualizer:
    """データビジュアライゼーション"""
    
    def __init__(self):
        plt.style.use('dark_background')
        self.colors = {
            'profit': '#00ff00',
            'loss': '#ff0000',
            'neutral': '#888888',
            'equity': '#00aaff',
            'ev': '#ffaa00'
        }
    
    def plot_profit_graph(self, performance_data: List[Dict], 
                         filename: str = 'profit_graph.png'):
        """利益グラフを生成"""
        if not performance_data:
            return
        
        timestamps = [d['timestamp'] for d in performance_data]
        profits = [d['profit_loss'] for d in performance_data]
        cumulative = np.cumsum(profits)
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        
        # 累積利益
        ax1.plot(timestamps, cumulative, color=self.colors['equity'], linewidth=2)
        ax1.fill_between(timestamps, cumulative, 0, 
                         where=(cumulative >= 0), color=self.colors['profit'], alpha=0.3)
        ax1.fill_between(timestamps, cumulative, 0, 
                         where=(cumulative < 0), color=self.colors['loss'], alpha=0.3)
        ax1.axhline(y=0, color=self.colors['neutral'], linestyle='--', alpha=0.5)
        ax1.set_title('Cumulative Profit/Loss', fontsize=16)
        ax1.set_ylabel('P/L ($)', fontsize=12)
        ax1.grid(True, alpha=0.3)
        
        # ハンドごとの利益
        colors = [self.colors['profit'] if p > 0 else self.colors['loss'] for p in profits]
        ax2.bar(range(len(profits)), profits, color=colors, alpha=0.6)
        ax2.axhline(y=0, color=self.colors['neutral'], linestyle='--', alpha=0.5)
        ax2.set_title('Per-Hand Profit/Loss', fontsize=16)
        ax2.set_xlabel('Hand Number', fontsize=12)
        ax2.set_ylabel('P/L ($)', fontsize=12)
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.close()
    
    def plot_equity_distribution(self, equities: List[float],
                                filename: str = 'equity_dist.png'):
        """エクイティ分布を可視化"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        ax.hist(equities, bins=50, color=self.colors['equity'], 
               alpha=0.7, edgecolor='white')
        ax.axvline(x=np.mean(equities), color=self.colors['profit'], 
                  linestyle='--', linewidth=2, label=f'Mean: {np.mean(equities):.1%}')
        ax.set_title('Equity Distribution', fontsize=16)
        ax.set_xlabel('Equity', fontsize=12)
        ax.set_ylabel('Frequency', fontsize=12)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.close()
    
    def plot_position_performance(self, position_stats: Dict,
                                 filename: str = 'position_perf.png'):
        """ポジション別パフォーマンス"""
        positions = list(position_stats.keys())
        profits = [position_stats[p]['avg_profit'] for p in positions]
        win_rates = [position_stats[p]['win_rate'] for p in positions]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # 平均利益
        colors = [self.colors['profit'] if p > 0 else self.colors['loss'] for p in profits]
        ax1.bar(positions, profits, color=colors, alpha=0.7)
        ax1.axhline(y=0, color=self.colors['neutral'], linestyle='--')
        ax1.set_title('Average Profit by Position', fontsize=14)
        ax1.set_ylabel('Avg P/L ($)', fontsize=12)
        ax1.grid(True, alpha=0.3)
        
        # 勝率
        ax2.bar(positions, win_rates, color=self.colors['equity'], alpha=0.7)
        ax2.axhline(y=0.5, color=self.colors['neutral'], linestyle='--')
        ax2.set_title('Win Rate by Position', fontsize=14)
        ax2.set_ylabel('Win Rate', fontsize=12)
        ax2.set_ylim(0, 1)
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.close()
