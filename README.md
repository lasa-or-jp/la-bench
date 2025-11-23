# LA-Bench: Laboratory Automation Benchmark

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Website](https://img.shields.io/badge/Website-LA--Bench-blue)](https://lasa-or-jp.github.io/la-bench/)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/lasa-or-jp/la-bench/blob/main/notebooks/baseline.ipynb)

🌐 **[公式Webサイト](https://lasa-or-jp.github.io/la-bench/)** | 📝 **[参加登録](https://docs.google.com/forms/d/e/1FAIpQLScXfW7lWC3NpfbvMfj9Nkg5eG76t51jKto2XtSfbV7GvWcLLQ/viewform)** | 🏅 **[リーダーボード](https://la-bench-leaderboard.onrender.com/)** | 📧 **[お問い合わせ](https://docs.google.com/forms/d/e/1FAIpQLSdoJSoDHxWxy7bF7I-rWvs5sTQxtdzGjmAskJm1OzGd-qzkPw/viewform)**


実験手順生成タスクのためのベンチマークデータセット

## 🚀 クイックスタート

### Google Colabで実行
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/lasa-or-jp/la-bench/blob/main/notebooks/baseline.ipynb)

上記ボタンをクリックして、ブラウザ上で即座にベースラインを実行できます。環境構築不要で、データセットのダウンロードから評価まで、すべての処理を体験できます。

## 📊 データセット

| Dataset | Size | Purpose | Availability |
|---------|------|---------|--------------|
| Example | 5 | Development Phase | 📅 2025-09-13 |
| Public Test | 10 | Development Phase | 📅 2025-10-10 |
| Private Test | 10 | Test Phase | 📅 2025-11-14 |

## 📝 データフォーマット

### 入力 (Input)

各問題には以下の情報が含まれます：

| フィールド | 日本語名 | 型 | 説明 |
|-----------|---------|-----|------|
| `instruction` | 実験指示 | str | 実験の目的と要求事項 |
| `mandatory_objects` | 使用する物品 | list[str] | 使用する物品（機器、ラボウェア、サンプルなど）<br>**記載内容**:<br>- `procedure_steps`で必ず使用する物品を列挙 |
| `source_protocol_steps` | 元プロトコルの手順 | list[dict] | 参考となる元の実験手順<br>- `id`: int - ステップ番号<br>- `text`: str - 手順内容 |
| `expected_final_states` | 期待される最終状態 | list[str] | 最終的に得られるサンプルや重要な中間生成物とその状態<br>**記載内容**:<br>- 最終的に得られるサンプル（生成物）<br>- 重要な中間生成物とその状態 |
| `references` | 参考文献 | list[dict] | 関連する論文や資料のURL<br>- `id`: int - 参考文献番号<br>- `text`: str - 参考文献情報 |

### 出力 (Output)

提出する実験手順は以下の形式で記述してください：

| フィールド | 日本語名 | 型 | 説明 | 制約 |
|-----------|---------|-----|------|------|
| `procedure_steps` | 手順 | list[dict] | 実験手順のリスト | - 要素数: **50以下**<br>- 1要素: **10文以下** |
| └ `id` | ステップ番号 | int | 手順の番号 | 1から順番に付与 |
| └ `text` | 手順内容 | str | 手順の詳細 | 明確で実行可能な記述 |

⚠️ **重要**: 上記の制約を満たさない出力は受け付けられません。特に以下の点にご注意ください：
- 手順数が50を超える場合は自動的に却下されます
- 各手順の文が10文を超える場合は自動的に却下されます

#### 出力の詳細度について

出力の手順（`procedure_steps`）は、単にプロトコルを構造化するだけではなく、当該分野の学部レベルのトレーニングを受けた人が読んで誤解なく実行できることを目指してください。そのために、すべてのパラメータと条件を明示化することが重要です。

完成された手順は以下の特徴を備えている必要があります：
- 暗黙知や省略が埋められている
- すべての条件が明示化されている
- 不完全な記述が完成されている
- 実行時に使用される具体的な数値が計算されている
- 操作対象や器具、装置など対象物が明示化されている

**例：水に砂糖を溶かす場合**

❌ **不十分な実験手順**
1. コップに水を入れる
2. 10%になるよう砂糖を加える
3. かき混ぜる

✅ **期待される実験手順**
1. コップに100 mLの水（25℃）を入れる
2. 砂糖を10 g加える
3. スプーンで30秒間かき混ぜる

詳細については、`data/example/`のサンプルデータをご参照ください。また、目指すべき詳細度の参考として、以下の論文のCompleted protocolセクションもご覧ください：
- [Multimodal Pragmatic Jailbreak on Text-to-image Models](https://arxiv.org/pdf/2411.00444v1)

## 🎯 評価方法

本コンペティションは2段階の評価フェーズで構成されます。

### Development Phase（開発フェーズ）
- **練習用データ**: Example Dataset（練習用、評価対象外）
- **評価対象データ**: Public Test Dataset
- **提出内容**: Public Test Datasetの処理結果を所定フォーマットで提出
- **提出回数**: 制限あり
- **評価方法**: LLM評価
- **結果公開**: GitHub Pagesのリーダーボードに反映

### Test Phase（テストフェーズ）
- **評価対象データ**: Private Test Dataset（Development Phase終了時に公開）
- **提出内容**: Private Test Datasetの処理結果を所定フォーマットで提出
- **提出回数**: 何度でも可能（**評価対象は最後に提出されたファイルのみ**）
- **提出期限**: データ公開から7日以内
- **評価方法**:
  - **第1次評価**: LLM評価（全チームを対象）
  - **第2次評価**: 専門家評価（LLM評価の上位10チームを対象）

### LLM評価の実施方針

- 公開済みのベースラインノートブックに含まれるプロンプトはLLM評価の一例です。
- リーダーボードおよびPrivate Testの評価では、ベースラインノートブックに含まれるプロンプトとは異なる3種類のプロンプトを使用します。それぞれ独立に採点を行った後に集約します。

評価に利用するプロンプトと採点フローは、最終的に参加者向けドキュメントで明示します。必要に応じてアップデートが行われる可能性があります。

## 📊 評価メトリクス

### 配点（10点満点）

- **共通採点基準**: 5点満点
- **個別採点基準**: 5点満点
- **合計**: 10点満点

### 共通採点基準 (General Criteria) - 5点満点

#### 加点項目
| 点数 | 評価内容 |
|------|----------|
| +1点 | 「実験指示」におけるパラメータを、すべて誤りなく反映している |
| +1点 | 「使用する物品」の要素が、すべて誤りなく反映されている |
| +1点 | 「元プロトコルの手順」の順序や分岐条件の論理構造を矛盾なく反映している |
| +1点 | 実行することで「期待される最終状態」を得られる（論理的破綻や計算ミスがない） |
| +1点 | 明示されていない部分を適切に補完できている（記述の具体性） |

#### 減点項目
| 点数 | 評価内容 |
|------|----------|
| -1点 | 過度に不自然な日本語やハルシネーション |
| -1点 | 計算ミス |
| -1点 | 手順の矛盾 |

※減点項目は各項目1回ずつ適用し、積算しない

#### 特別制限：過度の安全性（合計点を最大2点に制限）

以下のような過度に安全側に倒した回答の場合、共通採点基準の合計点を最大2点に制限します：
- 入力の手順をそのまま出力として記載
- 出典の情報を適切な取捨選択なく記載
- 実験指示や元プロトコルに反して中間物を必要量の100倍用意するなど、みだりに実験条件を安全側に倒す

**適用例**：
- 採点結果が1点の場合 → 1点のまま
- 採点結果が3点の場合 → 2点に制限
- 採点結果が5点の場合 → 2点に制限

### 個別採点基準 (Specific Criteria) - 5点満点

問題ごとに個別に設定された採点項目に基づいて加点します。採点項目は以下のような観点で設定されます：
- 出題意図への適合性
- 安全性の考慮
- コスト効率
- 作業効率
- 実験精度向上への貢献

※Example DatasetとPublic Test Datasetでは個別採点基準が公開されますが、Private Test Datasetでは非公開となります。

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

### 必要なファイル

Test Phaseでは以下の3点すべての提出が必要です：

1. **予測結果ファイル** - 出力フォーマットに従ったJSONL形式
2. **実行コード** - 結果を再現可能なプログラム（単一または複数ファイル）
3. **README** - 手法の説明、実行環境、依存ライブラリ等を記載

※ 実行コードは評価の再現性確認のために使用します。

### 提出システム

提出は以下のシステムから行ってください：

**提出システムURL**: https://la-bench-leaderboard.onrender.com/

- Development Phase: 「提出フォーム」セクションから提出
- Test Phase: 「プライベートテスト提出」セクションから提出

※ IDとパスワードは参加登録後にメールでお知らせしています。

## 📅 スケジュール

| 日付        | 内容                                                                 |
|-------------|----------------------------------------------------------------------|
| 2025-09-13  | 公式サイト公開・参加登録開始<br>ルール、Example Dataset、サンプルコード 公開 |
| 2025-10-10  | Public Test Dataset 公開                                             |
| 2025-11-14  | Private Test Dataset 公開                                            |
| 2025-11-21  | 提出締切 (23:59 JST)                                                 |
| 2025-12-20  | 結果公開                                                             |
| 2026-02-01  | 人工知能学会 全国大会 予稿提出締切                                   |
| 2026-06     | 人工知能学会 全国大会にて表彰・発表                                  |

## 📢 過去のアナウンス

重要な更新情報やルール変更について、過去のアナウンスを確認できます：

- [2025-11-23: Test Phase終了のお知らせ](announcements/2025-11-23_test_phase_end.md)
  - 結果発表（12月20日）までのスケジュール、今後の展望について
- [2025-11-21: 【緊急】ファイルサイズ制限について](announcements/2025-11-21_2_file_size_limit.md)
  - 実行コード50MB、README5MBの制限と対処法
- [2025-11-21: 本日提出締切のお知らせ](announcements/2025-11-21_1_submission_deadline.md)
  - 50チーム超の参加、賞金増額（90万円）、サーバー増強について
- [2025-11-14: Test Phase提出フォーム公開のお知らせ](announcements/2025-11-14_2_submission_form.md)
  - 提出フォームのURL、提出方法、注意事項について（**提出は何度でも可能、評価対象は最後の提出のみ**）
- [2025-11-14: Test Phase開始のお知らせ（日程変更あり）](announcements/2025-11-14_1_test_phase_start.md)
  - Private Test Dataset公開と提出締切の1日延長について
- [2025-10-22: 参加規約の明文化に関するお知らせ](announcements/2025-10-22_participation_rules.md)
  - 複数チーム登録の禁止、コラボレーションルールなど

すべてのアナウンスは[announcements/](announcements/)ディレクトリでご確認いただけます。


## 🏆 主催
[一般社団法人 ラボラトリーオートメーション協会](https://lasa.or.jp/)

## 🤝 支援
本コンペティションは、2025年度人工知能学会コンペティション開催支援制度の支援を受けています

## 🔒 セキュリティポリシー

**重要**: データセット構築に関する詳細な議論は、情報漏洩を防ぐため、GitHubではなくDiscordで運営メンバーのみで行われます。GitHubのissueやPRには、公開可能な情報のみを記載してください。

## 💰 スポンサー

LA-Bench 2025の運営費および賞金の充実のため、スポンサーを募集しています。
ご支援いただいた企業・団体様のロゴを本サイトに掲載させていただきます。

- 📄 [スポンサー募集のご案内](https://drive.google.com/file/d/1TjXRgEloQAcw4fOTdNkzdZeJCTP7NG_3/view)
- 📝 [スポンサー申し込みフォーム](https://docs.google.com/forms/d/e/1FAIpQLSdzlgiq2qmHAbJuLuFg8WAUeBvJUDcnu9waQBaqAlihS8f6RQ/viewform)

## 📘 更新履歴

- 2025-10-13: Public Test 6のサンプルのバッファ配合を更新。
- 2025-10-11: Private Test向けJSONLローダーの利用手順を整備。

## 📜 ライセンス

本プロジェクトはMITライセンスの下で公開されています。詳細は[LICENSE](LICENSE)ファイルをご参照ください。

## 🤝 引用

本データセットを研究で使用される場合の引用方法については、論文公開後にこちらに記載いたします。
