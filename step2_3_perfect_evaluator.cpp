// step2_3_perfect_evaluator.cpp
#include <array>
#include <cstdint>
#include <algorithm>

namespace PokerEval {

using namespace PokerCore;

// ハンドランク定数
constexpr int RANK_STRAIGHT_FLUSH = 8;
constexpr int RANK_FOUR_OF_KIND = 7;
constexpr int RANK_FULL_HOUSE = 6;
constexpr int RANK_FLUSH = 5;
constexpr int RANK_STRAIGHT = 4;
constexpr int RANK_THREE_OF_KIND = 3;
constexpr int RANK_TWO_PAIR = 2;
constexpr int RANK_ONE_PAIR = 1;
constexpr int RANK_HIGH_CARD = 0;

// ルックアップテーブル (初期化時に生成)
class EvaluatorTables {
public:
    std::array<uint16_t, 8192> flush_lookup;
    std::array<uint16_t, 8192> unique5_lookup;
    
    EvaluatorTables() {
        init_flush_lookup();
        init_unique5_lookup();
    }
    
private:
    void init_flush_lookup() {
        // 13ビットの全組み合わせ（フラッシュの場合）
        for (int i = 0; i < 8192; ++i) {
            flush_lookup[i] = evaluate_flush_hand(i);
        }
    }
    
    uint16_t evaluate_flush_hand(int mask) {
        // ストレートフラッシュチェック
        if (is_straight(mask)) {
            int high = get_highest_straight(mask);
            return (RANK_STRAIGHT_FLUSH << 12) | (high << 8);
        }
        // 通常のフラッシュ
        return (RANK_FLUSH << 12) | get_top_cards(mask, 5);
    }
    
    bool is_straight(int mask) {
        // 5連続ビットをチェック
        for (int i = 8; i >= 0; --i) {
            if (((mask >> i) & 0x1F) == 0x1F) return true;
        }
        // A-2-3-4-5 (ホイール)
        return (mask & 0x100F) == 0x100F;
    }
    
    int get_highest_straight(int mask) {
        for (int i = 12; i >= 3; --i) {
            if (((mask >> (i-4)) & 0x1F) == 0x1F) return i;
        }
        return 3; // A-2-3-4-5
    }
    
    int get_top_cards(int mask, int count) {
        int result = 0;
        int found = 0;
        for (int i = 12; i >= 0 && found < count; --i) {
            if (mask & (1 << i)) {
                result |= (i << (found * 4));
                found++;
            }
        }
        return result;
    }
    
    void init_unique5_lookup() {
        // ユニークな5枚のカード評価
        for (int i = 0; i < 8192; ++i) {
            if (__builtin_popcount(i) == 5) {
                unique5_lookup[i] = evaluate_unique5(i);
            }
        }
    }
    
