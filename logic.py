"""
TBD:

"""
import math, copy, time


class GameState():
    """Encapsulate the current board state of the game, as well as the prev"""
    def __init__(self, end, turn, halfmove, fullmove, prev_state, board, 
                 wrapper_dict, PGN=''):
        self.end = end
        self.turn = turn
        self.halfmove = halfmove
        self.fullmove = fullmove
        self.prev_state = prev_state
        self.board = board
        self.PGN = PGN

        self.wrapper_dict = wrapper_dict
    def copy(self):
        return GameState(self.end, self.turn, self.halfmove, self.fullmove,
                         self.prev_state, self.board.copy(), self.wrapper_dict,
                         self.PGN)

    def change_ip_state(self, state):
        (self.end, self.turn, self.halfmove, self.fullmove,
        self.prev_state, self.board, self.wrapper_dict, self.PGN) = (
        state.end, state.turn, state.halfmove, state.fullmove,
        state.prev_state, state.board.copy(), state.wrapper_dict, state.PGN)

    def get_FEN(self):
        FEN = []
        for j in range(8):
            Nones = 0
            for i in range(8):
                piece = self.board.squares[(i, j)]
                if piece is None:
                    Nones += 1
                    if Nones == 8:
                        FEN.append(str(Nones))
                    continue
                if Nones:
                    FEN.append(str(Nones))
                    Nones = 0
                l = NAME_TO_LETTER[piece.name]
                FEN.append(l.capitalize() if piece.color == 'w' else l)
            if Nones:
                FEN.append(str(Nones))
                Nones = 0
            FEN.append('/')   
        FEN = ''.join(FEN)    
        translation_table = ''.maketrans('wWbB', 'KQkq')
        castling = self.board.castling.translate(translation_table)  

        if self.board.passanted_pawn and self.board.passanted_pawn.square:  
            passanted_square = (self.board.passanted_pawn.square[0],
                                self.board.passanted_pawn.square[1]
                            - self.board.passanted_pawn.direction)
            passanted_square = get_coordinate_from_square(passanted_square)
        else:
            passanted_square = '-'

        return ' '.join((FEN, self.turn, castling, passanted_square, 
                        str(self.halfmove), str(self.fullmove)))     
            
class chessBoard():
    def __init__(self, occupied_squares={}, castling='bwBW', passanted_pawn = None, replace=False):
        # (0, 0), (1, 0), (2, 0), (3, 0), ...
        # (0, 1), ...

        # Using dict because faster look-up, and it also makes more sense

        # Also, to speed up, replace: just gives you a squares dict to work with
        if replace:
            self.squares = occupied_squares
        else:    
            self.squares = {(i, j):None for i in range(8) for j in range(8)}
            for index in occupied_squares:
                self.squares[index] = occupied_squares[index]

        # castling is a '-' if no one can castle
        # or could be bwBW where upper case is queen-side
        self.castling = castling
        self.passanted_pawn = passanted_pawn

    def copy(self):
        new_squares = {}
        for square in self.squares:
            piece = self.squares[square]
            if piece is None:
                new_squares[square] = piece
                continue
            new_piece = piece.__class__(piece.color)
            new_piece.square = square
            new_squares[square] = new_piece    
        return chessBoard(new_squares, self.castling, self.passanted_pawn, True)

