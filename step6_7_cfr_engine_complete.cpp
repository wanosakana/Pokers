// step6_7_cfr_engine_complete.cpp
#include <map>
#include <vector>
#include <string>
#include <cmath>
#include <algorithm>
#include <memory>

namespace CFREngine {

using Action = int;
using Utility = double;

// 情報セット（ゲーム状態の抽象化）
struct InfoSet {
    std::map<Action, double> regret_sum;
    std::map<Action, double> strategy_sum;
    int visit_count = 0;
    
    // 現在の戦略を取得（Regret Matching）
    std::map<Action, double> get_strategy(const std::vector<Action>& legal_actions) {
        std::map<Action, double> strategy;
        double normalizing_sum = 0.0;
        
        for (Action a : legal_actions) {
            // CFR+: 負の後悔値を0にクリップ
            double regret = std::max(0.0, regret_sum[a]);
            strategy[a] = regret;
            normalizing_sum += regret;
        }
        
        // 正規化
        if (normalizing_sum > 0) {
            for (Action a : legal_actions) {
                strategy[a] /= normalizing_sum;
            }
        } else {
            // 均等分布
            double uniform = 1.0 / legal_actions.size();
            for (Action a : legal_actions) {
                strategy[a] = uniform;
            }
        }
        
        return strategy;
    }
    
    // 平均戦略を取得（最終出力用）
    std::map<Action, double> get_average_strategy(const std::vector<Action>& legal_actions) {
        std::map<Action, double> avg_strategy;
        double normalizing_sum = 0.0;
        
        for (Action a : legal_actions) {
            normalizing_sum += strategy_sum[a];
        }
        
        if (normalizing_sum > 0) {
            for (Action a : legal_actions) {
                avg_strategy[a] = strategy_sum[a] / normalizing_sum;
            }
        } else {
            double uniform = 1.0 / legal_actions.size();
            for (Action a : legal_actions) {
                avg_strategy[a] = uniform;
            }
        }
        
        return avg_strategy;
    }
    
    // 戦略を蓄積（Linear CFR）
    void accumulate_strategy(const std::map<Action, double>& strategy, int iteration) {
        // Linear weighting: より最近の戦略に重みを付ける
        double weight = static_cast<double>(iteration) / (iteration + 1);
        for (const auto& [action, prob] : strategy) {
            strategy_sum[action] += prob * weight;
        }
    }
    
    // 後悔値を更新（CFR+）
    void update_regrets(const std::map<Action, double>& regrets, double weight) {
        for (const auto& [action, regret] : regrets) {
            regret_sum[action] += weight * regret;
            // CFR+: 負の後悔値を即座に0にする
            regret_sum[action] = std::max(0.0, regret_sum[action]);
        }
    }
};

// CFRソルバー
class CFRSolver {
private:
    std::map<std::string, InfoSet> info_sets;
    int iteration = 0;
    double discount_alpha = 1.5;  // Discounted CFR用
    double discount_beta = 0.5;
    
public:
    // CFRイテレーション
    void train(int iterations) {
        for (int i = 0; i < iterations; ++i) {
            iteration++;
            
            // プレイヤー1とプレイヤー2の視点で交互に学習
            for (int player = 0; player < 2; ++player) {
                cfr_recursive(0, player, 1.0, 1.0);
            }
            
            // Discounted CFR: 定期的に後悔値を割引
            if (iteration % 100 == 0) {
                discount_regrets();
            }
        }
    }
    
    // 再帰的CFR
    Utility cfr_recursive(int depth, int player, double pi_reach_player, double pi_reach_opponent) {
        // 簡易的なゲームツリー（実際にはポーカー特有のロジックを実装）
        // ここでは抽象化したゲーム進行を仮定
        
        // 終端ノードの判定
        if (is_terminal()) {
            return get_payoff(player);
        }
        
        // チャンスノード（カードが配られる）
        if (is_chance_node()) {
            return handle_chance_node(depth, player, pi_reach_player, pi_reach_opponent);
        }
        
        // 現在のプレイヤーが行動する
        if (get_current_player() == player) {
            return handle_player_node(depth, player, pi_reach_player, pi_reach_opponent);
        } else {
            return handle_opponent_node(depth, player, pi_reach_player, pi_reach_opponent);
        }
    }
    
private:
    Utility handle_player_node(int depth, int player, double pi_reach_player, double pi_reach_opponent) {
        std::string info_set_key = get_info_set_key();
        InfoSet& info_set = info_sets[info_set_key];
        
        std::vector<Action> legal_actions = get_legal_actions();
        auto strategy = info_set.get_strategy(legal_actions);
        
        std::map<Action, Utility> action_utilities;
        Utility node_utility = 0.0;
        
        // 各アクションの効用を計算
        for (Action action : legal_actions) {
            double action_prob = strategy[action];
            
            // 再帰的に子ノードを評価
            Utility utility = cfr_recursive(
                depth + 1, 
                player,
                pi_reach_player * action_prob,
                pi_reach_opponent
            );
            
            action_utilities[action] = utility;
            node_utility += action_prob * utility;
        }
        
        // 後悔値を計算
        std::map<Action, double> regrets;
        for (Action action : legal_actions) {
            regrets[action] = action_utilities[action] - node_utility;
        }
        
        // 後悔値を更新
        info_set.update_regrets(regrets, pi_reach_opponent);
        
        // 戦略を蓄積
        info_set.accumulate_strategy(strategy, iteration);
        info_set.visit_count++;
        
        return node_utility;
    }
    
