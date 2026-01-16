// step8_mcts_complete.cpp
#include <vector>
#include <cmath>
#include <memory>
#include <random>

namespace MCTSEngine {

constexpr double EXPLORATION_CONSTANT = 1.41; // √2

struct MCTSNode {
    int visits = 0;
    double total_value = 0.0;
    int action = -1;
    MCTSNode* parent = nullptr;
    std::vector<std::unique_ptr<MCTSNode>> children;
    std::vector<int> untried_actions;
    bool is_terminal = false;
    
    double get_ucb1_score() const {
        if (visits == 0) return INFINITY;
        if (parent == nullptr) return 0.0;
        
        double exploitation = total_value / visits;
        double exploration = EXPLORATION_CONSTANT * 
                           std::sqrt(std::log(parent->visits) / visits);
        
        return exploitation + exploration;
    }
    
    double get_average_value() const {
        return visits > 0 ? total_value / visits : 0.0;
    }
};

class MCTSSearch {
private:
    std::unique_ptr<MCTSNode> root;
    std::mt19937 rng;
    int simulation_count = 0;
    
public:
    MCTSSearch(const std::vector<int>& legal_actions, uint64_t seed = 0) {
        root = std::make_unique<MCTSNode>();
        root->untried_actions = legal_actions;
        
        if (seed == 0) {
            std::random_device rd;
            seed = rd();
        }
        rng.seed(seed);
    }
    
    // 指定回数のシミュレーションを実行
    void search(int iterations) {
        for (int i = 0; i < iterations; ++i) {
            MCTSNode* node = root.get();
            
            // 1. Selection: UCB1で最も有望なノードを選択
            while (node->untried_actions.empty() && !node->children.empty()) {
                node = select_best_child(node);
            }
            
            // 2. Expansion: 未試行のアクションを展開
            if (!node->untried_actions.empty() && !node->is_terminal) {
                node = expand(node);
            }
            
            // 3. Simulation: ランダムプレイアウト
            double value = simulate(node);
            
            // 4. Backpropagation: 結果を伝播
            backpropagate(node, value);
            
            simulation_count++;
        }
    }
    
    // 最良のアクションを取得（訪問回数ベース）
    int get_best_action() const {
        if (root->children.empty()) return -1;
        
        MCTSNode* best = nullptr;
        int max_visits = 0;
        
        for (const auto& child : root->children) {
            if (child->visits > max_visits) {
                max_visits = child->visits;
                best = child.get();
            }
        }
        
        return best ? best->action : -1;
    }
    
    // 訪問回数ベースの確率分布を取得
    std::vector<double> get_policy_distribution() const {
        std::vector<double> distribution(root->children.size(), 0.0);
        int total_visits = 0;
        
        for (const auto& child : root->children) {
            total_visits += child->visits;
        }
        
        if (total_visits > 0) {
            for (size_t i = 0; i < root->children.size(); ++i) {
                distribution[i] = static_cast<double>(root->children[i]->visits) / total_visits;
            }
        }
        
        return distribution;
    }
    
    // 統計情報を取得
    struct Statistics {
        int total_simulations;
        int tree_depth;
        int node_count;
        double best_value;
    };
    
    Statistics get_statistics() const {
        Statistics stats;
        stats.total_simulations = simulation_count;
        stats.tree_depth = calculate_tree_depth(root.get());
        stats.node_count = count_nodes(root.get());
        
        if (!root->children.empty()) {
            double best = -INFINITY;
            for (const auto& child : root->children) {
                best = std::max(best, child->get_average_value());
            }
            stats.best_value = best;
        } else {
            stats.best_value = 0.0;
        }
        
        return stats;
    }
    
private:
    MCTSNode* select_best_child(MCTSNode* node) {
        MCTSNode* best = nullptr;
        double best_score = -INFINITY;
        
        for (const auto& child : node->children) {
            double score = child->get_ucb1_score();
            if (score > best_score) {
                best_score = score;
                best = child.get();
            }
        }
        
        return best;
    }
    
    MCTSNode* expand(MCTSNode* node) {
        // ランダムに未試行アクションを選択
        std::uniform_int_distribution<> dist(0, node->untried_actions.size() - 1);
        int idx = dist(rng);
        int action = node->untried_actions[idx];
        
        // リストから削除
        node->untried_actions.erase(node->untried_actions.begin() + idx);
        
        // 新しい子ノードを作成
        auto child = std::make_unique<MCTSNode>();
        child->action = action;
        child->parent = node;
        
        // ゲーム状態を進めて合法手を設定（実際のゲームロジック）
        child->untried_actions = get_legal_actions_after(action);
        child->is_terminal = is_terminal_state_after(action);
        
        MCTSNode* child_ptr = child.get();
        node->children.push_back(std::move(child));
        
        return child_ptr;
    }
    
    double simulate(MCTSNode* node) {
        // ランダムプレイアウト
        // 実際のゲームでは、ヒューリスティックなポリシーを使用
        
        if (node->is_terminal) {
            return evaluate_terminal_state();
        }
        
        // ランダムに最後まで進める
        int depth = 0;
        const int max_depth = 100;
        
        while (depth < max_depth && !is_terminal_in_simulation()) {
            auto actions = get_available_actions_simulation();
            if (actions.empty()) break;
            
            std::uniform_int_distribution<> dist(0, actions.size() - 1);
            int action = actions[dist(rng)];
            
            apply_action_simulation(action);
            depth++;
        }
        
        double value = evaluate_final_state();
        revert_simulation_state(depth);
        
        return value;
    }
    
    void backpropagate(MCTSNode* node, double value) {
        while (node != nullptr) {
            node->visits++;
            node->total_value += value;
            
            // 相手のターンでは価値を反転
            value = -value;
            node = node->parent;
        }
    }
    
    int calculate_tree_depth(const MCTSNode* node) const {
        if (node->children.empty()) return 0;
        
        int max_depth = 0;
        for (const auto& child : node->children) {
            max_depth = std::max(max_depth, calculate_tree_depth(child.get()));
        }
        
        return max_depth + 1;
    }
    
    int count_nodes(const MCTSNode* node) const {
        int count = 1;
        for (const auto& child : node->children) {
            count += count_nodes(child.get());
        }
        return count;
    }
    
    // ゲーム固有の関数（実装は省略）
    std::vector<int> get_legal_actions_after(int action) { return {}; }
    bool is_terminal_state_after(int action) { return false; }
    double evaluate_terminal_state() { return 0.0; }
    bool is_terminal_in_simulation() { return false; }
    std::vector<int> get_available_actions_simulation() { return {}; }
    void apply_action_simulation(int action) {}
    double evaluate_final_state() { return 0.0; }
    void revert_simulation_state(int depth) {}
};

} // namespace MCTSEngine
