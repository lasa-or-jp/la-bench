# LA-Bench: Laboratory Automation Benchmark

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Website](https://img.shields.io/badge/Website-LA--Bench-blue)](https://lasa-or-jp.github.io/la-bench/)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/lasa-or-jp/la-bench/blob/main/notebooks/baseline.ipynb)


実験手順生成タスクのためのベンチマークデータセット

## 🚀 Quick Start

### Google Colabで実行
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/lasa-or-jp/la-bench/blob/main/notebooks/baseline.ipynb)

上記ボタンをクリックして、ブラウザ上で即座にベースラインを実行できます。環境構築不要で、データセットのダウンロードから評価まで、すべての処理を体験できます。

## 📊 Dataset

| Dataset | Size | Purpose | Availability |
|---------|------|---------|--------------|
| Example | 10 | Development | ✅ Available |
| Public Test | 10 | Development Phase | 📅 2025-10-10 |
| Private Test | 10 | Test Phase | 📅 2025-11-13 |

## 📝 Data Format

### Input Format (YAML)
```yaml
experiment_id: "exp_001"
instruction: "T75フラスコ2本の線維芽細胞の培地交換をする"
protocols:
  - 準備するもの:
    - DMEM + 10% FBS培地
    - 70%エタノール
  - 手順:
    - 培地を37℃に温める
    - 古い培地を除去する
final_state:
  - 得られるもの: "培地交換済みのT75フラスコ2本"
  - 状態: "細胞は新しい培地中で培養継続"
```

### Output Format (YAML)
```yaml
experiment_id: "exp_001"
procedure:
  - step: 1
    action: "準備"
    details:
      - "クリーンベンチを70%エタノールで清拭する"
      - "培地DMEM + 10% FBSを37℃に温める"
    materials:
      - name: "70%エタノール"
        amount: "適量"
    equipment:
      - "クリーンベンチ"
    duration: "10分"
```

## 🎯 Evaluation Metrics

評価は以下の4つの観点で行われます：

- **正確性** (25%): 生成された手順の正確さ
- **論理的整合性** (25%): 手順の論理的な一貫性
- **網羅性** (25%): 必要な情報の網羅
- **実行可能性** (25%): 実際に実行可能な手順

## 🏗️ Repository Structure

```
la-bench/
├── data/
│   ├── example/          # Example dataset
│   ├── public_test/      # Public test dataset (Oct 10)
│   └── private_test/     # Private test dataset (Nov 13)
├── notebooks/
│   └── baseline.ipynb    # Google Colab notebook
├── docs/                 # Website files
└── submissions/          # Submission examples
```

## 💻 Baseline

ベースライン実装は[Google Colabノートブック](https://colab.research.google.com/github/lasa-or-jp/la-bench/blob/main/notebooks/baseline.ipynb)で提供しています。
以下の機能が含まれています：

- データセットの読み込みと前処理
- シンプルなベースラインモデル
- 評価メトリクスの計算
- 結果の可視化

## 📤 Submission

提出には以下が必要です：

1. **predictions.yaml** - 全ての予測結果
2. **notebook.ipynb** - Google Colabノートブック
3. **README.md** - 手法の説明

詳細は[Submission Guide](docs/submission-guide.md)を参照してください。

## 🔗 Links

- 🌐 [Competition Website](https://lasa-or-jp.github.io/la-bench/)
- 📊 [Leaderboard](https://lasa-or-jp.github.io/la-bench/#leaderboard)
- 📧 [Contact Form](https://docs.google.com/forms/d/e/1FAIpQLSdoJSoDHxWxy7bF7I-rWvs5sTQxtdzGjmAskJm1OzGd-qzkPw/viewform)
- 🏢 [LASA](https://lasa.or.jp/)

## 📅 Important Dates

- **2025-09-01**: Competition launch
- **2025-10-10**: Public test data release
- **2025-11-13**: Private test data release
- **2025-11-20**: Submission deadline
- **2025-12-20**: Results announcement

## 🏆 Organizers

**主催**: 一般社団法人 ラボラトリーオートメーション協会
**支援**: 一般社団法人 人工知能学会

## 🔒 セキュリティポリシー

**重要**: データセット構築に関する詳細な議論は、情報漏洩を防ぐため、GitHubではなくDiscordで運営メンバーのみで行われます。GitHubのissueやPRには、公開可能な情報のみを記載してください。

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Citation

```bibtex
@misc{labench2025,
  title={LA-Bench: Laboratory Automation Benchmark},
  author={Laboratory Automation Society of Japan},
  year={2025},
  howpublished={\url{https://github.com/lasa-or-jp/la-bench}}
}
```