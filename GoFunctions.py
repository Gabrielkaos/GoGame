import numpy as np
from GoConstants import board_size

def rand64():
    return np.random.randint(1,2**64,dtype=np.uint64)
def index_from_row_col(row,col):
    return col + row * board_size