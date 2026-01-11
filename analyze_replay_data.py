"""
リプレイ入力データ分析サンプルスクリプト

このスクリプトは、ReplayInputExtractorで抽出したCSVデータを
Pythonで読み込んで分析する例を示します。
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def load_replay_data(csv_path):
    """CSVファイルを読み込む"""
    df = pd.read_csv(csv_path)
    print(f"データ読み込み完了: {len(df)} 行")
    print(f"フレーム数: {df['Frame'].max() + 1}")
    print(f"プレイヤー数: {df['PlayerIndex'].nunique()}")
    return df

def analyze_button_usage(df, player_index=0):
    """ボタンの使用頻度を分析"""
    player_data = df[df['PlayerIndex'] == player_index]
    
    buttons = ['Up', 'Down', 'Left', 'Right', 'Jump', 'Sprint', 
               'PowerupAction', 'FireballPowerupAction', 'PropellerPowerupAction']
    
    usage_stats = {}
    for button in buttons:
        is_down_col = f'{button}_IsDown'
        was_pressed_col = f'{button}_WasPressed'
        
        total_frames = len(player_data)
        frames_held = player_data[is_down_col].sum()
        times_pressed = player_data[was_pressed_col].sum()
        
        usage_stats[button] = {
            'held_frames': frames_held,
            'held_percentage': (frames_held / total_frames) * 100,
            'times_pressed': times_pressed
        }
    
    return usage_stats

def plot_button_usage(usage_stats):
    """ボタン使用頻度をグラフ化"""
    buttons = list(usage_stats.keys())
    percentages = [usage_stats[b]['held_percentage'] for b in buttons]
    
    plt.figure(figsize=(12, 6))
    plt.bar(buttons, percentages)
    plt.xlabel('ボタン')
    plt.ylabel('押されている割合 (%)')
    plt.title('ボタン使用頻度')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig('button_usage.png')
    print("グラフを保存しました: button_usage.png")

def analyze_input_patterns(df, player_index=0):
    """入力パターンを分析"""
    player_data = df[df['PlayerIndex'] == player_index]
    
    # 移動方向の分析
    left_frames = player_data['Left_IsDown'].sum()
    right_frames = player_data['Right_IsDown'].sum()
    total_frames = len(player_data)
    
    print("\n=== 移動分析 ===")
    print(f"左移動: {left_frames} フレーム ({left_frames/total_frames*100:.1f}%)")
    print(f"右移動: {right_frames} フレーム ({right_frames/total_frames*100:.1f}%)")
    
    # ジャンプ分析
    jump_count = player_data['Jump_WasPressed'].sum()
    print(f"\n=== ジャンプ分析 ===")
    print(f"総ジャンプ回数: {jump_count}")
    print(f"平均ジャンプ間隔: {total_frames/jump_count:.1f} フレーム")
    
    # ダッシュ分析
    sprint_frames = player_data['Sprint_IsDown'].sum()
    print(f"\n=== ダッシュ分析 ===")
    print(f"ダッシュ使用: {sprint_frames} フレーム ({sprint_frames/total_frames*100:.1f}%)")

def create_training_dataset(df, player_index=0, sequence_length=10):
    """
    機械学習用のシーケンスデータセットを作成
    
    Args:
        df: 入力データフレーム
        player_index: 対象プレイヤー
        sequence_length: シーケンスの長さ(フレーム数)
    
    Returns:
        X: 入力シーケンス (samples, sequence_length, features)
        y: 次のフレームの入力 (samples, features)
    """
    player_data = df[df['PlayerIndex'] == player_index].sort_values('Frame')
    
    # 入力特徴量のカラムを選択(IsDownのみ)
    feature_cols = [col for col in player_data.columns if '_IsDown' in col]
    
    X, y = [], []
    
    for i in range(len(player_data) - sequence_length):
        # 過去sequence_lengthフレームの入力
        sequence = player_data.iloc[i:i+sequence_length][feature_cols].values
        # 次のフレームの入力
        next_input = player_data.iloc[i+sequence_length][feature_cols].values
        
        X.append(sequence)
        y.append(next_input)
    
    X = np.array(X)
    y = np.array(y)
    
    print(f"\n=== トレーニングデータセット作成 ===")
    print(f"入力シーケンス形状: {X.shape}")
    print(f"出力形状: {y.shape}")
    
    return X, y

def main():
    """メイン処理"""
    # CSVファイルのパスを指定
    csv_path = 'ReplayInputData.csv'
    
    print("=== リプレイ入力データ分析 ===\n")
    
    # データ読み込み
    df = load_replay_data(csv_path)
    
    # ボタン使用頻度分析
    print("\n=== ボタン使用統計 ===")
    usage_stats = analyze_button_usage(df, player_index=0)
    for button, stats in usage_stats.items():
        print(f"{button:25s}: {stats['held_percentage']:5.1f}% ({stats['times_pressed']:4d} 回押下)")
    
    # グラフ化
    plot_button_usage(usage_stats)
    
    # 入力パターン分析
    analyze_input_patterns(df, player_index=0)
    
    # 機械学習用データセット作成
    X, y = create_training_dataset(df, player_index=0, sequence_length=10)
    
    # データセットを保存
    np.save('training_X.npy', X)
    np.save('training_y.npy', y)
    print("\nトレーニングデータを保存しました: training_X.npy, training_y.npy")

if __name__ == '__main__':
    main()
