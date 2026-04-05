"""分析パラメータ設定

全分析モジュールのハードコード閾値を一箇所に集約。
チューニング時はこのファイルのみ変更する。
"""

# 項目分析 (CTT)
ITEM_ANALYSIS = {
    "percentile_cutoff": 0.27,       # 上位/下位群の分割点（27%ルール）
    "flag_difficulty_low": 0.10,     # 難しすぎる問題の閾値
    "flag_difficulty_high": 0.90,    # 易しすぎる問題の閾値
    "flag_discrimination_low": 0.20, # 識別力不足の閾値
}

# アソシエーションルール
ASSOCIATION = {
    "min_support": 0.15,         # 最小支持度
    "min_confidence": 0.50,      # 最小信頼度
    "min_lift": 1.2,             # 最小リフト
    "fallback_support": 0.10,    # ルール未検出時の緩和支持度
    "fallback_confidence": 0.40, # ルール未検出時の緩和信頼度
    "fallback_lift": 1.1,        # ルール未検出時の緩和リフト
    "mastery_threshold": 0.50,   # スキル習得判定の正答率閾値
    "top_patterns": 15,          # 出力するパターン上限数
}

# ネットワーク分析
NETWORK = {
    "partial_corr_threshold": 0.08,  # 偏相関のエッジ閾値
    "ridge_alpha": 0.01,             # 正則化パラメータ
}

# 生徒タイプ分類 (GMM)
STUDENT_TYPES = {
    "max_k": 8,                      # 最大クラス数
    "min_k": 2,                      # 最小クラス数
    "covariance_type": "full",       # 共分散タイプ
    "n_init": 10,                    # 初期化回数
}

# 相互情報量
MUTUAL_INFO = {
    "n_neighbors": 5,                # MI推定のk近傍数
    "nonlinear_threshold": 0.15,     # MI高/相関低の検出閾値
    "correlation_low": 0.3,          # 「相関が低い」と判定する閾値
}

# 教科別分析
SUBJECT_ANALYSIS = {
    "mastery_threshold": 0.60,       # スキル習得判定の閾値
}

# 教科横断分析
CROSS_SUBJECT = {
    "prerequisite_confirmed": 0.30,  # 前提チェーン「確認」の相関閾値
    "prerequisite_weak": 0.15,       # 「弱い関連」の相関閾値
    "min_sample_size": 30,           # 相関計算の最小サンプルサイズ
}

# 生徒プロファイル
STUDENT_PROFILER = {
    "grade_drop_threshold": 3.0,     # 成績低下と判定する点数差
    "balanced_scale": 0.3,           # Balanced指標のスケーリング係数
}
