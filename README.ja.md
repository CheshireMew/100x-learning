<!-- readme-header:start -->

<p align="center">
  <img src="./assets/readme/logo.svg" width="160" alt="100x Learning">
</p>

<h1 align="center">100x Learning</h1>

<p align="center">
  <strong>学習、個人知識、コンテンツ改善を、明確で組み合わせ可能な入口に分けます。</strong>
</p>

<p align="center">
  <a href="./README.md">中文</a> · <a href="./README.en.md">English</a> · <strong>日本語</strong> | <a href="./skills/100x-learning/SKILL.md">ドキュメント</a> | <a href="./CONTRIBUTING.md">貢献</a> | <a href="https://github.com/CheshireMew/100x-learning/issues">フィードバック</a>
</p>

<p align="center">
  <a href="https://x.com/0xCheshire" title="X"><img src="https://img.shields.io/badge/X-%400xCheshire-000000?logo=x&amp;logoColor=white" alt="X：@0xCheshire"></a>
  <a href="https://t.me/CheshireBTC" title="Telegram"><img src="https://img.shields.io/badge/Telegram-CheshireBTC-26A5E4?logo=telegram&amp;logoColor=white" alt="Telegram：CheshireBTC"></a>
  <a href="https://blog.blacknico.com/" title="Blog"><img src="https://img.shields.io/badge/Blog-blog.blacknico.com-2E7D32?logo=rss&amp;logoColor=white" alt="博客：blog.blacknico.com"></a>
  <a href="https://blacknico.com/" title="Homepage"><img src="https://img.shields.io/badge/Home-blacknico.com-1F6FEB?logo=googlechrome&amp;logoColor=white" alt="个人主页：blacknico.com"></a>
</p>

<p align="center">
  <a href="https://github.com/CheshireMew/100x-learning/stargazers"><img src="https://img.shields.io/github/stars/CheshireMew/100x-learning?style=flat" alt="GitHub Stars"></a>
  <a href="https://github.com/CheshireMew/100x-learning/forks"><img src="https://img.shields.io/github/forks/CheshireMew/100x-learning?style=flat" alt="GitHub Forks"></a>
  <a href="https://github.com/CheshireMew/100x-learning/blob/main/LICENSING.md"><img src="https://img.shields.io/github/license/CheshireMew/100x-learning?style=flat" alt="Repository License"></a>
</p>

<!-- readme-header:end -->