class Pawn():
    def __init__(self, color):
        self.color = color
        self.opposite_color = 'b' if color == 'w' else 'w'
        self.name = 'pawn'

        self.direction = -1 if color == 'w' else 1
        self.queening = 0 if color == 'w' else 7
        self.start = 6 if color == 'w' else 1
        # relevant y values for relevant places


        self.square = (0, 0)

    def legal_move(self, board, new_square):
        """In addition to 0 and 1, return 2 if double-move (for passant)
            , 3 if passanting and 4 if queening"""
        difference_y = new_square[1] - self.square[1]
        difference_x = new_square[0] - self.square[0]

        if ((difference_y == self.direction)
                and new_square[0] - self.square[0] in (-1, 1)):
            # moving diagonally
            if (board.squares[new_square] is not None and
                    board.squares[new_square].color == self.opposite_color):
                return 1 + 3*((new_square[1] == self.queening))
            # en passant
            pp = board.squares[new_square[0], new_square[1] - self.direction]
            if (pp is not None and pp.color == self.opposite_color
                    and board.passanted_pawn 
                    and board.passanted_pawn.square == (
                        new_square[0], new_square[1] - self.direction)):
                return 3

        elif difference_y == self.direction and board.squares[new_square] is None and not difference_x:
            return 1 + 3*(new_square[1] == self.queening) 
        elif (difference_y == self.direction * 2 and not difference_x
              and self.square[1] == self.start
              and board.squares[new_square[0], new_square[1] - self.direction] is None
              and board.squares[new_square] is None):
            # double_move from start, nothing in the way
            return 2

        return 0   

    def promote(self, new_piece):
        pass # Intended to be subclassed
class Knight():
    def __init__(self, color):
        self.color = color
        self.opposite_color = 'b' if color == 'w' else 'w'
        self.name = 'knight'

        self.square = (0, 0)

    def legal_move(self, board, new_square):
        # won't check for negative values for movements
        # we'll assume whoever calls it checks it
        abs_x = math.fabs(new_square[0] - self.square[0])
        abs_y = math.fabs(new_square[1] - self.square[1])
        return  (abs_x + abs_y == 3 and abs_x in (1, 2)
                     and (board.squares[new_square] is None or
                     board.squares[new_square].color == self.opposite_color))
class Bishop():
    def __init__(self, color):
        self.color = color
        self.opposite_color = 'b' if color == 'w' else 'w'
        self.name = 'bishop'

        self.square = (0, 0)

    def legal_move(self, board, new_square):
        if new_square[0] - self.square[0] == new_square[1] - self.square[1]:
            difference_x = new_square[0] - self.square[0]
            difference_y = difference_x
        elif new_square[0] - self.square[0] == self.square[1] - new_square[1]:
            difference_x = new_square[0] - self.square[0]
            difference_y = -difference_x
        else:
            return 0

        cur_x = self.square[0]
        cur_y = self.square[1]
        for _ in range(1,  int(math.fabs(difference_x))):
            # 1 because we don't want it to be illegal if target_square is 
            # opposite_color
            cur_x += sign(difference_x)
            cur_y += sign(difference_y)
            if board.squares[cur_x, cur_y] is not None:
                return 0            

        if board.squares[new_square] is None:
            return 1
        elif board.squares[new_square].color == self.opposite_color:
            return 1
        return 0               
class Rook():
    def __init__(self, color):
        self.color = color
        self.opposite_color = 'b' if color == 'w' else 'w'
        self.square = (0, 0)
        self.name = 'rook' # could use that later in other classes if needed

        self.original_square = (0, 0)

    def legal_move(self, board, new_square):
        if new_square[0] == self.square[0]:
            difference_x = 0
            difference_y = new_square[1] - self.square[1]

        elif self.square[1] == new_square[1]:
            difference_x = new_square[0] - self.square[0]
            difference_y = 0
        else:
            return 0
  

        cur_difference = difference_x if difference_x else difference_y
        cur_x = self.square[0]
        cur_y = self.square[1]
        for _ in range(1, int(math.fabs(cur_difference))):
            cur_x += sign(difference_x)
            cur_y += sign(difference_y)
            if board.squares[cur_x, cur_y] is not None:
                return 0            

        if board.squares[new_square] is None:
            return 1
        elif board.squares[new_square].color == self.opposite_color:
            return 1
        return 0         
