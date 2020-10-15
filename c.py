# I've added a tick 60fps and it has decreasesd cpu USAGE significantly
# If going to rollback, remmeber to convert background
"""
TBD:
1. Fix how bad the buttons look
2. Make it so that when I click on a move, I automatically jump onto it
3. Add a scrolling for that, and maybe throw wordwrap away
4. Start doing puzzles


x. make a hash function for the FEN
xx. make text monospaced
xxx. modify wordwrap so as to use smaller fonts
xxxx. change mouse cursor when hovering over a button


"""

import sys
import pygame, pygame.freetype
import logic
import pygame_toolbox, puzzle_file

WHITE_SQR = (181, 136, 99)
BLACK_SQR = (240, 217, 181)
BLACK = (0, 0, 0)
WHITE = (230, 230, 230)
BLUE = (0, 0, 255)
RED = (160, 0, 0)
YELLOW = (180, 180, 0)
LIGHT_BLUE = (0, 0, 160)
LIGHT_GREEN = (0, 160, 0)
HIGHLIGHT = (120, 120, 0, 120)
PURPLE = (160, 0, 160)

FOLDER = 'data/'
SCREEN_COLOR = BLACK
puzzle_filenames = (FOLDER+'white.txt', FOLDER+'black.txt')

PROMOTE_ORDER = ('queen', 'knight', 'rook', 'bishop')
class State:
    def __init__(self, screen, background, highlightSurf,
                PGN_surf, clock, pieces, buttons, moving_piece, end_label, game):
        self.screen = screen
        self.background = background
        self.highlightSurf = highlightSurf
        self.PGN_surf = PGN_surf
        self.clock = clock
        self.pieces = pieces
        self.buttons = buttons
        self.moving_piece = moving_piece
        self.end_label = end_label
        self.game = game

        self.promote_button = None
        self.mode_button = None
        self.highlight_button = None
        self.color_button = None

        self.white_dict = {}
        self.black_dict = {}

    def group_pieces(self, clear_first=1):
        if clear_first:
            self.pieces.empty()
        for square in self.game.board.squares:
            piece = self.game.board.squares[square]
            if piece is not None and not piece.groups():
                self.pieces.add(piece)

    def load_puzzle(self):
        self.puzzle_dict = puzzle_file.read(self.puzzle_file)

    def save_puzzle(self):
        puzzle_file.write(self.puzzle_file, self.puzzle_dict)

class Box(pygame.sprite.Sprite):
    length = 60
    def __init__(self, square): # (x, y) from (0, 0) to (7, 7)
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.square = square
        self.color = get_color_for_square(square)
        self.rect = get_rect_from_square(square)

        self.image = pygame.surface.Surface(self.rect[-2:]).convert()
        self.image.fill(self.color)
class Piece(pygame.sprite.Sprite):
    images = {
        'pawn':(pygame.image.load(FOLDER + 'bP.png'), 
               pygame.image.load(FOLDER + 'wP.png')),
        'knight':(pygame.image.load(FOLDER + 'bN.png'), 
               pygame.image.load(FOLDER + 'wN.png')),
        'bishop':(pygame.image.load(FOLDER + 'bB.png'), 
               pygame.image.load(FOLDER + 'wB.png')),
        'rook':(pygame.image.load(FOLDER + 'bR.png'), 
               pygame.image.load(FOLDER + 'wR.png')),
        'queen':(pygame.image.load(FOLDER + 'bQ.png'), 
               pygame.image.load(FOLDER + 'wQ.png')),
        'king':(pygame.image.load(FOLDER + 'bK.png'), 
               pygame.image.load(FOLDER + 'wK.png')),
    }
    def __init__(self, color):
        # name is in smaller-case
        if hasattr(self, 'containers'):
            pygame.sprite.Sprite.__init__(self, self.containers)
        else:
            pygame.sprite.Sprite.__init__(self)    
        self.parent.__init__(self, color)

        self.image = self.images[self.name][0 if color == 'b' else 1]
        self.rect = self.image.get_rect()


    def update(self):
        if self.square is None:
            self.kill()
            return

        self.rect.center = get_rect_from_square(self.square).center

    @classmethod
    def prepare_sprites(cls):
        for x in cls.images:
            w = cls.images[x][0].convert_alpha()
            b = cls.images[x][1].convert_alpha()

            Piece.images[x] = (w, b)    