    uint16_t evaluate_unique5(int mask) {
        if (is_straight(mask)) {
            return (RANK_STRAIGHT << 12) | (get_highest_straight(mask) << 8);
        }
        return (RANK_HIGH_CARD << 12) | get_top_cards(mask, 5);
    }
};

static EvaluatorTables g_tables;

// 7枚からの最強5枚評価
class HandEvaluator {
public:
    static uint32_t evaluate_7cards(const Card cards[7]) {
        // ランクとスートのビットマスク
        std::array<uint16_t, 4> suit_masks = {0, 0, 0, 0};
        std::array<uint8_t, 13> rank_counts = {0};
        uint16_t rank_mask = 0;
        
        for (int i = 0; i < 7; ++i) {
            Rank r = get_rank(cards[i]);
            Suit s = get_suit(cards[i]);
            suit_masks[s] |= (1 << r);
            rank_counts[r]++;
            rank_mask |= (1 << r);
        }
        
        // フラッシュチェック
        for (int s = 0; s < 4; ++s) {
            if (__builtin_popcount(suit_masks[s]) >= 5) {
                return g_tables.flush_lookup[suit_masks[s]];
            }
        }
        
        // ペア系の判定
        return evaluate_non_flush(rank_counts, rank_mask);
    }
    
private:
    static uint32_t evaluate_non_flush(const std::array<uint8_t, 13>& counts, 
                                       uint16_t rank_mask) {
        int quads = -1, trips = -1;
        int pairs[2] = {-1, -1};
        int pair_count = 0;
        
        // 降順でスキャン（高いカードを優先）
        for (int r = 12; r >= 0; --r) {
            if (counts[r] == 4) quads = r;
            else if (counts[r] == 3) {
                if (trips == -1) trips = r;
            }
            else if (counts[r] == 2) {
                if (pair_count < 2) pairs[pair_count++] = r;
            }
        }
        
        // フォーカード
        if (quads != -1) {
            int kicker = get_highest_kicker(counts, quads);
            return (RANK_FOUR_OF_KIND << 12) | (quads << 8) | kicker;
        }
        
        // フルハウス
        if (trips != -1 && (pairs[0] != -1 || pair_count > 0)) {
            int pair = pairs[0];
            // トリップスが複数ある場合、2番目のトリップスをペアとする
            for (int r = 12; r >= 0; --r) {
                if (counts[r] == 3 && r != trips) {
                    pair = r;
                    break;
                }
            }
            return (RANK_FULL_HOUSE << 12) | (trips << 8) | pair;
        }
        
        // ストレート
        if (is_straight_from_mask(rank_mask)) {
            int high = get_straight_high(rank_mask);
            return (RANK_STRAIGHT << 12) | (high << 8);
        }
        
        // スリーカード
        if (trips != -1) {
            int kickers = get_top_kickers(counts, trips, 2);
            return (RANK_THREE_OF_KIND << 12) | (trips << 8) | kickers;
        }
        
        // ツーペア
        if (pair_count >= 2) {
            int kicker = get_highest_kicker_exclude(counts, pairs[0], pairs[1]);
            return (RANK_TWO_PAIR << 12) | (pairs[0] << 8) | (pairs[1] << 4) | kicker;
        }
        
        // ワンペア
        if (pair_count == 1) {
            int kickers = get_top_kickers(counts, pairs[0], 3);
            return (RANK_ONE_PAIR << 12) | (pairs[0] << 8) | kickers;
        }
        
        // ハイカード
        return g_tables.unique5_lookup[rank_mask & 0x1FFF];
    }
    
    static bool is_straight_from_mask(uint16_t mask) {
        for (int i = 8; i >= 0; --i) {
            if (((mask >> i) & 0x1F) == 0x1F) return true;
        }
        return (mask & 0x100F) == 0x100F; // A-5
    }
    
    static int get_straight_high(uint16_t mask) {
        for (int i = 12; i >= 4; --i) {
            if (((mask >> (i-4)) & 0x1F) == 0x1F) return i;
        }
        return 3; // A-5
    }
    
    static int get_highest_kicker(const std::array<uint8_t, 13>& counts, int exclude) {
        for (int r = 12; r >= 0; --r) {
            if (r != exclude && counts[r] > 0) return r;
        }
        return 0;
    }
    
    static int get_highest_kicker_exclude(const std::array<uint8_t, 13>& counts, 
                                         int ex1, int ex2) {
        for (int r = 12; r >= 0; --r) {
            if (r != ex1 && r != ex2 && counts[r] > 0) return r;
        }
        return 0;
    }
    
    static int get_top_kickers(const std::array<uint8_t, 13>& counts, 
                              int exclude, int n) {
        int result = 0;
        int found = 0;
        for (int r = 12; r >= 0 && found < n; --r) {
            if (r != exclude && counts[r] > 0) {
                result |= (r << (found * 4));
                found++;
            }
        }
        return result;
    }
};

} // namespace PokerEval

extern "C" {
    using namespace PokerEval;
    
    uint32_t evaluate_7cards_perfect(const PokerCore::Card cards[7]) {
        return HandEvaluator::evaluate_7cards(cards);
    }
}