class Queen():
    def __init__(self, color):
        self.color = color
        self.opposite_color = 'b' if color == 'w' else 'w'
        self.name = 'queen'
        self.square = (0, 0)

    def legal_move(self, board, new_square):
        if new_square[0] - self.square[0] == new_square[1] - self.square[1]:
            difference_x = new_square[0] - self.square[0]
            difference_y = difference_x

        elif new_square[0] - self.square[0] == self.square[1] - new_square[1]:
            # Avoids the 16 <---> 23 movement thing
            # so, moving in the same row, which can happen at the edges
            difference_x = new_square[0] - self.square[0]
            difference_y = -difference_x

        elif new_square[0] == self.square[0]:
            difference_x = 0
            difference_y = new_square[1] - self.square[1]

        elif self.square[1] == new_square[1]:
            difference_x = new_square[0] - self.square[0]
            difference_y = 0
        else:
            return 0



        cur_difference = difference_x if difference_x else difference_y
        # should work for both cases of bishop and rook
        cur_x = self.square[0]
        cur_y = self.square[1]

        for _ in range(1, int(math.fabs(cur_difference))):
            cur_x += sign(difference_x)
            cur_y += sign(difference_y)
            if board.squares[cur_x, cur_y] is not None:
                return 0            

        if board.squares[new_square] is None:
            return 1
        elif board.squares[new_square].color == self.opposite_color:
            return 1
        return 0             
class King():

    def __init__(self, color):
        self.color = color
        self.opposite_color = 'b' if color == 'w' else 'w'
        self.name = 'king'

        self.square = (0, 0)

    def legal_move(self, board, new_square):
        """Return 5 if castling"""

        if (new_square[0] - self.square[0] in (-2, 2) 
            and new_square[1] == self.square[1]):

            increment = sign(new_square[0] - self.square[0])
            # increment is positive if kingside, else negative
            rook_square = (int(self.square[0] - 0.5 + 3.5 * increment), self.square[1]) # (either +3 or -4)
            # 1. If either has moved
            if not(increment == 1 and self.color in board.castling or
                   increment == -1 and self.color.capitalize() in board.castling):
                return 0
            # 2. Castling through check
            for x in range(self.square[0], new_square[0] + increment, increment):
                y = self.square[1]

                temp_king = King(self.color)
                temp_king.square = (x, y)

                temp_board = board.copy()
                temp_board.squares[x, y] = temp_king
                temp_board.squares[self.square] = None
                if temp_king.in_check(temp_board):
                    return 0
            return 5 * increment # 5 kingside, -5 queenside        

        elif not(-1 <= new_square[0] - self.square[0] <= 1 
              and -1 <= new_square[1] - self.square[1] <= 1):
            return 0 
        elif new_square == self.square:
            return 0    
        elif board.squares[new_square] is None:
            return 1
        elif board.squares[new_square].color == self.opposite_color:
            return 1
        return 0               
     
    def in_check(self, board):
        for square in board.squares:
            piece = board.squares[square]
            if piece is None or piece.color == self.color:
                continue
            if piece.legal_move(board, self.square) and piece.color == self.opposite_color:
                return 1
        return 0        
LETTER_TO_PIECE = {'p':Pawn, 'n':Knight, 'b':Bishop, 'r':Rook, 'q':Queen, 'k':King}
LETTER_TO_NAME = {'p':'pawn', 'n':'knight', 'b':'bishop', 'r':'rook', 'q':'queen', 'k':'king'}
NAME_TO_LETTER = {'pawn':'p', 'knight':'n', 'bishop':'b', 'rook':'r', 'queen':'q', 'king':'k'}

def sign(n):
    return (n > 0) - (n < 0)
def get_square_from_coordinate(cord):
    # coordinate is like e4 etc..
    # TBD: add an isnumeric exception or something
    letter, number = cord
    return (ord(letter) - ord('a'), 8 - int(number))   
def get_coordinate_from_square(square):
    return chr(square[0] + ord('a')) + str(8 - square[1])
def final_square_from_PGN(cord):
    if '=' not in cord:
        return get_square_from_coordinate(cord[-2:])
    i = cord.index('=')
    return get_square_from_coordinate(cord[i-2:i])

def get_king(board, color):
    for square in board.squares:
        if board.squares[square] is not None and board.squares[square].name == 'king' and board.squares[square].color == color:
            return board.squares[square]
def passanted_pawn_from_square(board, square):
    """Take the passanting square as an input and return the captured pawn"""

    return  (board.squares[square[0], square[1]+1] or
            board.squares[square[0], square[1]-1])
def get_pieces(board, color, name):
    """
    I.e. give w as color and pawn as name to get all white pawns
    """

