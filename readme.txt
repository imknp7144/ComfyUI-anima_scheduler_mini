# anima_scheduler_lite

`beta57` と `bong_tangent` の2つのスケジューラーを、ComfyUI標準のスケジューラー一覧に**直接登録**するComfyUIカスタムノードパックです。RES4LYFと同じ方式で `comfy.samplers.SCHEDULER_HANDLERS` / `SCHEDULER_NAMES` に登録するため、KSampler等の標準スケジューラードロップダウンからそのまま選択できるようになります（専用のSIGMAS出力ノードを別途つなぐ必要はありません）。

加えて、`bong_tangent` の各種パラメータ（pivot / slope）を細かく調整したい場合向けに、単体の `Bong Tangent Scheduler` ノード（SIGMAS出力）も同梱しています。

## ✨ 特徴

- **標準ドロップダウンへの直接登録**: `beta57`・`bong_tangent` をComfyUI標準のスケジューラーリストに追加し、KSampler等の`scheduler`入力から直接選択可能に
- **RES4LYFとの共存**: RES4LYFが先に読み込まれ、同名のスケジューラーが既に登録済みの場合は登録をスキップ（衝突・上書きを回避）
- **調整可能な単体ノード**: `bong_tangent`のpivot_1 / pivot_2 / slope_1 / slope_2を個別に調整できる`Bong Tangent Scheduler`ノードを提供
- **denoise対応**: 単体ノードはdenoise値に応じてステップ数を自動調整し、部分denoise（img2img等）に対応

## 📦 構成ファイル

| ファイル | 役割 |
|---------|------|
| `__init__.py` | ComfyUI起動時に`beta57`・`bong_tangent`を標準スケジューラーとして登録するエントリーポイント |
| `bong_tangent.py` | `bong_tangent`スケジューラーのコア計算ロジック（RES4LYF由来の移植コード＋ComfyUI用ラッパー） |
| `nodes.py` | パラメータ調整可能な単体ノード`BongTangentScheduler`を定義 |

## 🧩 登録されるスケジューラー

### beta57（標準ドロップダウンに登録）
ComfyUI組み込みの`beta_scheduler`を`alpha=0.5, beta=0.7`で呼び出したもので、追加の数式は実装していません。RES4LYF自身もbeta57をこの定義で扱っているため、そのまま踏襲しています。

### bong_tangent（標準ドロップダウンに登録）
2段階のタンジェント補間（start → middle → end）でsigma列を生成するスケジューラーです。標準ドロップダウン経由で使う場合、ComfyUIのコアディスパッチャーは`handler(model_sampling, steps)`しか呼び出せない仕様のため、pivot_1 / pivot_2 / slope_1 / slope_2はすべてデフォルト値（0.6, 0.6, 0.2, 0.2）で固定されます。これらのパラメータを調整したい場合は、下記の単体ノード`Bong Tangent Scheduler`を使用してください。

## 🎛️ Bong Tangent Scheduler（単体ノード）

RES4LYFの`bong_tangent`と同じ入出力規約（`model` + `steps` → `SIGMAS`）を持つ、ComfyUI標準の`BasicScheduler`/`KarrasScheduler`と同じ形でSamplerCustom(Advanced)チェーンに組み込める単体ノードです。

### 入力パラメータ

| パラメータ | 型 | デフォルト | 範囲 | 説明 |
|----------|-----|-----------|------|------|
| model | MODEL | - | - | sigma_max / sigma_minの取得元となるモデル |
| steps | INT | 30 | 1-10000 | サンプリングステップ数 |
| pivot_1 | FLOAT | 0.6 | 0.0-1.0 | ステージ1（start→middle）のタンジェント曲線の変曲点位置 |
| pivot_2 | FLOAT | 0.6 | 0.0-1.0 | ステージ2（middle→end）のタンジェント曲線の変曲点位置 |
| slope_1 | FLOAT | 0.2 | 0.01-5.0 | ステージ1の曲線の急峻さ |
| slope_2 | FLOAT | 0.2 | 0.01-5.0 | ステージ2の曲線の急峻さ |
| denoise | FLOAT | 1.0 | 0.0-1.0 | denoise強度。1.0未満の場合、`steps / denoise`で内部的な総ステップ数を計算し、末尾`steps + 1`個のsigmaを切り出す（denoise ≤ 0.0の場合は空のSIGMASを返す） |

### 出力

| 出力名 | 型 | 説明 |
|-------|-----|------|
| SIGMAS | SIGMAS | 生成されたsigma列（`bong_tangent`形状、末尾は0.0） |

カテゴリ: `sampling/custom_sampling/schedulers`
表示名: `Bong Tangent Scheduler (RES4LYF-derived)`

## 💡 使用例

### 例1: 標準KSamplerでbong_tangentを使う
```
KSampler
    scheduler: bong_tangent  ← ComfyUI起動時に自動登録されたもの
    ↓
（pivot/slopeはデフォルト値 0.6, 0.6, 0.2, 0.2 で固定）
```

### 例2: pivot/slopeを調整してSamplerCustom(Advanced)で使う
```
Bong Tangent Scheduler
    model: (Load Checkpoint等から接続)
    steps: 30
    pivot_1: 0.55
    pivot_2: 0.65
    slope_1: 0.3
    slope_2: 0.15
    denoise: 1.0
    ↓ (SIGMAS)
SamplerCustomAdvanced
    ↓
VAE Decode → Save Image
```

### 例3: img2img的な部分denoiseで使う
```
Bong Tangent Scheduler
    steps: 20
    denoise: 0.6  ← 内部的に steps/denoise ≈ 33 ステップ分を計算し、末尾21個を使用
    ↓ (SIGMAS)
SamplerCustomAdvanced (latentは事前にノイズを乗せたものを接続)
```

