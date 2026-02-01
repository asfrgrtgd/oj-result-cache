# OJ 正規化ハッシュチェッカー

`program/` ディレクトリ内のC++ファイルに対してlibclangトークン化を実行し、コメントを除去してトークンストリーム `(kind, spelling)` をSHA-256でハッシュ化します。

## 実行方法

実行前に `program/` ディレクトリ内にC++ファイルを配置してください。

```bash
docker compose up --build
```

## オプション

カスタムフラグを使用してコンテナ内で実行：

```bash
docker compose run --rm oj-hash python oj_hash.py --help
```

よく使う例：

```bash
# .cpp/.ccファイルのみを対象
docker compose run --rm oj-hash python oj_hash.py --extensions cpp,cc

# トップレベルのみ（再帰なし）
docker compose run --rm oj-hash python oj_hash.py --no-recursive

# キャッシュをリセットしてクリーンに実行
docker compose run --rm oj-hash python oj_hash.py --reset-cache

# カラー出力を無効化
docker compose run --rm oj-hash python oj_hash.py --no-color
```

キャッシュはプロジェクトルートの `cache.json` に書き込まれます。
