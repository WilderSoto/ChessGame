#!/usr/bin/env python
# coding: utf-8

# In[5]:


import numpy as np
import math
import matplotlib.pyplot as plt


# In[6]:


class Board:
    
    def __init__(self,pieces,squares,players):
        
        self.squares = squares
        self.pieces = pieces
        self.board = []
        self.players = players
        self.current_player = players['White']
        self.en_passant = {'White':{},'Black':{}}
        self.heatdict = {'White':'Black','Black':'White'}
        self.move_log = []
        self.notake = 0
        self.move_count = 0
        self.wcastle_rights = 'KQ'
        self.bcastle_rights = 'kq'
        self.FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 0"
        self.kings = []
        self.dp = []
    def __str__(self):
        print(self.board)
        
    def heat_setup(self):
        
        for i in self.squares:
            for j in i:
                for col in self.pieces:
                    for name in self.pieces[col]:
                        j.heat[col][name] = [0,0]
    
    def en_passant_setup(self):
        
        for i in self.pieces:
            for j in self.pieces[i]:
                if j.lower()[0] == 'p':
                    self.en_passant[i][j] = False
        
    def update_board(self):
        board = [['*','*','*','*','*','*','*','*'],
                 ['*','*','*','*','*','*','*','*'],
                 ['*','*','*','*','*','*','*','*'],
                 ['*','*','*','*','*','*','*','*'],
                 ['*','*','*','*','*','*','*','*'],
                 ['*','*','*','*','*','*','*','*'],
                 ['*','*','*','*','*','*','*','*'],
                 ['*','*','*','*','*','*','*','*']]

        for i in self.pieces['White']:
            if self.pieces['White'][i]:
                j,k = self.pieces['White'][i].position
                a = board[k].copy()
                a[j] = i
                board[k] = a
        for l in self.pieces['Black']:
            if self.pieces['Black'][l]:
                j,k = self.pieces['Black'][l].position
                a = board[k].copy()
                a[j] = l
                board[k] = a
                board[k][j] = l
        
        return board
    
    def heatmap(self):
        
        wh = self.players['White'].possible_moves()
        bl = self.players['Black'].possible_moves()
        
        hotp = {'P':8*[8*[0]],'N':8*[8*[0]],'B':8*[8*[0]],'R':8*[8*[0]],'Q':8*[8*[0]],'K':8*[8*[0]]}

        for col in ['White','Black']:
            
            for name in self.pieces[col]:
                
                for rows in self.squares:
                    for sq in rows:
                        x,y = sq.coords
                        if sq.heat[col][name][0] == 1:
                            
                            b = hotp[name[0].upper()][y].copy()
                            
                            val = 1 if col == 'White' else -1
                            b[x] = b[x]+val
                            
                            hotp[name[0].upper()][y] = b
        return hotp
        
    def add_pieces(self,stuff):
    
        for i in stuff:
            self.pieces[i.color][i.name] = i
            x,y = i.position
            self.squares[y][x].heat[i.color][i.name] = [0,0]
            
    def add_players(self,players):
        
        for i in players:
            self.players[i.color] = i
            
    def state(self):
        
        nametype = {'White':'K','Black':'k'}
        
        moveposs = 0
        moveset = self.current_player.possible_moves()
        for piece in moveset:
            if moveset[piece]:
                moveposs += 1
            
        bplist = sorted([i for i in self.pieces['Black'].keys() if self.pieces['Black'][i]])
        wplist = sorted([i for i in self.pieces['White'].keys() if self.pieces['White'][i]])
        erstr = ''
        
        try:
            if int(self.FEN.split(' ')[-2]) >= 100:
                return (1e-16,'Technical Draw: 50 move rule')
            
            if len(self.move_log) > 6:
                l = [i.split(' ')[0]+i.split(' ')[1]+i.split(' ')[2] for i in self.move_log[-6:]]

                if len(set(l)) <=  4:
                    return (1e-16,'Technical Draw: Repeat Positions')

            if len(bplist) <= 2 and len(wplist) <= 2:
                if len(bplist) == 1 and len(wplist) == 1:
                    return (1e-16,'Material Draw: Kings')
                elif len(bplist) == 2 and len(wplist) == 1:
                    if bplist[1] == 'k' and bplist[0][0] == 'b':
                        return (1e-16,'Material Draw: k b')
                    elif bplist[0] == 'k' and bplist[1][0] == 'n':
                        return (1e-16,'Material Draw: k n')
                elif len(bplist) == 1 and len(wplist) == 2:
                    if wplist[0][0] == 'B' and wplist[1] == 'K':
                        return (1e-16,'Material Draw: K B')
                    elif wplist[0] == 'K' and wplist[1][0] == 'N':
                        return (1e-16,'Material Draw: K N')

                elif len(bplist) == 2 and len(wplist) == 2:

                    if wplist[0][0] == 'B' and bplist[0][0] == 'b':

                        wcoord = self.pieces['White'][wplist[0]].position
                        bcoord = self.pieces['Black'][bplist[0]].position
                        if sum(bcoord)%2 == sum(wcoord) %2:

                            return (1e-16,'Material Draw: Same Bishop Color')

            if moveposs == 0:
                if self.current_player.pieces[nametype[self.current_player.color]].in_check():
                    
                    erstr = f'Error in Getting Kings for {self.current_player.color}'
                    
                    return (-1, f'Loss for {self.current_player.color}') 
                else:
                    
                    if not self.current_player.pieces[nametype[self.current_player.color]].in_check():
                        
                        erstr = f'Error in Getting Kings for {self.current_player.color}'
                        
                        return (1e-16,'Forced Draw: No Moves')

            return False
        
        except:
            
            return (f'Error Requesting Board State: {erstr}')
                
