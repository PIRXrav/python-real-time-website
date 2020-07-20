#!/usr/bin/env python

from itertools import product

conv = lambda x, y: f"{x}{y}"

class TicTacToe():
    def __init__(self):
        self.table = {conv(i, j): 2 for i, j in product(range(3), range(3))}
        self.player = 0
        self.winner = None

    def play(self, x, y):
        if 0 <= x <= 2 and  0 <= x <= 2: # valid pos
            if self.table[conv(x, y)] == 2: # free pos
                self.table[conv(x, y)] = self.player
                if self.win():
                    self.winner = self.player
                self.player = 1 - self.player
                return True
        return False

    def win(self):
        pos = [((i, 0), (i, 1), (i, 2)) for i in range(3)]
        pos += [((0, j), (1, j), (2, j)) for j in range(3)]
        pos += [((0, 0), (1, 1), (2, 2)), ((2, 0), (1, 1), (0, 2))]

        for p0, p1, p2 in pos:
            if (self.table[conv(*p0)] == self.table[conv(*p1)]
                == self.table[conv(*p2)] != 2):
                return True
        return False

    def __str__(self):
        syms = ['X', 'O', '.']
        ret = ''
        for y in range(3):
            for x in range(3):
                ret += syms[self.table[conv(x, y)]]
            ret += '\n'
        return ret

if __name__ == '__main__':
    ttt = TicTacToe()
    while ttt.winner == None:
        print(ttt)
        print("x \\n y")
        ttt.play(int(input()), int(input()))
    print(f"winner is : {ttt.winner}")
