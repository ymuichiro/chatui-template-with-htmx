# チャットUIテンプレート設計（HTMX + FastAPI）

## 1. 目的

このテンプレートの目的は、**最小構成で AI チャット UI を素早く立ち上げること**です。具体的には次を満たします。

- FastAPI で API とサーバーサイドレンダリングを提供
- HTMX でフロントエンドのインタラクションを軽量実装
- 将来的に任意の LLM プロバイダ（OpenAI / Azure OpenAI / Ollama など）へ差し替え可能
- 小規模プロジェクトから拡張しやすい責務分離

---

## 2. 全体アーキテクチャ

```text
Browser (HTMX)
  ├─ GET  /                    -> 初期画面（chat page）
  ├─ POST /chat/messages       -> ユーザー発言を送信、ユーザー吹き出し + 空のAI吹き出しを返却
  └─ GET  /chat/messages/{id}/stream (SSE) -> AI返答を段階的に受信

Reverse Proxy (OAuth2認証)
  ├─ OAuth2/OIDC ログインを終端
  ├─ 検証済みJWTを `X-Forwarded-JWT` などのヘッダで FastAPI へ中継
  └─ FastAPI はヘッダJWTを検証してアプリ認可に利用

FastAPI
  ├─ Router (UI / API)
  ├─ Auth Middleware / Dependency
  ├─ Application Service (ChatService)
  ├─ Domain Model (Message, Conversation)
  ├─ Repository (InMemory / DB)
  └─ LLM Gateway (Provider Adapter)
```

### レイヤー方針

1. **Router 層**
   - HTTP 入出力とテンプレートレンダリングだけを担当。
   - ただし `current_user` の取得（Dependency注入）はここで実施。
2. **Service 層**
   - 会話の生成、履歴取得、LLM 呼び出しのユースケースを担当。
   - ユーザー境界（誰の会話か）を常に受け取って処理。
3. **Gateway 層**
   - LLM プロバイダ SDK 依存を隔離（実装差し替え可能）。
4. **Repository 層**
   - 履歴保存先を抽象化（最初はメモリ実装）。

---

## 3. 推奨ディレクトリ構成

```text
app/
  main.py
  core/
    config.py
    logging.py
    auth.py
  routers/
    pages.py
    chat.py
  services/
    chat_service.py
  domain/
    models.py
  gateways/
    llm/
      base.py
      openai_gateway.py
      mock_gateway.py
  repositories/
    base.py
    in_memory.py
  schemas/
    auth.py
    stream_events.py
  templates/
    base.html
    chat.html
    components/
      message_user.html
      message_ai.html
  static/
    css/app.css
```

---

## 4. 画面と HTMX インタラクション設計

## 4.1 初期表示

- `GET /` で `chat.html` を返却。
- 画面要素:
  - メッセージ一覧（`#chat-log`）
  - 入力フォーム（`#chat-form`）
  - 送信ボタン

## 4.2 送信時の流れ

1. フォームが `hx-post="/chat/messages"` で送信。
2. サーバーは次の HTML フラグメントを返す。
   - ユーザー発言バブル
   - AI 応答用のプレースホルダ（`id="ai-msg-{message_id}"`）
3. HTMX で `#chat-log` の末尾に追加。
4. 追加後に `hx-trigger` もしくは `sse` 連携で AI 応答ストリームを開始。

## 4.3 ストリーミング応答

- `GET /chat/messages/{id}/stream` を SSE で購読。
- サーバーはイベント種別付きで `event:` + `data:` を送信。
- フロントエンドはイベント種別ごとに UI を更新する。

### SSE イベント設計（リアルタイム描画）

- `event: token`
  - 用途: AI の自然言語トークンを逐次描画
  - 描画先: assistant バブル本文
- `event: tool_call_start`
  - 用途: ツール呼び出し開始（関数名、call_id）
  - 描画先: 「ツール実行中」カード
- `event: tool_call_args`
  - 用途: ツール引数(JSON)を段階表示
  - 描画先: ツールカード内 `args` セクション
- `event: tool_result`
  - 用途: ツール実行結果を表示
  - 描画先: ツールカード内 `result` セクション
- `event: done`
  - 用途: ストリーム終了通知
  - 描画先: カーソル/ローディング停止
- `event: error`
  - 用途: ストリーム中の失敗通知
  - 描画先: assistant バブル内エラー表示

---

## 5. バックエンド API 設計（最小）

## 5.1 ページ表示

- `GET /`
  - 返却: `chat.html`

## 5.2 メッセージ投稿

