import pygame
from GoEngine import Board, Move, opposite_turn
from GoConstants import board_size, white, black, empty, col_to_char, komi
from GoMoveSelector import select_best_move, count_score

if board_size == 9:
    sq_size = 60
elif board_size == 13:
    sq_size = 40
else:
    sq_size = 30

height = ((board_size + 1) * sq_size)
width = ((board_size + 1) * sq_size)

pygame.init()
screen = pygame.display.set_mode((width, height))
move_sfx = pygame.mixer.Sound("Sounds/moves_sound.mp3")
font_row = pygame.font.Font("freesansbold.ttf", 17)
font_col = pygame.font.Font("freesansbold.ttf", 19)

"""

p      => print board in console
e      => prints stats
RIGHT  => pass move
LEFT   => undo move

"""


def calculate_pos(row, col):
    x = sq_size * col + sq_size
    y = sq_size * row + sq_size
    return x, y


class Game:
    line_thickness = 3
    piece_radius = int(sq_size / 2)

    def __init__(self, display):
        self.pos = Board()
        self.display = display
        self.move_log = []
        self.two_players = True

    def draw_rows(self, text, x, y):
        text_object = font_row.render(text, True, pygame.Color("black"))
        text_location = pygame.Rect(x, y, self.piece_radius, self.piece_radius)
        self.display.blit(text_object, text_location)

    def draw_cols(self, text, x, y):
        text_object = font_col.render(text, True, pygame.Color("black"))
        text_location = pygame.Rect(x, y, self.piece_radius, self.piece_radius)
        self.display.blit(text_object, text_location)

    def draw_squares(self):
        for row in range(board_size):
            for col in range(board_size):
                x, y = calculate_pos(row, col)

                pygame.draw.rect(self.display, (128, 128, 128), (x - sq_size // 2, y - sq_size // 2, sq_size, sq_size))

    def draw_grids(self):
        for row in range(board_size):
            for col in range(board_size):
                x, y = calculate_pos(row, col)

                if col < board_size - 1:
                    pygame.draw.line(
                        self.display, (0, 0, 0),
                        (x, y), (x + sq_size, y), self.line_thickness
                    )
                if row < board_size - 1:
                    pygame.draw.line(
                        self.display, (0, 0, 0),
                        (x, y), (x, y + sq_size), self.line_thickness
                    )

                if board_size == 19:
                    if row == 3 or row == board_size // 2 or row == board_size - 4:
                        if col == 3 or col == board_size // 2 or col == board_size - 4:
                            pygame.draw.circle(screen, pygame.Color("black"), (x, y), self.piece_radius - 9)
                elif board_size == 13:
                    if row == 3 or row == board_size // 2 or row == board_size - 4:
                        if col == 3 or col == board_size // 2 or col == board_size - 4:
                            pygame.draw.circle(screen, pygame.Color("black"), (x, y), self.piece_radius - 14)
                elif board_size == 9:
                    if row == 2 or row == board_size // 2 or row == board_size - 3:
                        if col == 2 or col == board_size // 2 or col == board_size - 3:
                            pygame.draw.circle(screen, pygame.Color("black"), (x, y), self.piece_radius - 23)

                self.draw_rows(f"{((board_size - 1) - row) + 1}", 0, y - sq_size // 5)
                self.draw_cols(f"{col_to_char[col].upper()}", x, 0)

    def draw_pieces(self):
        for row in range(board_size):
            for col in range(board_size):
                element = self.pos.board[row][col]
                x, y = calculate_pos(row, col)
                if element == white:
                    pygame.draw.circle(self.display, pygame.Color("white"), (x, y), self.piece_radius)
                elif element == black:
                    pygame.draw.circle(self.display, pygame.Color("black"), (x, y), self.piece_radius)

        if self.pos.his_ply > 0:
            row, col = self.pos.history[self.pos.his_ply - 1].move.row, self.pos.history[self.pos.his_ply - 1].move.col
            x, y = calculate_pos(row, col)
            pygame.draw.circle(self.display, pygame.Color("red"), (x, y), self.piece_radius // 2)

    def draw_board(self, x=None, y=None):
        self.draw_squares()
        self.draw_grids()
        self.draw_pieces()
        if x is not None and y is not None:
            if self.pos.turn == black:
                pygame.draw.circle(screen, pygame.Color("black"), (x, y), self.piece_radius - 7)
            elif self.pos.turn == white:
                pygame.draw.circle(screen, pygame.Color("white"), (x, y), self.piece_radius - 7)
        pygame.display.update()

    def select_square(self, move):
        try:
            if self.pos.board[move.row][move.col] != empty:
                print("square already taken")
                return False
        except IndexError:
            print("out of bounds")
            return False
        if self.pos.make_move(move):
            print(f"valid move={str(move)}")
            return True
        else:
            print("no liberty or position is repeated")
            return False


def main():
    game = Game(screen)
    game.two_players = False

    human = white

    game.draw_board()
    while True:
        screen.fill((153, 73, 0))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit(0)

            elif event.type == pygame.MOUSEMOTION:
                x, y = pygame.mouse.get_pos()

                row = ((y - sq_size // 2) // sq_size)
                col = ((x - sq_size // 2) // sq_size)
                x1 = y1 = None
                if (0 <= row < board_size) and (0 <= col < board_size):
                    if game.pos.board[row][col] == empty:
                        x1, y1 = calculate_pos(row, col)
                game.draw_board(x=x1, y=y1)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()

                row = ((y - sq_size // 2) // sq_size)
                col = ((x - sq_size // 2) // sq_size)
                move = Move(row, col)
                if (game.two_players or game.pos.turn == human) and game.select_square(move):
                    game.move_log.append(move)
                    pygame.mixer.Sound.play(move_sfx)
                    game.draw_board()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    if game.two_players and len(game.move_log) > 0:
                        game.pos.undo_move()
                        print(f"removed:{str(game.move_log.pop())}")
                        game.draw_board()
                    elif not game.two_players and len(game.move_log) > 1:
                        for _ in range(2):
                            game.pos.undo_move()
                            print(f"removed:{str(game.move_log.pop())}")
                        game.draw_board()
                elif event.key == pygame.K_RIGHT:
                    move = Move(0, 0, is_passing_move=True)
                    if game.two_players or game.pos.turn == human:
                        game.pos.make_move(move)
                        pygame.mixer.Sound.play(move_sfx)
                        print("valid move=" + str(move))
                        game.move_log.append(move)
                        game.draw_board()

                elif event.key == pygame.K_e:
                    print("\nwhite stats:")
                    print(f"\twhite territory={game.pos.get_territory_of(white)}")
                    print(f"\tyour number of captures={game.pos.captured[black]}")
                    print(f"\tplus komi={komi}")
                    print("\nblack stats:")
                    print(f"\tblack territory={game.pos.get_territory_of(black)}")
                    print(f"\tyour number of captures={game.pos.captured[white]}")
                    print(f"\tplus komi=0")

                elif event.key == pygame.K_p:
                    game.pos.print_board()

        if not game.two_players and game.pos.turn == opposite_turn(human):
            # bitch ai
            move = select_best_move(game.pos)

            print("bestmove=" + str(move))
            game.pos.make_move(move)
            game.move_log.append(move)
            pygame.mixer.Sound.play(move_sfx)
            game.draw_board()

        if game.pos.is_terminal_state():
            white_ter = count_score(game.pos, white)
            black_ter = count_score(game.pos, black)
            print(f"\n\nwhite score={white_ter}")
            print(f"black score={black_ter}")
            if white_ter > black_ter:
                print("WINNER IS WHITE")
            else:
                print("WINNER IS BLACK")
            pygame.time.wait(3000)
            exit(0)


if __name__ == "__main__":
    main()