class square:
    
    def __init__(self,coords,occupied=False):
        self.coords = coords
        if self.coords[1]== 7 or self.coords[1] == 0:
            self.occupied = occupied
        else:
            self.occupied = False
        self.heat = {'White':{},'Black':{}}
            
    def __repr__(self):
        return f'Square on {self.coords}'
    
    def newowner(self,piece):
        self.occupied = piece


# In[7]:


class Player:
    
    def __init__(self,name,color,board):
        
        self.name = name
        self.color = color
        self.board = board
        self.pieces = self.board.pieces[self.color]
        
    def add_pieces(self,piece):
        
        self.pieces[piece.name] = piece
        
    def remove_pieces(self,piece):
        self.pieces[piece.name] = None
        
    def possible_moves(self):
        
        cold = {'White':'Black','Black':'White'}
        moves = {}
        
        c = cold[self.color]
        for piece in self.board.pieces[c]:
            if not self.board.pieces[c][piece]:
                for sq in self.board.squares:
                    for s in sq:
                        if s.heat[c][piece]:
                            
                            s.heat[c][piece] = [0,0]
                            
        for piece in self.pieces:
            if self.board.pieces[self.color][piece]:
                try:
                    moves[piece] = self.pieces[piece].get_moves()
                except:
                    print(f'Error: Issues Requesting Possible Moves for {piece}')
                    return self.pieces[piece].get_moves()

        return moves


# In[215]:


