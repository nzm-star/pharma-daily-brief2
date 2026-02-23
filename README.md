# Pharma Daily Brief

医薬・バイオ業界の重要ニュースを毎朝まとめる朝刊です。**自動生成**と**メール送信**の両方に対応しています。

---

## 毎朝自動更新・Web公開（推奨）

**あなたが何もしなくても**、毎朝5時（シンガポール時間）に最新のBriefが自動生成され、誰でもURLで閲覧できます。

👉 **セットアップ手順は [DEPLOY.md](DEPLOY.md) を参照してください。**

- 新規 GitHub リポジトリを作成
- このフォルダの中身を push
- `GEMINI_API_KEY` を Secrets に追加
- GitHub Pages を有効化

完了後: `https://あなたのユーザー名.github.io/リポジトリ名/` でアクセス可能になります。

---

## Webで手動公開する（代替）

以下のいずれかの方法で、誰でもアクセスできるURLを取得できます。

### 方法1: Netlify Drop（最も簡単）

1. [Netlify Drop](https://app.netlify.com/drop) を開く
2. `pharma_daily_brief` フォルダをドラッグ＆ドロップ
3. 表示されたURL（例: `https://xxxx.netlify.app`）を共有

※ 初回は無料アカウント作成が必要です。デプロイ後、`index.html` を更新して再ドラッグすれば内容を更新できます。

### 方法2: GitHub Pages

1. GitHub で新規リポジトリ作成（例: `pharma-daily-brief`）
2. `pharma_daily_brief` フォルダの内容をリポジトリに push
3. リポジトリの **Settings** → **Pages** → Source を **main**  branch に設定
4. 数分後に `https://あなたのユーザー名.github.io/pharma-daily-brief/` でアクセス可能

### 方法3: ローカルサーバー + ngrok（開発・一時共有用）

ワークスペースの `server.js` で Pharma Brief を配信しています。

```powershell
# サーバー起動
npm start

# 別ターミナルで ngrok（要インストール）
ngrok http 3001
```

ブラウザで `http://localhost:3001/pharma` にアクセス。ngrok が表示する URL（例: `https://xxxx.ngrok.io/pharma`）を共有すれば、一時的に他者からも閲覧可能です。

---

## メール送信

## 1. 初期設定（初回のみ）

### Gmail アプリパスワードの取得

1. [Google アカウント](https://myaccount.google.com/) にログイン
2. **セキュリティ** → **2段階認証** を有効化（必須）
3. **アプリパスワード** → アプリを選択「メール」→ デバイスを選択「その他」→ 名前を入力「Pharma Brief」
4. 表示された16文字のパスワードをコピー

### .env ファイルの作成

1. `.env.example` をコピーして `.env` を作成
2. `.env` を開き、`PHARMA_BRIEF_APP_PASSWORD=` の後にアプリパスワードを貼り付け

```
PHARMA_BRIEF_APP_PASSWORD=abcd efgh ijkl mnop
```

## 2. 手動で送信する

```powershell
cd pharma_daily_brief
python send_brief.py
```

成功すると「送信完了: nzm0302@gmail.com」と表示されます。

## 3. 毎朝自動送信（タスクスケジューラ）

1. **タスクスケジューラ** を開く（Windows 検索で「タスクスケジューラ」）
2. **タスクの作成** をクリック
3. **全般** タブ:
   - 名前: `Pharma Daily Brief`
   - 「ユーザーがログオンしているかどうかにかかわらず実行する」を選択
4. **トリガー** タブ:
   - **新規** → 日次、毎日、開始: 午前7:00（任意の時刻）→ OK
5. **操作** タブ:
   - **新規** → プログラム: `powershell.exe`
   - 引数: `-ExecutionPolicy Bypass -File "C:\Users\nzm03\OneDrive\Desktop\claude code Yo\pharma_daily_brief\run_daily.ps1"`
   - （パスは環境に合わせて変更）
6. **条件** タブ: 「コンピューターをAC電源で使用している場合のみ...」のチェックを外す（推奨）
7. OK で保存

## 4. コンテンツの更新

送信されるのは `index.html` の内容です。  
Geminiでサマリーを取得したら、`index.html` の記事部分を更新してから送信するか、  
毎朝送信前に手動で更新してください。

※ 日付は送信時に自動で今日の日付に差し替わります。