## 🛠️ インストール方法

### 手動インストール
1. ComfyUIのインストールディレクトリに移動
2. `custom_nodes`フォルダ内に新しいフォルダを作成
   ```bash
   cd ComfyUI/custom_nodes
   mkdir anima_scheduler_lite
   ```
3. `__init__.py`・`bong_tangent.py`・`nodes.py`をコピー
4. ComfyUIを再起動

### インストール後の確認
1. ComfyUIを起動し、コンソールログに以下のような行が出力されることを確認
   ```
   [anima_scheduler_lite] registered 'beta57' scheduler.
   [anima_scheduler_lite] registered 'bong_tangent' scheduler.
   ```
   （RES4LYFが先に読み込まれ既に登録済みの場合は代わりに`... is already registered (likely by RES4LYF) - skipping.`と表示される）
2. KSampler等の`scheduler`ドロップダウンに`beta57`・`bong_tangent`が追加されていることを確認
3. ノード追加メニューで`sampling/custom_sampling/schedulers`カテゴリを開き、`Bong Tangent Scheduler (RES4LYF-derived)`が表示されることを確認

## ⚙️ 技術仕様

### beta57
- `comfy.samplers.beta_scheduler`を`alpha=0.5, beta=0.7`で呼び出すだけの薄いラッパー
- 独自の数式実装は無し

### bong_tangentのコア計算（`get_bong_tangent_sigmas` / `bong_tangent_scheduler`）
- 単一ステージのタンジェント補間を`get_bong_tangent_sigmas(steps, slope, pivot, start, end)`で計算し、`arctan`ベースの曲線を`start`〜`end`の範囲に正規化
- `bong_tangent_scheduler`はこれを2回（start→middle、middle→end）呼び出して連結する2段階スケジュール
- pivot_1/pivot_2はステップ数に対する割合として内部でインデックスに変換され、slope_1/slope_2は`steps/40`でスケーリングされる
- RES4LYF（ClownsharkBatwing）の公開ソースを移植したものです（出典は`bong_tangent.py`冒頭のコメント参照）

### `bong_tangent_scheduler_for_model`（ComfyUI用ラッパー）
- モデルの実際の`sigma_max` / `sigma_min`を取得し、正規化されたstart=1.0/end=0.0の代わりに使用
- `steps - 1`個のsigmaを`sigma_max`→`sigma_min`で生成した後、末尾に厳密な`0.0`を1つ追加（ComfyUI組み込みスケジューラーと同じ流儀）
- **このラッパー部分はRES4LYFからの直接移植ではなく、独自の再構成です**（下記「移植に関する注記」参照）

### 単体ノードのdenoise処理
- `denoise < 1.0`の場合、`total_steps = int(steps / denoise)`で総ステップ数を計算してsigma列を生成した後、末尾`steps + 1`個を切り出す
- `denoise <= 0.0`の場合は空の`SIGMAS`を返す

## ⚠️ 移植に関する注記（重要）

`bong_tangent.py`のコメントに記載の通り、このスケジューラーは以下の前提で実装されています。

- `get_bong_tangent_sigmas`と`bong_tangent_scheduler`は、RES4LYFの公開ソース（下記出典）を忠実に移植したものです。ただし元コードは巨大なため行単位の完全な差分確認はできておらず、サードパーティのミラー経由での照合による確認である旨が明記されています。
- `bong_tangent_scheduler_for_model`（正規化されたstart/endを実モデルのsigma_max/sigma_minに置き換える橋渡し部分）は、RES4LYFの内部実装をそのまま確認したものではなく、ComfyUI組み込みスケジューラー（karras/exponential等）と同じ流儀に沿って独自に再構成したものです。本番用途で使う前に、実際のRES4LYFノードとA/B比較することが推奨されています。

出典（コード内コメントより）:
```
https://github.com/ClownsharkBatwing/RES4LYF/blob/a3999a56a650da5cffe9e8f9f8b115f764603620/sigmas.py#L4065
```

## 📜 ライセンス

RES4LYF（ClownsharkBatwing）はAGPL-3.0（商用利用に関する追加条項付き）でライセンスされています。このコードパックを配布する場合は、`bong_tangent.py`冒頭の帰属表示（attribution header）を保持し、AGPL-3.0（該当する場合は商用利用条項も含む）に自身の配布形態が準拠しているか確認してください。

## 🔧 トラブルシューティング

### `beta57`・`bong_tangent`がスケジューラー一覧に出てこない
- コンソールログで登録成功メッセージが出ているか確認
- RES4LYFが導入済みで、かつRES4LYFが先に同名スケジューラーを登録している場合は意図的にスキップされる仕様（ログに`already registered`と出力される）
- `comfy.samplers`のバージョン差異等で`_register_scheduler`が例外を投げていないか、起動ログの`[anima_scheduler_lite] failed to register core schedulers: ...`を確認

### 標準ドロップダウン経由の`bong_tangent`でpivot/slopeを変えたい
- コアディスパッチャーの都合上、標準ドロップダウン経由ではデフォルト値固定です
- パラメータを調整したい場合は単体ノード`Bong Tangent Scheduler`を使用してください

### RES4LYFと併用した場合の挙動が不安
- 登録処理は「先に読み込まれた方が優先」で、どちらが読み込まれても`beta57`は数値的に完全に同一の定義です
- `bong_tangent`はベストエフォートの再構成のため、RES4LYF版との厳密な数値一致は保証されません（上記「移植に関する注記」参照）

## 🙏 クレジット

`beta57`・`bong_tangent`のコア数式はRES4LYF（ClownsharkBatwing）由来です。このノードパックはComfyUIのエコシステムの一部として、標準スケジューラー一覧への統合を目的に開発されました。

---

**Happy Scheduling! 🎨✨**