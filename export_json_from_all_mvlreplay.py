import os
import subprocess

# ====================================================================
# このプログラムについて
# ====================================================================
# 指定フォルダ内のすべての.mvlreplayファイルを自動的に処理し、
# NSMB-MarioVsLuigi.exeを使ってJSON形式でエクスポートするバッチ処理ツールです。
#
# 【重要】実行前に以下の設定を必ず変更してください：
#   1. NSMB_EXE_ABSOLUTE_PATH: NSMB-MarioVsLuigi.exeの絶対パス
#   2. MVL_REPLAY_DIR_PATH: .mvlreplayファイルが格納されているフォルダの絶対パス
#   3. IS_HEADLESS_MODE: ゲームウィンドウを表示せずに処理する場合はTrue
# ====================================================================

# --- ここから設定について記載する ---

# NSMB-MarioVsLuigi.exe自体の絶対パスを入れること
NSMB_EXE_ABSOLUTE_PATH = r"C:\Users\tktho\Documents\★Download\MvLO\MvLOAI\NSMB-MarioVsLuigi.exe"
# mvlreplayが存在するフォルダの絶対パスを入れること
MVL_REPLAY_DIR_PATH = r"C:\Users\tktho\Documents\★Download\MvLO\replay\大会動画（20251230）"
# headlessモードを有効にするかどうか
IS_HEADLESS_MODE = True

# -- ここで設定については終了 ---

# --- 定数定義部分(プログラム本体にかかわるため、変えないこと) ---

# mvlreplayファイルの拡張子
MVL_REPLAY_FILE_EXTENSION = ".mvlreplay"

# --- 定数定義終了 ---

def get_command(mvl_replay_path):
    # これから実行するコマンドを構成する
    command = [
        NSMB_EXE_ABSOLUTE_PATH, 
    ]
    
    # headlessモードを有効にする
    if IS_HEADLESS_MODE:
        command.append("-batchmode")
        command.append("-nographics")
    
    # logを標準出力する(ゲームが自動で閉じるまで待つため)
    command.append("-logFile")
    command.append("-")

    # mvlreplayのパスを指定
    command.append("-replay")
    command.append(mvl_replay_path)

    return command

def main():
    print("以下のフォルダに存在するすべてのmvlreplayファイルをJSON出力します：")
    print(f" - {MVL_REPLAY_DIR_PATH}")
    print()

    # MVL_REPLAY_DIR_PATHにあるすべてのファイルを取得する
    mvl_replay_files = os.listdir(MVL_REPLAY_DIR_PATH)

    # mvlreplayファイル以外は無視してフィルタリングする
    mvl_replay_files = list(filter(lambda x: x.endswith(MVL_REPLAY_FILE_EXTENSION), mvl_replay_files))

    print("リプレイファイルの件数: ", len(mvl_replay_files))
    print()

    # MVL_REPLAY_DIR_PATHにあるすべてのファイルを処理する
    for file in mvl_replay_files:
        print(f"リプレイファイルの{file}をロードしています...")

        # mvlreplayファイル自体の絶対パスを作る
        mvl_replay_path = os.path.join(MVL_REPLAY_DIR_PATH, file)

        # コマンドを構成する
        command = get_command(mvl_replay_path)

        # コマンドを実行する
        subprocess.call(command)

        print(f"{file}のJSON出力が完了しました！")
        print()
    
    print("すべてのmvlreplayファイルのJSON出力が完了しました！")

if __name__ == "__main__":
    main()