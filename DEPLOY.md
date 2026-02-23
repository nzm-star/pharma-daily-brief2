# 毎朝自動更新・Web公開のセットアップ

**あなたが何もしなくても**、毎朝7時（JST）に最新のPharma Briefが自動生成され、誰でもWebで閲覧できるようにする手順です。

## 前提
- GitHub アカウント
- [Google AI Studio](https://aistudio.google.com/) で Gemini API キーを取得（無料枠あり）

---

## ステップ1: 新規リポジトリを作成

1. GitHub で **New repository** をクリック
2. リポジトリ名: `pharma-daily-brief`（任意）
3. Public、README なしで作成

## ステップ2: ファイルをプッシュ

**重要**: リポジトリのルート（トップ）に、`pharma_daily_brief` フォルダの**中身**をそのまま配置します。

例: リポジトリのルートに次のファイル・フォルダがある状態
```
pharma-daily-brief/
├── .github/
│   └── workflows/
│       └── daily-brief.yml
├── index.html
├── generate_brief.py
├── requirements.txt
├── README.md
└── ...
```

ローカルで実行する場合:
```powershell
cd "c:\Users\nzm03\OneDrive\Desktop\claude code Yo\pharma_daily_brief"
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/あなたのユーザー名/pharma-daily-brief.git
git branch -M main
git push -u origin main
```

※ 既に親フォルダが git リポジトリの場合は、`pharma_daily_brief` だけを別リポジトリとして push するか、別の方法でアップロードしてください。

## ステップ3: Gemini API キーを設定

1. [Google AI Studio](https://aistudio.google.com/apikey) で API キーを発行
2. リポジトリの **Settings** → **Secrets and variables** → **Actions**
3. **New repository secret** をクリック
4. Name: `GEMINI_API_KEY`
5. Value: 発行した API キーを貼り付け

## ステップ4: GitHub Pages を有効化

1. リポジトリの **Settings** → **Pages**
2. **Source**: `Deploy from a branch`
3. **Branch**: `main` / `/(root)`
4. Save

数分後、次の URL でアクセスできます:
```
https://あなたのユーザー名.github.io/pharma-daily-brief/
```

## 動作確認

- **手動実行**: リポジトリの **Actions** タブ → **Pharma Daily Brief** → **Run workflow** で即時実行
- **自動実行**: 毎朝 7:00 JST に自動で更新されます

## 注意
- `.env` はリポジトリに含めないでください（API キー漏洩防止）
- 初回はサンプル記事が表示されます。翌朝以降、自動生成された内容に切り替わります
- Gemini API の無料枠を超えるとエラーになります。その場合は RSS のみのフォールバックで表示されます
