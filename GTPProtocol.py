import sys
from GoConstants import board_size,black,white
from GoEngine import Board,Move
from GoMoveSelector import select_best_move

def set_board_size(command,board):
    size = int(command.split()[-1])

    if size != board_size:
        print("? not supported bitch\n")
        return
    board.__init__()
def play(command,board):
    color = black if command.split()[1] == 'B' else white

    move = Move(0,0)

    if command.split()[-1] == 'pass':
        move.is_passing_move = True
        board.make_move(move)
        return

    square_str = command.split()[-1]
    row_str = square_str[1:]
    col = ord(square_str[0]) - ord('A') + 1 - (1 if ord(square_str[0]) > ord('I') else 0)
    row = int(row_str if len(row_str) > 1 else ord(row_str) - ord('0'))

    row = (board_size - 1) - row

    move.row = row
    move.col = col

    board.turn = color
    if not board.make_move(move):
        print("? illegal move\n")

def main():
    board = Board()
    while True:
        command = input()

        if 'name' in command:
            print("= GoEngine beta\n")
        elif 'protocol_version' in command:
            print("= 1\n")
        elif 'version' in command:
            print("= 1.0.0\n")
        elif 'list_commands' in command:
            print("= protocol_version\n")
        elif 'boardsize' in command:
            set_board_size(command,board);print("=\n")
        elif 'clear_board' in command:
            board=Board();print("=\n")
        elif 'print' in command:
            board.print_board();print("=\n")
        elif 'play' in command:
            play(command,board);print("=\n")
        elif 'genmove' in command:
            board.turn = black if command.split()[-1]=='B' else white
            move = select_best_move(board)
            print(f"= {str(move)}\n")
            if not board.make_move(move):
                print("? illegal move\n")
                continue
        elif 'quit' in command:sys.exit()
        else:print("=\n")


if __name__=="__main__":
    main()