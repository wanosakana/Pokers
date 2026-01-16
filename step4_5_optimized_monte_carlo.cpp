// step4_5_optimized_monte_carlo.cpp
#include <immintrin.h>
#include <random>
#include <thread>
#include <vector>

namespace MonteCarloEngine {

using namespace PokerCore;
using namespace PokerEval;

class FastRNG {
private:
    uint64_t state;
    
public:
    explicit FastRNG(uint64_t seed) : state(seed) {}
    
    uint64_t next() {
        state ^= state << 13;
        state ^= state >> 7;
        state ^= state << 17;
        return state;
    }
    
    uint32_t next32() {
        return static_cast<uint32_t>(next());
    }
    
    int next_int(int max) {
        return next32() % max;
    }
};

class EquityCalculator {
public:
    struct Result {
        float equity;
        int wins;
        int ties;
        int losses;
        int iterations;
    };
    
    static Result calculate_equity(
        Card hero_card1, Card hero_card2,
        const Card* board, int board_count,
        int opponents,
        int iterations,
        uint64_t seed = 0
    ) {
        if (seed == 0) {
            std::random_device rd;
            seed = rd();
        }
        
        // マルチスレッド処理
        int num_threads = std::thread::hardware_concurrency();
        int iters_per_thread = iterations / num_threads;
        
        std::vector<std::thread> threads;
        std::vector<Result> results(num_threads);
        
        for (int t = 0; t < num_threads; ++t) {
            threads.emplace_back([&, t]() {
                results[t] = run_simulation(
                    hero_card1, hero_card2,
                    board, board_count,
                    opponents,
                    iters_per_thread,
                    seed + t
                );
            });
        }
        
        for (auto& thread : threads) {
            thread.join();
        }
        
        // 結果を集約
        Result final = {0, 0, 0, 0, 0};
        for (const auto& r : results) {
            final.wins += r.wins;
            final.ties += r.ties;
            final.losses += r.losses;
            final.iterations += r.iterations;
        }
        
        final.equity = static_cast<float>(final.wins + final.ties * 0.5f) / final.iterations;
        return final;
    }
    
private:
    static Result run_simulation(
        Card hero_card1, Card hero_card2,
        const Card* board, int board_count,
        int opponents,
        int iterations,
        uint64_t seed
    ) {
        Result result = {0, 0, 0, 0, iterations};
        FastRNG rng(seed);
        
        // 使用済みカードのマスク
        CardMask dead_cards = card_to_mask(hero_card1) | card_to_mask(hero_card2);
        for (int i = 0; i < board_count; ++i) {
            dead_cards |= card_to_mask(board[i]);
        }
        
        // 利用可能なデッキを作成
        std::array<Card, DECK_SIZE> deck;
        int deck_size = 0;
        for (int c = 0; c < DECK_SIZE; ++c) {
            if (!has_card(dead_cards, c)) {
                deck[deck_size++] = c;
            }
        }
        
        Card full_board[5];
        Card hero_hand[7];
        Card opp_hand[7];
        
        // ヒーローのハンド前半
        hero_hand[0] = hero_card1;
        hero_hand[1] = hero_card2;
        
        for (int iter = 0; iter < iterations; ++iter) {
            // デッキをシャッフル（Fisher-Yates）
            for (int i = deck_size - 1; i > 0; --i) {
                int j = rng.next_int(i + 1);
                std::swap(deck[i], deck[j]);
            }
            
            // ボードを完成させる
            int deck_pos = 0;
            for (int i = 0; i < board_count; ++i) {
                full_board[i] = board[i];
            }
            for (int i = board_count; i < 5; ++i) {
                full_board[i] = deck[deck_pos++];
            }
            
            // ヒーローのハンドを評価
            for (int i = 0; i < 5; ++i) {
                hero_hand[i + 2] = full_board[i];
            }
            uint32_t hero_score = evaluate_7cards_perfect(hero_hand);
            
            // 相手のハンドを評価
            bool won = true;
            bool tied = false;
            
            for (int opp = 0; opp < opponents; ++opp) {
                opp_hand[0] = deck[deck_pos++];
                opp_hand[1] = deck[deck_pos++];
                for (int i = 0; i < 5; ++i) {
                    opp_hand[i + 2] = full_board[i];
                }
                
                uint32_t opp_score = evaluate_7cards_perfect(opp_hand);
                
                if (opp_score > hero_score) {
                    won = false;
                    break;
                } else if (opp_score == hero_score) {
                    tied = true;
                }
            }
            
            if (won) {
                if (tied) result.ties++;
                else result.wins++;
            } else {
                result.losses++;
            }
        }
        
        return result;
    }
};

} // namespace MonteCarloEngine

extern "C" {
    using namespace MonteCarloEngine;
    
    float calculate_equity_optimized(
        uint8_t h1, uint8_t h2,
        const uint8_t* board, int board_count,
        int opponents, int iterations
    ) {
        auto result = EquityCalculator::calculate_equity(
            h1, h2, board, board_count, opponents, iterations
        );
        return result.equity;
    }
}
