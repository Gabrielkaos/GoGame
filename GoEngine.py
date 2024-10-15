import numpy as np
from GoConstants import board_size, empty, black, white, max_moves, col_to_char, heatmap_values
from GoFunctions import rand64, index_from_row_col

"""
    JAPANESE METHOD
        -surrounded by the pieces is considered its territory minus the opponents capture piece
    CHINESE METHOD
    -number of piece + opponent captured or;
    -number of piece - captured piece
"""


# TODO improve the move selector
# TODO fix GTPProtocol

def is_offboard(row, col):
    return row >= board_size or row < 0 or col >= board_size or col < 0


def opposite_turn(turn):
    return white if turn == black else black


def does_repeat(rep_table, pos_key):
    for i in rep_table:
        if i.pos_key == pos_key:
            return True
    return False


class History:
    def __init__(self):
        self.pos_key = np.uint64(0)
        self.move = None
        self.removed_blocks = []


class Move:
    def __init__(self, row, col, is_passing_move=False):
        self.row = row
        self.col = col
        self.is_passing_move = is_passing_move
        self.move_id = (row * 1000) + (col * 100) + (10 * row * col) + self.is_passing_move

    def __eq__(self, other):
        if isinstance(other, Move):
            return other.move_id == self.move_id
        return False

    def __str__(self):
        if self.is_passing_move: return "pass"
        return col_to_char[self.col].upper() + str(((board_size - 1) - self.row) + 1)


