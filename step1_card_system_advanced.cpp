// step1_card_system_advanced.cpp
#include <cstdint>
#include <array>
#include <algorithm>
#include <cassert>

namespace PokerCore {

// カード表現: 0-51 (0-12: スペード, 13-25: ハート, 26-38: ダイヤ, 39-51: クラブ)
using Card = uint8_t;
using CardMask = uint64_t;

constexpr int RANK_COUNT = 13;
constexpr int SUIT_COUNT = 4;
constexpr int DECK_SIZE = 52;

// ランクとスートの定数
enum Rank : uint8_t {
    RANK_2 = 0, RANK_3, RANK_4, RANK_5, RANK_6, RANK_7, RANK_8,
    RANK_9, RANK_T, RANK_J, RANK_Q, RANK_K, RANK_A
};

enum Suit : uint8_t {
    SUIT_SPADES = 0, SUIT_HEARTS, SUIT_DIAMONDS, SUIT_CLUBS
};

// インライン関数で高速化
inline Card make_card(Rank rank, Suit suit) {
    return static_cast<Card>(suit * RANK_COUNT + rank);
}

inline Rank get_rank(Card card) {
    return static_cast<Rank>(card % RANK_COUNT);
}

inline Suit get_suit(Card card) {
    return static_cast<Suit>(card / RANK_COUNT);
}

inline CardMask card_to_mask(Card card) {
    return 1ULL << card;
}

inline bool has_card(CardMask mask, Card card) {
    return (mask & card_to_mask(card)) != 0;
}

inline CardMask add_card(CardMask mask, Card card) {
    return mask | card_to_mask(card);
}

inline CardMask remove_card(CardMask mask, Card card) {
    return mask & ~card_to_mask(card);
}

inline int count_cards(CardMask mask) {
    return __builtin_popcountll(mask);
}

// デッキ生成
class Deck {
private:
    std::array<Card, DECK_SIZE> cards;
    int position;
    
public:
    Deck() : position(0) {
        for (int i = 0; i < DECK_SIZE; ++i) {
            cards[i] = static_cast<Card>(i);
        }
    }
    
    void shuffle(uint64_t seed) {
        // Xorshift64
        position = 0;
        for (int i = DECK_SIZE - 1; i > 0; --i) {
            seed ^= seed << 13;
            seed ^= seed >> 7;
            seed ^= seed << 17;
            int j = seed % (i + 1);
            std::swap(cards[i], cards[j]);
        }
    }
    
    Card deal() {
        assert(position < DECK_SIZE);
        return cards[position++];
    }
    
    void reset() {
        position = 0;
    }
    
    void exclude_cards(CardMask excluded) {
        int write_pos = 0;
        for (int i = 0; i < DECK_SIZE; ++i) {
            if (!has_card(excluded, cards[i])) {
                cards[write_pos++] = cards[i];
            }
        }
        // 残りを無効化
        for (int i = write_pos; i < DECK_SIZE; ++i) {
            cards[i] = 255; // 無効マーカー
        }
    }
};

} // namespace PokerCore

extern "C" {
    using namespace PokerCore;
    
    Card create_card_c(int rank, int suit) {
        return make_card(static_cast<Rank>(rank), static_cast<Suit>(suit));
    }
    
    int get_rank_c(Card card) {
        return get_rank(card);
    }
    
    int get_suit_c(Card card) {
        return get_suit(card);
    }
}