def make_PGN_move(game, move, color):
    """
    Take a move like e4, Bgxe8 and make it in the game, if its legal
    Just like make_move

    Takes no spaces

    I'm assuming that the enpassant has a capture symbol "X" TBD
    """
    move = move.replace('#', '').replace('+', '')
    # Should replace everything except for O-O, O-O-O and e8=Q and the capture
    p = move[0]
    if p in 'NBRQK':
        move = move.replace('x', '')
        pieces = []
        name = LETTER_TO_NAME[p.casefold()]
        for square in game.board.squares:
            piece = game.board.squares[square]
            if piece is not None and piece.color == color and piece.name == name:
                pieces.append(piece)     
        if len(move) == 4:
            # Basically in the form of Red6
            line = move[1]
            if line.isnumeric():
                line = 8 - int(line)
                piece = filter(lambda x: x.square[1] == line, pieces).__next__()
            else:
                line = ord(line) - ord('a')
                piece = filter(lambda x: x.square[0] == line, pieces).__next__()   
            target = get_square_from_coordinate(move[-2:]) 
            return make_move(game, piece.square, target)
        else:
            target = get_square_from_coordinate(move[-2:])
            # There are two pieces involved, try both.
            # Wait, first could be queen!

            for piece in pieces:
                res = make_move(game, piece.square, target)
                if res: return res      
    elif p == 'O':
        piece = get_king(game.board, color)
        if move.count('O') == 2:
            square = (piece.square[0] + 2, piece.square[1])
        elif move.count('O') == 3:
            square = (piece.square[0] - 2, piece.square[1])
        return make_move(game, piece.square, square)    
    # Is a pawn move!
    if '=' in move:
        promote_to = LETTER_TO_NAME[move[-1].casefold()] # makes Q --> q
        move = move[:-2] # Should exclude =Q for example
    else:
        promote_to = 'queen'    
    target = get_square_from_coordinate(move[-2:])
    line = ord(p) - ord('a')
    for square in game.board.squares:
        piece = game.board.squares[square]
        if piece is not None and piece.color == color and \
           piece.name == 'pawn' and \
           piece.square[0] == line:
            res = make_move(game, piece.square, target)
            if res: return res
    return 0
def PGN_state_gen(PGN, wrapper_dict = LETTER_TO_PIECE):
    i = PGN.find('FEN')
    FEN = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
    if i != -1:
        i_2 = PGN.find('"', i)
        i_3 = PGN.find('"', i_2)
        FEN = PGN[i_2+1:i_3]

    # We find the last bracket, if there is one, and then search for first 1.
    i = PGN.rfind(']') + 1 # Assure that -1 is handled
    i = PGN.find('1.', i)

    next_move = 2
 
    game = state_from_FEN(FEN, wrapper_dict)

    yield game

    while i != -1:
        h = i
        i = PGN.find(str(next_move)+'.', h)
        moves = PGN[h+len(str(next_move-1))+1:i].strip().split(' ')
        if len(moves) != 1:
            move1, move2 = moves[0], moves[1] # dealing with 0-1 at end
        else:
            move1, move2 = moves[0], ''
        a = make_PGN_move(game, move1, 'w')
        if not a:
            break
        yield game
        if not move2.strip(): # Final move is white's
            break

        b = make_PGN_move(game, move2, 'b')
        if not b: # Illegal move
            break

        yield game
        next_move += 1
