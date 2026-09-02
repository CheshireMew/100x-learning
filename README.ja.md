<!-- readme-header:start -->

<p align="center">
  <img src="./assets/readme/logo.svg" width="160" alt="100x Learning">
</p>

<h1 align="center">100x Learning</h1>

<p align="center">
  <strong>素材・テーマ・現実の問題を、理解・判断・活用できる知識に変えます。</strong>
</p>

<p align="center">
  <a href="./README.md">中文</a> · <a href="./README.en.md">English</a> · <strong>日本語</strong> | <a href="./SKILL.md">ドキュメント</a> | <a href="./CONTRIBUTING.md">コントリビューション</a> | <a href="https://github.com/CheshireMew/100x-learning/issues">Issues</a>
</p>

<p align="center">
  <a href="https://x.com/0xCheshire" title="X"><img src="https://img.shields.io/badge/X-%400xCheshire-000000?logo=x&amp;logoColor=white" alt="X: @0xCheshire"></a>
  <a href="https://t.me/CheshireBTC" title="Telegram"><img src="https://img.shields.io/badge/Telegram-CheshireBTC-26A5E4?logo=telegram&amp;logoColor=white" alt="Telegram: CheshireBTC"></a>
  <a href="https://blog.blacknico.com/" title="Blog"><img src="https://img.shields.io/badge/Blog-blog.blacknico.com-2E7D32?logo=rss&amp;logoColor=white" alt="Blog: blog.blacknico.com"></a>
  <a href="https://blacknico.com/" title="Homepage"><img src="https://img.shields.io/badge/Home-blacknico.com-1F6FEB?logo=googlechrome&amp;logoColor=white" alt="Homepage: blacknico.com"></a>
</p>

<p align="center">
  <a href="https://github.com/CheshireMew/100x-learning/stargazers"><img src="https://img.shields.io/github/stars/CheshireMew/100x-learning?style=flat" alt="GitHub Stars"></a>
  <a href="https://github.com/CheshireMew/100x-learning/forks"><img src="https://img.shields.io/github/forks/CheshireMew/100x-learning?style=flat" alt="GitHub Forks"></a>
  <a href="https://github.com/CheshireMew/100x-learning/blob/main/LICENSING.md"><img src="https://img.shields.io/github/license/CheshireMew/100x-learning?style=flat" alt="Repository License"></a>
</p>

<!-- readme-header:end -->

`100x-learning` は、オープンな [Agent Skills 仕様](https://agentskills.io/specification)に準拠した学習・調査 Skill です。資料、字幕、リンク、テーマ、現実の問題を読み取り、理解、調査、概念説明、実践、知識保存のうち、依頼された成果に合う方法を選びます。

<p align="center">
  <img src="./assets/readme/hero-ja.png" width="100%" alt="素材・テーマ・現実の問いから、理解・判断・活用へつなげる 100x Learning の仕組み">
</p>

## 依頼例

- **資料を理解する**：`この文書が実際に定めていることを説明し、直接の事実、妥当な推論、不明点を分けてください。`
- **調査・検証する**：`これらの主張をオンラインで確認し、同時代の一次資料を優先して、資料間の矛盾も説明してください。`
- **概念を説明する**：`ハイウォーターマークを具体例で説明し、その後に正確な定義と限界を示してください。`
- **知識を使う**：`この枠組みを私のケースに適用し、仮定、観察可能な結果、次の検証を示してください。`
- **字幕を整える**：`字幕の機械的な書式と確認できる誤認識だけを直し、意味・順序・内容を保った読みやすい全文にしてください。`
- **知識を保存する**：`今回確認した資料と結論を、設定済みの個人知識ライブラリへ保存してください。`

Skill は依頼された成果で停止します。調査を自動で長期プロジェクトにせず、字幕を自動で要約せず、候補部分を自動でメディア成果物にせず、書き込み許可なしに個人知識ライブラリを変更しません。

## 主な機能

| 目的 | 方法 | 成果 |
| --- | --- | --- |
| 資料理解 | 主張、証拠、関係、条件、欠落を確認 | 追跡可能な説明 |
| テーマ調査 | 一次資料を開き、文脈と時点を照合 | 事実・推論・意見・不明点を分けた結論 |
| 概念説明 | 現実の問題、仕組み、例から入り、正式な定義も保持 | 現在の用途で使える説明 |
| 実践 | 知識を目標、行動、指標、フィードバックへ対応 | 計画、ツール、判断、振り返り |
| 情報源の取り込み | 動画、SNS、字幕、重要画面を取得 | 追跡可能な情報源パッケージ |
| 字幕整理 | 機械的な書式と確認済みノイズを除去 | 忠実で連続した読みやすい情報源 |
| 個人知識ライブラリ | 初期化、接続、検索、検証、健康確認 | 継続利用できるローカル知識 |

記事、投稿、既存の下書きは、理解、調査、事実確認の入力として利用できます。ただし、この Skill は公開向けコンテンツの作成、続筆、推敲、文体審査、テーマ運用、事例・フック管理、作者の声のモデル化、公開後の評価を担当しません。

## 個人知識ライブラリ

保存先はユーザーがローカルに指定し、個人内容はこのリポジトリに含まれません。

```powershell
python scripts/private_library.py init --root "D:\Knowledge\My Library"
python scripts/private_library.py show
python scripts/private_library.py validate
python scripts/private_library_health.py
```

既存の互換ライブラリは `adopt --root <path>` で接続できます。設定にはバージョンとルートパスだけを保存します。`init` は空でないディレクトリを上書きせず、`adopt` は既存知識を移動・書き換えません。旧版が残した非アクティブなディレクトリは削除や移行をせず、そのまま無視します。

アクティブなディレクトリは `00-Inbox`、`10-Knowledge`、`20-Sources`、`30-Projects`、`40-Outputs`、`50-Areas`、`60-Systems`、`90-Archive` です。

## インストールと互換性

リポジトリを Agent Skills 対応ホストの Skill ディレクトリへクローンまたはコピーし、依頼で `$100x-learning` を指定します。正確な読み込み方法はホストに従います。個人知識ライブラリは Skill のソースと分離されます。

Python ユーティリティは標準ライブラリで動作します。現在の自動受け入れテストは Windows を主対象としています。

## リポジトリ構成

```text
100x-learning/
├── SKILL.md                   # 入口と責任範囲
├── agents/openai.yaml         # クライアント表示情報
├── references/                # 学習、調査、実践、知識庫の方法
├── scripts/                   # 字幕、情報源、個人知識庫のツール
├── assets/private-library/    # 新規知識庫用の汎用テンプレート
├── tests/                     # 振る舞いとスクリプトのテスト
└── archive/                   # 終了した機能の履歴ファイル
```

## ライセンス

コード、オリジナル文書、第三者資料の境界は [LICENSING.md](./LICENSING.md) を参照してください。
