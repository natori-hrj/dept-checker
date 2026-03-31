# debt-checker

Python コードの技術的負債を検出・可視化する CLI ツール。

AST 解析により問題箇所を特定し、100 点満点のスコアで健全性を評価します。

## 検出項目

| チェック | `--ignore` キー | デフォルト閾値 |
|---|---|---|
| 長すぎる関数 | `long_function` | 50 行 |
| 深すぎるネスト | `deep_nesting` | 4 重 |
| docstring なし | `no_docstring` | - |
| TODO コメント | `todo` | - |
| FIXME コメント | `fixme` | - |
| 短すぎる変数名 (1文字) | `short_variable` | i,j,k,x,y,z,_ は除外 |
| 循環的複雑度 | `complexity` | CC > 10 |

## インストール

```bash
pip install -e .
```

## 使い方

```bash
# ディレクトリ全体をチェック
debt-checker ./src

# 単一ファイルをチェック
debt-checker ./src/debt_checker/analyzers.py

# Markdown レポートを出力
debt-checker ./src --report output.md

# 特定のチェックを無効化
debt-checker ./src --ignore no_docstring
debt-checker ./src --ignore todo --ignore fixme

# 閾値を変更
debt-checker ./src --max-lines 30 --max-nesting 3
```

## 出力例

```
╭──────────────── 技術的負債スコア ────────────────╮
│  83 / 100                                        │
╰──────────── 6ファイル解析 | 2件検出 ─────────────╯

    カテゴリ別サマリ
┏━━━━━━━━━━━━━━━━┳━━━━━━┓
┃ カテゴリ       ┃ 件数 ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━┩
│ 深すぎるネスト │    2 │
└────────────────┴──────┘
```

## 技術スタック

- **CLI**: [click](https://click.palletsprojects.com/)
- **表示**: [rich](https://rich.readthedocs.io/)
- **構文解析**: ast (標準ライブラリ)

## ライセンス

MIT
