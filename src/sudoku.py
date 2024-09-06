# imports
import numpy as np
import itertools
import copy as cp
import sys
import os

class Sudoku(object):
    ### sudoku object with solving methods

    def __init__(self,startgrid,verbose=True,logfilename=None,appendlogfile=False):
        ### intializer: assign dimension, starting grid and other useful variables
        # input arguments:
        # - starting grid: a 2D square numpy array (dimension d), with values between 0 and d
        #   (use 0 for unknown values in the grid)
        # - verbose: boolean whether to do printing during solving
        # - logfilename: path to a log file where a record of solving procedures will be kept
        #   (same info as printed to screen if verbose is true) (default: no log file)
        # - appendlogfile: boolean whether to append to log file (if it exists) or overwrite it
        #   (ignored if logfilename is None)

        # check validity of starting grid
        if 'numpy.ndarray' not in str(type(startgrid)):
            print('ERROR: starting grid (type numpy array) required for initialization!')
            print('       Instead, found object of type '+str(type(startgrid)))
            sys.exit()
        if len(startgrid.shape)!=2 or startgrid.shape[0]!=startgrid.shape[1]:
            print('ERROR: starting grid has wrong dimensions!')
            print('       Found shape '+str(startgrid.shape))
            sys.exit()
        if np.sqrt(startgrid.shape[0])-int(np.sqrt(startgrid.shape[0]))>1e-12:
            print('ERROR: only proper squares are supported as grid size!')
            print('       Found shape '+str(startgrid.shape))
            sys.exit()

        # intialize grid properties
        self.size = startgrid.shape[0] # size of the square grid
        self.blocksize = int(np.sqrt(self.size)) # size of a single block
        self.grid = startgrid.astype(int) # 2D-grid with values (0 means unfilled)
        self.candidates = [] # 3D-grid with candidates for each cell
        self.nunfilled = np.power(self.size,2) # number of unfilled cells in the grid (= 0 if solved)
        self.ncands = self.nunfilled*self.size # number of candidates (= number of cells if solved)
        for i in range(self.size):
            self.candidates.append([])
            for j in range(self.size):
                self.candidates[i].append([])
                if self.grid[i,j] == 0:
                    self.candidates[i][j] = list(range(1,self.size+1))
                else:
                    self.candidates[i][j] = [self.grid[i,j]]
                    self.nunfilled -= 1
                    self.ncands -= 8

        # intialize log file
        self.doprint = verbose
        self.dolog = False
        self.logname = None
        if logfilename is not None:
            self.dolog = True
            self.logname = logfilename # log file to keep track of solving procedure
            if(appendlogfile and os.path.exists(logfilename)): 
                self.logfile = open(self.logname,'a') # check if opening for appending works
            else: 
                self.logfile = open(self.logname,'w') # create file
            self.logfile.close()
			
        # initialize flag used for aborting solving process
        self.contin = True
		
    def setbreak(self):
        # set continue parameter to false
        self.contin = False
		
    def setcontinue(self):
        # set continue parameter to true
        self.contin = True

    def writemessage(self,message):
        # write a message to log file and/or stdout
        if self.dolog:
            self.logfile = open(self.logname,'a')
            self.logfile.write(message+'\n')
            self.logfile.close()
        if self.doprint:
            print(message)

    def copy(self,logfilename=None,appendlogfile=False):
        # make a deep copy of a sudoku grid
        # potentially with different log file
        S = Sudoku(np.zeros((self.size,self.size)),verbose=self.doprint,logfilename=logfilename,
                    appendlogfile=appendlogfile)
        S.grid = np.copy(self.grid)
        S.candidates = cp.deepcopy(self.candidates)
        S.nunfilled = self.nunfilled
        S.ncands = self.ncands
        S.contin = self.contin
        return S

    def set(self,S):
        # set self to a deepcopy of S (log file is shared)
        self.size = S.size
        self.blocksize = S.blocksize
        self.grid = S.grid.astype(int)
        self.candidates = [[[int(x) for x in col] for col in row] for row in S.candidates]
        self.nunfilled = S.nunfilled
        self.ncands = S.ncands
        self.doprint = S.doprint
        self.dolog = S.dolog
        self.logname = S.logname
        
    def getgrid(self):
        # get copy of grid for read-only purposes
        return np.copy(self.grid)
    
    def getrow(self, index):
        # get copy of row at position 'index'
        # numbering convention: from 0 until self.size (not included), from top to bottom
        if index<0 or index>self.size:
            print('ERROR: getrow function got unexpected index: '+str(index))
            sys.exit()
        res1 = []; res2 = []
        for i in range(self.size):
            res1.append(self.grid[index,i])
            res2.append(self.candidates[index][i])
        return (res1,res2)
    
    def getcolumn(self, index):
        # get copy of column at position 'index'
        # numbering convention: from 0 until self.size (not included), from left to right
        if index<0 or index>self.size:
            print('ERROR: getcolumn function got unexpected index: '+str(index))
            sys.exit()
        res1 = []; res2 = []
        for i in range(self.size):
            res1.append(self.grid[i,index])
            res2.append(self.candidates[i][index])
        return (res1,res2)
    
    def getblock(self, index1, index2=None):
        # get copy of block
        # case 1: index2 == None: index1 is global block index
        # numbering convention: from 0 until self.size (not included), in reading order
        # case 2: index2 is not None: index1 and index2 are global grid indices
        if (index1<0 or index1>self.size or (index2 is not None and index2<0) 
          or (index2 is not None and index2>self.size)):
            print('ERROR: getblock function got unexpected index: '+str(index1)+','+str(index2)+')')
            sys.exit()
        if index2==None:
            (row,column) = divmod(index1,self.blocksize)
        else:
            row = divmod(index1,self.blocksize)[0]
            column = divmod(index2,self.blocksize)[0]
        res1 = []; res2 = []
        for i in range(self.blocksize*row,self.blocksize*(row+1)):
            for j in range(self.blocksize*column,self.blocksize*(column+1)):
                res1.append(self.grid[i,j])
                res2.append(self.candidates[i][j])
        return (res1,res2)
    
    def getblockindex(self,row,column):
        # get global block index from cell position (row,column)
        blockrow = divmod(row,self.blocksize)[0]
        blockcolumn = divmod(column,self.blocksize)[0]
        blockindex = self.blocksize*blockrow+blockcolumn
        return blockindex
    
    def getgroup(self,label,index,index2=None):
        # generalization of getrow, getcolumn and getblock, useful in looping functions
        if(label=='row'): return self.getrow(index)
        if(label=='column'): return self.getcolumn(index)
        if(label=='block'): return self.getblock(index,index2)

    def getgroupfromcell(self,label,rw,clmn):
        # analogous to getgroup but arguments are interpreted differently
        if(label=='row'): return self.getrow(rw)
        if(label=='column'): return self.getcolumn(clmn)
        if(label=='block'): return self.getblock(rw,clmn)
    
    def getcell(self,grouptype,groupindex,localindex):
        # get cell indices of element number 'localindex' of group number 'groupindex' of type 'grouptype'
        if grouptype=='row':
            rowindex = groupindex
            columnindex = localindex
            return (rowindex,columnindex)
        if grouptype=='column':
            rowindex = localindex
            columnindex = groupindex
            return (rowindex,columnindex)
        if grouptype=='block':
            rowindex = divmod(groupindex,self.blocksize)[0]*self.blocksize+divmod(localindex,self.blocksize)[0]
            columnindex = divmod(groupindex,self.blocksize)[1]*self.blocksize+divmod(localindex,self.blocksize)[1]
            return (rowindex,columnindex)
        print('ERROR: grouptype parameter in getcell function not recognized, found '+str(grouptype))
        
    def setcell(self,rowindex,columnindex,value):
        # fill a cell with a value (if not already filled) and modify counters
        if self.grid[rowindex, columnindex]!=0:
            return (self.nunfilled, self.ncands)
            # to find out where this is used,
            # maybe raise warning or exception instead?
        self.nunfilled -= 1
        self.grid[rowindex, columnindex] = value
        self.ncands -= len(self.candidates[rowindex][columnindex])-1
        self.candidates[rowindex][columnindex] = [value]
        return (self.nunfilled, self.ncands)
    
    def removecandidate(self, rowindex, columnindex, value):
        # remove a candidate (if present) and modify counters
        if value not in self.candidates[rowindex][columnindex]:
            return (self.nunfilled, self.ncands)
            # to find out where this is used,
            # maybe raise warning or exception instead?
        # remove candidate
        self.candidates[rowindex][columnindex].remove(value)
        self.ncands -= 1
        # if only one candidate remains for the current cell, fill it
        if len(self.candidates[rowindex][columnindex])==1:
            candidate = self.candidates[rowindex][columnindex][0]
            return self.setcell(rowindex, columnindex, candidate)
    
    def isvalid(self):
        # check if a sudoku grid does not contain contradictions so far; 
        # zeros (unfilled cells) are ignored.
        for i in range(self.size):
            if not self.groupisvalid(self.getrow(i)[0]):
                return False
            if not self.groupisvalid(self.getcolumn(i)[0]):
                return False
            if not self.groupisvalid(self.getblock(i)[0]):
                return False
        return True
            
    def groupisvalid(self,group):
        # help function for isvalid; check if a group does not contain any contradictions; 
        # zeros are ignored.
        containslist = []
        for i in group:
            if i == 0:
                continue
            if i in containslist:
                return False
            else:
                containslist.append(i)
        return True

    def issolved(self):
        # check if a sudoku is solved
        return (self.isvalid() and self.nunfilled==0)
    
    def reducecandidates(self, solve=True, verbose=False):
        # BASIC solving method (element-based)
        # loop over all elements in the grid and remove candidates 
        # based on row, column and block restrictions.
        # note: when only one candidate remains for a given cell,
        #       the cell is filled with this candidate
        #       (this solving method is also known as 'sole candidate')
        # input arguments:
        # - solve: boolean whether to modify the grid or only return hint
        
        #if verbose: self.writemessage('Running basic reduction method...')
        res = []
        # loop over rows and columns in the grid
        for i in range(self.size):
            for j in range(self.size):
                # skip already filled cells
                if self.grid[i][j] != 0: continue
                # loop over all groups (row, column, block)
                # that this cell belongs to
                row = self.getrow(i)[0]
                col = self.getcolumn(j)[0]
                block = self.getblock(i,j)[0]
                for k, group in enumerate([row, col, block]):
                    # for each number in the group,
                    # if it is also a candidate in the current cell,
                    # that candidate can be removed
                    for number in group:
                        if number in self.candidates[i][j]:
                            groupname = ['row', 'column', 'block'][k]
                            res.append({'method': 'reducecandidates',
                                        'infokeys': ['cell', 'label', 'value'],
                                        'cell': (i,j),
                                        'label': groupname,
                                        'value':int(number)})
                            if solve: self.removecandidate(i, j, number)
        #if verbose:
        #    msg = '{} candidates were removed by basic reduction.'.format(len(res))
        #    self.writemessage(msg)
        return res
                    
    def loopgroups(self, groupfunctions,
            labels=['row','column','block'],
            solve=True, verbose=False):
        # generic looper over all groups in the grid
        # helper function for group-based solving methods below
        # input arguments:
        # - groupfunctions: a list of function names to be called on each group
        # - labels: a list of types of groups to loop over, default all groups
        # - solve: boolean whether to modify the grid or only return hint
        # - verbose: boolean determining level of printouts
        labels = labels[:] # copy to local variable since it might be altered
        groupfunctions = groupfunctions[:] # see above
        # check validity of labels
        for label in labels[:]:
            if label not in ['row', 'column', 'block']:
                msg = 'WARNING: group label "{}" not recognized;'.format(label)
                msg += ' skipping it.'
                print(msg)
                labels.remove(label)
        res = []
        # loop over all groups
        for i in range(self.size):
            for label in labels:
                group, cands = self.getgroup(label, i)
                args = [group, i, label, cands]
                # loop over al functions to be called on each group
                for f in groupfunctions:
                    # part 1: functions applicable to all groups
                    if f=='complement':
                        res += self.complement(*args, solve=solve, verbose=verbose)
                    elif f=='nakedsubset':
                        res += self.nakedsubset(*args, solve=solve, verbose=verbose)
                    elif f=='hiddensubset':
                        res += self.hiddensubset(*args, solve=solve, verbose=verbose)
                    # part 2: functions applicable to rows and columns
                    elif f=='lineblockinteraction': 
                        if label in ['row','column']:
                            res += self.lineblockinteraction(*args, solve=solve, verbose=verbose)
                    # part 3: functions applicable to blocks
                    elif f=='blocklineinteraction': 
                        if label=='block':
                            res += self.blocklineinteraction(*args, solve=solve, verbose=verbose)
                    elif f=='blockblockinteraction':
                        if label=='block':
                            res += self.blockblockhorizontalinteraction(*args,
                                    solve=solve, verbose=verbose)
                            res += self.blockblockverticalinteraction(*args,
                                    solve=solve, verbose=verbose)
                    else:
                        msg = 'WARNING: groupfunction "{}" not recognized,'.format(f)
                        msg += ' skipping it.'
                        print(msg)
        return res
                
    def complement(self, group, groupindex, label, candidates, solve=True, verbose=False):
        # BASIC solving method (group-based)
        # if only one possible position for an element is present within a group, 
        # fill this position with this element
        # (this solving method is also known as 'unique candidate')
        # input arguments:
        # - solve: boolean whether to modify the grid or only return hint
        
        #if verbose: self.writemessage('Running basic complement method...')
        res = []
        # loop over all elements to be filled in the group
        for el in range(1,self.size+1):
            # skip elements already present in the group
            if el in group: continue
            # find all positions where the element is a candidate
            pos = []
            for j in range(self.size):
                if el in candidates[j]: pos.append(j)
            # if only one position, fill it with this element
            if len(pos)==1:
                (row, column) = self.getcell(label, groupindex, pos[0])
                res.append({'method': 'complement',
                            'infokeys': ['cell','label','value'],
                            'cell': (row, column),
                            'label': label,
                            'value': el})
                if solve: self.setcell(row, column, el)
                if verbose:
                    msg = 'Cell ({},{}) was filled'.format(row, column)
                    msg += ' using basic {} complementing.'.format(label)
                    self.writemessage(msg)
        #if verbose and len(res)==0:
        #    msg = '(No cells could be filled using basic {} complementing.)'.format(label)
        #    self.writemessage(msg)
        return res

    def issubset(self, smalllist, biglist):
        # help function for nakedsubset and hiddensubset
        # return values:
        #   -1: not a single element of smalllist in biglist
        #   0: some but not all elements of smalllist in biglist
        #   1: all elements of smalllist in biglist
        nels = 0
        for el in smalllist:
            if el in biglist:
                nels += 1
        if nels==0: return -1
        if nels==len(smalllist): return 1
        return 0

    def nakedsubset(self, group, groupindex, label, candidates, solve=True, verbose=False):
        # ADVANCED method (group-based)
        # if n candidate sets together contain only a set of n numbers, 
        # remove those numbers from all other candidate sets in the group
        # input arguments:
        # - solve: boolean whether to modify the grid or only return hint
        # todo: this method can be even more generalized compared to current implementation:
        #       see e.g. the sets [5,6], [6,8] and [5,8].
        #       there is none of these candidate sets of which all other ones are a subset,
        #       but yet they form a naked triplet.
        #       this is not yet implemented.
        
        #if verbose: self.writemessage('Searching for naked subsets...')
        res = []
        # loop over all candidate sets in the group
        for i in range(self.size-1):
            candsi = candidates[i]
            # skip cells with only one candidate left
            if len(candsi)<2: continue
            # loop over all other candidate sets in the group
            subindices = [i]
            for j in range(self.size):
                if j==i: continue
                candsj = candidates[j]
                if len(candsj)<2: continue
                if len(candsj)>len(candsi): continue
                # check if candidates at position j are a subset
                # (i.e. fully contained in or equal to)
                # of candidates at position i
                sub = self.issubset(candsj, candsi)
                if sub==1: subindices.append(j)
            # if the number of subsets is equal to the number of candidates,
            # those candidates can be removed from all other cells in the group
            if len(subindices) == len(candsi):
                useful = False
                # loop over other cells in the group
                for j in range(self.size):
                    if j in subindices: continue
                    (row, column) = self.getcell(label, groupindex, j)
                    for cand in candsi:
                        if cand in self.candidates[row][column]: useful = True
                        if solve: self.removecandidate(row, column, cand)
                if useful:
                    cells = []
                    for s in subindices: cells.append(self.getcell(label, groupindex, s))
                    res.append({'method': 'nakedsubset',
                                'infokeys': ['grouplabel','groupindex','indices','values','cells'],
                                'grouplabel':label, 'groupindex':groupindex,
                                'indices':subindices, 'values':candsi, 'cells':cells})
                    if verbose: self.writemessage('Found naked subset in cells {}'.format(cells))
        #if verbose and len(res)==0: self.writemessage('(no naked subsets found.)')
        return res
                
    def hiddensubset(self, group, groupindex, label, candidates, solve=True, verbose=False):
        # ADVANCED method (group-based)
        # if a subset of n candidates is shared between exactly n cells, 
        # remove all other candidates from these cells
        # input arguments:
        # - solve: boolean whether to modify the grid or only return hint
        
        #if verbose: self.writemessage('Searching for hidden subsets...')
        res = []
        # make a list of unique candidates
        # in all cells that are not already filled
        allcands = []
        for candset in candidates:
            if len(candset)<2: continue
            allcands += candset
        uniquecands = list(set(allcands))
        # build all possible subsets of all unique candidates
        subsets = list(itertools.combinations(uniquecands, 2))
        for j in range(3, len(uniquecands)+1):
            toappend = list(itertools.combinations(uniquecands, j))
            for subset in toappend: subsets.append(subset)
        # loop over all subsets
        for subset in subsets:
            # find cells where this subset is (at least partially) present
            shareindices = []
            for j in range(self.size):
                sub = self.issubset(subset, candidates[j])
                if(sub==0 or sub==1): shareindices.append(j)
            # if a subset of size n is shared by n cells,
            # remove all other candidates from these cells
            if(len(subset)==len(shareindices)):
                useful = False
                for k in shareindices:
                    (row, column) = self.getcell(label, groupindex, k)
                    for cand in range(1, self.size+1):
                        if cand in subset: continue
                        if cand in self.candidates[row][column]: useful = True
                        if solve: self.removecandidate(row, column, cand)
                if useful:
                    cells = []
                    for s in shareindices: cells.append(self.getcell(label, groupindex, s))
                    res.append({'method': 'hiddensubset',
                                'infokeys': ['grouplabel','groupindex','indices','values','cells'],
                                'grouplabel':label, 'groupindex':groupindex,
                                'indices':shareindices, 'values':subset, 'cells':cells})
                    if verbose: self.writemessage('Found hidden subset in cells '+str(cells))
        #if verbose and len(res)==0: self.writemessage('(no hidden subsets found.)')
        return res
                   
    def blocklineinteraction(self, block, blockindex, label, blockcands,
            solve=True, verbose=False):
        # ADVANCED solving method (block-based)
        # if a candidate occurs in only one row/column within a block, 
        # remove it from the rest of the row/column
        # input arguments:
        # - solve: boolean whether to modify the grid or only return hint
        
        #if verbose: self.writemessage('Searching for block-line interactions...')
        res = []
        # loop over all elements to be filled
        for el in range(1,self.size+1):
            if el in block: continue
            # find all rows and columns where this element is a candidate
            # (within this block)
            rows = []
            columns = []
            for i in range(self.size):
                if el not in blockcands[i]: continue
                row, column = self.getcell('block', blockindex, i)
                rows.append(row)
                columns.append(column)
            # find unique rows and columns
            unique_rows = list(set(rows))
            unique_columns = list(set(columns))
            # case where all candidates are in one row
            if len(unique_rows)==1:
                useful = False
                row = unique_rows[0]
                for column in range(self.size):
                    if column in unique_columns: continue
                    if el in self.candidates[row][column]: useful = True
                    if solve: self.removecandidate(row, column, el)
                if useful:
                    cells = []
                    for s in unique_columns: cells.append((row, s))
                    res.append({'method':'blocklineinteraction',
                                'infokeys':['blockindex','linelabel','lineindex','value','cells'],
                                'blockindex':blockindex, 'linelabel':'row', 'lineindex':row,
                                'value':el, 'cells':cells})
                    if verbose: self.writemessage('Found block-row interaction')
            # case where all candidates are in one column
            if len(unique_columns)==1:
                useful = False
                column = unique_columns[0]
                for row in range(self.size):
                    if row in unique_rows: continue
                    if el in self.candidates[row][column]: useful = True
                    if solve: self.removecandidate(row, column, el)
                if useful: 
                    cells = []
                    for s in unique_rows: cells.append((s, column))
                    res.append({'method': 'blocklineinteraction',
                                'infokeys': ['blockindex','linelabel','lineindex','value','cells'],
                                'blockindex': blockindex, 'linelabel': 'column',
                                'lineindex': column, 'value': el, 'cells': cells})
                    if verbose: self.writemessage('Found block-column interaction')
        #if verbose and len(res)==0: self.writemessage('(no block-line interactions found.)')
        return res 
                                
    def lineblockinteraction(self, line, lineindex, linelabel, linecands,
            solve=True, verbose=False):
        # ADVANCED solving method (row/column-based)
        # if a candidate occurs in only one block within a row/column, 
        # remove it from the rest of the block
        # input arguments:
        # - solve: boolean whether to modify the grid or only return hint
        
        #if verbose: self.writemessage('Searching for line-block interactions...')
        res = []
        # loop over all elements to be filled
        for el in range(1,self.size+1):
            if el in line: continue
            # find all blocks where this element is a candidate
            # (within this line)
            blocks = []
            for i in range(self.size):
                if el not in linecands[i]: continue
                row, column = self.getcell(linelabel, lineindex, i)
                blocks.append(self.getblockindex(row,column))
            unique_blocks = list(set(blocks))
            # case where all candidates occur within a single block
            if len(unique_blocks)==1:
                useful = False
                block = unique_blocks[0]
                # loop over all other cells in the block
                firstrow, firstcolumn = np.multiply(divmod(block, self.blocksize), self.blocksize)
                for row in range(firstrow, firstrow+self.blocksize):
                    for column in range(firstcolumn, firstcolumn+self.blocksize):
                        if linelabel=='row' and row==lineindex: continue
                        if linelabel=='column' and column==lineindex: continue
                        if el in self.candidates[row][column]: useful = True
                        if solve: self.removecandidate(row, column, el)
                if useful:
                    res.append({'method': 'lineblockinteraction',
                                'infokeys': ['lineindex','linelabel','blockindex','value','cells'],
                                'lineindex': lineindex, 'linelabel':linelabel,
                                'blockindex': block, 'value': el, 'cells': cells})
                    if verbose: self.writemessage('Found line-block interaction')
        #if verbose and len(res)==0: self.writemessage('(no line-block interactions found.)')
        return res
                                
    def blockblockhorizontalinteraction(self, group, groupindex, label, candidates,
            solve=True, verbose=False):
        # ADVANCED solving method (block-based)
        # if a candidate occurs in only two rows in two horizontally aligned blocks, 
        # remove it from the remaining positions in those rows
        # input arguments:
        # - solve: boolean whether to modify the grid or only return hint
        # todo: generalize to grids of different sizes (?)
        
        #if verbose: self.writemessage('Searching for horizontal block-block interactions.')
        res = []
        # loop over all other blocks than the one provided as argument
        for i in range(self.size):
            if i<=groupindex: continue
            # (note: the above should be != instead of <= to be fully general,
            #  but in practice this is always run in a loop, so it is ok)
            # ignore blocks that are not horizontally aligned
            firstrow = self.getcell(label, groupindex, 0)[0]
            testrow = self.getcell(label, i, 0)[0]
            if testrow!=firstrow: continue
            groupi, candidatesi = self.getblock(i)
            # loop over all elements to be filled
            for el in range(1, self.size+1):
                if(el in group or el in groupi): continue
                # find unique rows and columns where this element is a candidate
                # (within these two blocks)
                rows = []
                columns = []
                for j in range(self.size):
                    if el in candidates[j]:
                        row,column = self.getcell(label, groupindex, j)
                        if row not in rows: rows.append(row)
                        if column not in columns: columns.append(column)
                    if el in candidatesi[j]:
                        row,column = self.getcell(label, i, j)
                        if row not in rows: rows.append(row)
                        if column not in columns: columns.append(column)
                # case where candidates are grouped in only two rows
                if len(rows)==2:
                    useful = False
                    for j in range(self.size):
                        if j in columns: continue
                        if el in self.candidates[rows[0]][j]:
                            useful = True
                            if solve: self.removecandidate(rows[0], j, el)
                        if el in self.candidates[rows[1]][j]:
                            useful = True
                            if solve: self.removecandidate(rows[1], j, el)
                    if useful:
                        cells = []
                        for j in range(self.size):
                            cells.append((rows[0],j))
                            cells.append((rows[1],j))
                        res.append({'method': 'blockblockhorizontalinteraction',
                                    'infokeys': ['block1index','block2index','value','cells'],
                                    'block1index': groupindex, 'block2index': i,
                                    'value':el, 'cells':cells})
                        if verbose: self.writemessage('Found horizontal block-block interaction')
        #if verbose and len(res)==0:
        #    self.writemessage('(no horizontal block-block interaction found.)')
        return res
        
    def blockblockverticalinteraction(self, group, groupindex, label, candidates,
            solve=True, verbose=False):
        # ADVANCED solving method (block-based)
        # if a candidate occurs in only two columns in two vertically aligned blocks, 
        # remove it from the remaining positions in those columns
        # input arguments:
        # - solve: boolean whether to modify the grid or only return hint
        
        #if verbose: self.writemessage('Searching for vertical block-block interactions...')
        res = []
        # loop over al other blocks than the one provided as argument
        for i in range(self.size):
            if i<=groupindex: continue
            # (note: the above should be != instead of <= to be fully general,
            #  but in practice this is always run in a loop, so it is ok)
            # ignore blocks that are not vertically aligned
            firstcolumn = self.getcell(label, groupindex, 0)[1]
            testcolumn = self.getcell(label, i, 0)[1]
            if testcolumn!=firstcolumn: continue
            groupi,candidatesi = self.getblock(i)
            # loop over all elements to be filled
            for el in range(1,self.size+1):
                if(el in group or el in groupi): continue
                # find unique rows and columns where this element is a candidate
                # (within these two blocks)
                rows = []
                columns = []
                for j in range(self.size):
                    if el in candidates[j]:
                        row,column = self.getcell(label, groupindex, j)
                        if row not in rows: rows.append(row)
                        if column not in columns: columns.append(column)
                    if el in candidatesi[j]:
                        row,column = self.getcell(label, i, j)
                        if row not in rows: rows.append(row)
                        if column not in columns: columns.append(column)
                # case where candidates are grouped in only two columns
                if len(columns)==2:
                    useful = False
                    for j in range(self.size):
                        if j in rows: continue
                        if el in self.candidates[j][columns[0]]:
                            useful = True
                            if solve: self.removecandidate(j, columns[0], el)
                        if el in self.candidates[j][columns[1]]:
                            useful = True
                            if solve: self.removecandidate(j, columns[1], el)
                    if useful:
                        cells = []
                        for j in range(self.size): 
                            cells.append((j,columns[0]))
                            cells.append((j,columns[1]))
                        res.append({'method': 'blockblockverticalinteraction',
                                    'infokeys': ['block1index','block2index','value','cells'],
                                    'block1index': groupindex, 'block2index': i,
                                    'value': el,'cells': cells})
                        if verbose: self.writemessage('Found vertical block-block interaction')
        #if verbose and len(res)==0:
        #    self.writemessage('(no vertical block-block interaction found.)')
        return res
    
    def swordfishcolumns(self, solve=True, verbose=False):
        # HYPERADVANCED solving method (grid-based)
        # find a swordfish pattern in the columns of the grid 
        # and eliminate suitable candidates from the rows
        # input arguments:
        # - solve: boolean whether to modify the grid or only return hint
        # todo: maybe rewrite in this style: https://www.learn-sudoku.com/swordfish.html
        # todo: it seems unnecessary to split into rows and column separately
        # STEP 1: find all columns that have exactly two spots for a given candidate
        res = []
        for el in range(1,self.size+1):
            cols = []
            rows = []
            for i in range(self.size):
                rowsi = []
                for j in range(self.size):
                    if el in self.candidates[j][i]: rowsi.append(j)
                rows.append(rowsi)
                if len(rowsi)==2:
                    cols.append(i)
            if len(cols)<2: continue
            # STEP 2: find a subset of properly aligning columns
            # STEP 2a: find all subsets of suitable columns
            colssubsets = list(itertools.combinations(cols,2))
            for i in range(3,len(cols)+1):
                toappend = list(itertools.combinations(cols,i))
                for subset in toappend: colssubsets.append(subset)
            for colssubset in colssubsets:
                # STEP 2b: for each subset, find unique rows
                uniquerows = []
                for j in colssubset:
                    if rows[j][0] not in uniquerows: uniquerows.append(rows[j][0])
                    if rows[j][1] not in uniquerows: uniquerows.append(rows[j][1])
                if len(uniquerows)!=len(colssubset): continue
                # STEP 3: remove candidates from these rows
                # that do not belong to the swordfish pattern
                # STEP 3a: define pattern in suitable format
                pattern = []
                for j in colssubset:
                    for i in rows[j]:
                        pattern.append((i,j))
                # STEP 3b: remove from all positions in unique rows except swordfish
                useful = False
                for i in uniquerows:
                    for j in range(self.size):
                        if((i,j) not in pattern): 
                            if el in self.candidates[i][j]: 
                                useful = True
                            if solve: self.removecandidate(i,j,el)
                if useful: 
                    res.append({'method': 'swordfishcolumns',
                                'infokeys': ['value','pattern'],
                                'value':el, 'pattern':pattern})
                    if verbose: self.writemessage('Found column-wise swordfish pattern')
        return res
                        
    def swordfishrows(self, solve=True, verbose=False):
        # HYPERADVANCED solving method (grid-based)
        # mirror of swordfishcolumns
        res = []
        for el in range(1,self.size+1):
            cols = []
            rows = []
            for i in range(self.size):
                colsi = []
                for j in range(self.size):
                    if el in self.candidates[i][j]: colsi.append(j)
                cols.append(colsi)
                if len(colsi)==2:
                    rows.append(i)
            if len(rows)<2: continue
            rowssubsets = list(itertools.combinations(rows,2))
            for i in range(3,len(rows)+1):
                toappend = list(itertools.combinations(rows,i))
                for subset in toappend: rowssubsets.append(subset)
            for rowssubset in rowssubsets:
                uniquecols = []
                for j in rowssubset:
                    if cols[j][0] not in uniquecols: uniquecols.append(cols[j][0])
                    if cols[j][1] not in uniquecols: uniquecols.append(cols[j][1])
                if len(uniquecols)!=len(rowssubset): continue
                pattern = []
                for i in rowssubset:
                    for j in cols[i]:
                            pattern.append((i,j))
                useful = False
                for j in uniquecols:
                    for i in range(self.size):
                        if((i,j) not in pattern): 
                            if el in self.candidates[i][j]: useful = True
                            if solve: self.removecandidate(i,j,el)
                if useful: 
                    res.append({'method':'swordfishrows','infokeys':['value','pattern'],
                                'value':el,'pattern':pattern})
                    if verbose: self.writemessage('Found row-wise swordfish pattern')
        return res

    def intersect(self, coords1, coords2):
        # help function for XY wing
        # returns True if coord1 and coords2 intersect,
        # i.e. if they are in the same row, column or block
        (rw1,clmn1) = coords1
        (rw2,clmn2) = coords2
        if rw1==rw2: return True
        if clmn1==clmn2: return True
        if self.getblockindex(rw1,clmn1)==self.getblockindex(rw2,clmn2): return True
        return False

    def shareone(self, cands1, cands2):
        # help function for XY wing
        # note: cands1 and cands2 are expected to be lists/arrays of length 2
        # returns: the unique element shared between cands1 and cands2, or -1 otherwise
        if(cands2[0] in cands1 and not cands2[1] in cands1): return cands2[0]
        if(cands2[0] not in cands1 and cands2[1] in cands1): return cands2[1]
        return -1

    def xywing(self, solve=True, verbose=False):
        # HYPERADVANCED solving method (grid-based)
        # find XY pattern and remove candidate from cells that intersect with both wings
        # input arguments:
        # - solve: boolean whether to modify the grid or only return hint
        res = []
        # loop over all cells in the grid
        for row1 in range(self.size):
            for column1 in range(self.size):
                # skip cells that do not have exactly 2 candidates
                if not len(self.candidates[row1][column1])==2: continue
                cands1 = self.candidates[row1][column1]
                shareone = []
                # loop over all other cells in the grid
                # that have exactly two candidates and interset with the first one
                for row2 in range(self.size):
                    for column2 in range(self.size):
                        if not len(self.candidates[row2][column2])==2: continue
                        if not self.intersect((row1,column1), (row2,column2)): continue
                        cands2 = self.candidates[row2][column2]
                        # find the unique element shared between the candidates
                        # of both cells
                        share = self.shareone(cands1,cands2)
                        if share>0: shareone.append((row2, column2))
                # if less than two cells that share a unique element
                # with the given cell are found, skip.
                if len(shareone)<2: continue
                # loop over pairs of cells that share a unique element
                # with the given cell
                for c1 in range(len(shareone)-1):
                    for c2 in range(c1+1, len(shareone)):
                        (rw2,clmn2) = shareone[c1]
                        (rw3,clmn3) = shareone[c2]
                        # they must not intersect
                        if self.intersect((rw3,clmn3), (rw2,clmn2)): continue
                        # they must share a unique element
                        # that is not in the candidates of the given cell
                        cands2 = self.candidates[rw2][clmn2]
                        cands3 = self.candidates[rw3][clmn3]
                        share = self.shareone(cands2, cands3)
                        if(share<0 or share in cands1): continue
                        # found an xy-wing, now check if it is useful
                        # for removing other candidates
                        useful = False
                        for rwa in range(self.size):
                            for clmna in range(self.size):
                                intersect = ( 
                                    self.intersect((rwa,clmna),(rw2,clmn2))
                                    and self.intersect((rwa,clmna),(rw3,clmn3))
                                )
                                if not intersect: continue
                                if(share in self.candidates[rwa][clmna]): useful = True
                                if solve: self.removecandidate(rwa, clmna, share)
                        if useful: 
                            res.append({'method':'xywing','infokeys':['cells','value'],
                                        'cells':[(row1,column1),(rw2,clmn2),(rw3,clmn3)],
                                        'value':share})
                            if verbose: self.writemessage('Found XY-wing')
        return res

    def uniquerectangle(self, solve=True, verbose=False):
        # HYPERADVANCED solving method (grid-based)
        # if the sudoku is assumed to have a unique solution,
        # there cannot be a rectangle (2 rows, 2 columns, 2 blocks)
        # with the same two candidates at each of the corner points
        res = []
        # loop over all cells in the grid
        for row1 in range(self.size):
            for column1 in range(self.size):
                # skip cells that do not have exactly 2 candidates
                if not len(self.candidates[row1][column1])==2: continue
                cands1 = self.candidates[row1][column1]
                # find cells in the same row that have exactly the same two candidates
                same_row_cols = []
                rowcands = self.getrow(row1)[1]
                for j in range(self.size):
                    if j==column1: continue
                    if set(rowcands[j])==set(cands1): same_row_cols.append(j)
                if len(same_row_cols)==0: continue
                # find the cells in the same column that have exactly the same two candidates
                same_col_rows = []
                colcands = self.getcolumn(column1)[1]
                for j in range(self.size):
                    if j==row1: continue
                    if set(colcands[j])==set(cands1): same_col_rows.append(j)
                if len(same_col_rows)==0: continue
                # loop over all combinations of second and third cells
                b1 = self.getblockindex(row1, column1)
                for same_row_col in same_row_cols:
                    b2 = self.getblockindex(row1, same_row_col)
                    for same_col_row in same_col_rows:
                        b3 = self.getblockindex(same_col_row, column1)
                        # the three cells must be in two blocks
                        # (i.e. not in three different blocks)
                        if len(set([b1, b2, b3]))>2: continue
                        # the fourth cell must not be filled
                        # and must contain at least one of the two candidates
                        cands4 = self.candidates[same_col_row][same_row_col]
                        if len(cands4)==1: continue
                        cands_to_remove = []
                        if cands1[0] in cands4: cands_to_remove.append(cands1[0])
                        if cands1[1] in cands4: cands_to_remove.append(cands1[1])
                        if len(cands_to_remove)>0:
                            res.append({'method':'uniquerectangle',
                                        'infokeys':['cells', 'target', 'values'],
                                        'cells':[
                                            (row1, column1),
                                            (row1, same_row_col),
                                            (same_col_row, column1),
                                            (same_col_row, same_row_col)],
                                        'target': (same_col_row, same_row_col),
                                        'values': cands_to_remove})
                            if solve:
                                for cand in cands_to_remove:
                                    self.removecandidate(same_col_row, same_row_col, cand)
                            if verbose: self.writemessage('Found unique rectangle')
        return res


    def forcingchain(self, solve=True, verbose=False):
        # HYPERADVANCED solving method (grid-based)
        # solve for all possibilities of a certain cell and check recurring patterns
        # input arguments:
        # - solve: boolean whether to modify the grid or only return hint
        res = []
        if verbose: self.writemessage('Attempting forcing chain...')
        # loop over all cells in the grid
        for i in range(self.size):
            for j in range(self.size):
                cands = self.candidates[i][j]
                if len(cands)==1: continue
                # loop over all candidates for this cell
                scopies = []
                for k,cand in enumerate(cands):
                    # special abortion check
                    if not self.contin: return [-1]
                    # make a copy and set the given candidate in the given cell
                    S = self.copy(logfilename=self.logname+'_'+str(k), appendlogfile=True)
                    if verbose:
                        msg = 'Checking candidate {} for cell {}'.format(cand, (i,j))
                        self.writemessage(msg)
                    S.setcell(i, j, cand)
                    # call solver on the sudoku but disable forcing chain method,
                    # since only one level of 'guessing' is allowed
                    # (else it is equivalent to brute force)
                    S.solve(useforcingchain=False)
                    scopies.append(S)
                if len(scopies)==0: continue
                # find candidates that were removed
                # in all of the different hypotheses
                candstoremove = cp.deepcopy(self.candidates)
                removelist = []
                useful = False
                # loop over all other cells than the given cell
                for ci in range(self.size):
                    for cj in range(self.size):
                        if(ci==i and cj==j): continue
                        # check if any of the copies still contains a given value
                        # (if so, erase it from candidates that can be removed;
                        #  only candidates that are not erased,
                        #  because they are in none of the copies,
                        #  can effectively be removed)
                        for scopy in scopies:
                            for val in scopy.candidates[ci][cj]:
                                if val in candstoremove[ci][cj]:
                                    candstoremove[ci][cj].remove(val)
                        if len(candstoremove[ci][cj])>0:
                            useful = True
                            for val in candstoremove[ci][cj]:
                                removelist.append((ci, cj, val))
                                if solve: self.removecandidate(ci, cj, val)
                if useful:
                    res.append({'method': 'forcingchain',
                                'infokeys': ['cell','results'],
                                'cell': (i,j), 'results': removelist})
                    if verbose: self.writemessage('Forcing chain found recurring pattern!')
        if verbose and len(res)>0: 
            self.writemessage('Forcing chain finished, continue regular solving...')
        return res
                    

    def solve_basic(self, verbose=False):
        ### helper function for full solver
        # including only basic solving methods
        # repeated in a loop until no further reduction is possible
        ncands = self.ncands
        self.reducecandidates(verbose=verbose)
        self.loopgroups(['complement'], verbose=verbose)
        if verbose: self.writemessage('Number of remaining candidates '+str(self.ncands))
        while self.ncands < ncands:
            ncands = self.ncands
            self.reducecandidates(verbose=verbose)
            self.loopgroups(['complement'], verbose=verbose)
            if verbose: self.writemessage('Number of remaining candidates '+str(self.ncands))
        return ncands

    def solve_advanced(self, verbose=False):
        ### helper function for full solver
        # including solving methods up to advanced level
        # repeated in a loop until no further reduction is possible
        ncands = self.ncands
        self.solve_basic(verbose=verbose)
        self.loopgroups(['nakedsubset','hiddensubset','blocklineinteraction',
                         'lineblockinteraction','blockblockinteraction'],
                         verbose=verbose)
        self.solve_basic(verbose=verbose)
        if verbose: self.writemessage('Number of remaining candidates '+str(self.ncands))
        while self.ncands < ncands:
            ncands = self.ncands
            self.loopgroups(['nakedsubset','hiddensubset','blocklineinteraction',
                             'lineblockinteraction','blockblockinteraction'],
                             verbose=verbose)
            self.solve_basic(verbose=verbose)
            if verbose: self.writemessage('Number of remaining candidates: '+str(self.ncands))
        return ncands

    def solve_hyperadvanced(self, verbose=False):
        ### helper function for full solver
        # including solving methods up to hyperadvanced level (but no forcing chain yet)
        # repeated in a loop until no further reduction is possible
        ncands = self.ncands
        self.solve_advanced(verbose=verbose)
        self.swordfishcolumns(verbose=verbose)
        self.swordfishrows(verbose=verbose)
        self.xywing(verbose=verbose)
        self.uniquerectangle(verbose=verbose)
        self.solve_advanced(verbose=verbose)
        if verbose: self.writemessage('Number of remaining candidates: '+str(self.ncands))
        while self.ncands < ncands:
            ncands = self.ncands
            self.swordfishcolumns(verbose=verbose)
            self.swordfishrows(verbose=verbose)
            self.xywing(verbose=verbose)
            self.uniquerectangle(verbose=verbose)
            self.solve_advanced(verbose=verbose)
            if verbose: self.writemessage('Number of remaining candidates: '+str(self.ncands))

    def solve(self, useforcingchain=True, usebruteforce=False, recursiondepth=0):
        ### main method grouping all solving methods 
        ### and calling them in increasing order of complexity
        # - useforcingchain: boolean whether to use forcing chain method
        #   (is set to false when calling solve from forcing chain 
        #    since only one recursion level allowed)
        # - usebruteforce: boolean whether to use brute force method
        # - recursiondepth: int representing level of recursion,
        #   in order to prevent infinite recursion loop for insolvable sudokus
        #   (only used for brute force solving method)

        self.writemessage('Start solving method on the following sudoku:'+'\n'+self.tostring())
        ncands = self.ncands # use ncands to keep track of changes made by each method
        self.writemessage('number of initial candidates: '+str(ncands))
        # STEP 1: basic methods
        self.writemessage('Starting solving procedure using basic methods...')
        self.solve_basic(verbose=True)
        self.writemessage('Basic methods finished.\n')
        (outputcode,message) = self.terminate()
        if outputcode!=0: return (outputcode,message)
        # STEP 2: advanced methods
        self.writemessage('Start using more advanced methods...')
        self.solve_advanced(verbose=True)
        self.writemessage('Advanced methods finished.\n')
        (outputcode,message) = self.terminate()
        if outputcode!=0: return (outputcode,message)
        # STEP 3: hyperadvanced methods
        self.writemessage('Start using hyperadvanced methods...')
        self.solve_hyperadvanced(verbose=True)
        self.writemessage('Hyperadvanced methods finished.\n')
        (outputcode,message) = self.terminate()
        if outputcode!=0: return (outputcode,message)
        # STEP 4: forcing chain
        if useforcingchain:
            self.writemessage('Start using forcing chain...')
            ncands = self.ncands
            self.forcingchain(verbose=True)
            self.solve_hyperadvanced(verbose=True)
            while self.ncands < ncands:
                ncands = self.ncands
                self.forcingchain(verbose=True)
                self.solve_hyperadvanced(verbose=True)
            (outputcode,message) = self.terminate()
            if outputcode!=0: return (outputcode,message)
        # STEP 5: give up or use brute force
        msg = 'Unable to solve sudoku with presently implemented methods...\n'
        msg += 'Got up to this point: \n'
        msg += self.tostring()
        self.writemessage(msg)
        if not usebruteforce: return (outputcode,message)
        if recursiondepth>10: 
            self.writemessage('Maximum recursion depth reached')
            return (outputcode,message)
        self.writemessage('Starting brute force methods...')
        (outcode,message) = self.solvebruteforce(recursiondepth=recursiondepth)
        return (outcode,message)

    def solvebruteforce(self, recursiondepth=0):
        # fill a cell by random guessing and recursively call solver

        # find (one of) the cell(s) with minimum number of candidates
        rowmin = 0; colmin = 0; candmin = self.size+1
        for i in range(self.size):
            for j in range(self.size):
                ncands = len(self.candidates[i][j])
                if(ncands<candmin and ncands>=2):
                    candmin = len(self.candidates[i][j])
                    rowmin = i; colmin = j
        # loop over candidates for this minimum-candidate cell
        for cand in self.candidates[rowmin][colmin]:
            self.writemessage(
                'row and column indices of cell with least candidates: '
                + str(rowmin)+','+str(colmin)+'\n'
                + 'candidates are: '+str(self.candidates[rowmin][colmin])+'\n'
                + 'now trying: '+str(cand)+'\n')
            # make a copy and set the cell to this candidate
            S = self.copy(logfilename=self.logname, appendlogfile=True)
            S.setcell(rowmin, colmin, cand)
            (outcode,message) = S.solve(usebruteforce=True, recursiondepth=recursiondepth+1)
            # if this leads to the correct solution, return
            if outcode==1:
                self.set(S)
                return (outcode,message)
        # if none of the above led to the correct solution,
        # a mistake must have been made in one of the previous steps
        return (-1,'All options invalid, go one step back...')
        
    def terminate(self):
        # check termination conditions and print final output to screen
        # output codes:
        #       -1: invalid sudoku detected, stop processing
        #       0: sudoku partially solved, continue processing
        #       1: sudoku fully solved, stop processing
        if not self.isvalid():
            message = 'ERROR: sudoku is invalid \n'
            message += '-> when running in brute force mode, this is part of the standard workflow \n'
            message += '-> if not, check solving methods for bugs or input for typos!\n'
            self.writemessage(message)
            return (-1,message)
        if self.nunfilled==0:
            message = 'Sudoku was solved successfully!\n'+self.tostring()
            self.writemessage(message)
            return (1,message)
        message = 'The sudoku at this point:\n'+self.tostring()
        self.writemessage(message)
        return (0,message)
    
    def tostring(self):
        # useful method for printing the grid in readable format
        gridstring = '- '*(self.size+self.blocksize+1)+'\n'
        for i in range(self.blocksize):
            for l in range(self.blocksize):
                gridstring += '| '
                for j in range(self.blocksize):
                    for k in range(self.blocksize):
                        val = int(self.grid[i*self.blocksize+l,j*self.blocksize+k])
                        if val!=0: gridstring += str(val)+' '
                        else: gridstring += '  '
                    gridstring += '| '
                gridstring += '\n'
            gridstring += '- '*(self.size+self.blocksize+1)+'\n'
        return gridstring
