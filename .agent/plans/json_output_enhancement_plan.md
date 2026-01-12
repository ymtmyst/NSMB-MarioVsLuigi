# JSONファイル出力拡張計画

## 概要
リプレイデータのJSON出力に、AI学習に必要な追加情報を含めるための実装計画です。

## 目標
現在のキー入力情報に加えて、以下の情報をJSON出力に追加する：

1. **所有スターの枚数**
2. **スタン時間（ノックバック状態）**
3. **無敵時間（残りフレーム数）**
4. **プレイヤーの位置（XY座標）**
5. **プレイヤーの速度**

---

## 現状分析

### 現在の実装状況

#### 1. 入力記録システム (`QuantumUtils.cs`)
- **構造体**: `InputRecord` (11-23行目)
  - 現在の記録内容：
    - フレーム番号
    - プレイヤーインデックス
    - キー入力（上下左右、ジャンプ、スプリント、パワーアップアクション等）

#### 2. JSON出力システム (`GameLogicSystem.cs`)
- **メソッド**: `SaveInputDataToJson` (223-288行目)
  - ゲーム終了時に入力データをJSON形式で保存
  - 保存先: `C:\Users\tktho\Documents\★Download\MvLO\replay\入力データ`

#### 3. プレイヤーデータ構造 (`MarioPlayer.qtn`)
確認できた主要なフィールド：
- **スター**: `GamemodeData.StarChasers->Stars` (byte, 147行目)
- **無敵時間**: `InvincibilityFrames` (ushort, 111行目) - スターマン無敵
- **ダメージ無敵**: `DamageInvincibilityFrames` (byte, 97行目) - ダメージ後の無敵
- **ノックバック状態**: 
  - `CurrentKnockback` (KnockbackStrength enum, 92行目)
  - `KnockbackGetupFrames` (byte, 98行目) - 起き上がり時間
  - `IsInWeakKnockback` (bool, 93行目) - 弱ノックバック判定
- **位置**: `Transform->Position` (FPVector2, 別コンポーネント)
- **速度**: `PhysicsObject->Velocity` (FPVector2, 別コンポーネント)

---

## ノックバック（スタン）状態の詳細調査

### KnockbackStrength の種類 (`MarioPlayer.qtn` 159-165行目)
```
enum KnockbackStrength : Byte {
    None,              // スタンなし
    FireballBump,      // ファイアーボールによる軽いノックバック
    CollisionBump,     // プレイヤー同士の衝突
    Normal,            // 通常のノックバック
    Groundpound,       // ヒップドロップによるノックバック
}
```

### ノックバック状態の具体的な動作 (`MarioPlayer.cs` 400-489行目)

#### 1. **地面で受けたファイアー** (`FireballBump`)
- **条件**: ファイアーボールを地上で受けた場合
- **速度**: `Constants._3_75 / 2` (水平), `0` (垂直)
- **特徴**: 弱いノックバック (`IsInWeakKnockback = true`)

#### 2. **空中で踏まれた** (該当なし - ストンプは別処理)
- 踏まれた側はストンプ処理を受ける

#### 3. **地面で踏まれた** (`Groundpound` または `Normal`)
- **ヒップドロップで踏まれた場合** (`Groundpound`, `MarioPlayerSystem.cs` 2385行目):
  - スター損失: 3個
  - 速度: `Constants._8_25 / 2` (水平), `Constants._3_50` (垂直)
  
- **通常踏みの場合** (`Normal`):
  - スター損失: 1個
  - 速度: `Constants._3_75 / 2` (水平), `Constants._3_50` (垂直)

#### 4. **プレイヤー衝突** (`CollisionBump`)
- **条件**: プレイヤー同士が横から衝突
- **速度**: `Constants._2_50` (水平), `Constants._3_50` (垂直)
- **特徴**: 弱いノックバック (`IsInWeakKnockback = true`)

