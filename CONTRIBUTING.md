# コントリビューティングガイドライン

LA-Bench 2025へのご協力ありがとうございます。このドキュメントでは、プロジェクトへの貢献方法について説明します。

## 行動規範

- 建設的で敬意のあるコミュニケーションを心がけてください
- 多様性を尊重し、包括的な環境を維持してください
- 技術的な議論に集中し、個人攻撃は避けてください

## 貢献の方法

### 1. Issue の報告

バグや改善提案がある場合：

1. 既存のIssueを確認し、重複がないか確認
2. 新しいIssueを作成する際は、適切なテンプレートを使用
3. 明確で詳細な説明を記載
4. 可能であれば再現手順を含める

### 2. Pull Request の提出

コードの改善や新機能の追加：

1. リポジトリをフォーク
2. 新しいブランチを作成（`git checkout -b feature/your-feature-name`）
3. 変更をコミット（コミットメッセージは明確に）
4. ブランチをプッシュ（`git push origin feature/your-feature-name`）
5. Pull Requestを作成

### 3. ドキュメントの改善

- 誤字脱字の修正
- 説明の明確化
- 新しい例の追加
- 翻訳の提供

## コーディング規約

### Python

- PEP 8 スタイルガイドに従う
- 型ヒントを使用する
- docstringを記載する
- テストを書く

```python
def process_experiment(instruction: str, protocols: List[str]) -> Dict[str, Any]:
    """
    実験手順を生成する
    
    Args:
        instruction: 実験指示
        protocols: プロトコルのリスト
        
    Returns:
        生成された実験手順
    """
    # 実装
    pass
```

### YAML

- 2スペースインデント
- 明確な構造
- コメントで説明を追加

## コミットメッセージ

- 明確で簡潔に
- 現在形で記述
- 何を変更したか、なぜ変更したかを説明

例：
```
Add baseline model for experiment procedure generation

- Implement transformer-based model
- Add data preprocessing pipeline
- Include evaluation metrics
```

## レビュープロセス

1. 全てのPull Requestはレビューが必要
2. CIテストが通過していることを確認
3. レビュアーのフィードバックに対応
4. 承認後にマージ

## 質問・サポート

- GitHubのDiscussionsを活用
- Issueでの技術的な質問も歓迎
- コミュニティとの積極的な交流を推奨

## ライセンス

貢献されたコードは、プロジェクトのライセンス（MIT）に従います。

---

ご協力ありがとうございます！