class Button(pygame.sprite.Sprite):
    def __init__(self, text, text_color, back_color, topleft, fn, font=None):
        if font is None:
            font = FONT # Use the global variable set by main instead

        pygame.sprite.Sprite.__init__(self, self.containers)

        self.image = font.render(text, text_color, back_color)[0].convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.topleft = topleft
        self.fn = fn
        self.text = text
        self.text_color = text_color
        self.back_color = back_color
        self.font = font

        self.hidden = False

    def change_text(self, text):
        self.text = text
        self.image = self.font.render(text, self.text_color, 
                     self.back_color)[0].convert_alpha()

    def hide(self, state):
        state.buttons.remove(self)
        self.hidden = True

    def show(self, state):
        state.buttons.add(self)
        self.hidden = False

    def switch(self, state):
        if self.hidden:
            self.show(state)
        else:
            self.hide(state)
class Label(Button):

    def __init__(self, text, text_color, back_color, topleft, font=None):
        Button.__init__(self, text, text_color, back_color, topleft, 
                        Button_functions.do_nothing, font) 

class Pawn(Piece, logic.Pawn): 
    parent = logic.Pawn

    def promote(self, new_piece):
        # At this point, Pawn is only a member in moving piece group
        state = self.groups()[0].state
        pieces = state.pieces
        pieces.add(new_piece)
class Bishop(Piece, logic.Bishop):
    parent = logic.Bishop
class Knight(Piece, logic.Knight):
    parent = logic.Knight
class Rook(Piece, logic.Rook):
    parent = logic.Rook
class King(Piece, logic.King): 
    parent = logic.King
class Queen(Piece, logic.Queen): 
    parent = logic.Queen
LETTER_TO_PIECE = {'p':Pawn, 'n':Knight, 'b':Bishop, 'r':Rook, 'q':Queen, 'k':King}
class Button_functions:

    @staticmethod
    def undo(state):
        if state.game.prev_state is None:
            return
        state.game.change_ip_state(state.game.prev_state)
    @staticmethod    
    def reset(state, FEN='rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'):
        state.game.change_ip_state(logic.state_from_FEN(FEN, wrapper_dict=LETTER_TO_PIECE))    
    @staticmethod
    def promote_cycle(state):
        i = PROMOTE_ORDER.index(state.promote_button.text) + 1
        if i == len(PROMOTE_ORDER): i = 0
        piece = PROMOTE_ORDER[i]

        state.promote_button.change_text(piece)

    @staticmethod
    def import_PGN(state):
        if 'text/plain;charset=utf-8' in pygame.scrap.get_types():
            type_ = 'text/plain;charset=utf-8'
        elif pygame.SCRAP_TEXT in pygame.scrap.get_types():
            type_ = pygame.SCRAP_TEXT    
        else:
            print(pygame.scrap.get_types())
            return
        try:
            PGN = pygame.scrap.get(type_).decode('ascii', 'ignore').replace('\x00', '')
            state.game.change_ip_state(logic.state_from_PGN(PGN, wrapper_dict=LETTER_TO_PIECE))
        except Exception:
            pass
    @staticmethod
    def import_FEN(state):
        if 'text/plain;charset=utf-8' in pygame.scrap.get_types():
            type_ = 'text/plain;charset=utf-8'
        elif pygame.SCRAP_TEXT in pygame.scrap.get_types():
            type_ = pygame.SCRAP_TEXT          
        else:
            return
        try:
            FEN = pygame.scrap.get(type_).decode('ascii', 'ignore').replace('\x00', '')
            state.game.change_ip_state(logic.state_from_FEN(FEN, wrapper_dict=LETTER_TO_PIECE))
        except Exception:
            pass
    @staticmethod
    def export_PGN(state):
        pygame.scrap.put(pygame.SCRAP_TEXT, bytes(state.game.PGN, encoding='utf-8'))
    @staticmethod
    def export_FEN(state):
        pygame.scrap.put(pygame.SCRAP_TEXT,  bytes(state.game.get_FEN(), encoding='utf-8'))      

    modes = ('Play', 'Add', 'Remove')
    @staticmethod
    def trigger_restricted(state):
        state.mode_button.switch(state)
        state.highlight_button.switch(state)
    @staticmethod
    def change_mode(state):
        i = state.mode_button.mode + 1
        if i == len(Button_functions.modes):
            i = 0
        state.mode_button.change_text(Button_functions.modes[i])
        state.mode_button.mode = i
    @staticmethod
    def highlight_squares(state):
        button = state.highlight_button
        if not button.hidden:
            new_color = RED if button.text_color == LIGHT_GREEN else LIGHT_GREEN
            button.text_color = new_color  
            button.change_text(button.text)
    @staticmethod
    def change_color(state):
        button = state.color_button
        button.text = 'black' if button.text == 'white' else 'white'
        button.change_text(button.text)


    @staticmethod
    def do_nothing(*arg):
        pass