def update_PGN(game, original_square, new_square, legality, piece, captured_piece,
               promote_to):
    """
    A supporting function called by make_move to update the PGN

    Should return the new PGN move
    """
    PGN = []
    if game.turn == 'w':
        PGN.append(str(game.fullmove)+'.')
    squares = game.prev_state.board.squares
    if legality in (-5, 5):
            PGN.append('O-O ' if legality == 5 else 'O-O-O ') # Do not forget the space
            game.PGN = game.PGN + ''.join(PGN)
            return 
    if piece.name != 'pawn':
        PGN.append(NAME_TO_LETTER[piece.name].capitalize())
    target = get_coordinate_from_square(new_square)    
    original = get_coordinate_from_square(original_square)    
    for square in squares:
        other = squares[square] 
        if other is None:
            continue
        if other.color == game.turn and other.name == piece.name \
           and other.square != original_square:
            if make_move(game.prev_state, other.square, new_square,
                         track_PGN=False):
                game.prev_state = game.prev_state.prev_state
                original = get_coordinate_from_square(original_square)
                if piece.square[0] == other.square[0]:
                    PGN.append(original[0])
                else:
                    PGN.append(original[1])
                break
    if captured_piece is not None or legality == 3:
        if piece.name == 'pawn' and original[0] not in PGN:
            PGN.append(original[0])
        PGN.append('x')
    PGN.append(target)
    if legality == 4:
        PGN.append('=' + NAME_TO_LETTER[promote_to])
    PGN.append(' ')
    PGN = ''.join(PGN)
    game.PGN = game.PGN + PGN
    return PGN

def state_from_PGN(PGN, wrapper_dict = LETTER_TO_PIECE):
    for x in PGN_state_gen(PGN, wrapper_dict):
        pass
    return x    
def state_from_FEN(FEN='rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1', wrapper_dict = LETTER_TO_PIECE):
    """
    Take a FEN and return a game state

    wrapper_dict, is an optional dict that can given where
    'p': Pawn and so on. To make different types of classes

    """
    cur_square= (0, 0)
    squares = {}
    fields = FEN.split(' ')

    for x in fields[0]:
        if x == '/':
            # end row
            cur_square = (0, cur_square[1] + 1)
            continue
        elif x == ' ':
            break    
        if x.isnumeric():
            cur_square = (cur_square[0] + int(x), cur_square[1])
            continue
        color = 'w' if x.isupper() else 'b'
        squares[cur_square] = wrapper_dict[x.lower()](color)
        squares[cur_square].square = cur_square

        if x == 'r':
            squares[cur_square].original_square = cur_square

        cur_square = (cur_square[0] + 1, cur_square[1])


    turn = fields[1]
    translation_table = ''.maketrans('KQkq', 'wWbB')
    castling = fields[2].translate(translation_table)
    board = chessBoard(squares, castling)

    passant_square = fields[3]
    if passant_square != '-':
        passant_square = get_square_from_coordinate(passant_square)
        pawn = passanted_pawn_from_square(board, passant_square)
        board.passanted_pawn = pawn

    halfmove = int(fields[4])
    fullmove = int(fields[5])
    z = GameState('', turn, halfmove, fullmove, None, board, wrapper_dict)
    return z
def make_move(game, original_square, new_square, promote_to='queen', 
              track_PGN=True, return_PGN=False):
    """
    Return
    0 ---> illegal move
    1 ---> legal move
    """
    result = 1 
    piece = game.board.squares[original_square]
    # some technical checks that the move is legal
    if (original_square == new_square 
            or game.end 
            or piece.color != game.turn):
        return 0    
    legality = piece.legal_move(game.board, new_square)
    if not legality:
        return 0
    prev_state = game.copy()

    captured_piece = game.board.squares[new_square]
    # Will be undoed if king is in check, this is basically
    # moving the piece
    game.board.squares[new_square] = piece
    game.board.squares[original_square] = None
    piece.square = new_square
    # If king would be in check then:
    if get_king(game.board, piece.color).in_check(game.board):
        old_piece = prev_state.board.squares[new_square]
        game.board.squares[original_square] = piece
        game.board.squares[new_square] = old_piece
        piece.square = original_square
        return 0

    if captured_piece is not None:
        game.halfmove = -1 # Will be 0 after this move is finished
        captured_piece.square = None

    passanted_pawn = game.board.passanted_pawn
    game.board.passanted_pawn = None 
    # Additional things to do after the move is made
    if legality == 2: # Change the passanted_pawn
        game.board.passanted_pawn = piece 
    elif legality == 3: # Eat the passanted_pawn if en passant
        passanted_square = passanted_pawn.square
        game.board.squares[passanted_square].square = None
        game.board.squares[passanted_square] = None
    elif legality == 4:
        new_piece = game.wrapper_dict[NAME_TO_LETTER[promote_to]](piece.color)
        piece.square = None
        game.board.squares[new_square] = new_piece
        piece.promote(new_piece) 
        new_piece.square = new_square
    elif legality in (-5, 5): # Move the rook
        rook_square = int(original_square[0] - 0.5 + (sign(legality) * 3.5)), original_square[1]
        rook = game.board.squares[rook_square]

        rook_destination = (piece.square[0] - sign(legality), original_square[1])
        game.board.squares[rook_destination] = rook
        game.board.squares[rook_square] = None
        rook.square = rook_destination
    # Update the game
    game.prev_state = prev_state
    if piece.color == 'b':
        game.fullmove += 1
    if piece.name == 'pawn':
        game.halfmove = -1    

    game.halfmove += 1
    if track_PGN:
        PGN = update_PGN(game, original_square, new_square, legality,
                              piece, captured_piece, promote_to)

    game.turn = 'b' if game.turn == 'w' else 'w'
    # And the castling
    if piece.name == 'king':
        # If king has moved
        game.board.castling=game.board.castling.replace(piece.color, '')
        game.board.castling=game.board.castling.replace(piece.color.capitalize(), '')
    elif piece.name == 'rook':
        # if longside / queenside castling, then it should be leftmost
        # so squares are 0, 8, 16, etc..
        color = piece.color if piece.original_square[0] % 8 else piece.color.capitalize()

        game.board.castling=game.board.castling.replace(color, '')

    if return_PGN:
        return PGN
    return result