#### 5. **起き上がり時間** (`KnockbackGetupFrames`)
- **値**: 通常は25フレーム (約0.4秒 @ 60fps)
- **条件**: 弱いノックバックでない場合に設定される (`MarioPlayer.cs` 507行目)

### ノックバック時間の計算方法
- **基本**: `KnockbackTick` フィールドに現在のフレーム番号を記録
- **スターマン時**: `KnockbackTick -= 25` で短縮 (460行目)
- **起き上がり**: 地面に着地後、`KnockbackGetupFrames` が0になるまで継続

---

## 実装計画

### フェーズ1: データ構造の拡張

#### 1.1 `InputRecord` 構造体の拡張 (`QuantumUtils.cs`)
現在の構造体に以下のフィールドを追加：

```csharp
public struct InputRecord {
    // --- 既存フィールド ---
    public int FrameNumber;
    public int PlayerIndex;
    public bool Up;
    public bool Down;
    public bool Left;
    public bool Right;
    public bool Jump;
    public bool Sprint;
    public bool PowerupAction;
    public bool FireballPowerupAction;
    public bool PropellerPowerupAction;
    
    // --- 新規追加フィールド ---
    // 所有スター
    public int Stars;
    
    // ノックバック（スタン）情報
    public int KnockbackStrength;  // 0=None, 1=FireballBump, 2=CollisionBump, 3=Normal, 4=Groundpound
    public bool IsInWeakKnockback;
    public int KnockbackGetupFrames;  // 起き上がりまでの残りフレーム
    
    // 無敵時間
    public int InvincibilityFrames;        // スターマン無敵の残りフレーム
    public int DamageInvincibilityFrames;  // ダメージ無敵の残りフレーム
    
    // 位置と速度
    public float PositionX;
    public float PositionY;
    public float VelocityX;
    public float VelocityY;
}
```

### フェーズ2: データ記録処理の更新

#### 2.1 `RecordInput` メソッドの拡張 (`QuantumUtils.cs`)
現在のメソッドシグネチャ：
```csharp
public static void RecordInput(int frameNumber, int playerIndex, Input input)
```

新しいシグネチャに変更：
```csharp
public static void RecordInput(
    int frameNumber, 
    int playerIndex, 
    Input input,
    MarioPlayer mario,
    Transform2D transform,
    PhysicsObject2D physicsObject
)
```

**実装内容**:
1. 既存の入力データ記録
2. `mario.GamemodeData.StarChasers->Stars` からスター枚数を取得
3. `mario.CurrentKnockback` からノックバック状態を取得
4. `mario.KnockbackGetupFrames` から起き上がり時間を取得
5. `mario.InvincibilityFrames` と `mario.DamageInvincibilityFrames` から無敵時間を取得
6. `transform.Position` から位置座標を取得
7. `physicsObject.Velocity` から速度を取得

#### 2.2 記録呼び出し箇所の更新 (`MarioPlayerSystem.cs`)
現在の記録処理を探して更新：
- プレイヤーの入力処理ループ内で `RecordInput` を呼び出している箇所を特定
- 必要なコンポーネント（`Transform2D`, `PhysicsObject2D`）を取得して渡す

### フェーズ3: JSON出力形式の更新

#### 3.1 `SaveInputDataToJson` メソッドの更新 (`GameLogicSystem.cs`)
JSON出力形式を以下のように拡張：

```json
{
  "winningTeam": 0,
  "hasWinner": true,
  "totalRecords": 1000,
  "inputs": [
    {
      "frame": 0,
      "player": 0,
      // キー入力
      "up": false,
      "down": false,
      "left": false,
      "right": true,
      "jump": false,
      "sprint": false,
      "powerupAction": false,
      "fireballPowerupAction": false,
      "propellerPowerupAction": false,
      
      // 所有スター
      "stars": 3,
      
      // ノックバック（スタン）情報
      "knockbackStrength": 0,
      "knockbackType": "None",
      "isInWeakKnockback": false,
      "knockbackGetupFrames": 0,
      
      // 無敵時間
      "invincibilityFrames": 0,
      "damageInvincibilityFrames": 0,
      
      // 位置
      "positionX": 10.5,
      "positionY": 5.25,
      
      // 速度
      "velocityX": 2.5,
      "velocityY": 0.0
    }
  ]
}
```