    Utility handle_opponent_node(int depth, int player, double pi_reach_player, double pi_reach_opponent) {
        std::string info_set_key = get_info_set_key();
        InfoSet& info_set = info_sets[info_set_key];
        
        std::vector<Action> legal_actions = get_legal_actions();
        auto strategy = info_set.get_strategy(legal_actions);
        
        Utility node_utility = 0.0;
        
        // 相手の戦略に従って期待値を計算
        for (Action action : legal_actions) {
            double action_prob = strategy[action];
            
            Utility utility = cfr_recursive(
                depth + 1,
                player,
                pi_reach_player,
                pi_reach_opponent * action_prob
            );
            
            node_utility += action_prob * utility;
        }
        
        return node_utility;
    }
    
    Utility handle_chance_node(int depth, int player, double pi_reach_player, double pi_reach_opponent) {
        // チャンスノード（例：フロップが配られる）
        // 全ての可能性を確率で重み付け
        Utility expected_utility = 0.0;
        
        auto outcomes = get_chance_outcomes();
        for (const auto& [outcome, probability] : outcomes) {
            apply_chance_outcome(outcome);
            expected_utility += probability * cfr_recursive(
                depth + 1, player, pi_reach_player, pi_reach_opponent
            );
            revert_chance_outcome(outcome);
        }
        
        return expected_utility;
    }
    
    void discount_regrets() {
        // Discounted CFR: 古い後悔値を割引
        for (auto& [key, info_set] : info_sets) {
            for (auto& [action, regret] : info_set.regret_sum) {
                regret *= std::pow(discount_alpha, -1.0);
            }
            for (auto& [action, strategy] : info_set.strategy_sum) {
                strategy *= std::pow(discount_beta, -1.0);
            }
        }
    }
    
    // ゲーム状態の判定（実際のポーカーロジックを実装）
    bool is_terminal() { return false; }
    bool is_chance_node() { return false; }
    int get_current_player() { return 0; }
    std::string get_info_set_key() { return "example_state"; }
    std::vector<Action> get_legal_actions() { return {0, 1, 2}; }
    Utility get_payoff(int player) { return 0.0; }
    std::vector<std::pair<int, double>> get_chance_outcomes() { return {}; }
    void apply_chance_outcome(int outcome) {}
    void revert_chance_outcome(int outcome) {}
    
public:
    // 最適戦略を取得
    std::map<Action, double> get_strategy(const std::string& info_set_key, 
                                         const std::vector<Action>& legal_actions) {
        if (info_sets.find(info_set_key) == info_sets.end()) {
            // 均等分布を返す
            std::map<Action, double> uniform;
            double prob = 1.0 / legal_actions.size();
            for (Action a : legal_actions) {
                uniform[a] = prob;
            }
            return uniform;
        }
        
        return info_sets[info_set_key].get_average_strategy(legal_actions);
    }
    
    // エクスプロイタビリティを計算（収束度の指標）
    double compute_exploitability() {
        double total_exploit = 0.0;
        
        for (const auto& [key, info_set] : info_sets) {
            if (info_set.visit_count > 0) {
                // ベストレスポンスとの差
                double best_response_value = 0.0;
                double strategy_value = 0.0;
                
                // 簡易計算
                for (const auto& [action, regret] : info_set.regret_sum) {
                    best_response_value += std::max(0.0, regret);
                }
                
                total_exploit += best_response_value;
            }
        }
        
        return total_exploit / info_sets.size();
    }
};

} // namespace CFREngine

extern "C" {
    using namespace CFREngine;
    
    void* create_cfr_solver() {
        return new CFRSolver();
    }
    
    void destroy_cfr_solver(void* solver) {
        delete static_cast<CFRSolver*>(solver);
    }
    
    void cfr_train(void* solver, int iterations) {
        static_cast<CFRSolver*>(solver)->train(iterations);
    }
    
    double cfr_exploitability(void* solver) {
        return static_cast<CFRSolver*>(solver)->compute_exploitability();
    }
}
