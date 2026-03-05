# chatui-template-with-htmx

FastAPI + HTMX で構成された、認証付きチャット UI テンプレートです。  
このリポジトリは公開されていますが、運用は内部利用を前提としています。

## 1. 起動方法

```bash
cp .env.example .env
uv sync
uv run uvicorn app.main:app --reload
```

アクセス:

- Chat UI: `http://127.0.0.1:8000/`
- Current user: `http://127.0.0.1:8000/auth/me`
- Health check: `http://127.0.0.1:8000/healthz`

## 2. 使い方

### チャット操作

- 左サイドバーで会話履歴を選択
- `New Chat` で新規会話モードへ切り替え
- 送信:
  - `Enter`: 送信（IME変換中は送信しない）
  - `Shift + Enter`: 改行
- 添付ボタンでファイル選択（画像 / PDF / Office / テキスト系）
- マイクボタンで音声入力（ブラウザ対応時のみ）

### 会話URL

- 会話ごとに URL でアクセス可能: `/c/{conversation_id}`
- 新規会話で最初のメッセージ送信後、URL は自動で `/c/{conversation_id}` に更新

## 3. 認証モード

- `AUTH_MODE=proxy`
  - `X-Forwarded-JWT` ヘッダを必須
- `AUTH_MODE=dev_demo`
  - `X-Forwarded-JWT` または `Authorization: Bearer ...` を許可
  - JWT 未指定時はダミーユーザーを自動適用（`DEV_DEMO_AUTO_AUTH_WITHOUT_JWT=true`）

主な認証系環境変数は [.env.example](/Users/you/github/ymuichiro/chatui-template-with-htmx/.env.example) を参照してください。

## 4. アーキテクチャ概要

- Router: HTTP 入出力・テンプレート返却・SSE エンドポイント
- Service: 会話作成/取得と LLM ストリーミング制御
- Repository: 会話・メッセージ永続化（現在は InMemory）
- Gateway: LLM 実装差し替え層（現在は Mock）

詳細は [docs/ARCHITECTURE.md](/Users/you/github/ymuichiro/chatui-template-with-htmx/docs/ARCHITECTURE.md) を参照してください。

## 5. ディレクトリ構造（要点）

```text
app/
  core/          # 設定・認証
  routers/       # ページ/チャットAPI
  services/      # ユースケース
  repositories/  # データアクセス
  gateways/      # LLM接続
  templates/     # Jinja2テンプレート
  static/        # CSS
docs/
  ARCHITECTURE.md
```

## 6. 補足

- 依存管理は `pyproject.toml` + `uv.lock` を利用
- 仕様設計の原本は [DESIGN.md](/Users/you/github/ymuichiro/chatui-template-with-htmx/DESIGN.md)