- `POST /chat/messages`
  - 入力:
    - `conversation_id` (任意。なければ新規)
    - `message` (ユーザー入力)
  - 処理:
    1. ユーザーメッセージ保存
    2. AI 応答メッセージIDを先行発行
  - 出力:
    - 2つのメッセージ HTML フラグメント

## 5.3 認証コンテキスト

- すべてのチャット系エンドポイントは認証必須
- 認証情報ソース:
  - 本番: リバースプロキシが注入した JWT ヘッダ
  - 開発: デモ用 JWT ヘッダ（後述）
- `sub` をアプリ内ユーザーIDとして採用（`tenant`/`email` は任意利用）

## 5.4 応答ストリーム

- `GET /chat/messages/{message_id}/stream`
  - 処理:
    1. 会話履歴を取得
    2. LLM Gateway に履歴を渡してストリーム生成
    3. 受信イベント（token / tool_call / tool_result）を永続化しつつ SSE 送信
  - 出力:
    - `text/event-stream`

## 5.5 認証メタ情報

- `GET /auth/me`
  - 入力: JWT ヘッダ
  - 出力: `user_id`, `claims`, `auth_mode`（`proxy` or `dev_demo`）
  - 用途: UI 側でログイン状態・デバッグ表示に利用

---

## 6. ドメインモデル

```python
Message:
  id: str
  conversation_id: str
  role: Literal["user", "assistant", "system"]
  content: str
  created_at: datetime

Conversation:
  id: str
  user_id: str
  title: str | None
  created_at: datetime
  updated_at: datetime
```

設計意図:
- `Message` と `Conversation` を分離して、履歴一覧や検索に拡張しやすくする。
- 先にメッセージIDを採番して、UI側でプレースホルダ更新を容易にする。
- `Conversation.user_id` を必須化し、会話の所有者境界を明確にする。

---

## 7. LLM Gateway 設計

共通インターフェース例:

```python
class LLMGateway(Protocol):
    async def stream_chat(self, messages: list[Message]) -> AsyncIterator[StreamEvent]:
        ...
```

実装候補:
- `MockGateway`: 開発用、固定文言を疑似ストリームで返す
- `OpenAIGateway`: OpenAI Responses / Chat Completions をラップ

ポイント:
- Router/Service からは `LLMGateway` しか見えないようにして依存逆転。
- プロバイダ固有のパラメータ（model, temperature など）は `config` 経由で注入。
- `StreamEvent` によってツール呼び出し中間状態を UI へそのまま中継可能にする。

---

## 8. 認証・認可設計（Reverse Proxy OAuth2）

### 8.1 基本方針

- OAuth2/OIDC の認証フローは **リバースプロキシ側で完結**。
- FastAPI は「プロキシが検証済みJWTをヘッダで渡す」前提で動作。
- FastAPI 側でも最低限の検証（署名/issuer/audience/exp）を行い、ヘッダ偽装に備える。

### 8.2 JWT 受け渡し

- 受け取りヘッダ（例）
  - `X-Forwarded-JWT`（推奨）
  - または `Authorization: Bearer <jwt>`
- 必須クレーム
  - `sub`: ユーザー識別子
  - `exp`: 有効期限
  - `iss`, `aud`: 検証対象

### 8.3 開発モード（デモJWT）

- `AUTH_MODE=dev_demo` のとき、固定シークレットで署名されたデモJWTを受け付ける。
- 目的はローカル開発の迅速化であり、本番では無効化（`AUTH_MODE=proxy`）。
- デモJWT例クレーム
  - `sub: demo-user`
  - `name: Demo User`
  - `email: demo@example.com`

### 8.4 認可

- すべての Conversation / Message は `user_id` でスコープ。
- 他ユーザーの `conversation_id` を指定しても 404（存在秘匿）で返す。
- 管理用途を除き、クロステナントアクセスを禁止。

---

## 9. 状態管理と永続化方針

初期フェーズ:
- `InMemoryRepository` で最速構築。

次フェーズ:
- SQLite + SQLModel / SQLAlchemy へ移行。
- 必要テーブル:
  - `conversations`
  - `messages`
  - （任意）`message_events`（token/toolイベントの監査保存）

移行容易性のため、Service から直接 ORM を触らず Repository 経由に統一。

---

## 10. エラーハンドリング方針

- ユーザー入力バリデーションエラー:
  - インラインでエラーメッセージ表示（フォーム近傍）
- LLM タイムアウト:
  - AI バブルに「応答取得に失敗しました。再試行してください。」を表示
- JWT 不正/期限切れ:
  - `401 Unauthorized` とログ出力（claims 機微情報はマスク）
- 予期しない例外:
  - サーバーログに詳細、UI には一般化メッセージ

---

## 11. 非機能要件（最初に決める）

