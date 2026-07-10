import searcher
import chess
import chess.polyglot
import sys

def UCI():
    board = chess.Board()

    while True:
        line = sys.stdin.readline().strip()
        parts = line.split()

        if parts == None:
            continue

        if parts[0] == "uci":
            print("id name pChess")
            print("uci ok")
        elif parts[0] == "isready":
            print("readyok")
        elif parts[0] == "position":
            if len(parts) > 1 and parts[1] == "fen":
                fen = " ".join(parts[2:8])
                board.set_fen(fen)
            elif len(parts) > 1 and parts[1] == "startpos":
                board.reset()
            
            if "moves" in parts:
                movesIndex = parts.index("moves") + 1
                for move in parts[movesIndex:]:
                    board.push_uci(move)
        elif parts[0] == "go":
            depth = 20 #default value(s)
            wtime, btime, winc, binc, movestogo = float('inf'), float('inf'), 0, 0, 0

            if "wtime" in parts:
                wtime = int(parts[parts.index("wtime") + 1])
            if "btime" in parts:
                btime = int(parts[parts.index("btime") + 1])
            if "winc" in parts:
                winc = int(parts[parts.index("winc") + 1])
            if "binc" in parts:
                binc = int(parts[parts.index("binc") + 1])
            if "movestogo" in parts:
                movestogo = int(parts[parts.index("movestogo") + 1])
            if "depth" in parts:
                depth = int(parts[parts.index("depth") + 1])
                
            key = chess.polyglot.zobrist_hash(board)
            if board.turn:
                info = searcher.Search(board, depth, wtime, winc)
            else:
                info = searcher.Search(board, depth, btime, binc)

            if info == None:
                print("bestmove resign")
                continue

            print(f"bestmove {info[0]}")
            print(f"info score cp {info[1]}")
            print(f"info depth {info[2]}")
        elif parts[0] == "quit":
            break

if __name__ == "__main__":
    UCI()