import chess
import chess.polyglot
from operator import itemgetter
import time
import math
import random

from pChess import evaluate

board = chess.Board()

#startFEN = "r1b1k1nr/ppp2ppp/2np4/2b5/8/2NBPQ1P/PPPP1P1N/R1B1K3"

#board.set_fen(startFEN)

def getBookMove(node):
    with chess.polyglot.open_reader("/Users/henrylynch/Desktop/Code/Python_/pChess/lichess-bot/pChess/baron30.bin") as file:
        entries = list(file.find_all(node))
        if entries:
            entry = random.choice(entries)
            return entry.move
        else:
            return None
        
EXACT = 0
LOWERBOUND = 1
UPPERBOUND = 2
class transTable:
    def __init__(self) -> None:
        self.table = {}
    def store(self, key, depth, value, flag, bestMove) -> None:
        if key in self.table:
            if self.table[key]['depth'] > depth:
                return
            
        self.table[key] = {
            'depth': depth,
            'value': value,
            'flag': flag,
            'bestMove': bestMove,

        }
    def getValue(self, key):
        return self.table.get(key, None)
    def clear(self) -> None:
        self.table.clear()
table = transTable()

def orderMoves(node, ttEntry, moves_array):
    moves = {}
    for move in moves_array:
        moveScore = 0
        if node.gives_check(move):
            moveScore += 12

        if move.promotion:
            moveScore += evaluate.getRawVal(move.promotion)
        
        if node.is_capture(move):
            victim = node.piece_at(move.to_square)
            aggressor = node.piece_at(move.from_square)
            
            moveScore += evaluate.getRawVal(victim) - evaluate.getRawVal(aggressor)

        moves[move] = moveScore
    
    ordered = [m for m, _ in sorted(moves.items(), key=itemgetter(1), reverse=True)]

    if ttEntry and ttEntry['bestMove'] in ordered:
        ordered.remove(ttEntry['bestMove'])
        ordered.insert(0, ttEntry['bestMove'])
    return ordered

def quiescence(node, a, b, reg_depth):
    #turn = 1 if node.turn else -1
        
    staticEval = evaluate.evaluate(node, reg_depth)

    bestQVal = staticEval
    if bestQVal >= b:
        return bestQVal
    elif bestQVal > a:
        a = bestQVal

    moves = list(node.generate_legal_captures())
    for move in moves:
        node.push(move)
        score = -quiescence(node, -b, -a, reg_depth)
        node.pop()

        if score >= b:
            return score
        if score > bestQVal:
            bestQVal = score
        if score > a:
            a = score
    return bestQVal

def PVS(node, depth, a, b, timeS, timeA):
    if timeS > timeA:
        return None
    
    #turn = 1 if node.turn else -1

    origAlpha = a
    origBeta = b

    key = chess.polyglot.zobrist_hash(node)
    ttEntry = table.getValue(key)
    if ttEntry is not None and ttEntry['depth'] >= depth:
        if ttEntry['flag'] == EXACT:
            return ttEntry['value']
        elif ttEntry['flag'] == LOWERBOUND:
            a = max(a, ttEntry['value'])
        elif ttEntry['flag'] == UPPERBOUND:
            b = min(b, ttEntry['value'])

        if a >= b:
            return ttEntry['value']
    
    if depth == 0 or node.is_game_over():
        return quiescence(node, a, b, depth)
    
    moves = list(node.legal_moves)
    moves = orderMoves(node, ttEntry, moves)
    bestMove = moves[0]
    score = 0

    for i, move in enumerate(moves):
        if i == 0:
            node.push(move)
            score = PVS(node, depth - 1, -b, -a, time.perf_counter(), timeA)
            node.pop()

            if score == None:
                return None
            score *= -1
        else:
            node.push(move)
            score = PVS(node, depth - 1, -a - 1, -a, time.perf_counter(), timeA)
            node.pop()

            if score == None:
                return None
            score *= -1

            if a < -score < b:
                node.push(move)
                score = PVS(node, depth - 1, -b, -a, time.perf_counter(), timeA)
                node.pop()

                if score == None:
                    return None
                score *= -1

        if score > a:
            a = score
            bestMove = move

        if a >= b:
            break

    if a <= origAlpha:
        flag = UPPERBOUND
    elif a >= origBeta:
        flag = LOWERBOUND
    else:
        flag = EXACT

    table.store(key, depth, a, flag, bestMove)
    return a

def Search(node, d, timer, inc, smartTime):
    table.clear()
    p_key = chess.polyglot.zobrist_hash(node)

    book = getBookMove(node)
    if book != None:
        info = [book, "book", 0]
        return info

    if smartTime:
        game_phase = evaluate.getPieceInfo(node)[2]

        #bell_max = (timer / 20) * 0.5 * (math.sin(math.pi * game_phase)) ** 2 + 1000
        logistic_max = (timer / 20)/(1 + math.pow(math.e, game_phase))

        allowedTime = (logistic_max + inc / 2) / 1000 + time.perf_counter()
    else:
        allowedTime = timer / 1000 + time.perf_counter()

    timeSpent = time.perf_counter()
    depth = 1
    bestinfo = []

    window = 15 #centipawns
    value = 0

    while depth <= d:
        if depth == 1:
            a = -float('inf')
            b = float('inf')
        else:
            a = value - window
            b = value + window

        value = PVS(node, depth, a, b, timeSpent, allowedTime)
        timeSpent = time.perf_counter()

        if value == None:
            return bestinfo

        if value <= a:
            value = PVS(node, depth, -float('inf'), b, timeSpent, allowedTime)
        elif value >= b:
            value = PVS(node, depth, a, float('inf'), timeSpent, allowedTime)
        timeSpent = time.perf_counter()

        info = table.getValue(p_key)

        if info == None:
            continue

        bestinfo = [info['bestMove'], info['value'], depth]

        if value == None:
            #print(f"info depth {depth}")
            return bestinfo 

        depth += 1
    #print(f"info depth {d}")
    return bestinfo

#Search(board, 10, 100000, 0)