- **観測性**: request_id を発行し、ログに含める
- **セキュリティ**:
  - `.env` で API キー管理
  - JWT 検証鍵（JWKS/secret）を設定管理
  - HTML エスケープ徹底
  - 必要であれば簡易レート制限
- **パフォーマンス**:
  - まずは同時接続 10〜50 程度を目安
  - SSE 接続のタイムアウトを明示
- **開発運用**:
  - Python依存は `pyproject.toml` + `uv.lock` で一元管理
  - ローカル実行は `uv sync` / `uv run ...` を標準とする

---

## 12. 開発ステップ（推奨）

1. **MVP-1**: 静的 UI + HTMX POST でメッセージ追加
2. **MVP-2**: 認証Dependency（`proxy/dev_demo` 切替）導入
3. **MVP-3**: MockGateway で token + tool イベント疑似ストリーミング
4. **MVP-4**: OpenAI Gateway 接続
5. **MVP-5**: Repository を SQLite 化
6. **MVP-6**: 会話一覧・削除・タイトル自動生成

---

## 13. 受け入れ基準（MVP）

- メッセージ送信でユーザー発言が即時表示される
- AI 応答が1文字以上の分割で段階描画される
- ツール呼び出し時に、引数と結果がストリームでリアルタイム表示される
- JWT ヘッダが有効な場合のみチャット機能を利用できる
- 開発モードではデモJWTで認証相当の動作確認ができる
- ページリロード後も同一会話の履歴が復元できる（SQLite移行後）
- LLM エラー時に UI が壊れず再送可能

---

## 14. MVP完成に向けた課題一覧（実装優先度つき）

以下は「ユーザーに実際に使わせられる状態」にするために、現時点の実装から追加で必要な課題です。

### P0（リリース前に必須）

1. **認証境界の厳格化**
   - 認証失敗時の振る舞いを一貫化する（401固定、監査ログ出力）。
   - `AUTH_MODE=proxy` で `X-Forwarded-JWT` を必須化し、信頼可能プロキシ以外からの直接アクセス防止策を追加。

2. **`dev_demo` / `proxy` モードの明確な分岐**
   - `dev_demo` でのみ固定シークレットJWTを許可し、本番はJWKS検証に切り替える。
   - モード不整合（例: proxyなのにsecret検証しかない）を起動時エラー化。

3. **永続化（SQLite以上）**
   - in-memory から SQLite へ移行し、再起動時に会話が消えないようにする。
   - `conversation.user_id` と `message.conversation_id` のインデックスを付与。

4. **入力バリデーションと制限**
   - 空文字/過大入力/不正パラメータを明示的に拒否。
   - 1メッセージ最大長、1リクエストあたりのツールイベント最大数を定義。

5. **SSEの運用安定化**
   - ハートビートイベント、切断時リトライ方針、タイムアウト設計を追加。
   - ストリーム中エラー時に UI と保存状態が破綻しないようにする。

6. **テスト整備（最低限）**
   - 認証（正常/異常/期限切れ）、チャット投稿、SSEイベント順序のAPIテスト。
   - `404` の存在秘匿（他ユーザーconversation指定）を自動テストで保証。

### P1（早期に必要）

1. **実LLM Gatewayの接続**
   - `OpenAIGateway` を実装し、`MockGateway` とDIで切替可能にする。
   - token/toolイベントへのマッピングを統一。

2. **会話管理UI**
   - 会話一覧、会話切替、会話削除、タイトル生成を実装。
   - ページ再読込時に最新会話を復元。

3. **観測性の実装**
   - request_id / conversation_id / user_id をログへ構造化出力。
   - エラー率、SSE接続数、平均応答時間を可視化。

4. **セキュリティ強化**
   - レート制限、CSP、セキュアヘッダ、ログの機微情報マスキング。
   - JWT鍵ローテーション手順を定義。

### P2（完成度向上）

1. **ツール実行UXの改善**
   - tool call をカードUI化（進行中/完了/失敗）し、引数と結果の可読性を上げる。

2. **再送・中断制御**
   - 生成停止ボタン、再生成ボタン、失敗時の部分再試行を追加。

3. **運用向けドキュメント**
   - 逆プロキシ設定例（nginx/traefik）とJWTヘッダ受け渡し例を追記。

### Definition of Done（MVP完了判定）

- 認証は `proxy` / `dev_demo` で仕様通りに動作し、異常系は401/404を一貫返却。
- 会話履歴は再起動後も保持され、ユーザー境界が壊れない。
- SSEは token + toolイベントを安定配信し、切断時にもUIが破綻しない。
- 最低限の自動テストがCIで通過する。