class Piece:
    
    def __init__(self,square,color,name,board,kings):
        self.position = square.coords
        square.occupied = [color,name]
        self.color = color
        self.move_count = 0
        self.alive = True
        self.square = square
        self.name = name
        self.board = board
        self.heatdict = {'White':'Black','Black':'White'}
        self.kings = kings
        
        def ru(curr):
            x0,y0 = curr

            sums = y0+x0
            for i in range(x0-1,-1,-1):
                if (i in range(8)) and (sums-i in range(8)): 
                    yield (i,sums-i)
                else:
                    yield ()
            yield ()

        def rd(curr):
            x0,y0 = curr
            diff = y0-x0
            for i in range(x0-1,-1,-1):
                if (i in range(8)) and (i+diff in range(8)): 
                    yield (i,i+diff)
                else:
                    yield ()
            yield ()

        def lu(curr):
            x0,y0 = curr
            diff = y0-x0
            for i in range(x0+1,8):
                if (i in range(8)) and (i+diff in range(8)): 
                    yield (i,i+diff)
                else:
                    yield ()
            yield ()

        def ld(curr):
            x0,y0 = curr

            sums = y0+x0
            for i in range(x0+1,8):
                if (i in range(8)) and (sums-i in range(8)): 
                    yield (i,sums-i)
                else:
                    yield () 
            yield ()


        def f(curr):
            x0,y0 = curr
            for i in range(y0+1,8):
                if (x0 in range(8)) and (i in range(8)):
                    yield (x0,i)
                else:
                    yield ()
            yield ()
            
        def b(curr):
            x0,y0 = curr
            for i in range(y0-1,-1,-1):
                if (x0 in range(8)) and (i in range(8)):
                    yield (x0,i)
                else:
                    yield ()
            yield ()

        def r(curr):
            x0,y0 = curr
            for i in range(x0-1,-1,-1):
                if (i in range(8)) and (y0 in range(8)):
                    yield (i,y0)
                else:
                    yield ()
            yield ()

        def l(curr):
            x0,y0 = curr
            for i in range(x0+1,8):
                if (i in range(8)) and (y0 in range(8)):
                    yield (i,y0)
                else:
                    yield ()
            yield ()
            
            
        def move_add(f):
            mvlst = []
            fun = next(f)
            fl = []
            hcnt = 1
            khcnt = 1
            while fun:
                x,y = fun
                fl += [fun]

                sq = self.board.squares[y][x]
                lst = [khcnt,[self.position]+fl]
                sq.heat[self.color][self.name] = 0
                sq.heat[self.color][self.name] = lst

                if sq.occupied:
                    col,oc = sq.occupied
                    if oc.lower() == 'k' and self.color != col:
                        khcnt -= 1
                    if oc[0].lower() == 'p':
                        if self.board.en_passant[col][oc] and col != self.color:
                            khcnt -= 1
                    khcnt += 1 
                    hcnt += 1

                if hcnt == 1:
                    mvlst.append(fun)

                elif hcnt == 2 and sq.occupied and col != self.color:
                    mvlst.append(fun)

                fun = next(f)

            return mvlst
                
        self.madd = move_add
                    
        self.f = f
        self.b = b
        self.r = r
        self.l = l
        self.ru = ru
        self.ld = ld
        self.rd = rd
        self.lu = lu
        
        
    def in_check(self):
        
        heats = self.square.heat[self.heatdict[self.color]]
        checks = {}
        for i in heats:
            if heats[i][0] == 1:
                checks[i] = heats[i][1]
        return checks
    
    def is_pinned(self):
        heat = self.square.heat[self.heatdict[self.color]]
        xk,yk = self.kings[self.color].position
        kheat = self.board.squares[yk][xk].heat[self.heatdict[self.color]]
        
        currpins = {}
        for i in heat:
            if heat[i][0] == 1 and kheat[i][0] == 2 and heat[i][1][:2] == kheat[i][1][:2]:
                
                currpins[i] = heat[i][1]
                
        return currpins
            
    def emergency_move(self,move):
        x,y = move
        self.square.occupied = False
        
        self.square = self.board.squares[y][x]
        self.board.squares[y][x].occupied = [self.color,self.name]
        self.position = self.square.coords
        self.move_count += 1
        for i in self.board.squares:
            for j in i:
                j.heat[self.color][self.name] = [0,0]
        m = self.get_moves()
            
    def move_to(self,mv):
        
        for piece in self.board.dp:
            for sqr in self.board.squares:
                for sq in sqr:
                    col,pc = piece.color,piece.name
                    sq.heat[col][pc] = [0,0]
        
        if self.board.state():
            return self.board.state()
                
        promotions = {'Queen':Queen,'Rook':Rook,'Bishop':Bishop,'Knight':Knight}
        moves = self.get_moves()
        
        pos = self.position
        
        if len(mv) == 2:
            x,y = mv
            prom = None
        elif len(mv) == 3:
            x,y,prom = mv
        
        xcurr,ycurr = self.position
        
        diff = 2*(ycurr-y)
        
        en_poss = {'White':(xcurr,ycurr+2),'Black':(xcurr,ycurr-2)}
        en_takes = {'White': [(xcurr-1,ycurr+1),(xcurr+1,ycurr+1)],'Black':[(xcurr-1,ycurr-1),(xcurr+1,ycurr-1)]}
        self.board.en_passant_setup()
        
        if mv in moves:
            #Promotions Here
            if (y == 0 and self.color == 'Black') or (y == 7 and self.color == 'White'):
                move_cnt = self.move_count
                if prom:
                    if self.color == 'Black':
                        pr = prom[0].lower()

                        if prom == 'Knight':
                            pr = 'n'
                    else:
                        pr = prom[0]
                    
                        if prom == 'Knight':
                            pr = 'N'
                  
                    old_name = self.name
                    pnew = promotions[prom](self.square,self.color,pr+old_name,self.board,self.kings)
                    self = pnew
              
                    del self.board.pieces[self.color][old_name]
                    
                    for sq in self.board.squares:
                        for s in sq:
                            lst = [0,0]
                            s.heat[self.color][old_name] = 0
                            s.heat[self.color][old_name] = lst.copy()
                    
                    self.board.add_pieces([self])
                    self.board.players[self.color].add_pieces(self)
            #Castling
            if self.name[0].lower() == 'k':
                if mv in self.castle():
                
                    if x == 2:
                        if self.board.squares[y][x-2].occupied:
                            color,occupant = self.board.squares[y][x-2].occupied
                            if occupant[0].lower() == 'r' and color == self.color and self.board.pieces[color][occupant].move_count == 0:
                                rook = self.board.pieces[color][occupant]

                                rook.emergency_move((x+1,y))

                    elif x == 6:
                        if self.board.squares[y][x+1].occupied:
                            color,occupant = self.board.squares[y][x+1].occupied
                            if occupant[0].lower() == 'r' and color == self.color and self.board.pieces[color][occupant].move_count == 0:
                                rook = self.board.pieces[color][occupant]
                                rook.emergency_move((x-1,y))
                                rookmoves = rook.get_moves()
                                    
            #Opening yourself up for an en_passant
            if mv == en_poss[self.color] and self.name[0].lower() == 'p':
                
                self.board.en_passant[self.color][self.name] = True
            #Performing an En Passant
            if mv in en_takes[self.color] and self.name[0].lower() == 'p':
                
                if not self.board.squares[y][x].occupied:    
                    check = self.board.squares[ycurr][x]
                    col,occ = check.occupied
                    if occ[0].lower() == 'p':
                        pawn = self.board.pieces[col][occ]
                        pawn.alive = False
                        pawn.square.occupied = False
                        
                        self.board.dp.append(self.board.players[col].pieces[occ])
                        del self.board.players[col].pieces[occ]
                        try:
                            del self.board.pieces[col][occ]
                        except:
                            print("En Passant-ed Pawn Doesn't Exist")
                        
                        if col == 'Black':
                            v = -1
                        else:
                            v = 1 
                        lst = [0,0]
                        self.board.squares[y+v][x+1].heat[col][occ] = 0
                        self.board.squares[y+v][x-1].heat[col][occ] = 0
                        self.board.squares[y+v][x+1].heat[col][occ] = lst.copy()
                        self.board.squares[y+v][x-1].heat[col][occ] = lst.copy()
            
            self.square.occupied = False
            
            #If the square was occupied 
            occupant = self.board.squares[y][x].occupied
            if occupant:
                col,occ = occupant
                if self.color != col:
                
                    self.board.notake = 0
                
                    self.board.pieces[col][occ].alive = False
                    self.board.dp.append(self.board.pieces[col][occ])
                    del self.board.players[col].pieces[occ]
                    #Reseting the heats for the squares
                    for sq in self.board.squares:
                        for s in sq:
                            lst = [0,0]
                            s.heat[col][occ] = 0
                            s.heat[col][occ] = lst.copy()
            
            else:
                
                self.board.notake += 1
            #Update the squares that are occupied
            self.square = self.board.squares[y][x]
            self.board.squares[y][x].occupied = [self.color,self.name]
            self.position = self.square.coords
            
            self.move_count += 1
        
        #Reset all the board squares for the pieces heat that just moved
            for i in self.board.squares:
                for j in i:
                    lst = [0,0]
                    j.heat[self.color][self.name] = 0
                    j.heat[self.color][self.name] = lst.copy()
                    
            self.get_moves()

            #Update Current fen
        if pos != self.position:
            if self.board.current_player.color == 'Black':
                self.board.move_count += 1

            if self.board.kings[self.color].move_count == 0:
                curr_rights = ''
                if self.color == 'White':
                    oc1 = self.board.squares[0][0].occupied
                    oc2 = self.board.squares[0][7].occupied
                    if oc2:
                        if self.board.pieces[oc2[0]][oc2[1]].move_count == 0 and oc2[1][0] == 'R':
                            curr_rights += 'K'
                    if oc1:
                        if self.board.pieces[oc1[0]][oc1[1]].move_count == 0 and oc1[1][0] == 'R':
                            curr_rights += 'Q'
                    self.board.wcastle_rights = curr_rights
                elif self.color == 'Black':
                    oc1 = self.board.squares[7][0].occupied
                    oc2 = self.board.squares[7][7].occupied
                    if oc2:
                        if self.board.pieces[oc2[0]][oc2[1]].move_count == 0 and oc2[1][0] == 'r':
                            curr_rights += 'k'
                    if oc1:
                        if self.board.pieces[oc1[0]][oc1[1]].move_count == 0 and oc1[1][0] == 'r':
                            curr_rights += 'q'
                    self.board.bcastle_rights = curr_rights

            else:
                if self.color == 'White':
                    self.board.wcastle_rights = ''
                elif self.color == 'Black':
                    self.board.bcastle_rights = ''

            fen = ''
            c = 0
            for row in self.board.update_board()[::-1]:
                for sq in row:

                    if sq == '*':
                        c += 1
                    else:
                        if c > 0:
                            fen += str(c)
                            c = 0
                        fen += sq[0]
                if c > 0 or c == 8:
                    fen += str(c)
                c = 0
                fen +='/'
            epstatus = ' - '
            for piece in self.board.en_passant[self.color]:

                if self.board.en_passant[self.color][piece]:
                    xc,yc = self.board.players[self.color].pieces[piece].position
                    epstatus = ' '+'abcdefgh'[xc]+str(yc+1)+' '
            colorsp = self.heatdict[self.board.current_player.color]
            fen += ' ' + colorsp[0].lower()+' '+self.board.wcastle_rights+self.board.bcastle_rights+epstatus+str(self.board.notake)+' '+str(self.board.move_count)
            self.board.FEN = fen

            #Update the heats and make sure everything is current
            #newmoves = self.get_moves()
            self.board.move_log.append(self.board.FEN)
            
            a = self.board.players['Black'].possible_moves()
            c = self.board.players['White'].possible_moves()
            self.board.current_player = self.board.players[self.heatdict[self.color]]
        else:
            print('Failure to move')
            newm = self.board.current_player.possible_moves() 
        
