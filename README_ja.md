# Dify対応 Wikipedia Q\&Aチャットボット バックエンド

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/Docker-20.10+-blue.svg)](https://www.docker.com/)

Dify AIチャットボットに、日本語版Wikipedia全体の知識をナレッジベースとして提供するために設計されたバックエンドシステムです。このプロジェクトは、高速な全文検索と最新の意味検索を組み合わせたハイブリッド検索APIを提供し、Difyにカスタムツールとして統合することで、チャットボットが検証済みの情報源に基づいて質問に回答できるようになります。

## 特徴

  - **堅牢なデータパイプライン**: 日本語版WikipediaのXMLダンプ全体を処理するための、複数ステージから成る、中断・再開可能なパイプラインを構築。
  - **ハイブリッド検索基盤**: キーワード検索（`pg_trgm`）とベクトル検索（`pg_vector`とHNSWインデックス）の両方を実装し、高度で正確な情報検索の基盤を提供。
  - **GPUによるベクトル化高速化**: Docker経由でNVIDIA GPUを活用し、Sentence Transformerモデルによる記事のベクトル化処理を劇的に高速化。
  - **FastAPIによるバックエンド**: FastAPIで構築された、モダンで高性能なAPIサーバーが検索とチャット履歴管理のエンドポイントを提供。
  - **Difyエージェント連携**: セルフホストしたDifyインスタンスに、動的に生成されたOpenAPIスキーマを介して、カスタムツールとしてシームレスに統合。
  - **完全なコンテナ化とネットワーク**: このプロジェクトとローカルDifyインスタンスの両方をDocker Composeで管理し、共有ネットワークでブリッジすることで、安定したコンテナ間通信を実現。

## アーキテクチャ

このシステムは、2つの独立した`docker-compose`プロジェクトが、共有のDockerネットワークを介して通信することで動作します。データ準備パイプラインは、堅牢性とメンテナンス性のために、責務が分離された一連の独立したスクリプトとして設計されています。


### 技術スタック

  - **バックエンド**: Python, FastAPI
  - **データベース**: PostgreSQL (`pg_trgm` & `pg_vector`拡張)
  - **AI/ML**: Dify (セルフホスト), Sentence Transformers
  - **インフラ**: Docker, Docker Compose, NVIDIA Container Toolkit (GPU利用時)

## 🚀 セットアップとインストール

このセットアップは、このリポジトリとローカルのDifyインスタンスの両方を起動し、接続することを伴います。

### 前提条件

  - Git
  - Docker & Docker Compose
  - （任意だが強く推奨）NVIDIA GPUと最新のドライバ、そしてOSに対応したNVIDIA Container Toolkitのサポート（例：WSL2上のDocker Desktop経由）

### ステップ1：リポジトリのクローン

このプロジェクトとDify公式リポジトリを、それぞれ別のディレクトリにクローンします。

```bash
# このプロジェクトをクローン
git clone https://github.com/automatedtomato/dify-rag-wiki.git
cd dify-rag-wiki

# 親ディレクトリに戻り、Difyをクローン
cd ..
git clone https://github.com/langgenius/dify.git
```

### ステップ2：共有Dockerネットワークの作成

2つのプロジェクトが互いに通信できるように、専用のDockerネットワークを作成します。これは一度だけ実行すればOKです。

```bash
docker network create chatbot-network
```

### ステップ3：各サービスの設定と起動

2つのターミナルを準備してください。

**ターミナル1（このプロジェクト用）:**

1.  `dify-rag-wiki`ディレクトリに移動します。
2.  環境変数ファイルを作成します: `cp .env.example .env`。
3.  新しい`.env`ファイルに必要な値を設定します。
4.  コンテナを起動します。
      - **GPU利用時:** `docker-compose -f docker-compose.yml -f docker-compose.gpu.yml up -d --build`
      - **CPUのみ:** `docker-compose up -d --build`

**ターミナル2（Difyプロジェクト用）:**

1.  `dify/docker`ディレクトリに移動します。
2.  Dify用の環境変数ファイルを作成します: `cp .env.example .env`。
3.  `dify/docker/docker-compose.yml`を修正し、共有ネットワークに参加させます（`networks:`ブロックに`chatbot-network`を追加し、`api`, `worker`, `db`サービスをそのネットワークに参加させる）。
4.  Difyのコンテナを起動します: `docker-compose up -d`。

### ステップ4：データ準備パイプラインの実行

全てのコンテナが起動したら、**`dify-rag-wiki`プロジェクトのルート**から、\*\*ホストマシン（WSL2ターミナル）\*\*で以下のコマンドを実行します。

```bash
docker-compose exec python-dev python scripts/init_pipeline.py
```

また、各ステップを個別で起動することもできます。

```bash
# 1. 必要なデータダンプをすべてダウンロード
docker-compose exec python-dev python scripts/wiki_loader.py

# 2. XMLを解析し、中間ファイル(JSONL)を生成
# (CPUに負荷がかかる、長時間の処理)
docker-compose exec python-dev python scripts/wiki_parser.py

# 3. 中間ファイルからDBにデータを投入
# (コンテナ内で実行)
docker-compose exec python-dev python scripts/inserter.py

# 4. 全記事をベクトル化
# (GPUを使用する、非常に高負荷の処理)
docker-compose exec python-dev pythonscripts/vectorizer.py

# 5. 最終的なDBインデックスをすべて作成
# (ディスクI/Oに負荷がかかる、長時間の処理)
docker-compose exec python-dev python scripts/index_generator.py
```

## 使い方とテスト (Usage and Testing)
パイプラインが完了したら、2つの方法でシステムをテストできます。
### **1. APIドキュメント（Swagger UI）でのテスト**
バックエンドAPIを単体でテストするのに最適です。
1. ブラウザで`http://localhost:8088/docs`を開きます。
2. `GET /api/articles/search`エンドポイントを開きます。
2. 「Try it out」をクリックし、クエリ（例: `恐竜`）を入力して「Execute」を押します。
4. ハイブリッド検索によって見つかった、関連性の高い記事のリストが、ほぼ一瞬で返ってくれば成功です。

### **2. フロントエンドとDifyを使ったテスト**
アプリケーション全体をエンドツーエンドでテストします。
1. **Difyツールの設定:**
      - ローカルのDify (`http://localhost/`) にアクセスし、**エージェント**（Agent）タイプのアプリを新規作成します。
      - **ツール** -> **ツールを追加** -> **カスタム**と進みます。
      - `http://localhost:8088/openapi.json`からOpenAPIスキーマをコピーします。
      - スキーマを修正し、`servers`ブロックにコンテナの内部アドレスを指すURLを追加します: `"servers": [ { "url": "http://dify-rag-dev:8000" } ]`。
      - 修正後のスキーマをDifyに貼り付けて、ツールを保存します。
      - エージェントの`オーケストレーション`画面で、ツールを追加し、プロンプトでツールを使うよう指示します。
2. **フロントエンドサーバーの起動:**
      - `dify-rag-wiki`プロジェクトのルートから、以下のコマンドを実行します。
        ```Bash
        python -m http.server 8000 --directory ./frontend
        ```
3. **チャットの実行:**
      - ブラウザで`http://localhost:8000`を開きます。
      - 質問を入力し、システム全体が連携して動作する様子を観察します。

## トラブルシューティング

  - **WSL2でのパーミッションエラー**: `docker build`やその他の操作中に`./postgres-data`ディレクトリ関連の`Permission Denied`エラーに遭遇した場合、コンテナを初回起動した後に、ホストのWSL2ターミナルから以下のコマンドを実行してください。
    ```bash
    sudo chmod -R 777 ./postgres-data
    ```
  - **インデックス作成中のメモリ不足**: `create_indexes.py`がメモリ不足で失敗する場合、`docker-compose.yml`の`db`サービスに`mem_limit`と`shm_size`が設定されていることを確認してください（例: `mem_limit: 4g`, `shm_size: 2g`）。

## ライセンス

このプロジェクトはMITライセンスです。

## 作成者
Hikaru Tomizawa（富澤晃）