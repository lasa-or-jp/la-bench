# LA-Bench 2025: 実験手順生成トラック

## 概要

LA-Bench 2025は、実験指示とプロトコルから実行可能な実験手順を自動生成するAIコンペティションです。生命科学実験の自動化（Laboratory Automation）の実現に向けて、専門的な実験手順の生成能力を競います。

### 背景

近年のAI技術の発展により、計算機内での研究自動化は進展していますが、実験科学の自動化には物理的な実験手順の詳細化が必要です。本コンペティションは、このギャップを埋めることを目的としています。

## タスク内容

### 入力
- **実験指示**: 実験目的を含む要件（例：「T75フラスコ2本の線維芽細胞の培地交換をする」）
- **プロトコル**: 参照する作業テンプレート（PDF形式）

### 出力
- **実験手順**: 具体的な名称、数値、単位を含む実行可能な手順（YAML形式）

## スケジュール

| 日付 | 内容 |
|------|------|
| 2025-09-01 | 公式サイト公開・参加登録開始 |
| 2025-10-10 | Public Test Dataset 公開 |
| 2025-11-13 | Private Test Dataset 公開 |
| 2025-11-20 | 提出締切 |
| 2025-12-20 | 結果公開 |
| 2026-05 | 人工知能学会全国大会にて表彰・発表 |

## データセット

- **Example Dataset**: 10件（手法開発用）
- **Public Test Dataset**: 10件（Development Phase評価用）
- **Private Test Dataset**: 10件（Test Phase評価用）

## 評価方法

### Development Phase
- LLM評価によるスコアリング
- リーダーボードでのリアルタイム順位表示

### Test Phase
- 第1次評価：LLM評価（全チーム対象）
- 第2次評価：専門家評価（上位10チーム対象）

### 評価観点
- 正確性
- 論理的整合性
- 必要な情報の網羅性
- 暗黙的要件の理解

## 賞金

### LLM評価部門
- 最優秀賞: 10万円
- 優秀賞: 5万円

### 専門家評価部門
- 最優秀賞: 10万円
- 優秀賞: 5万円

## 参加方法

1. GitHubリポジトリからデータセットとサンプルコードをダウンロード
2. 実験手順生成システムを開発
3. 指定フォーマットで結果を提出
4. Google Colabノートブックとドキュメントの提出が必須

## リポジトリ構成

```
la-bench/
├── data/                    # データセット
│   ├── example/            # Example Dataset
│   ├── public_test/        # Public Test Dataset
│   └── private_test/       # Private Test Dataset (開催後公開)
├── code/                   # コード
│   ├── baseline/           # ベースラインコード
│   └── evaluation/         # 評価スクリプト
├── docs/                   # ドキュメント
│   └── _site/             # GitHub Pages用
└── submissions/           # 提出サンプル
```

## 参加規則

- コード提出義務：Google ColabノートブックとREADMEの提出必須
- 発表義務：受賞チームは人工知能学会全国大会での発表必須

## 主催・後援

- **責任者**: 山田 涼太（Science Aid株式会社）
- **後援**: 一般社団法人 ラボラトリーオートメーション協会（LASA）

## お問い合わせ

コンペティションに関するお問い合わせは、[Issues](https://github.com/lasa-jp/la-bench/issues)からお願いします。

## ライセンス

本リポジトリのコンテンツは[MITライセンス](LICENSE)の下で公開されています。