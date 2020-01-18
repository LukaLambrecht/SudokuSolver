# -*- coding: utf-8 -*-

### PYTHON SCRIPT FOR SUDOKU SOLVING ###
# This script implements a class containing a Sudoku grid and related variables and functions useful for solving it.
# Main use: a very basic GUI class is implemented as well, so running the solver should be straightforward.
# Use from the command line: 
#       - define a two-dimensional python list (called e.g. 'initialvalues') containing the initial values, and 0 for empty cells.
#       - create a Sudoku object using 'S = Sudoku(initialvalues)'
#       - call the main solving method 'S.solve()'
#       - the solved grid is available through 'S.getgrid()'

# MAIN REFERENCES for the implemented methods
# https://www.kristanix.com/sudokuepic/sudoku-solving-techniques.php
# https://www.learn-sudoku.com/advanced-techniques.html

# KNOWN ISSUES OR FORESEEN IMPROVEMENTS
#       - The algorithm for block-block interaction is perhaps not the most general one if self.size > 9.
#       - The following algorithms were not yet implemented: XY-wing, unique rectangle.
#         However, the combination of the current algorithms is already very, very powerful.
#       - The content of the log file should be integrated in the GUI one way or another.
#         At this point only very minimal information is printed to the message box in the GUI.
#       - Currently only one saved grid is supported which is automatially overwritten if the 'Save' button is clicked.
#         This could be generalized using a dedicated save and load window.
#       - Need to implement more checks on input when using GUI.
#       - Support for 4x4, 16x16, etc. grids is in principle included in the code but has not been checked yet.
#         Also, this is not supported in the GUI yet.
 
import numpy as np
import itertools
import sys