def get_square_from_position(pos):
    """also aligns to nearest square"""
    return (pos[0] // Box.length), (pos[1] // Box.length)
def get_rect_from_square(square):
    x = Box.length * square[0]
    y = Box.length * square[1]
    
    return pygame.Rect(x, y, Box.length, Box.length)
def get_color_for_square(square):
    return WHITE_SQR if  (square[0] + square[1]) % 2 else BLACK_SQR

def prepare_background():
    surface = pygame.surface.Surface((Box.length*8+20, Box.length*8)).convert()
    for i in range(8):
        for j in range(8): 
            pygame.draw.rect(surface, get_color_for_square((i, j)), get_rect_from_square((i, j)))
    pygame.draw.rect(surface, BLACK, (Box.length*8, 0, Box.length*8, 20))       
    return surface      
def setup_buttons(state, font=None):
    topleft = (Box.length * 8 + 20, 0)
    b = Button('undo', BLACK, BLUE, topleft, Button_functions.undo)

    topleft = (topleft[0], b.rect.bottom + 10)
    c = Button('reset', BLACK, BLUE, topleft, Button_functions.reset)

    topleft = (topleft[0], c.rect.bottom + 20)
    d = Button('queen', BLACK, BLUE, topleft, Button_functions.promote_cycle)
    state.promote_button = d

    topleft = (topleft[0], d.rect.bottom + 10)
    e = Label('checkmate', YELLOW, None, topleft)
    state.end_label = e
    e.hide(state)
    # Import and Export PGN
    topleft = (topleft[0], e.rect.bottom + 10)
    f = Button('Import PGN', LIGHT_BLUE, YELLOW, topleft, Button_functions.import_PGN)

    topleft = (topleft[0], f.rect.bottom + 10)
    g = Button('Import FEN', LIGHT_BLUE, YELLOW, topleft, Button_functions.import_FEN)

    topleft = (topleft[0], g.rect.bottom + 20)
    h = Button('Export PGN', RED, YELLOW, topleft, Button_functions.export_PGN)

    topleft = (topleft[0], h.rect.bottom + 10)
    i = Button('Export FEN', RED, YELLOW, topleft, Button_functions.export_FEN)

    topleft = (topleft[0], i.rect.bottom + 10)
    j = Button('Standard', WHITE_SQR, None, topleft, Button_functions.trigger_restricted)

    topleft = (topleft[0], j.rect.bottom + 10)
    k = Button('Play', WHITE_SQR, None, topleft, Button_functions.change_mode)
    k.mode = 0
    state.mode_button = k
    k.hide(state)

    topleft = (topleft[0], k.rect.bottom + 10)
    l = Button('Highlight', LIGHT_GREEN, None, topleft, Button_functions.highlight_squares)   
    state.highlight_button = l
    l.hide(state)

    topleft = (topleft[0], l.rect.bottom + 10)
    m = Button('white', PURPLE, None, topleft, Button_functions.change_color)
    state.color_button = m



def initialize(game=logic.state_from_FEN(wrapper_dict=LETTER_TO_PIECE)):
    global FONT
    global SMALLFONT
    pygame.init()
    FONT = pygame.freetype.Font(FOLDER+'sans.ttf', 32)
    SMALLFONT = pygame.freetype.Font(FOLDER+'sans.ttf', 12)
    screen = pygame.display.set_mode((Box.length*8+200, Box.length*8+150))
    pygame.display.set_caption('Chess')
    clock = pygame.time.Clock()
    pygame.scrap.init()

    Piece.prepare_sprites()
    PGN_surf = pygame.Surface((screen.get_rect().width, 200)).convert()
    PGN_rect = PGN_surf.get_rect().topleft = (0, Box.length*8)
    background = prepare_background()
    highlightSurf = pygame.Surface(background.get_rect().size).convert_alpha()
    pieces = pygame.sprite.Group()
    buttons = pygame.sprite.Group()
    moving_piece = pygame.sprite.GroupSingle()
    end_label = pygame.sprite.GroupSingle()
    Piece.containers = pieces
    Button.containers = buttons
    
    s = State(screen, background, highlightSurf, PGN_surf, 
              clock, pieces, buttons, moving_piece, None, game)
    moving_piece.state = s # will help with promote later
    setup_buttons(s)
    s.group_pieces()
    s.white_dict = puzzle_file.read(puzzle_filenames[0])
    s.black_dict = puzzle_file.read(puzzle_filenames[1])

    return s

def highlight(state):
    highlightSurf = state.highlightSurf
    turn = state.game.turn
    dict_ = state.white_dict if turn == 'w' else state.black_dict
    FEN = puzzle_file.simplify_FEN(state.game.get_FEN()) 

    highlightSurf.fill((0, 0, 0, 0))
    if FEN not in dict_:
        return None
    rects = (get_rect_from_square(logic.final_square_from_PGN(cord)) for cord in dict_[FEN])
    for rect in rects:
        pygame.draw.rect(highlightSurf, HIGHLIGHT, rect)
    return 1




def handle_mode(state, move, turn):
    mode_button = state.mode_button

    dict_ = state.white_dict if turn == 'w' else state.black_dict
    if mode_button.hidden or state.color_button.text[0] != turn:
        return 1
    FEN = puzzle_file.simplify_FEN(state.game.prev_state.get_FEN())
    if not mode_button.mode: # Play
        if FEN not in dict_:
            print(FEN)
            return 1
        return move in dict_[FEN]
    elif mode_button.mode == 1: # Add
        if FEN not in dict_:
            dict_[FEN] = set()
        dict_[FEN].add(move)
        return 1
    elif mode_button.mode == 2: # Remove
        if FEN in dict_ and move in dict_[FEN]:
            dict_[FEN].remove(move)    
        return 0

def handle_game_end(state):
    if state.game.end == '-' and state.end_label.text != 'stalemate':
        state.end_label.change_text('stalemate')
    elif state.game.end in ('w', 'b') and state.end_label.text != 'checkmate':
        state.end_label.change_text('stalemate')
    state.end_label.show(state)
def mouse_down(event, state):
    if event.pos[0] > 8*Box.length or event.pos[1] > 8*Box.length:
        for button in state.buttons.sprites():
            if button.rect.collidepoint(event.pos):
                button.fn(state) 
                state.group_pieces()
                state.end_label.hide(state)
    elif not state.game.end:            
        square = get_square_from_position(event.pos)   
        piece = state.game.board.squares[square]
        if piece is not None and piece.color == state.game.turn:
            state.pieces.remove(piece)
            state.moving_piece.add(piece)
def mouse_up(event, state):
    new_square = get_square_from_position(event.pos)
    piece = state.moving_piece.sprites()[0]
    turn = state.game.turn
    original_square = piece.square
    move = logic.make_move(state.game, original_square, new_square, 
                            state.promote_button.text, return_PGN=True)
    if move:
        state.game.end = logic.check_game_end(state.game,
                   state.moving_piece.sprites()[0].opposite_color)
        if state.game.end:
            handle_game_end(state)
        if turn == 'w': # white has just moved
            move = move[move.index('.')+1:] # Get rid of 1., 10. etc..
        move = move.strip()
        res = handle_mode(state, move, turn)
        if not res:
            state.game = state.game.prev_state
            piece.rect.center = get_rect_from_square(piece.square).center
    else: # back to starting position
        piece.rect.center = get_rect_from_square(piece.square).center
    state.moving_piece.remove(piece)
    state.pieces.add(piece)
def update_screen(state):
    state.screen.blit(state.background, state.background.get_rect())
    if not state.highlight_button.hidden and state.highlight_button.text_color == LIGHT_GREEN:
        if highlight(state):
            state.screen.blit(state.highlightSurf, state.highlightSurf.get_rect())
    state.pieces.update()
    state.pieces.draw(state.screen)
    state.buttons.draw(state.screen)
    if state.moving_piece:
        pos = pygame.mouse.get_pos()
        piece = state.moving_piece.sprites()[0]
        if pos[0] > 8*Box.length or pos[1] > 8*Box.length:
            state.moving_piece.draw(state.screen)
            state.moving_piece.remove(piece)
            state.pieces.add(piece)
        else:
            piece.rect.center = pos
            state.screen.blit(piece.image, piece.rect) 
    PGN_rect = state.PGN_surf.get_rect()
    PGN_rect.topleft = (state.background.get_rect().bottomleft)

    state.PGN_surf.fill(WHITE)
    pygame_toolbox.word_wrap(state.PGN_surf, state.game.PGN, SMALLFONT, BLACK)
    state.screen.blit(state.PGN_surf, PGN_rect)

def show_PGN(PGN, fps=5):
    """
    TBD, no one's interested in an automatic game,
    maybe add something to progress the game to next move.
    """
    game_gen = logic.PGN_state_gen(PGN, wrapper_dict=LETTER_TO_PIECE)
    game = game_gen.__next__()
    state = initialize(game)


    for game in game_gen:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        state.group_pieces()
        update_screen(state)
        pygame.display.update()
        state.clock.tick(fps)
    return game    
def normal_game(state):
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                puzzle_file.write(puzzle_filenames[0], state.white_dict)
                puzzle_file.write(puzzle_filenames[1], state.black_dict)
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and \
                           event.button == 1 and not state.moving_piece:
                mouse_down(event, state)
            elif event.type == pygame.MOUSEBUTTONUP and state.moving_piece:
                mouse_up(event, state)
                state.group_pieces()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_m and \
                 not state.mode_button.hidden:
                 Button_functions.change_mode(state)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_n and \
                 not state.mode_button.hidden:
                 Button_functions.change_color(state)

        state.screen.fill(SCREEN_COLOR)
        update_screen(state)
        pygame.display.update()
        state.clock.tick(60)


if __name__ == '__main__':
    PGN =  """
    1.e4 e6 2.e5 d5 3.d4 c5 4.c3 cxd4 5.cxd4 Bb4 6.Nc3 Qb6 7.f4 f6 8.Nf3 fxe5 9.fxe5 Ne7 10.g3 O-O 11.Bd2 Nec6 12.Be3 Nd7 13.Bf4 
    """
    #g = show_PGN(PGN)
    g = logic.state_from_PGN(PGN, wrapper_dict=LETTER_TO_PIECE)
    s = initialize()
    normal_game(s)