def check_game_end(game, color):
    game = state_from_FEN(game.get_FEN(), LETTER_TO_PIECE)
    if not get_all_moves_for_color(game, color):
        if get_king(game.board, color).in_check(game.board):
            game.end = 'w' if color == 'b' else 'w'
            return game.end
        game.end = '-'
        return game.end
    return 0            
def get_all_moves_for_color(game, color, end_quickly = True):
    """ 
    Given a game, and a color, Return all possible moves.

    end_quickly --> if True, return the first move found
    moves are tuples of (piece, new_square)
    """
    moves = []

    for square in game.board.squares:
        i, j = square
        piece = game.board.squares[square]

        if piece is None or piece.color != color:
            continue

        moves_to_check = []

        if piece.name == 'pawn':
            d = piece.direction
            temp_tup = ((i, j+d),
                      (i, j+2*d),
                      (i+1, j+d),
                      (i-1, j+d))
            moves_to_check.extend(x for x in temp_tup if 0 <= x[0] <= 7
                                                      and 0 <= x[1] <= 7)
        elif piece.name == 'knight':
            moves_to_check.extend((i+a, j+b) for a in (-2, 2, 1, -1) 
                                    for b in (3-math.fabs(a), math.fabs(a)-3)
                                    if (0 <= i+a <= 7 
                                    and 0 <= j+b<= 7))
        elif piece.name == 'bishop' or piece.name == 'queen':
            for inc in range(8):
                temp_tup = ((i+inc, j+inc),
                            (i+inc, j-inc),
                            (i-inc, j+inc),
                            (i-inc, j-inc))
                moves_to_check.extend(square for square in temp_tup if 
                                      0 <= square[0] <= 7 
                                      and 0 <= square[1] <= 7)
        if piece.name == 'rook' or piece.name == 'queen':
            for inc in range(8):
                temp_tup = ((i+inc, j),
                            (i-inc, j),
                            (i, j+inc),
                            (i, j-inc))
                moves_to_check.extend(square for square in temp_tup if 
                                      0 <= square[0] <= 7 
                                      and 0 <= square[1] <= 7)

        elif piece.name == 'king':
            for x in (-1, 0, 1):
                for y in (-1, 0, 1):
                    if 0 <= (i+x) <= 7 and 0 <= (j+y) <= 7: 
                        moves_to_check.append((i+x, j+y)) 

        for x in moves_to_check:
            temp_game = game.copy()
            temp_game.turn = piece.color
            res = make_move(temp_game, piece.square, x, track_PGN=False)
            if not res:
                continue
            moves.append((piece, x)) 

            if end_quickly:
                return moves 
    return moves            