class King(Piece):
    
    def __init__(self,square,color,name,board):
        
        super().__init__(square,color,name,board,None)
        
    def get_moves(self):
        
        moves = []
        
        f = self.f(self.position)
        b = self.b(self.position)
        r = self.r(self.position)
        l = self.l(self.position)
        ru = self.ru(self.position)
        ld = self.ld(self.position)
        rd = self.rd(self.position)
        lu = self.lu(self.position)
        
        
        movepos = [next(rd),next(ru),next(r),next(f),next(b),next(l),next(ld),next(lu)]
        
        hv1 = 0
        
        mv2 = []
        
        for i in movepos:
            if i:
                x,y = i
                self.board.squares[y][x].heat[self.color][self.name] = [1,[self.position]]
                sq = self.board.squares[y][x]
                hots = sq.heat[self.heatdict[self.color]]
                for key in hots:
                    if hots[key][0] == 1:
                        hv1 += 1
                if hv1 == 0:
                    if sq.occupied:
                        if sq.occupied[0] != self.color:
                            mv2.append(i)
                    else:
                        mv2.append(i)            
            hv1 = 0          
        
        final_moves = mv2+self.castle()
        
        heatvals = 0
        
        self.square.heat[self.color][self.name] = [0,[self.position]]
        return list(set(final_moves))
    
    
    def castle(self):
        direct = {'White':[(6,0),(2,0)],'Black':[(6,7),(2,7)]}

        castles = []
        ks = 0
        qs = 0
        hq = 0
        hk = 0
        x,y = self.position
        
        if self.move_count!=0 or self.in_check():
            return castles
        
        if self.move_count == 0:
            rQ = self.board.squares[y][0]
            rK = self.board.squares[y][-1]
            
            if rQ.occupied: # Have to scan the side of the queen to see if a few conditions are met
        # Firstly, we have to see whether the rook on that side can even participate in a castle
        #Then we have to check and see if the king is castling through check
        #Then repeat this for the King side and Queen side
                c,p = rQ.occupied
                pn = p[0]
                piece = self.board.pieces[c][p]
                if self.color == c and piece.move_count == 0 and pn.lower() == 'r':
                    queencastle = self.board.squares[y][1:x]
                    for Qs in queencastle:
                        if not Qs.occupied:
                            qs += 1
                            for h in Qs.heat[self.heatdict[self.color]].values():
                                if 1 in h:
                                    hq += 1 
            if rK.occupied:
                c,p = rK.occupied
                pn = p[0]
                piece = self.board.pieces[c][p]
                if self.color == c and piece.move_count == 0 and pn.lower() == 'r':
                    kingcastle = self.board.squares[y][x+1:-1]
                    for Ks in kingcastle:
                        if not Ks.occupied:
                            ks += 1
                            for h in Ks.heat[self.heatdict[self.color]].values():
                                if 1 in h:
                                    hk += 1 
                                    
            if ks == 2 and hk == 0:
                castles.append(direct[self.color][0])
            if qs == 3 and hq == 0:
                castles.append(direct[self.color][1])
                
        return castles