class Sudoku:
    def __init__(self,startgrid):
        # intializer: assign dimension, starting grid and other useful variables
        if 'numpy.ndarray' not in str(type(startgrid)):
            print('ERROR: starting grid (type numpy array) required for initialization!')
            print('       Instead, found object of type '+str(type(startgrid)))
            sys.exit()
        if len(startgrid.shape)!=2 or startgrid.shape[0]!=startgrid.shape[1]:
            print('ERROR: starting grid has wrong dimensions!')
            print('       Found shape '+str(startgrid.shape))
        if np.sqrt(startgrid.shape[0])-int(np.sqrt(startgrid.shape[0]))>1e-12:
            print('ERROR: only proper squares are supported as grid size!')
            sys.exit()
        self.size = startgrid.shape[0] # size of the square grid
        self.blocksize = int(np.sqrt(self.size)) # size of a single block
        self.grid = startgrid # 2D-grid with values (0 means unfilled)
        self.candidates = [] # 3D-grid with candidates for each cell
        self.nunfilled = np.power(self.size,2) # number of unfilled cells in the grid (= 0 if solved)
        self.ncands = self.nunfilled*self.size # number of candidates (= number of cells if solved)
        for i in range(self.size):
            self.candidates.append([])
            for j in range(self.size):
                self.candidates[i].append([])
                if self.grid[i,j] == 0:
                    self.candidates[i][j] = range(1,self.size+1)
                else:
                    self.candidates[i][j] = [self.grid[i,j]]
                    self.nunfilled -= 1
                    self.ncands -= 8
        self.logname = 'sudokulog.txt' # log file to keep track of solving procedure
        self.logfile = open(self.logname,'w+') # create file
        self.logfile.close() # close file for safety (open it only just before writing)
        
    def getgrid(self):
        # get copy of grid for read-only purposes
        return np.copy(self.grid)
    
    def getrow(self,index):
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
    
    def getcolumn(self,index):
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
    
    def getblock(self,index1,index2=None):
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
        if self.grid[rowindex,columnindex]!=0:
            return (self.nunfilled,self.ncands)
        self.nunfilled -= 1
        self.grid[rowindex,columnindex] = value
        self.ncands -= len(self.candidates[rowindex][columnindex])-1
        self.candidates[rowindex][columnindex] = [value]
        return (self.nunfilled,self.ncands)
    
    def removecandidate(self,rowindex,columnindex,value):
        # remove a candidate (if present) and modify counters
        if value not in self.candidates[rowindex][columnindex]:
            return (self.nunfilled,self.ncands)
        self.candidates[rowindex][columnindex].remove(value)
        self.ncands -= 1
        if len(self.candidates[rowindex][columnindex])==1:
            return self.setcell(rowindex,columnindex,self.candidates[rowindex][columnindex][0])
    
    def isvalid(self):
        # check if a sudoku grid does not contain contradictions so far; zeros (unfilled cells) are ignored.
        for i in range(self.size):
            if not self.groupisvalid(self.getrow(i)[0]):
                return False
            if not self.groupisvalid(self.getcolumn(i)[0]):
                return False
            if not self.groupisvalid(self.getblock(i)[0]):
                return False
        return True
            
    def groupisvalid(self,group):
        # help function for isvalid; check if a group does not contain any contradictions; zeros are ignored.
        containslist = []
        for i in group:
            if i == 0:
                continue
            if i in containslist:
                return False
            else:
                containslist.append(i)
        return True
    
    def reducecandidates(self):
        # BASIC solving method (element-based)
        # loop over all elements in the grid and remove candidates based on row, column and block restrictions.
        for i in range(self.size):
            for j in range(self.size):
                if self.grid[i][j]!=0:
                    continue
                for group in [self.getrow(i)[0],self.getcolumn(j)[0],self.getblock(i,j)[0]]:
                    for number in group:
                        self.removecandidate(i,j,number)
                    
    def loopgroups(self,groupfunctions,labels=['row','column','block']):
        # generic looper over all groups in the grid
        # groupfunctions is a list of function to be called on each group
        # labels is a list of types of groups to loop over, default all groups
        labels = labels[:] # copy to local variable since it might be altered
        groupfunctions = groupfunctions[:] # see above
        validlabels = []
        if 'row' in labels: validlabels.append('row'); labels.remove('row')
        if 'column' in labels: validlabels.append('column'); labels.remove('column')
        if 'block' in labels: validlabels.append('block'); labels.remove('block')
        if len(labels)>0: print('WARNING: group label not recognized, skipping it; found '+str(labels))
        for i in range(self.size):
            for validlabel in validlabels:
                group,cands = self.getgroup(validlabel,i)
                for f in groupfunctions:
                    # part 1: functions applicable to all groups
                    if f=='complement': self.complement(group,i,validlabel,cands);
                    elif f=='nakedsubset': self.nakedsubset(group,i,validlabel,cands)
                    elif f=='hiddensubset': self.hiddensubset(group,i,validlabel,cands)
                    # part 2: functions applicable to rows and columns
                    elif f=='lineblockinteraction': 
                        if validlabel=='row' or validlabel=='column':
                            self.lineblockinteraction(group,i,validlabel,cands)
                    # part 3: functions applicable to blocks
                    elif f=='blocklineinteraction': 
                        if validlabel=='block':
                            self.blocklineinteraction(group,i,cands)
                    elif f=='blockblockinteraction':
                        if validlabel=='block':
                            self.blockblockhorizontalinteraction(group,i,validlabel,cands)
                            self.blockblockverticalinteraction(group,i,validlabel,cands)
                    else: print('WARNING: groupfunction not recognized, skipping it; found '+str(f))
                
    def complement(self,group,groupindex,label,candidates):
        # BASIC solving method (group-based)
        # if only one possible position for an element is present in a group, fill it with this element
        for el in range(1,self.size+1):
            if el in group:
                continue
            npossible = 0
            indexj = -1
            for j in range(self.size):
                if el in candidates[j]:
                    npossible += 1
                    indexj = j
            if npossible==1:
                (rw,clmn) = self.getcell(label,groupindex,indexj)
                self.setcell(rw,clmn,el)
    
    def nakedsubset(self,group,groupindex,label,candidates):
        # ADVANCED method (group-based)
        # if n candidate sets together contain only n numbers, remove those numbers from all other candidate sets
        for i in range(self.size-1):
            candsi = candidates[i]
            if len(candsi)<2: continue
            nsubs = 1
            subindices = [i]
            for j in range(self.size):
                if j==i: continue
                candsj = candidates[j]
                sub = self.issubset(candsj,candsi)
                if sub==1:
                    nsubs += 1
                    subindices.append(j)
            if(nsubs==len(candsi)):
                for j in range(self.size):
                    if j not in subindices:
                        (rw,clmn) = self.getcell(label,groupindex,j)
                        candsj = candidates[j]
                        for cand in candsi:
                            self.removecandidate(rw,clmn,cand)
                
    def hiddensubset(self,group,groupindex,label,candidates):
        # ADVANCED method (group-based)
        # if a subset of n candidates is shared between exactly n cells, remove all other candidates from these cells
        uniquecands = []
        for candset in candidates:
            if len(candset)<2: continue
            for cand in candset:
                if cand not in uniquecands: uniquecands.append(cand)
        subsets = list(itertools.combinations(uniquecands,2))
        for j in range(3,len(uniquecands)+1):
            toappend = list(itertools.combinations(uniquecands,j))
            for subset in toappend: subsets.append(subset)
        for subset in subsets:
            shareindices = []
            for j in range(self.size):
                sub = self.issubset(subset,candidates[j])
                if(sub==0 or sub==1): shareindices.append(j)
            if(len(subset)==len(shareindices)):
                for k in shareindices:
                    (rw,clmn) = self.getcell(label,groupindex,k)
                    for cand in range(1,self.size+1):
                        if cand not in subset: 
                            self.removecandidate(rw,clmn,cand)
                   
    def issubset(self,smallist,biglist):
        # help function for nakedsubset and hiddensubset
        # return values:
        #   -1: not a single element of smallist in biglist
        #   0: some but not all elements of smallist in biglist
        #   1: all elements of smallist in biglist
        nels = 0
        for el in smallist:
            if el in biglist:
                nels += 1
        if nels==0: return -1
        if nels==len(smallist): return 1
        return 0
    
    def blocklineinteraction(self,block,blockindex,blockcands):
        # ADVANCED solving method (block-based)
        # if a candidate occurs in only one row/column within a block, remove it from the rest of the row/column
        for el in range(1,self.size+1):
            if el in block: continue
            firstindex = -1
            i = 0
            while(i<self.size and firstindex==-1):
                if el in blockcands[i]:
                    firstindex = i
                i += 1
            testrw,testclmn = self.getcell('block',blockindex,firstindex)
            allrows = [testrw]
            uniquerows = [testrw]
            allcols = [testclmn]
            uniquecols = [testclmn]
            for i in range(firstindex+1,self.size):
                if el in blockcands[i]:
                    rw,clmn = self.getcell('block',blockindex,i)
                    allrows.append(rw); allcols.append(clmn)
                    if rw not in uniquerows: uniquerows.append(rw)
                    if clmn not in uniquecols: uniquecols.append(clmn)
            if len(uniquerows)==1:
                for clmn in range(self.size):
                    if clmn not in allcols:
                        self.removecandidate(testrw,clmn,el)
            if len(uniquecols)==1:
                for rw in range(self.size):
                    if rw not in allrows:
                        self.removecandidate(rw,testclmn,el)
                                
    def lineblockinteraction(self,line,lineindex,linelabel,linecands):
        # ADVANCED solving method (row/column-based)
        # if a candidate occurs in only one block within a row/column, remove it from the rest of the block
        for el in range(1,self.size+1):
            if el in line: continue
            firstindex = -1
            i = 0
            while(i<self.size and firstindex==-1):
                if el in linecands[i]:
                    firstindex = i
                i += 1
            testrw,testclmn = self.getcell(linelabel,lineindex,firstindex)
            testblock = self.getblockindex(testrw,testclmn)
            oneblock = True
            for i in range(firstindex+1,self.size):
                if el in linecands[i]:
                    rw,clmn = self.getcell(linelabel,lineindex,i)
                    block = self.getblockindex(rw,clmn)
                    if block!=testblock: oneblock = False
            if oneblock:
                firstrow,firstcolumn = np.multiply(divmod(testblock,self.blocksize),self.blocksize)
                for rw in range(firstrow,firstrow+self.blocksize):
                    for clmn in range(firstcolumn,firstcolumn+self.blocksize):
                        if((linelabel=='row' and not rw==lineindex)
                           or (linelabel=='column' and not clmn==lineindex)):
                            self.removecandidate(rw,clmn,el)
                                
    def blockblockhorizontalinteraction(self,group,groupindex,label,candidates):
        # ADVANCED solving method (block-based)
        # if a candidate occurs in only two rows in two horizontally aligned blocks, remove it from the remaining positions in those rows
        for i in range(self.size):
            if(i<=groupindex or self.getcell(label,i,0)[0]!=self.getcell(label,groupindex,0)[0]): continue
            groupi,candidatesi = self.getblock(i)
            for el in range(1,self.size+1):
                if(el in group or el in groupi): continue
                rows = []
                columns = []
                for j in range(self.size):
                    if el in candidates[j]:
                        row,column = self.getcell(label,groupindex,j)
                        if row not in rows: rows.append(row)
                        if column not in columns: columns.append(column)
                    if el in candidatesi[j]:
                        row,column = self.getcell(label,i,j)
                        if row not in rows: rows.append(row)
                        if column not in columns: columns.append(column)
                if len(rows)==2:
                        for j in range(self.size):
                            if j not in columns:
                                self.removecandidate(rows[0],j,el)
                                self.removecandidate(rows[1],j,el)
        
    def blockblockverticalinteraction(self,group,groupindex,label,candidates):
        # ADVANCED solving method (block-based)
        # if a candidate occurs in only two columns in two vertically aligned blocks, remove it from the remaining positions in those columns
        for i in range(self.size):
            if(i<=groupindex or self.getcell(label,i,0)[1]!=self.getcell(label,groupindex,0)[1]): continue
            groupi,candidatesi = self.getblock(i)
            for el in range(1,self.size+1):
                if(el in group or el in groupi): continue
                rows = []
                columns = []
                for j in range(self.size):
                    if el in candidates[j]:
                        row,column = self.getcell(label,groupindex,j)
                        if row not in rows: rows.append(row)
                        if column not in columns: columns.append(column)
                    if el in candidatesi[j]:
                        row,column = self.getcell(label,i,j)
                        if row not in rows: rows.append(row)
                        if column not in columns: columns.append(column)
                if len(columns)==2:
                        for j in range(self.size):
                            if j not in rows:
                                self.removecandidate(j,columns[0],el)
                                self.removecandidate(j,columns[1],el)
    
    def swordfishcolumns(self):
        # HYPERADVANCED solving method (grid-based)
        # find a swordfish pattern in the columns of the grid and eliminate suitable candidates from the rows
        # STEP 1: find all columns that have exactly two spots for a given candidate
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
                # STEP 3: remove candidates from these rows that do not belong to the swordfish pattern
                # STEP 3a: define pattern in suitable format
                pattern = []
                for j in colssubset:
                    for i in rows[j]:
                            pattern.append([i,j])
                # STEP 3b: remove from all positions in unique rows except swordfish
                for i in uniquerows:
                    for j in range(self.size):
                        if([i,j] not in pattern): self.removecandidate(i,j,el)
                        
    def swordfishrows(self):
        # HYPERADVANCED solving method (grid-based)
        # mirror of swordfishcolumns
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
                            pattern.append([i,j])
                for j in uniquecols:
                    for i in range(self.size):
                        if([i,j] not in pattern): self.removecandidate(i,j,el)
                
                        
    def solve(self):
        # main method grouping all solving methods and calling them in increasing order of complexity
        self.logfile = open(self.logname,'a')
        ncands = self.ncands # use ncands to keep track of changes made by each method
        self.logfile.write('number of initial candidates: '+str(ncands)+'\n')
        # STEP 1: basic methods
        self.logfile.write('Starting solving procedure using basic methods...\n')
        self.reducecandidates()
        self.loopgroups(['complement'])
        self.logfile.write('number of remaining candidates '+str(self.ncands)+'\n')
        while self.ncands < ncands:
            ncands = self.ncands
            self.reducecandidates()
            self.loopgroups(['complement'])
            self.logfile.write('number of remaining candidates '+str(self.ncands)+'\n')
        self.logfile.write('Basic methods finished.\n')
        (outputcode,message) = self.terminate()
        if outputcode!=0: return (outputcode,message)
        self.logfile.write('Start using more advanced methods...\n')
        self.loopgroups(['nakedsubset','hiddensubset','blocklineinteraction',
                         'lineblockinteraction','blockblockinteraction'])
        self.reducecandidates()
        self.loopgroups(['complement'])
        self.logfile.write('number of remaining candidates '+str(self.ncands)+'\n')
        while self.ncands < ncands:
            ncands = self.ncands
            self.loopgroups(['nakedsubset','hiddensubset','blocklineinteraction',
                         'lineblockinteraction','blockblockinteraction'])
            self.reducecandidates()
            self.loopgroups(['complement'])
            self.logfile.write('number of remaining candidates: '+str(self.ncands)+'\n')
        self.logfile.write('Advanced methods finished.\n')
        (outputcode,message) = self.terminate()
        if outputcode!=0: return (outputcode,message)
        self.logfile.write('Start using hyperadvanced methods...\n')
        self.swordfishcolumns()
        self.swordfishrows()
        self.loopgroups(['nakedsubset','hiddensubset','blocklineinteraction',
                         'lineblockinteraction','blockblockinteraction'])
        self.reducecandidates()
        self.loopgroups(['complement'])
        self.logfile.write('number of remaining candidates: '+str(self.ncands)+'\n')
        while self.ncands < ncands:
            ncands = self.ncands
            self.swordfishcolumns()
            self.swordfishrows()
            self.loopgroups(['nakedsubset','hiddensubset','blocklineinteraction',
                             'lineblockinteraction','blockblockinteraction'])
            self.reducecandidates()
            self.loopgroups(['complement'])
            self.logfile.write('number of remaining candidates: '+str(self.ncands)+'\n')
        self.logfile.write('Hyperadvanced methods finished.\n')
        (outputcode,message) = self.terminate()
        if outputcode!=0: return (outputcode,message)
        message = 'Unable to solve sudoku with presently implemented methods...\n'
        self.logfile.write(message)
        self.logfile.write('Got up to this point: \n')
        self.logfile.write(self.grid)
        self.logfile.close()
        return (0,message)
        
    def terminate(self):
        # check termination conditions and print final output to screen
        # output codes:
        #       -1: invalid sudoku detected, stop processing
        #       0: sudoku partially solved, continue processing
        #       1: sudoku fully solved, stop processing
        if not self.isvalid(): 
            message = 'ERROR: sudoku is invalid \n -> check solving methods for bugs or input for typos!\n'
            self.logfile.write(message)
            self.logfile.close()
            return (-1,message)
        if self.nunfilled==0:
            message = 'Sudoku was solved successfully!\n'
            self.logfile.write(message)
            self.logfile.write(self.tostring())
            self.logfile.close()
            return (1,message)
        message = 'The sudoku at this point:\n'
        self.logfile.write(message)
        self.logfile.write(self.tostring())
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
        
