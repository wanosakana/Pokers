// step9_eqr_complete.cpp
#include <cmath>
#include <algorithm>
#include <array>

namespace EQRCalculator {

// ポジションファクター（詳細版）
struct PositionFactors {
    static constexpr std::array<double, 9> FACTORS = {
        0.75,  // UTG
        0.78,  // UTG+1
        0.82,  // UTG+2
        0.86,  // MP
        0.92,  // HJ (Hijack)
        0.98,  // CO (Cutoff)
        1.18,  // BTN (Button)
        0.70,  // SB (Small Blind)
        0.68   // BB (Big Blind)
    };
    
    static double get_factor(int position) {
        return FACTORS[std::min(position, 8)];
    }
};

// スタックデプスファクター
class StackDepthAdjustment {
public:
    static double calculate(double spr) {
        // SPR (Stack-to-Pot Ratio) に基づく調整
        if (spr < 1.0) {
            return 1.25;  // ほぼコミット状態
        } else if (spr < 3.0) {
            return 1.15;  // ショートスタック
        } else if (spr < 7.0) {
            return 1.05;  // ミディアムスタック
        } else if (spr < 13.0) {
            return 1.00;  // 標準
        } else if (spr < 25.0) {
            return 0.95;  // ディープスタック
        } else {
            return 0.90;  // 非常にディープ
        }
    }
};

// ボードテクスチャファクター
class BoardTextureAdjustment {
public:
    static double calculate(int texture_score, bool in_position) {
        // texture_score: 0=dry, 1=semi-wet, 2=wet
        
        if (texture_score == 0) { // Dry board
            return in_position ? 1.08 : 0.95;
        } else if (texture_score == 1) { // Semi-wet
            return in_position ? 1.02 : 0.98;
        } else { // Wet board
            return in_position ? 0.95 : 0.92;
        }
    }
};

// マルチウェイファクター
class MultiwayAdjustment {
public:
    static double calculate(int opponents) {
        // 相手が多いほど実現勝率は低下
        return 1.0 / (1.0 + 0.18 * (opponents - 1));
    }
};

// スキルファクター（相手の強さ）
class SkillAdjustment {
public:
    static double calculate(double opponent_skill) {
        // opponent_skill: 0.0 (weak) ~ 1.0 (strong)
        // 強い相手ほどEQRは低下
        return 1.05 - (opponent_skill * 0.15);
    }
};

// 統合EQR計算
class EQREngine {
public:
    struct EQRResult {
        double raw_equity;
        double eqr;
        double position_factor;
        double stack_factor;
        double board_factor;
        double multiway_factor;
        double skill_factor;
    };
    
    static EQRResult calculate_complete(
        double raw_equity,
        int position,
        double stack,
        double pot,
        int board_texture,
        int opponents,
        bool in_position,
        double opponent_skill = 0.5
    ) {
        EQRResult result;
        result.raw_equity = raw_equity;
        
        // 各ファクターを計算
        result.position_factor = PositionFactors::get_factor(position);
        
        double spr = pot > 0 ? stack / pot : 100.0;
        result.stack_factor = StackDepthAdjustment::calculate(spr);
        
        result.board_factor = BoardTextureAdjustment::calculate(board_texture, in_position);
        result.multiway_factor = MultiwayAdjustment::calculate(opponents);
        result.skill_factor = SkillAdjustment::calculate(opponent_skill);
        
        // 総合EQR
        result.eqr = raw_equity * 
                    result.position_factor *
                    result.stack_factor *
                    result.board_factor *
                    result.multiway_factor *
                    result.skill_factor;
        
        // 0-1の範囲にクリップ
        result.eqr = std::min(1.0, std::max(0.0, result.eqr));
        
        return result;
    }
    
    // ストリート別のEQR調整
    static double adjust_for_street(double eqr, int street) {
        // street: 0=preflop, 1=flop, 2=turn, 3=river
        constexpr std::array<double, 4> STREET_FACTORS = {0.95, 1.00, 1.03, 1.05};
        return eqr * STREET_FACTORS[std::min(street, 3)];
    }
};

} // namespace EQRCalculator

extern "C" {
    using namespace EQRCalculator;
    
    double calculate_eqr_advanced(
        double raw_equity,
        int position,
        double stack,
        double pot,
        int board_texture,
        int opponents,
        bool in_position,
        double opponent_skill
    ) {
        auto result = EQREngine::calculate_complete(
            raw_equity, position, stack, pot,
            board_texture, opponents, in_position, opponent_skill
        );
        return result.eqr;
    }
}