class Bishop(Piece):
    
    def __init__(self,square,color,name,board,kings):

        super().__init__(square,color,name,board,kings)
        

    def get_moves(self):
        
        heats = self.square.heat[self.color]
        
        if self.alive == False:
            return []
        
        pins = self.is_pinned()
        
        kchecks = self.kings[self.color].in_check()
        
        ru = self.ru(self.position)
        ld = self.ld(self.position)
        rd = self.rd(self.position)
        lu = self.lu(self.position)
    
        fin = []
        
        rum = self.madd(ru)
        rdm = self.madd(rd)
        lum = self.madd(lu)
        ldm = self.madd(ld)

        fin = rum+lum+ldm+rdm
        
        mvs = list(set(fin))  
        
        self.square.heat[self.color][self.name] = [0,[self.position]]
        
        if pins and not kchecks:
            nwp = []
            if len(pins.keys())>1:
                return nwp
            else:
                for p in pins:
                    for pin in pins[p]:
                        if pin in mvs:
                            nwp.append(pin)
                return nwp
            
        elif (not pins) and kchecks:
            m = []

            if len(kchecks.keys()) == 1:
                for key in kchecks:
                    mv = kchecks[key]
                    for mpos in mv:
                        if mpos in mvs:
                            m.append(mpos)
            return m

        elif not pins and not kchecks:
            return mvs

class Rook(Piece):
    
    def __init__(self,square,color,name,board,kings):

        super().__init__(square,color,name,board,kings)
        

    def get_moves(self):
        heats = self.square.heat[self.color]
        
        if self.alive == False:
            return []
        
        pins = self.is_pinned()
        
        kchecks = self.kings[self.color].in_check()
        
        f = self.f(self.position)
        b = self.b(self.position)
        r = self.r(self.position)
        l = self.l(self.position)
        
        fin = []
        
        rm = self.madd(r)
        lm = self.madd(l)
        fm = self.madd(f)
        bm = self.madd(b)

        fin = rm+lm+fm+bm
        
        mvs = list(set(fin)) 
        
        self.square.heat[self.color][self.name] = [0,[self.position]]
        
        if pins and not kchecks:
            nwp = []
            if len(pins.keys())>1:
                return nwp
            else:
                for p in pins:
                    for pin in pins[p]:
                        if pin in mvs:
                            nwp.append(pin)
                return nwp
            
        elif (not pins) and kchecks:
            m = []

            if len(kchecks.keys()) == 1:
                for key in kchecks:
                    mv = kchecks[key]
                    for mpos in mv:
                        if mpos in mvs:
                            m.append(mpos)
            return m

        elif not pins and not kchecks:
            return mvs
        
class Knight(Piece):
    
    def __init__(self,square,color,name,board,kings):
        
        super().__init__(square,color,name,board,kings)
        
    def get_moves(self):
        
        if self.alive == False:
            return []
        
        pins = self.is_pinned()
        
        kchecks = self.kings[self.color].in_check()
    
        x0,y0 = self.position

        kd = lambda x: -2*x+2*x0+y0
        ku = lambda x: 2*x-2*x0+y0
        kl = lambda x: -0.5*x+0.5*x0+y0
        kr = lambda x: 0.5*x-0.5*x0+y0
        mu = [(x0+i,int(ku(x0+i))) for i in [-1,1]]
        md = [(x0+i,int(kd(x0+i))) for i in [-1,1]]
        ml = [(x0+i,int(kl(i+x0))) for i in [-2,2]]
        mr = [(x0+i,int(kr(i+x0))) for i in [-2,2]]
        moves = mu+md+ml+mr
        moves = [m for m in moves if (m[0] in range(8)) and (m[1] in range(8))]
        fm = []
        for m in moves:
            xloc,yloc = m
            sq = self.board.squares[yloc][xloc]
            lst = [1,[self.position]]
            sq.heat[self.color][self.name] = 0
            sq.heat[self.color][self.name] = lst
            
            if not sq.occupied:
                fm += [m]
            elif sq.occupied:
                if sq.occupied[0] != self.color:
                    fm += [m]
                    
        mvs = list(set(fm))
        self.square.heat[self.color][self.name] = [0,self.position]
        
        if pins and not kchecks:
            nwp = []
            if len(pins.keys())>1:
                return nwp
            else:
                for p in pins:
                    for pin in pins[p]:
                        if pin in mvs:
                            nwp.append(pin)
                return nwp
            
        elif (not pins) and kchecks:
            m = []

            if len(kchecks.keys()) == 1:
                for key in kchecks:
                    mv = kchecks[key]
                    if len(mv) == 1:
                        
                        if mv[0] in mvs:
                            m.append(mv[0])
                            
                    else:
                        for mpos in mv:
                            if mpos in mvs:
                                m.append(mpos)
            return m

        elif not pins and not kchecks:
            return mvs