**ノックバック種別の文字列マッピング**:
- 0: "None"
- 1: "FireballBump"
- 2: "CollisionBump"
- 3: "Normal"
- 4: "Groundpound"

---

## 実装手順

### ステップ1: データ構造の準備
1. `QuantumUtils.cs` の `InputRecord` 構造体を拡張
2. コンパイルして構文エラーがないか確認

### ステップ2: データ記録処理の実装
1. `QuantumUtils.RecordInput` メソッドのシグネチャを変更
2. 新しいフィールドへのデータ設定処理を追加
3. `MarioPlayerSystem.cs` で記録呼び出し箇所を探す
4. 必要なコンポーネントを取得して `RecordInput` に渡す
5. コンパイル確認

### ステップ3: JSON出力の更新
1. `GameLogicSystem.SaveInputDataToJson` メソッドを更新
2. 新しいフィールドをJSON文字列に追加
3. ノックバック種別の文字列変換処理を追加
4. コンパイル確認

### ステップ4: テストと検証
1. ゲームをビルド
2. リプレイを再生してゲーム終了まで実行
3. 出力されたJSONファイルを確認
   - すべての新しいフィールドが含まれているか
   - 値が正しく記録されているか
   - フォーマットが正しいか

---

## 注意事項

### 1. Quantumの固定小数点型（FP型）について
- `FPVector2` は Quantum の固定小数点ベクトル型
- JSON出力時には `float` に変換が必要
- 変換方法: `FP.AsFloat` または `(float)fpValue`

### 2. unsafeポインタの扱い
- `MarioPlayer*` のようなポインタ型を扱う場合
- `unsafe` コンテキスト内で処理する必要がある
- `QuantumUtils.RecordInput` メソッドに `unsafe` キーワードを追加する可能性

### 3. GamemodeData のユニオン型
- `GamemodeData.StarChasers->Stars` は Star Chasers モード専用
- 他のゲームモード（Coin Runners等）では別のデータ構造
- 現在のゲームモードを確認してから適切なフィールドにアクセス

### 4. パフォーマンスへの影響
- 毎フレーム全プレイヤーの詳細情報を記録するため、データ量が増加
- リスト操作のパフォーマンスに注意
- 必要に応じて `List<InputRecord>` の初期容量を設定（例: `new List<InputRecord>(10000)`）

---

## 期待される成果物

1. **拡張されたJSONファイル**
   - すべてのフレームでプレイヤーの詳細状態を記録
   - AI学習に必要な情報を網羅
   
2. **データの活用例**
   - スター所有状況の時系列分析
   - ノックバック発生タイミングと種類の把握
   - 無敵時間を考慮した行動選択の学習
   - 位置・速度情報を用いた移動パターン学習

---

## 今後の拡張可能性

### 追加候補のデータ
- 現在のパワーアップ状態 (`CurrentPowerupState`)
- リザーブアイテム (`ReserveItem`)
- 地面接触状態 (`PhysicsObject->IsTouchingGround`)
- ジャンプ状態 (`JumpState`)
- 保持しているアイテム (`HeldEntity`)
- 向き (`FacingRight`)
- 現在のコイン数 (`Coins`)

これらのデータを追加することで、さらに詳細なAI学習が可能になります。

---

## まとめ

この計画に従って実装することで、JSONファイルにプレイヤーの詳細な状態情報が記録されるようになります。特にノックバック（スタン）状態については、5種類の状態を正確に記録し、AI学習に活用できるようになります。
