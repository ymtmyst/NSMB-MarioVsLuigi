# 自動JSON出力機能の実装計画

このドキュメントは、`.mvlreplay` ファイルをコマンドライン引数として渡し、自動的に入力データをJSON形式で出力するための実装プランです。

## 1. 概要
`nsmb.mariovsluigi.exe` に対して特定のコマンドライン引数（例: `-replayFile "path/to/input.mvlreplay"`）を渡すことで、以下のプロセスを自動実行する仕組みを構築します。

1. **アプリ起動**: コマンドライン引数を解析。
2. **リプレイ読み込み**: 指定されたリプレイファイルをロード。
3. **自動再生**: リプレイを最高速度（ヘッドレスモード想定）で再生シミュレーション。
4. **JSON出力**: 既存の `QuantumUtils` の入力記録と `GameLogicSystem` の出力機能を利用してJSONを保存。
5. **アプリ終了**: 処理完了後に自動的に終了。

---

## 2. 必要な変更・新規作成ファイル

### 2.1 新規スクリプト: `ReplayBatchProcessor.cs`
起動時の引数チェックと、一連のバッチ処理フローを制御するコンポーネントを作成します。

- **場所**: `Assets/Scripts/Utils/ReplayBatchProcessor.cs` (推奨)
- **役割**:
    - `[RuntimeInitializeOnLoadMethod]` を使用し、シーンロード直後に初期化。
    - `System.Environment.GetCommandLineArgs()` で引数を取得。
    - `.mvlreplay` ファイルパスが検出された場合、以下のオートメーションモードへ移行。
        - `ActiveReplayManager` にリプレイロードを指示。
        - シミュレーション速度 (`Time.timeScale` や `QuantumRunner.Session.Update`) を制御して高速再生。
        - ゲーム終了イベントを監視し、終了後に `Application.Quit()` を呼び出し。

### 2.2 既存スクリプト修正: `GameLogicSystem.cs`
現在の `SaveInputDataToJson` メソッドは保存先が特定のフォルダに固定されています。これをコマンド実行時の利用に合わせて柔軟に変更できるようにします。

- **変更箇所**:
    - JSONの保存先ディレクトリおよびファイル名を、固定パスではなく動的に決定できるよう修正。
    - `ReplayBatchProcessor` から保存先パスを指定できる静的プロパティ（例: `string OutputJsonPath`）を追加、または参照するように変更。
    - バッチモード実行時は、リプレイファイルと同じディレクトリ、または指定された出力先にJSONを生成するようにロジックを追加。

---

## 3. 実装詳細フロー

### Step 1: 引数の解析とモード判定
`ReplayBatchProcessor` の `Awake` または `Start` にて:
```csharp
string[] args = System.Environment.GetCommandLineArgs();
// 引数から "-replayFile" などを探索し、対象ファイルパスを取得
```

### Step 2: リプレイのロードと再生
`ActiveReplayManager.Instance` を利用してロードを行います。
- UIの非表示化（`-batchmode` 時のエラー回避のため、LoadingCanvas等の操作にNullチェックを追加する必要があるかもしれません）。
- `ActiveReplayManager.Instance.StartReplayPlayback(replayFile)` を呼び出し。

### Step 3: 高速シミュレーション
UIでの再生 (`StartReplayPlayback`) は通常速度になる可能性があるため、バッチモード時は `Update` ループ内で以下のように強制進行させます。
```csharp
if (isBatchMode) {
    // 描画を待たずにシミュレーションを進める（必要であれば）
    Time.timeScale = 100.0f; 
    // または QuantumRunner.Default.Session.Update(deltaTime) をループ実行
}
```

### Step 4: 終了検知と出力
`GameLogicSystem.EndGame` が呼び出されると、現在の実装通り `SaveInputDataToJson` が走ります。
- `ReplayBatchProcessor` は `CallbackGameDestroyed` や `EventGameEnded` を監視。
- JSON保存が完了したタイミング（数秒の猶予またはコールバック）で `Application.Quit()` を実行。

---

## 4. 実行コマンド例

ビルド後に以下のようなコマンドで実行することを想定します。

```powershell
# 基本実行
./nsmb.mariovsluigi.exe -replayFile "C:\Path\To\Replay.mvlreplay"

# ヘッドレスモード（ウィンドウを表示せず高速実行）
./nsmb.mariovsluigi.exe -batchmode -nographics -replayFile "C:\Path\To\Replay.mvlreplay"
```

## 5. 注意事項
- **UI依存**: `ActiveReplayManager` がUI要素 (`loadingCanvas` など) に依存している場合、バッチモードでNull参照エラーが出ないようガード処理を入れる必要があります。
- **保存パス**: 現状の `GameLogicSystem` は入力データを `Documents/...` に保存しています。これを運用しやすいパスに変更する修正が重要です。