class Queen(Piece):
    
    def __init__(self,square,color,name,board,kings):
        
        super().__init__(square,color,name,board,kings)
    
    def get_moves(self):
        
        heats = self.square.heat[self.color]
        
        if self.alive == False:
            return []
        
        pins = self.is_pinned()
        
        kchecks = self.kings[self.color].in_check()
            
        f = self.f(self.position)
        b = self.b(self.position)
        r = self.r(self.position)
        l = self.l(self.position)
        ru = self.ru(self.position)
        ld = self.ld(self.position)
        rd = self.rd(self.position)
        lu = self.lu(self.position)
        
        fin = []
        
        rum = self.madd(ru)
        rdm = self.madd(rd)
        lum = self.madd(lu)
        ldm = self.madd(ld)
        rm = self.madd(r)
        lm = self.madd(l)
        fm = self.madd(f)
        bm = self.madd(b)

        fin = rm+lm+fm+bm+rum+lum+ldm+rdm

        mvs = list(set(fin))  
        
        self.square.heat[self.color][self.name] = [0,[self.position]]
        
        if pins and not kchecks:
            nwp = []
            if len(pins.keys())>1:
                return nwp
            else:
                for p in pins:
                    for pin in pins[p]:
                        if pin in mvs:
                            nwp.append(pin)
                return nwp
            
        elif (not pins) and kchecks:
            m = []

            if len(kchecks.keys()) == 1:
                for key in kchecks:
                    mv = kchecks[key]
                    for mpos in mv:
                        if mpos in mvs:
                            m.append(mpos)
            return m

        elif not pins and not kchecks:
            return mvs
        
class Pawn(Piece):
    
    def __init__(self,square,color,name,board,kings):
        
        super().__init__(square,color,name,board,kings)
    
    def get_moves(self):
        
        heats = self.square.heat[self.color]
        
        if self.alive == False:
            return []
        
        pins = self.is_pinned()
        
        kchecks = self.kings[self.color].in_check()
        
        if self.color == 'White':
            
            mgen = self.f(self.position)
            tgenl = self.lu(self.position)
            tgenr = self.ru(self.position)
            
        elif self.color == 'Black':
            
            mgen = self.b(self.position)
            tgenl = self.ld(self.position)
            tgenr = self.rd(self.position)
            
        x,y = self.position
        
        fin = []
        
        m1 = next(mgen)
        
        if self.move_count == 0:
            m2 = next(mgen)
        else:
            m2 = ()
            
        moves = [m1,m2]
        
        x1,y1 = m1
        
        for m in moves:
            if m:
                xloc,yloc = m
                
                if not self.board.squares[yloc][xloc].occupied:
                    
                    if abs(y-yloc) != 2:
                        if yloc == 7 or yloc == 0:

                            fin.append((xloc,yloc,'Queen'))
                            fin.append((xloc,yloc,'Rook'))
                            fin.append((xloc,yloc,'Bishop'))
                            fin.append((xloc,yloc,'Knight'))

                        else:
                            
                            fin.append(m)
                        
                    if self.move_count == 0 and abs(y-yloc) == 2 and not self.board.squares[y1][x1].occupied:

                        fin.append(m)
        
        tl,tr = [next(tgenl),next(tgenr)]
        takes = [tl,tr]
        
        for t in takes:
            if t:
                xloc,yloc = t

                self.board.squares[yloc][xloc].heat[self.color][self.name] = [1,[self.position]]

                if self.board.squares[yloc][xloc].occupied:
                    col,oc = self.board.squares[yloc][xloc].occupied
                    if col != self.color and oc.lower() != 'k':

                        if yloc == 7 or yloc == 0:

                            fin.append((xloc,yloc,'Queen'))
                            fin.append((xloc,yloc,'Rook'))
                            fin.append((xloc,yloc,'Bishop'))
                            fin.append((xloc,yloc,'Knight'))
                        else:
                            fin.append(t)
                else:

                    if self.board.squares[y][xloc].occupied:
                        col,oc = self.board.squares[y][xloc].occupied
                        if oc[0].lower() == 'p':
                            if self.board.en_passant[col][oc] and col != self.color:
                                fin.append(t)
                    
        mvs = list(set(fin))
                    
        self.square.heat[self.color][self.name] = [0,self.position]
        
        if pins and not kchecks:
            nwp = []
            if len(pins.keys())>1:
                return nwp
            else:
                for p in pins:
                    for pin in pins[p]:
                        if pin in mvs:
                            nwp.append(pin)
                    if p[0].lower() == 'p':
                        if p[0] == p[0].lower():
                            direc = -1
                        else:
                            direc = 1
                        pinx,piny = pin[p][0]
                        newm = (pinx,piny-direc)
                        if newm in mvs:
                            nwp.append(newm)
                return nwp
            
        elif (not pins) and kchecks:
            m = []

            if len(kchecks.keys()) == 1:
                for key in kchecks:
                    mv = kchecks[key]
                    for mpos in mv:
                        if mpos in mvs:
                            m.append(mpos)
                    if key[0].lower() == 'p':
                        if key[0] == key[0].lower():
                            direc = 1
                        else:
                            direc = -1
                        kchx,kchy = kchecks[key][0]
                        newm = (kchx,kchy+direc)
                        if newm in mvs:
                            m.append(newm)
            return m

        elif not pins and not kchecks:
            return mvs