import Tkinter as tk

class SudokuSolverGUI:
    def __init__(self,master):
        self.master = master
        master.title("SudokuSolver GUI")
        
        self.grid_frame = tk.Frame(master,height=200,width=200)
        self.grid_frame.pack()
        
        self.gridsize = 9
        self.gridcells = []
        for i in range(self.gridsize):
            self.gridcells.append([])
            for j in range(self.gridsize):
                cell_entry = tk.Entry(self.grid_frame,font="Calibri 20",justify='center',width=2)
                cell_entry.grid(row=i,column=j)
                self.gridcells[i].append(cell_entry)
                
        self.options_frame = tk.Frame(master,width=200)
        self.options_frame.pack()
        
        self.solve_button = tk.Button(self.options_frame,text='Solve',command=self.solve)
        self.solve_button.pack(side=tk.LEFT)
        
        self.save_button = tk.Button(self.options_frame,text='Save',command=self.save)
        self.save_button.pack(side=tk.LEFT)
        
        self.load_button = tk.Button(self.options_frame,text='Load',command=self.load)
        self.load_button.pack(side=tk.LEFT)
        
        self.clear_button = tk.Button(self.options_frame,text='Clear',command=self.clear)
        self.clear_button.pack(side=tk.LEFT)
        
        self.close_button = tk.Button(self.options_frame,text='Close',command=master.destroy)
        self.close_button.pack(side=tk.RIGHT)
        
        self.messages_text = tk.Text(master,width=80,height=10)
        self.messages_text.pack()
        initstring = 'Welcome to the Sudoku Solver!\n'
        initstring += '- Click on the cells in the grid above to set the intial values \n'+'  or press "Load" to load a previously saved grid.\n'
        initstring += '- (Optional:) Save the grid you filled in by pressing "Save" \n'+'  (this will overwrite any previously saved grid)\n'
        initstring += '- Solve your sudoku by pressing "Solve"!\n\n'
        self.messages_text.insert(tk.INSERT,initstring)
        
    def getgrid(self):
        grid = np.zeros((self.gridsize,self.gridsize))
        for i in range(self.gridsize):
            for j in range(self.gridsize):
                val = self.gridcells[i][j].get()
                if(val==''): continue
                message =  '[notification:] ERROR: invalid value found in input grid: "'+str(val)+'"\n\n'
                try:
                    intval = int(val)
                except:
                    self.messages_text.insert(tk.INSERT,message)
                    self.messages_text.see(tk.END)
                    return None
                if(intval<1 or intval>self.gridsize):
                    self.messages_text.insert(tk.INSERT,message)
                    self.messages_text.see(tk.END)
                    return None
                grid[i,j] = intval
        return grid
        
    def solve(self):
        grid = self.getgrid()
        if grid is None: return None 
        S = Sudoku(grid)
        (outputcode,message) = S.solve()
        message = '[notification:] '+message+'\n\n'
        self.messages_text.insert(tk.INSERT,message)
        self.messages_text.see(tk.END)
        for i in range(self.gridsize):
            for j in range(self.gridsize):
                val = self.gridcells[i][j].get()
                if(val==''): 
                    newval = int(S.grid[i,j])
                    if newval==0:
                        self.gridcells[i][j].insert(0,'_')
                        self.gridcells[i][j].config(foreground='red')
                    else:
                        self.gridcells[i][j].insert(0,str(newval))
                        self.gridcells[i][j].config(foreground='green')
            
    def save(self):
        grid = self.getgrid()
        np.savetxt('sudokusave.txt',grid,fmt='%.1i')
        message =  '[notification:] Current grid saved successfully.\n'
        message += '                You can load it in future runs using the "Load" button.\n\n'
        self.messages_text.insert(tk.INSERT,message)
        self.messages_text.see(tk.END)
        
    def load(self):
        try:
            grid = np.loadtxt('sudokusave.txt')
        except:
            message = '[notification:] ERROR: no previously saved grid was found!\n\n'
            self.messages_text.insert(tk.INSERT,message)
            return None
        for i in range(self.gridsize):
            for j in range(self.gridsize):
                val = grid[i,j]
                if(val!=0): self.gridcells[i][j].insert(0,str(int(grid[i,j])))
        message =  '[notification:] Grid loaded successfully.\n\n'
        self.messages_text.insert(tk.INSERT,message)
        self.messages_text.see(tk.END)
        
    def clear(self):
        for i in range(self.gridsize):
            for j in range(self.gridsize):
                self.gridcells[i][j].delete(0,tk.END)
                self.gridcells[i][j].config(foreground='black')
        message = '[notification:] Current grid cleared. \n\n'
        self.messages_text.insert(tk.INSERT,message)
        self.messages_text.see(tk.END)

root = tk.Tk()
gui = SudokuSolverGUI(root)
root.mainloop()
