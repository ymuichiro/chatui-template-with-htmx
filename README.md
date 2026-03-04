# chatui-template-with-htmx

HTMX + FastAPI で AI チャット UI を構築するためのテンプレートリポジトリです。

## 設計ドキュメント

詳細は `DESIGN.md` を参照してください。

## 実装済み MVP（このブランチ）

- Reverse Proxy OAuth2 を想定した JWT ヘッダ認証
  - `AUTH_MODE=proxy` では `X-Forwarded-JWT` を必須化
  - `AUTH_MODE=dev_demo` では `X-Forwarded-JWT` または `Authorization: Bearer ...` を許可
- 開発モードでのデモ JWT 認証（`AUTH_MODE=dev_demo`）
- HTMX で送信し、SSE ストリームで AI 応答をリアルタイム描画
- ツール呼び出しイベント（開始・引数・結果）をリアルタイム表示

## ローカル起動

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

## デモJWTの作成

```bash
python scripts_gen_demo_jwt.py
```

生成された JWT を使って、例えば以下でアクセスできます。

```bash
TOKEN="<paste-jwt>"
curl -H "X-Forwarded-JWT: $TOKEN" http://127.0.0.1:8000/auth/me
```

## 次の開発課題（MVP完成に向けて）

- `DESIGN.md` の「14. MVP完成に向けた課題一覧（実装優先度つき）」を参照してください。


- 入力バリデーション（空文字拒否・最大文字数制限: `MAX_MESSAGE_LENGTH`）