`100x-learning` は、オープンな [Agent Skills 仕様](https://agentskills.io/specification)に準拠した複数 Skill のリポジトリです。三つの入口が同じ永続リソース契約を共有し、学習、個人知識、コンテンツシステムを別々に扱います。

<p align="center">
  <img src="./assets/readme/hero-ja.png" width="100%" alt="素材・テーマ・現実の問いから、理解・判断・実践・発信につなげる 100x Learning の仕組み">
</p>

## まず欲しい成果を伝える

内部フローを選ぶ必要はありません。欲しい成果をそのまま伝えてください。

- **素材を理解する**：`このインタビューの流れと重要な関係を説明し、見返す価値が高い箇所も示してください。`
- **調査して判断する**：`X を調査し、私の目的には A と B のどちらが合うか比較し、まだ分からない点も残してください。`
- **説明して応用する**：`実際の場面で X を説明し、それを使って私が直面している Y を分析してください。`
- **継続して学ぶ**：`X を継続して学びます。今回は最も役立つ一課を終え、私の反応から次を決めてください。`
- **知識を残す**：`$private-knowledge を使い、確認済みの結論を保存して同じテーマの正本を更新してください。`
- **コンテンツを改善する**：`$content-system を使い、この公開済みコンテンツを振り返って次に検証することを決めてください。`

各 Skill は自分の成果で停止します。学習は自動保存せず、共有候補は投稿文にならず、一度の振り返りが長期戦略を書き換えることもありません。公開用文章は既存の `prep-this`、`write-this`、`clean-copy` が担当します。

## クイックスタート

Agent Skills 対応のインストーラーでリポジトリ全体を導入します。

```bash
npx skills add CheshireMew/100x-learning
```

インストーラーは `100x-learning`、`private-knowledge`、`content-system` を検出します。リポジトリを clone し、`skills/` から必要な入口を導入することもできます。

導入後は、欲しい成果をそのまま伝えます。

```text
この素材を読んでください。まず内容、主な流れ、重要な関係を忠実に説明し、
そのうえで、さらに掘り下げる価値が高い箇所を教えてください。
```

Skill 名の明示呼び出しに対応するホストでは `$100x-learning`、`$private-knowledge`、`$content-system` を使えます。

## 成果からずれない仕組み

| 依頼 | Skill の処理 | 成果と停止位置 |
| --- | --- | --- |
| 素材を理解する | 内容、流れ、関係、実際の位置を忠実に復元する | 明快な説明と重要箇所。調査プロジェクトには広げない |
| 調査・検証する | 情報源を比較し、事実、判断、未知の点を分ける | 出典付きの結論と、まだ確認が必要な問い |
| 知識を保存・確認する | 一つの設定済み個人ライブラリを特定し、書き込み、検証する | 次回も読める正式知識と実状態 |
| 共有する内容を選ぶ | 素材全体を理解してから読者と用途に合わせて選ぶ | 候補と理由。自動で執筆しない |
| 公開結果を振り返る | 観測結果、説明、別の可能性を分ける | 次に検証できるコンテンツ判断 |

単発の依頼に永続的な仕組みは不要です。長期的なコンテンツ方向、成果の保存、履歴、個人の文体を明示的に求めた場合だけ、対応する継続資料を利用します。

## 任意：個人知識ライブラリと継続作業

個人知識ライブラリは Skill ディレクトリの外に置かれ、公開リポジトリには含まれません。Agent に新しいライブラリの初期化、または既存の Markdown ライブラリの接続を依頼できます。

```text
$private-knowledge を使って D:\Knowledge\100x-learning に個人知識ライブラリを作成してください。
$private-knowledge を使って E:\Knowledge\Existing Library の既存ライブラリを接続してください。
```

選択されたルートは `~/.100x-learning/config.json` に記録されます。設定が保存するのはライブラリのバージョンとパスだけで、個人の本文ではありません。`init` は中身のあるディレクトリを上書きしません。`adopt` はプロジェクトの識別情報とローカル参照だけを追加し、既存の知識を移動・書き換えません。

接続後、`private-knowledge` は原資料、テーマ知識、プロジェクト、成果を管理します。`content-system` は同じライブラリで事例、書き出し、公開記録、コンテンツ方向、継続テーマを管理し、別のデータルートは作りません。

<details>
<summary>知識ライブラリの保守スクリプトを直接実行する</summary>

```powershell
python skills/private-knowledge/scripts/private_library.py init --root "D:\Knowledge\100x-learning"
python skills/private-knowledge/scripts/private_library.py adopt --root "E:\Knowledge\Existing Library"
python skills/private-knowledge/scripts/private_library.py show
python skills/private-knowledge/scripts/private_library.py validate
```

</details>

個人ライブラリが未設定でも、素材理解、調査、共有候補の選択、現在の応答内での判断は続行できます。公開リポジトリを clone しても個人資料は含まれません。

## 対象範囲

このリポジトリは学習と調査、個人知識、コンテンツシステムを扱います。短文、Thread、GitHub プロジェクト紹介、記事は既存の執筆 Skill が担当します。画像、GIF、動画、音声、Podcast の制作、一般翻訳、広告運用、実際の公開も別の能力です。

ファイルへの書き込み、メディア制作、アップロード、公開は互いに別の操作です。明示的な許可がなければ、成果は現在の応答またはローカル作業領域に留まります。

## リポジトリ構成と保守

```text
100x-learning/
├── skills/
│   ├── 100x-learning/         # 学習、調査、説明、実践、長い素材
│   ├── private-knowledge/     # 個人ライブラリ、知識、検査、Marktree
│   └── content-system/        # 戦略、テーマ、振り返り、事例、書き出し、記憶
├── assets/readme/             # GitHub README の画像
├── tests/                     # Skill 間の動作と生成・利用経路のテスト
└── archive/                   # 廃止済み資料。現在の実行では読み込まない
```

各 `skills/<name>/SKILL.md` が独立した入口です。`private-knowledge` が他の入口から利用される唯一のライブラリ契約を所有します。`archive/` の旧経路は現在の実行に参加しません。

保守スクリプトは Python 標準ライブラリを使用します。全行動テストを実行するには次を使います。

```bash
python -m pytest -q
```

コントリビューションの前に [CONTRIBUTING.md](./CONTRIBUTING.md) を確認してください。動作とスクリプトの入口は [skills/](./skills/) にあります。README に内部ルールの複製は置きません。

## Star History

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/CheshireMew/100x-learning/star-history/star-history-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/CheshireMew/100x-learning/star-history/star-history.svg">
  <img alt="CheshireMew/100x-learning GitHub Star History" src="https://raw.githubusercontent.com/CheshireMew/100x-learning/star-history/star-history.svg">
</picture>

## ライセンス

オリジナルの Skill 指示、ソースコード、テスト、スクリプト、再利用可能なテンプレートは [Mozilla Public License 2.0](./LICENSE) で提供されます。`archive/`、`output/`、取り込まれた事例、出典記事、ソーシャル投稿、スクリーンショット、その他の第三者・参考資料はこの許諾の対象外です。正確な範囲は [LICENSING.md](./LICENSING.md) を参照してください。