# In[216]:


class Game:
    def __init__(self):
        a1 = square((0,0))
        a2 = square((0,1))
        a3 = square((0,2))
        a4 = square((0,3))
        a5 = square((0,4))
        a6 = square((0,5))
        a7 = square((0,6))
        a8 = square((0,7))
        b1 = square((1,0))
        b2 = square((1,1))
        b3 = square((1,2))
        b4 = square((1,3))
        b5 = square((1,4))
        b6 = square((1,5))
        b7 = square((1,6))
        b8 = square((1,7))
        c1 = square((2,0))
        c2 = square((2,1))
        c3 = square((2,2))
        c4 = square((2,3))
        c5 = square((2,4))
        c6 = square((2,5))
        c7 = square((2,6))
        c8 = square((2,7))
        d1 = square((3,0))
        d2 = square((3,1))
        d3 = square((3,2))
        d4 = square((3,3))
        d5 = square((3,4))
        d6 = square((3,5))
        d7 = square((3,6))
        d8 = square((3,7))
        e1 = square((4,0))
        e2 = square((4,1))
        e3 = square((4,2))
        e4 = square((4,3))
        e5 = square((4,4))
        e6 = square((4,5))
        e7 = square((4,6))
        e8 = square((4,7))
        f1 = square((5,0))
        f2 = square((5,1))
        f3 = square((5,2))
        f4 = square((5,3))
        f5 = square((5,4))
        f6 = square((5,5))
        f7 = square((5,6))
        f8 = square((5,7))
        g1 = square((6,0))
        g2 = square((6,1))
        g3 = square((6,2))
        g4 = square((6,3))
        g5 = square((6,4))
        g6 = square((6,5))
        g7 = square((6,6))
        g8 = square((6,7))
        h1 = square((7,0))
        h2 = square((7,1))
        h3 = square((7,2))
        h4 = square((7,3))
        h5 = square((7,4))
        h6 = square((7,5))
        h7 = square((7,6))
        h8 = square((7,7))

        boardsquares = [[a1,b1,c1,d1,e1,f1,g1,h1],[a2,b2,c2,d2,e2,f2,g2,h2],[a3,b3,c3,d3,e3,f3,g3,h3],[a4,b4,c4,d4,e4,f4,g4,h4]
                        ,[a5,b5,c5,d5,e5,f5,g5,h5],[a6,b6,c6,d6,e6,f6,g6,h6],[a7,b7,c7,d7,e7,f7,g7,h7],[a8,b8,c8,d8,e8,f8,g8,h8]]

        players = {'White':[],'Black':[]}
        self.ChessBoard = Board({'White':{},'Black':{}},boardsquares,players)


        k = King(e8,'Black','k',self.ChessBoard)             
        K = King(e1, 'White','K',self.ChessBoard)
        kings = {'White':K,'Black':k} #remove self reference

        p1 = Pawn(a7,'Black','p1',self.ChessBoard,kings)
        p2 = Pawn(b7,'Black','p2',self.ChessBoard,kings)
        p3 = Pawn(c7,'Black','p3',self.ChessBoard,kings)
        p4 = Pawn(d7,'Black','p4',self.ChessBoard,kings)
        p5 = Pawn(e7,'Black','p5',self.ChessBoard,kings)
        p6 = Pawn(f7,'Black','p6',self.ChessBoard,kings)
        p7 = Pawn(g7,'Black','p7',self.ChessBoard,kings)
        p8 = Pawn(h7,'Black','p8',self.ChessBoard,kings)
        P1 = Pawn(a2,'White','P1',self.ChessBoard,kings)
        P2 = Pawn(b2,'White','P2',self.ChessBoard,kings)
        P3 = Pawn(c2,'White','P3',self.ChessBoard,kings)
        P4 = Pawn(d2,'White','P4',self.ChessBoard,kings)
        P5 = Pawn(e2,'White','P5',self.ChessBoard,kings)
        P6 = Pawn(f2,'White','P6',self.ChessBoard,kings)
        P7 = Pawn(g2,'White','P7',self.ChessBoard,kings)
        P8 = Pawn(h2,'White','P8',self.ChessBoard,kings)
        nq = Knight(b8,'Black','nq',self.ChessBoard,kings)
        nk = Knight(g8,'Black','nk',self.ChessBoard,kings)
        NQ = Knight(b1,'White','NQ',self.ChessBoard,kings)
        NK = Knight(g1,'White','NK',self.ChessBoard,kings)
        rq = Rook(a8,'Black','rq',self.ChessBoard,kings)
        rk = Rook(h8,'Black','rk',self.ChessBoard,kings)
        RQ = Rook(a1,'White','RQ',self.ChessBoard,kings)
        RK = Rook(h1,'White','RK',self.ChessBoard,kings)
        bq = Bishop(c8,'Black','bq',self.ChessBoard,kings)
        bk = Bishop(f8,'Black','bk',self.ChessBoard,kings)
        BQ = Bishop(c1,'White','BQ',self.ChessBoard,kings)
        BK = Bishop(f1,'White','BK',self.ChessBoard,kings)
        Q = Queen(d1,'White','Q',self.ChessBoard,kings)
        q = Queen(d8,'Black','q',self.ChessBoard,kings)

        piece_list = [p1,p2,p3,p4,p5,p6,p7,p8,nq,nk,bq,bk,rq,rk,q,k,P1,P2,P3,P4,P5,P6,P7,P8,NQ,NK,BQ,BK,RQ,RK,Q,K]
        self.ChessBoard.add_pieces(piece_list) #pieces to piece list


        b = Player('PeePee','Black',self.ChessBoard)
        W = Player('PooPoo','White',self.ChessBoard)
        self.WhitePlayer = W
        self.BlackPlayer = b
        
        self.ChessBoard.heat_setup()
        self.ChessBoard.en_passant_setup()
        self.ChessBoard.players = {'White':W,'Black':b}
        self.ChessBoard.current_player = W
        self.ChessBoard.kings = kings

    def make_query(self, player_color, piece_data):
        #print(piece_data)
        piece_i = piece_data['piece_i']
        piece_j = piece_data['piece_j']
        #print("\n\n\n\n",self.ChessBoard.squares[piece_i][piece_j],self.ChessBoard.squares[piece_i][piece_j].occupied)
        if self.ChessBoard.squares[piece_i][piece_j].occupied != False:
            piece_name = self.ChessBoard.squares[piece_i][piece_j].occupied[1]
            if player_color == "black":

                moves_list_temp = self.BlackPlayer.possible_moves()
            else:
                moves_list_temp = self.WhitePlayer.possible_moves()
            #print(moves_list_temp)
            if piece_name in moves_list_temp:
                moves_list_temp = moves_list_temp[piece_name]
                if type(moves_list_temp[0]) is tuple:
                    return moves_list_temp
                moves_list = []
                for l in moves_list_temp:
                    moves_list += l
                #print(moves_list)
                return moves_list
            else:
                return []
        return []
    
    def make_move(self,piece_data):
        source_i = piece_data['source_i']
        source_j = piece_data['source_j']
        move_i = piece_data['move_i']
        move_j = piece_data['move_j']
        if self.ChessBoard.squares[source_i][source_j].occupied != False:
            piece_color, piece_name = self.ChessBoard.squares[source_i][source_j].occupied
            piece = self.ChessBoard.pieces[piece_color][piece_name]
            piece.move_to((move_j,move_i))


