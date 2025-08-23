# LA-Bench: Laboratory Automation Benchmark

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Website](https://img.shields.io/badge/Website-LA--Bench-blue)](https://lasa-or-jp.github.io/la-bench/)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/lasa-or-jp/la-bench/blob/main/notebooks/baseline.ipynb)

🌐 **[公式Webサイト](https://lasa-or-jp.github.io/la-bench/)** | 📧 **[お問い合わせ](https://docs.google.com/forms/d/e/1FAIpQLSdoJSoDHxWxy7bF7I-rWvs5sTQxtdzGjmAskJm1OzGd-qzkPw/viewform)**


実験手順生成タスクのためのベンチマークデータセット

## 🚀 クイックスタート

### Google Colabで実行
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/lasa-or-jp/la-bench/blob/main/notebooks/baseline.ipynb)

上記ボタンをクリックして、ブラウザ上で即座にベースラインを実行できます。環境構築不要で、データセットのダウンロードから評価まで、すべての処理を体験できます。

## 📊 データセット

| Dataset | Size | Purpose | Availability |
|---------|------|---------|--------------|
| Example | 10 | Development Phase | 📅 2025-09-10 |
| Public Test | 10 | Development Phase | 📅 2025-10-10 |
| Private Test | 10 | Test Phase | 📅 2025-11-13 |

## 📝 データフォーマット

### 入力フォーマット (YAML)
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

### 出力フォーマット (YAML)
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

## 🎯 評価メトリクス

評価メトリクスは現在調整中です。決定次第、詳細を公開いたします。

## 🏗️ リポジトリ構成

```
la-bench/
├── data/
│   ├── example/          # Example dataset
│   ├── public_test/      # Public test dataset (Oct 10)
│   └── private_test/     # Private test dataset (Nov 13)
├── notebooks/
│   └── baseline.ipynb    # Google Colab notebook
└── docs/                 # Website files
```

## 💻 ベースライン実装

ベースライン実装は[Google Colabノートブック](https://colab.research.google.com/github/lasa-or-jp/la-bench/blob/main/notebooks/baseline.ipynb)で提供しています。
以下の機能が含まれています：

- データセットの読み込みと前処理
- シンプルなベースラインモデル
- 評価メトリクスの計算
- 結果の可視化

## 📤 提出方法

提出には以下が必要です：

1. **predictions.yaml** - 全ての予測結果
2. **notebook.ipynb** - Google Colabノートブック
3. **README.md** - 手法の説明

提出方法の詳細は現在準備中です。決定次第、公開いたします。

## 📅 スケジュール

| 日付        | 内容                                                                 |
|-------------|----------------------------------------------------------------------|
| 2025-09-10  | 公式サイト公開・参加登録開始<br>ルール、Example Dataset、サンプルコード 公開 |
| 2025-10-10  | Public Test Dataset 公開                                             |
| 2025-11-13  | Private Test Dataset 公開                                            |
| 2025-11-20  | 提出締切                                                             |
| 2025-12-20  | 結果公開                                                             |
| 2026-02-01  | 人工知能学会 全国大会 予稿提出締切                                   |
| 2026-05     | 人工知能学会 全国大会にて表彰・発表                                  |

## 🏆 主催・支援

- **主催**: 一般社団法人 ラボラトリーオートメーション協会
- **支援**: 一般社団法人 人工知能学会

## 🔒 セキュリティポリシー

**重要**: データセット構築に関する詳細な議論は、情報漏洩を防ぐため、GitHubではなくDiscordで運営メンバーのみで行われます。GitHubのissueやPRには、公開可能な情報のみを記載してください。

## 💰 スポンサー

LA-Bench 2025の運営費および賞金の充実のため、スポンサーを募集しています。
ご支援いただいた企業・団体様のロゴを本サイトに掲載させていただきます。

詳細については[お問い合わせフォーム](https://docs.google.com/forms/d/e/1FAIpQLSdoJSoDHxWxy7bF7I-rWvs5sTQxtdzGjmAskJm1OzGd-qzkPw/viewform)よりご連絡ください。

## 📜 ライセンス

本プロジェクトはMITライセンスの下で公開されています。詳細は[LICENSE](LICENSE)ファイルをご参照ください。

## 🤝 引用

```bibtex
@misc{labench2025,
  title={LA-Bench: Laboratory Automation Benchmark},
  author={Laboratory Automation Society of Japan},
  year={2025},
  howpublished={\url{https://github.com/lasa-or-jp/la-bench}}
}
```