class Board:
    def __init__(self):
        """
        board essentials
        """
        self.board = np.zeros((board_size, board_size), dtype=int)
        self.turn = black
        self.history = [History() for _ in range(max_moves)]
        self.his_ply = 0
        self.marked = np.zeros((board_size, board_size), dtype=int)
        self.liberties = []
        self.block = []
        self.is_game_over = False
        self.captured = np.zeros(3, dtype=int)
        self.heatmap = np.zeros((3, board_size, board_size), dtype=int)

        """
        hash keys
        """
        self.piece_keys = np.zeros((3, board_size * board_size), dtype=np.uint64)
        self.side_key = np.uint64(0)
        self._init_hash_keys()
        self.pos_key = self.generate_pos_key()

    def _init_hash_keys(self):
        for i in range(3):
            for row in range(board_size):
                for col in range(board_size):
                    index = index_from_row_col(row, col)
                    self.piece_keys[i][index] = rand64()

        self.side_key = rand64()

    def _update_heatmaps(self, row, col, color):

        self.heatmap[color][row][col] += heatmap_values[0]

        # east directions
        for i in range(1, 3):
            if not is_offboard(row, col + i):
                self.heatmap[color][row][col + i] += heatmap_values[i]
            else:
                break

        # west directions
        for i in range(1, 3):
            if not is_offboard(row, col - i):
                self.heatmap[color][row][col - i] += heatmap_values[i]
            else:
                break

        # north directions
        for i in range(1, 3):
            if not is_offboard(row - i, col):
                self.heatmap[color][row - i][col] += heatmap_values[i]
            else:
                break

        # south directions
        for i in range(1, 3):
            if not is_offboard(row + i, col):
                self.heatmap[color][row + i][col] += heatmap_values[i]
            else:
                break

        # northeast directions
        for i in range(1, 3):
            if not is_offboard(row - i, col + i):
                self.heatmap[color][row - i][col + i] += heatmap_values[i]
            else:
                break

        # northwest directions
        for i in range(1, 3):
            if not is_offboard(row - i, col - i):
                self.heatmap[color][row - i][col - i] += heatmap_values[i]
            else:
                break

        # southeast directions
        for i in range(1, 3):
            if not is_offboard(row + i, col + i):
                self.heatmap[color][row + i][col + i] += heatmap_values[i]
            else:
                break

        # southwest directions
        for i in range(1, 3):
            if not is_offboard(row + i, col - i):
                self.heatmap[color][row + i][col - i] += heatmap_values[i]
            else:
                break

        if not is_offboard(row - 2, col + 1): self.heatmap[color][row - 2][col + 1] += heatmap_values[2]
        if not is_offboard(row - 2, col - 1): self.heatmap[color][row - 2][col - 1] += heatmap_values[2]
        if not is_offboard(row + 2, col + 1): self.heatmap[color][row + 2][col + 1] += heatmap_values[2]
        if not is_offboard(row + 2, col - 1): self.heatmap[color][row + 2][col - 1] += heatmap_values[2]

        if not is_offboard(row - 1, col + 2): self.heatmap[color][row - 1][col + 2] += heatmap_values[2]
        if not is_offboard(row - 1, col - 2): self.heatmap[color][row - 1][col - 2] += heatmap_values[2]
        if not is_offboard(row + 1, col + 2): self.heatmap[color][row + 1][col + 2] += heatmap_values[2]
        if not is_offboard(row + 1, col - 2): self.heatmap[color][row + 1][col - 2] += heatmap_values[2]

    def _remove_heatmaps(self, row, col, color):

        self.heatmap[color][row][col] -= heatmap_values[0]

        # east directions
        for i in range(1, 3):
            if not is_offboard(row, col + i):
                self.heatmap[color][row][col + i] -= heatmap_values[i]
            else:
                break

        # west directions
        for i in range(1, 3):
            if not is_offboard(row, col - i):
                self.heatmap[color][row][col - i] -= heatmap_values[i]
            else:
                break

        # north directions
        for i in range(1, 3):
            if not is_offboard(row - i, col):
                self.heatmap[color][row - i][col] -= heatmap_values[i]
            else:
                break

        # south directions
        for i in range(1, 3):
            if not is_offboard(row + i, col):
                self.heatmap[color][row + i][col] -= heatmap_values[i]
            else:
                break

        # northeast directions
        for i in range(1, 3):
            if not is_offboard(row - i, col + i):
                self.heatmap[color][row - i][col + i] -= heatmap_values[i]
            else:
                break

        # northwest directions
        for i in range(1, 3):
            if not is_offboard(row - i, col - i):
                self.heatmap[color][row - i][col - i] -= heatmap_values[i]
            else:
                break

        # southeast directions
        for i in range(1, 3):
            if not is_offboard(row + i, col + i):
                self.heatmap[color][row + i][col + i] -= heatmap_values[i]
            else:
                break

        # southwest directions
        for i in range(1, 3):
            if not is_offboard(row + i, col - i):
                self.heatmap[color][row + i][col - i] -= heatmap_values[i]
            else:
                break

        if not is_offboard(row - 2, col + 1): self.heatmap[color][row - 2][col + 1] -= heatmap_values[2]
        if not is_offboard(row - 2, col - 1): self.heatmap[color][row - 2][col - 1] -= heatmap_values[2]
        if not is_offboard(row + 2, col + 1): self.heatmap[color][row + 2][col + 1] -= heatmap_values[2]
        if not is_offboard(row + 2, col - 1): self.heatmap[color][row + 2][col - 1] -= heatmap_values[2]

        if not is_offboard(row - 1, col + 2): self.heatmap[color][row - 1][col + 2] -= heatmap_values[2]
        if not is_offboard(row - 1, col - 2): self.heatmap[color][row - 1][col - 2] -= heatmap_values[2]
        if not is_offboard(row + 1, col + 2): self.heatmap[color][row + 1][col + 2] -= heatmap_values[2]
        if not is_offboard(row + 1, col - 2): self.heatmap[color][row + 1][col - 2] -= heatmap_values[2]

    def get_territory_of(self, color):
        return np.count_nonzero((self.heatmap[color] - self.heatmap[opposite_turn(color)]) > 0)

    def is_terminal_state(self):
        return self.is_game_over

    def add_piece(self, row, col):
        self.board[row][col] = self.turn

    def remove_piece(self, row, col):
        self.board[row][col] = empty

    def flip_side(self):
        self.turn = opposite_turn(self.turn)

    def make_pass_move(self, move):
        if self.his_ply > 0: self.is_game_over = self.history[self.his_ply - 1].move.is_passing_move
        self.history[self.his_ply].move = move
        self.history[self.his_ply].pos_key = self.pos_key

        self.his_ply += 1
        self.flip_side()
        self.pos_key = self.generate_pos_key()

        return True

    def undo_pass_move(self):

        self.pos_key = self.history[self.his_ply].pos_key
        self.history[self.his_ply].pos_key = np.uint64(0)

        self.flip_side()

    def make_move(self, move):
        if move.is_passing_move:
            return self.make_pass_move(move)
        self.history[self.his_ply].move = move
        self.history[self.his_ply].pos_key = self.pos_key

        self.add_piece(move.row, move.col)
        self._update_heatmaps(move.row, move.col, self.turn)
        our_liberty = self.just_count_liberty_of_this_square(move.row, move.col, self.turn)
        we_removed = self.remove_no_liberties(opposite_turn(self.turn))

        self.his_ply += 1
        self.flip_side()
        self.pos_key = self.generate_pos_key()

        if (len(our_liberty) == 0 and not we_removed) or \
                does_repeat(self.history, self.pos_key):
            self.undo_move()
            return False
        return True

    def undo_move(self):
        self.is_game_over = False
        self.his_ply -= 1

        move = self.history[self.his_ply].move
        if move.is_passing_move:
            self.undo_pass_move()
            return
        self.pos_key = self.history[self.his_ply].pos_key
        self.history[self.his_ply].pos_key = np.uint64(0)
        removed_blocks = self.history[self.his_ply].removed_blocks

        self.captured[self.turn] -= len(removed_blocks)

        for row, col in removed_blocks:
            self.add_piece(row, col)
            self._update_heatmaps(row, col, self.turn)
        self.remove_piece(move.row, move.col)
        self._remove_heatmaps(move.row, move.col, opposite_turn(self.turn))
        self.flip_side()
        # if remove:self.repetition_tables.pop()

    def generate_pseudo_legal_moves(self):
        moves = []
        for row in range(board_size):
            for col in range(board_size):
                if self.board[row][col] == empty:
                    move = Move(row, col)
                    moves.append(move)
        moves.append(Move(0, 0, is_passing_move=True))
        return moves

    def generate_all_legal_moves(self):
        moves = self.generate_pseudo_legal_moves()
        new_moves = []

        for move in moves:
            if not self.make_move(move):
                continue
            self.undo_move()
            new_moves.append(move)

        return new_moves

    def generate_pos_key(self):
        pos_key = np.uint64(0)
        for row in range(board_size):
            for col in range(board_size):
                element = self.board[row][col]
                index = index_from_row_col(row, col)
                if element != empty:
                    pos_key ^= self.piece_keys[element][index]

        if self.turn == black:
            pos_key ^= self.side_key

        return pos_key

    def remove_no_liberties(self, color):
        self.marked = np.zeros((board_size, board_size), dtype=int)
        to_be_removed = []
        we_removed_some_blocks = False

        for row in range(board_size):
            for col in range(board_size):
                if self.board[row][col] == color:
                    self.call_count(row, col, color)
                    if len(self.liberties) == 0:
                        to_be_removed.extend(self.block)

        for row, col in to_be_removed:
            self.remove_piece(row, col)
            self._remove_heatmaps(row, col, opposite_turn(self.turn))
            we_removed_some_blocks = True

        self.captured[color] += len(to_be_removed)
        self.history[self.his_ply].removed_blocks = to_be_removed
        return we_removed_some_blocks

    def call_count(self, row, col, color, empty_marked=False):
        if empty_marked: self.marked = np.zeros((board_size, board_size), dtype=int)
        self.liberties = []
        self.block = []
        self.count_liberties(row, col, color)

    def just_count_liberty_of_this_square(self, row, col, color):
        self.marked = np.zeros((board_size, board_size), dtype=int)
        self.liberties = []
        self.block = []
        self.count_liberties(row, col, color)
        return self.liberties

    def count_liberties(self, row, col, color):
        if is_offboard(row, col): return

        piece = self.board[row][col]

        if piece != empty and piece == color and self.marked[row][col] == 0:
            self.block.append((row, col))
            self.marked[row][col] = 1

            # north
            self.count_liberties(row - 1, col, color)
            # south
            self.count_liberties(row + 1, col, color)
            # east
            self.count_liberties(row, col + 1, color)
            # west
            self.count_liberties(row, col - 1, color)

        elif piece == empty:
            if (row, col) not in self.liberties: self.liberties.append((row, col))

    def print_board(self):
        print()
        for row in range(board_size):
            for col in range(board_size):
                element = self.board[row][col]

                if element == black:
                    print(" B ", end="")
                elif element == white:
                    print(" W ", end="")
                else:
                    print(" . ", end="")
            print()


if __name__ == "__main__":
    board = Board()
    board.board[0][0] = black
    board.board[1][0] = white
    board.board[4][18] = white
    board.print_board()