# In[217]:


class Custom_Game:
    def __init__(self):
        a1 = square((0,0))
        a2 = square((0,1))
        a3 = square((0,2))
        a4 = square((0,3))
        a5 = square((0,4))
        a6 = square((0,5))
        a7 = square((0,6))
        a8 = square((0,7))
        b1 = square((1,0))
        b2 = square((1,1))
        b3 = square((1,2))
        b4 = square((1,3))
        b5 = square((1,4))
        b6 = square((1,5))
        b7 = square((1,6))
        b8 = square((1,7))
        c1 = square((2,0))
        c2 = square((2,1))
        c3 = square((2,2))
        c4 = square((2,3))
        c5 = square((2,4))
        c6 = square((2,5))
        c7 = square((2,6))
        c8 = square((2,7))
        d1 = square((3,0))
        d2 = square((3,1))
        d3 = square((3,2))
        d4 = square((3,3))
        d5 = square((3,4))
        d6 = square((3,5))
        d7 = square((3,6))
        d8 = square((3,7))
        e1 = square((4,0))
        e2 = square((4,1))
        e3 = square((4,2))
        e4 = square((4,3))
        e5 = square((4,4))
        e6 = square((4,5))
        e7 = square((4,6))
        e8 = square((4,7))
        f1 = square((5,0))
        f2 = square((5,1))
        f3 = square((5,2))
        f4 = square((5,3))
        f5 = square((5,4))
        f6 = square((5,5))
        f7 = square((5,6))
        f8 = square((5,7))
        g1 = square((6,0))
        g2 = square((6,1))
        g3 = square((6,2))
        g4 = square((6,3))
        g5 = square((6,4))
        g6 = square((6,5))
        g7 = square((6,6))
        g8 = square((6,7))
        h1 = square((7,0))
        h2 = square((7,1))
        h3 = square((7,2))
        h4 = square((7,3))
        h5 = square((7,4))
        h6 = square((7,5))
        h7 = square((7,6))
        h8 = square((7,7))

        boardsquares = [[a1,b1,c1,d1,e1,f1,g1,h1],[a2,b2,c2,d2,e2,f2,g2,h2],[a3,b3,c3,d3,e3,f3,g3,h3],[a4,b4,c4,d4,e4,f4,g4,h4]
                        ,[a5,b5,c5,d5,e5,f5,g5,h5],[a6,b6,c6,d6,e6,f6,g6,h6],[a7,b7,c7,d7,e7,f7,g7,h7],[a8,b8,c8,d8,e8,f8,g8,h8]]

        players = {'White':[],'Black':[]}
        self.ChessBoard = Board({'White':{},'Black':{}},boardsquares,players)
        