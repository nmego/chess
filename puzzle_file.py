"""
TBD:
1. Might want to give puzzle_file.txt its own CREATIVE format
2. I might need to have a universal FOLDER in an __init__

3. I need a way to compare 2 FENs or are they all equal? I mean halfmove and
full move don't count


VERY VERY IMPORTANT
I NEED TO OPEN THE FILE ONLY ONCE AT START WITH MODE WRITE AND READ AT
SAME TIME!!!!!
"""
"""
All functions in this helper-module assume that pygame.scrap has been initialized
"""
def simplify_FEN(FEN):
    # For starters, we're going to assume that fullmove and halfmove don't count
    fields = FEN.split(' ')[:4]
    return ''.join(fields)

def encode_FEN(FEN):
    return simplify_FEN(FEN)

def write(file, dict_):
    """
    Take a dict of FEN:Legal moves and write that to the file
    """
    with open(file, 'w') as f:
        for FEN in dict_:
            legal_moves = dict_[FEN]
            FEN = encode_FEN(FEN)
            f.write(FEN+'^')
            for move in legal_moves:
                f.write(move+'&')
            f.write('$')
            f.write('\n')
def read(file):
    dict_ = {}
    with open(file, 'r') as f:
        for line in f.readlines():
            FEN, moves = line.split('^')
            moves = moves.split('&')
            del moves[-1] # is an '$' element
            dict_[FEN] = set(moves)
    return dict_




