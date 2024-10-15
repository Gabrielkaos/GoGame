import random
import numpy as np
from GoEngine import Board, Move, opposite_turn
from GoConstants import board_size, empty, white, komi, infinite


def count_score(board: Board, color):
    return board.get_territory_of(color) + \
           board.captured[opposite_turn(color)] + \
           (komi if color == white else 0)


def is_edge(row, col):
    return row == 0 or col == 0 or row == (board_size - 1) or col == (board_size - 1)


def score_of_rowcol(i):
    return abs(board_size // 3 - i)


def evaluate_center_ness(moves, in_select_if_random=False):
    if len(moves) == 0:
        return None
    rowcol_with_scores = []
    is_passing = False
    for i in moves:
        if in_select_if_random:
            is_passing = i.is_passing_move
            row, col = i.row, i.col
        else:
            row, col = i[0], i[1]
        score = 0
        score -= score_of_rowcol(row)
        score -= score_of_rowcol(col)

        rowcol_with_scores.append(((row, col), score, is_passing))

    if in_select_if_random: return sorted(rowcol_with_scores, key=lambda t: t[1], reverse=True)
    best_move = sorted(rowcol_with_scores, key=lambda t: t[1], reverse=True)[0]
    return best_move[0]


def evaluate_liberty(state: Board, color, liberties):
    best_liberty = liberties[0]
    best_count = 0

    for liberty in liberties:
        state.board[liberty[0]][liberty[1]] = color

        state.call_count(liberty[0], liberty[1], color, empty_marked=True)

        if len(state.liberties) > best_count and not is_edge(liberty[0], liberty[1]):
            best_liberty = liberty
            best_count = len(state.liberties)

        state.board[liberty[0]][liberty[1]] = empty

    return best_liberty


def evaluate_captures(captures):
    if len(captures) == 0:
        return None
    best_move = sorted(captures, key=lambda t: t[1], reverse=True)[0]
    return best_move[0]


def select_move(state: Board, legal_moves, not_main=False):
    # book moves
    ###########################################################################################################
    if state.his_ply > 0:
        if state.history[state.his_ply - 1].move.is_passing_move:
            if count_score(state, state.turn) > count_score(state, opposite_turn(state.turn)):
                return Move(0, 0, is_passing_move=True)

    if np.count_nonzero(state.board) < 4:
        targets = []
        if board_size == 19 or board_size == 13:
            targets = [(3, 3), (3, board_size - 4), (board_size - 4, 3), (board_size - 4, board_size - 4)]
        if board_size == 9:
            targets = [(2, 2), (2, board_size - 3), (board_size - 3, 2), (board_size - 3, board_size - 3)]

        for target in targets:
            if state.board[target[0]][target[1]] == empty:
                return Move(target[0], target[1])

    ###########################################################################################################

    best_move = None
    save = None

    defend_moves = []
    surround_moves = []
    capture_moves = []

    # capturing
    for row in range(board_size):
        for col in range(board_size):
            piece = state.board[row][col]
            if piece == opposite_turn(state.turn):
                state.call_count(row, col, opposite_turn(state.turn), empty_marked=True)
                if len(state.liberties) == 1:
                    target_sq = state.liberties[0]
                    capture_moves.append((target_sq, len(state.block)))

    # saving
    # if the saving square is in edge we do not consider that save
    # if we make the saving move and the liberty is still 1 we also don't consider that
    for row in range(board_size):
        for col in range(board_size):
            piece = state.board[row][col]
            if piece == state.turn:
                state.call_count(row, col, state.turn, empty_marked=True)
                if len(state.liberties) == 1:
                    target_sq = state.liberties[0]
                    state.board[target_sq[0]][target_sq[1]] = state.turn
                    state.call_count(target_sq[0], target_sq[1], state.turn, empty_marked=True)
                    if len(state.liberties) == 1:
                        state.board[target_sq[0]][target_sq[1]] = empty
                        continue
                    state.board[target_sq[0]][target_sq[1]] = empty
                    if not is_edge(target_sq[0], target_sq[1]):
                        best_move = target_sq
                        save = target_sq
                        break

    # defend
    # if we detect that our liberty==2 we select square where we get more liberty
    # if target_sq in edge skip that
    # if we make move and liberty <= 2 still skip that also
    for row in range(board_size):
        for col in range(board_size):
            piece = state.board[row][col]
            if piece == state.turn:
                state.call_count(row, col, state.turn, empty_marked=True)
                if len(state.liberties) == 2:
                    best_liberty = evaluate_liberty(state, state.turn, state.liberties)

                    if is_edge(best_liberty[0], best_liberty[1]):
                        continue
                    state.board[best_liberty[0]][best_liberty[1]] = state.turn
                    state.call_count(best_liberty[0], best_liberty[1], state.turn, empty_marked=True)
                    if len(state.liberties) <= 2:
                        state.board[best_liberty[0]][best_liberty[1]] = empty
                        continue
                    state.board[best_liberty[0]][best_liberty[1]] = empty

                    defend_moves.append(best_liberty)

    # surround
    # if selected sq is illegal skip that
    # if we surround but our liberty becomes <=2 skip that
    for row in range(board_size):
        for col in range(board_size):
            piece = state.board[row][col]
            if piece == opposite_turn(state.turn):
                state.call_count(row, col, opposite_turn(state.turn), empty_marked=True)

                if len(state.liberties) > 1:
                    liberties = state.liberties
                    for liberty in liberties:
                        move = Move(liberty[0], liberty[1])
                        if not state.make_move(move):
                            continue
                        state.undo_move()

                        ###################
                        state.board[liberty[0]][liberty[1]] = state.turn
                        state.call_count(liberty[0], liberty[1], state.turn, empty_marked=True)
                        if len(state.liberties) <= 2:
                            state.board[liberty[0]][liberty[1]] = empty
                            continue
                        state.board[liberty[0]][liberty[1]] = empty
                        ###################

                        surround_moves.append(liberty)

    # select defend moves
    defend = evaluate_center_ness(defend_moves)
    if defend: best_move = defend
    # select surround moves
    surround = evaluate_center_ness(surround_moves)
    if surround: best_move = surround
    capture = evaluate_captures(capture_moves)
    if capture: best_move = capture

    if best_move:
        if not capture and not save and not defend:
            best_move = surround
        elif not capture and not save and defend:
            best_move = defend
        if save:
            best_move = save
        if capture:
            best_move = capture

        if Move(best_move[0], best_move[1]) in legal_moves:
            return Move(best_move[0], best_move[1])
        if not_main:
            return random.choice(legal_moves)
        return None

    if not_main:
        return random.choice(legal_moves)
    return None


def select_best_move(board: Board):
    legal_moves = board.generate_all_legal_moves()
    best_move = select_move(board, legal_moves)
    if best_move: return best_move
    print('territorial mode')
    sorted_moves = evaluate_center_ness(legal_moves, in_select_if_random=True)

    color = board.turn
    best_score = -infinite

    for i in sorted_moves:
        move = Move(i[0][0], i[0][1], is_passing_move=i[2])
        board.make_move(move)

        score = (count_score(board, color) - count_score(board, opposite_turn(color)))

        if score > best_score:
            best_move = move
            best_score = score

        board.undo_move()

    if best_move: return best_move
    row = sorted_moves[0][0][0]
    col = sorted_moves[0][0][1]
    passing = sorted_moves[0][2]
    best_move = Move(row, col, is_passing_move=passing)
    return best_move
