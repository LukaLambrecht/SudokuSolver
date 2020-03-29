# imports
import numpy as np
import itertools
import copy as cp
import sys

class Sudoku(object):
    def __init__(self,startgrid,logfilename,newlogfile=True):
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
        self.grid = startgrid.astype(int) # 2D-grid with values (0 means unfilled)
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
        self.logname = logfilename # log file to keep track of solving procedure
        if newlogfile: self.logfile = open(self.logname,'w') # create file
        else: self.logfile = open(self.logname,'a')
        self.logfile.close() # close file for safety (open it only just before writing)

    def copy(self,logfilename,newlogfile=True):
        # make a deep copy of an entire sudoku
        S = Sudoku(np.zeros((self.size,self.size)),logfilename,newlogfile)
        S.grid = np.copy(self.grid)
        S.candidates = cp.deepcopy(self.candidates)
        S.nunfilled = self.nunfilled
        S.ncands = self.ncands
        return S

    def set(self,S):
        # set self to a deepcopy of S (log file is shared) 
        self.size = S.size
        self.blocksize = S.blocksize
        self.grid = S.grid.astype(int)
        self.candidates = [[[int(x) for x in col] for col in row] for row in S.candidates]
        self.nunfilled = S.nunfilled
        self.ncands = S.ncands
        self.logname = S.logname
        
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
    
    def reducecandidates(self,solve=True):
        # BASIC solving method (element-based)
        # loop over all elements in the grid and remove candidates based on row, column and block restrictions.
        self.logfile = open(self.logname,'a')
        self.logfile.write('- running basic reduction method...\n')
        self.logfile.close()
        res = []
        for i in range(self.size):
            for j in range(self.size):
                if self.grid[i][j]!=0:
                    continue
                for k,group in enumerate([self.getrow(i)[0],self.getcolumn(j)[0],self.getblock(i,j)[0]]):
                    for number in group:
                        if number in self.candidates[i][j]:
                            groupname = ['row','column','block'][k]
                            res.append({'method':'reducecandidates',
                                        'infokeys':['cell','label','value'],
                                        'cell':(i,j),'label':groupname,'value':int(number)})
                            if solve: self.removecandidate(i,j,number)
        return res
                    
    def loopgroups(self,groupfunctions,labels=['row','column','block'],solve=True):
        # generic looper over all groups in the grid
        # groupfunctions is a list of function to be called on each group
        # labels is a list of types of groups to loop over, default all groups
        labels = labels[:] # copy to local variable since it might be altered
        groupfunctions = groupfunctions[:] # see above
        validlabels = []
        res = []
        if 'row' in labels: validlabels.append('row'); labels.remove('row')
        if 'column' in labels: validlabels.append('column'); labels.remove('column')
        if 'block' in labels: validlabels.append('block'); labels.remove('block')
        if len(labels)>0: print('WARNING: group label not recognized, skipping it; found '+str(labels))
        for i in range(self.size):
            for validlabel in validlabels:
                group,cands = self.getgroup(validlabel,i)
                for f in groupfunctions:
                    # part 1: functions applicable to all groups
                    if f=='complement': res += self.complement(group,i,validlabel,cands,solve=solve);
                    elif f=='nakedsubset': res += self.nakedsubset(group,i,validlabel,cands,solve=solve)
                    elif f=='hiddensubset': res += self.hiddensubset(group,i,validlabel,cands,solve=solve)
                    # part 2: functions applicable to rows and columns
                    elif f=='lineblockinteraction': 
                        if validlabel=='row' or validlabel=='column':
                            res += self.lineblockinteraction(group,i,validlabel,cands,solve=solve)
                    # part 3: functions applicable to blocks
                    elif f=='blocklineinteraction': 
                        if validlabel=='block':
                            res += self.blocklineinteraction(group,i,cands,solve=solve)
                    elif f=='blockblockinteraction':
                        if validlabel=='block':
                            res += self.blockblockhorizontalinteraction(group,i,validlabel,cands,solve=solve)
                            res += self.blockblockverticalinteraction(group,i,validlabel,cands,solve=solve)
                    else: print('WARNING: groupfunction not recognized, skipping it; found '+str(f))
        return res
                
    def complement(self,group,groupindex,label,candidates,solve=True):
        # BASIC solving method (group-based)
        # if only one possible position for an element is present in a group, fill it with this element
        res = []
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
                res.append({'method':'complement',
                            'infokeys':['cell','label','value'],
                            'cell':(rw,clmn),'label':label,'value':el})
                if solve:
                    self.setcell(rw,clmn,el)
                    self.logfile = open(self.logname,'a')
                    self.logfile.write('- cell '+str((rw,clmn))+' was filled using basic ')
                    self.logfile.write(label+' complementing.\n')
                    self.logfile.close() 
        return res
    
    def nakedsubset(self,group,groupindex,label,candidates,solve=True):
        # ADVANCED method (group-based)
        # if n candidate sets together contain only n numbers, remove those numbers from all other candidate sets
        res = []
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
                useful = False
                for j in range(self.size):
                    if j not in subindices:
                        (rw,clmn) = self.getcell(label,groupindex,j)
                        for cand in candsi:
                            if cand in self.candidates[rw][clmn]: useful = True
                            if solve: self.removecandidate(rw,clmn,cand)
                if useful: 
                    cells = []
                    for s in subindices: cells.append(self.getcell(label,groupindex,s))
                    res.append({'method':'nakedsubset',
                                    'infokeys':['grouplabel','groupindex','indices','values','cells'],
                                    'grouplabel':label,'groupindex':groupindex,
                                    'indices':subindices,'values':candsi,'cells':cells})
                    if solve:
                        self.logfile = open(self.logname,'a')
                        self.logfile.write('- found naked subset in cells '+str(cells)+'\n')
                        self.logfile.close()
        return res
                
    def hiddensubset(self,group,groupindex,label,candidates,solve=True):
        # ADVANCED method (group-based)
        # if a subset of n candidates is shared between exactly n cells, remove all other candidates from these cells
        res = []
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
                useful = False
                for k in shareindices:
                    (rw,clmn) = self.getcell(label,groupindex,k)
                    for cand in range(1,self.size+1):
                        if cand not in subset:
                            if cand in self.candidates[rw][clmn]: useful = True
                            if solve: self.removecandidate(rw,clmn,cand)
                if useful:
                    cells = []
                    for s in shareindices: cells.append(self.getcell(label,groupindex,s))
                    res.append({'method':'hiddensubset',
                                        'infokeys':['grouplabel','groupindex','indices','values','cells'],
                                        'grouplabel':label,'groupindex':groupindex,
                                        'indices':shareindices,'values':subset,'cells':cells})
                    if solve:
                        self.logfile = open(self.logname,'a')
                        self.logfile.write('- found hidden subset in cells '+str(cells)+'\n')
        return res
                   
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
    
    def blocklineinteraction(self,block,blockindex,blockcands,solve=True):
        # ADVANCED solving method (block-based)
        # if a candidate occurs in only one row/column within a block, remove it from the rest of the row/column
        res = []
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
                useful = False
                for clmn in range(self.size):
                    if clmn not in allcols:
                        if el in self.candidates[testrw][clmn]: useful = True
                        if solve: self.removecandidate(testrw,clmn,el)
                if useful:
                    cells = []
                    for s in allcols: cells.append((uniquerows[0],s)) 
                    res.append({'method':'blocklineinteraction',
                                        'infokeys':['blockindex','linelabel','lineindex','value','cells'],
                                        'blockindex':blockindex,'linelabel':'row','lineindex':testrw,
                                        'value':el,'cells':cells})
                    if solve:
                        self.logfile = open(self.logname,'a')
                        self.logfile.write('- found block-row interaction\n')
                        self.logfile.close()
            if len(uniquecols)==1:
                useful = False
                for rw in range(self.size):
                    if rw not in allrows:
                        if el in self.candidates[rw][testclmn]: useful = True
                        if solve: self.removecandidate(rw,testclmn,el)
                if useful: 
                    cells = []
                    for s in allrows: cells.append((s,uniquecols[0]))
                    res.append({'method':'blocklineinteraction',
                                        'infokeys':['blockindex','linelabel','lineindex','value','cells'],
                                        'blockindex':blockindex,'linelabel':'column','lineindex':testclmn,
                                        'value':el,'cells':cells})
                    if solve:
                        self.logfile = open(self.logname,'a')
                        self.logfile.write('- found block-column interaction\n')
                        self.logfile.close()
        return res 
                                
    def lineblockinteraction(self,line,lineindex,linelabel,linecands,solve=True):
        # ADVANCED solving method (row/column-based)
        # if a candidate occurs in only one block within a row/column, remove it from the rest of the block
        res = []
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
            cells = [(testrw,testclmn)]
            for i in range(firstindex+1,self.size):
                if el in linecands[i]:
                    rw,clmn = self.getcell(linelabel,lineindex,i)
                    cells.append((rw,clmn))
                    block = self.getblockindex(rw,clmn)
                    if block!=testblock: oneblock = False
            if oneblock:
                useful = False
                firstrow,firstcolumn = np.multiply(divmod(testblock,self.blocksize),self.blocksize)
                for rw in range(firstrow,firstrow+self.blocksize):
                    for clmn in range(firstcolumn,firstcolumn+self.blocksize):
                        if((linelabel=='row' and not rw==lineindex)
                           or (linelabel=='column' and not clmn==lineindex)):
                            if el in self.candidates[rw][clmn]: useful = True
                            if solve: self.removecandidate(rw,clmn,el)
                if useful:
                    res.append({'method':'lineblockinteraction',
                                'infokeys':['lineindex','linelabel','blockindex','value','cells'],
                                'lineindex':lineindex,'linelabel':linelabel,'blockindex':testblock,
                                'value':el,'cells':cells})
                    if solve:
                        self.logfile = open(self.logname,'a')
                        self.logfile.write('- found line-block interaction\n')
                        self.logfile.close()
        return res
                                
    def blockblockhorizontalinteraction(self,group,groupindex,label,candidates,solve=True):
        # ADVANCED solving method (block-based)
        # if a candidate occurs in only two rows in two horizontally aligned blocks, 
        # remove it from the remaining positions in those rows
        res = []
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
                    useful = False
                    for j in range(self.size):
                        if j not in columns:
                            if(el in self.candidates[rows[0]][j] or el in self.candidates[rows[1]][j]):
                                useful = True
                            if solve:
                                self.removecandidate(rows[0],j,el)
                                self.removecandidate(rows[1],j,el)
                    if useful: 
                        cells = []
                        for j in range(self.size): cells.append((rows[0],j)); cells.append((rows[1],j))
                        res.append({'method':'blockblockhorizontalinteraction',
                                            'infokeys':['block1index','block2index','value','cells'],
                                            'block1index':groupindex,'block2index':i,'value':el,'cells':cells})
                        if solve:
                            self.logfile = open(self.logname,'a')
                            self.logfile.write('- found horizontal block-block interaction\n')
                            self.logfile.close()
        return res
        
    def blockblockverticalinteraction(self,group,groupindex,label,candidates,solve=True):
        # ADVANCED solving method (block-based)
        # if a candidate occurs in only two columns in two vertically aligned blocks, 
        # remove it from the remaining positions in those columns
        res = []
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
                    useful = False
                    for j in range(self.size):
                        if j not in rows:
                            if(el in self.candidates[j][columns[0]] or el in self.candidates[j][columns[1]]):
                                useful = True
                            if solve:
                                self.removecandidate(j,columns[0],el)
                                self.removecandidate(j,columns[1],el)
                    if useful:
                        cells = []
                        for j in range(self.size): cells.append((j,columns[0])); cells.append((j,columns[1])) 
                        res.append({'method':'blockblockverticalinteraction',
                                            'infokeys':['block1index','block2index','value','cells'],
                                            'block1index':groupindex,'block2index':i,'value':el,'cells':cells})
                        if solve:
                            self.logfile = open(self.logname,'a')
                            self.logfile.write('- found vertical block-block interaction\n')
                            self.logfile.close()
        return res
    
    def swordfishcolumns(self,solve=True):
        # HYPERADVANCED solving method (grid-based)
        # find a swordfish pattern in the columns of the grid and eliminate suitable candidates from the rows
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
                # STEP 3: remove candidates from these rows that do not belong to the swordfish pattern
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
                    res.append({'method':'swordfishcolumns','infokeys':['value','pattern'],
                                'value':el,'pattern':pattern})
                    if solve:
                        self.logfile = open(self.logname,'a')
                        self.logfile.write('- found column-wise swordfish pattern\n')
                        self.logfile.close()
        return res
                        
    def swordfishrows(self,solve=True):
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
                    if solve:
                        self.logfile = open(self.logname,'a')
                        self.logfile.write('- found row-wise swordfish pattern\n')
                        self.logfile.close()
        return res

    def intersect(self,coords1,coords2):
        # help function for XY wing
        (rw1,clmn1) = coords1
        (rw2,clmn2) = coords2
        if rw1==rw2: return True
        if clmn1==clmn2: return True
        if self.getblockindex(rw1,clmn1)==self.getblockindex(rw2,clmn2): return True
        return False

    def shareone(self,cands1,cands2):
        # help function for XY wing
        if(cands2[0] in cands1 and not cands2[1] in cands1): return cands2[0]
        if(cands2[0] not in cands1 and cands2[1] in cands1): return cands2[1]
        return -1

    def xywing(self,solve=True):
        # HYPERADVANCED solving method (grid-based)
        # find XY pattern and remove candidate from cells that intersect with both wings
        res = []
        for rw1 in range(self.size):
            for clmn1 in range(self.size):
                if not len(self.candidates[rw1][clmn1])==2: continue
                cands1 = self.candidates[rw1][clmn1]
                uniquecands = cp.deepcopy(self.candidates[rw1][clmn1])
                shareone = []
                for rw2 in range(self.size):
                    for clmn2 in range(self.size):
                        if not len(self.candidates[rw2][clmn2])==2: continue
                        if not self.intersect((rw1,clmn1),(rw2,clmn2)): continue
                        cands2 = self.candidates[rw2][clmn2]
                        share = self.shareone(cands1,cands2)
                        if share>0: shareone.append((rw2,clmn2))
                if len(shareone)<2: continue
                for c1 in range(len(shareone)-1):
                    for c2 in range(c1+1,len(shareone)):
                        (rw2,clmn2) = shareone[c1]
                        (rw3,clmn3) = shareone[c2]
                        if self.intersect((rw3,clmn3),(rw2,clmn2)): continue
                        share = self.shareone(self.candidates[rw2][clmn2],
                                                self.candidates[rw3][clmn3])
                        if(share<0 or share in cands1): continue
                        useful = False
                        for rwa in range(self.size):
                            for clmna in range(self.size):
                                if(not (self.intersect((rwa,clmna),(rw2,clmn2)) 
                                    and self.intersect((rwa,clmna),(rw3,clmn3)))): continue
                                if(share in self.candidates[rwa][clmna]): useful = True
                                if solve: self.removecandidate(rwa,clmna,share)
                        if useful: 
                            res.append({'method':'xywing','infokeys':['cells','value'],
                                        'cells':[(rw1,clmn1),(rw2,clmn2),(rw3,clmn3)],
                                        'value':share})
                            if solve:
                                self.logfile = open(self.logname,'a')
                                self.logfile.write('- found XY-wing\n')
                                self.logfile.close()
        return res

    def forcingchain(self,solve=True):
        # HYPERADVANCED solving method (grid-based)
        # solve for all possibilities of a certain cell and check recurring patterns
        res = []
        if solve:
            self.logfile = open(self.logname,'a')
            self.logfile.write('- attempting forcing chain...\n')
            self.logfile.close()
        for i in range(self.size):
            for j in range(self.size):
                cands = self.candidates[i][j]
                if len(cands)==1: continue
                scopies = []
                for k,cand in enumerate(cands):
                    S = self.copy(self.logname+'_'+str(k),newlogfile=False)
                    if solve:
                        self.logfile = open(self.logname,'a')
                        self.logfile.write('    checking candidate '+str(cand)+' for cell '+str((i,j))+'\n')
                        self.logfile.close()
                    S.setcell(i,j,cand)
                    S.solve(userecursive=False)
                    scopies.append(S)
                if len(scopies)==0: continue
                candstoremove = cp.deepcopy(self.candidates)
                removelist = []
                useful = False
                for ci in range(self.size):
                    for cj in range(self.size):
                        if(ci==i and cj==j): continue
                        for scopy in scopies:
                            for val in scopy.candidates[ci][cj]:
                                if val in candstoremove[ci][cj]:
                                    candstoremove[ci][cj].remove(val)
                        if len(candstoremove[ci][cj])>0:
                            useful = True
                            for val in candstoremove[ci][cj]:
                                removelist.append((ci,cj,val))
                                if solve: self.removecandidate(ci,cj,val)
                if useful:
                    res.append({'method':'forcingchain','infokeys':['cell','results'],
                                'cell':(i,j),'results':removelist})
        if (len(res)>0 and solve): 
            self.logfile = open(self.logname,'a')
            self.logfile.write('  forcing chain found recurring pattern! Continue solving...\n')
            self.logfile.close()
        return res
                    

    def solve(self,userecursive=True):
        # main method grouping all solving methods and calling them in increasing order of complexity
        self.logfile = open(self.logname,'a')
        self.logfile.write('Start solving method on the following sudoku:\n')
        self.logfile.write(self.tostring())
        ncands = self.ncands # use ncands to keep track of changes made by each method
        self.logfile.write('number of initial candidates: '+str(ncands)+'\n')
        # STEP 1: basic methods
        self.logfile.write('Starting solving procedure using basic methods...\n')
        self.logfile.close()
        self.reducecandidates()
        self.loopgroups(['complement'])
        self.logfile = open(self.logname,'a')
        self.logfile.write('number of remaining candidates '+str(self.ncands)+'\n')
        self.logfile.close()
        while self.ncands < ncands:
            ncands = self.ncands
            self.reducecandidates()
            self.loopgroups(['complement'])
            self.logfile = open(self.logname,'a')
            self.logfile.write('number of remaining candidates '+str(self.ncands)+'\n')
            self.logfile.close()
        self.logfile = open(self.logname,'a')
        self.logfile.write('Basic methods finished.\n')
        self.logfile.close()
        (outputcode,message) = self.terminate()
        if outputcode!=0: return (outputcode,message)
        # STEP 2: advanced methods
        self.logfile = open(self.logname,'a')
        self.logfile.write('Start using more advanced methods...\n')
        self.logfile.close()
        self.loopgroups(['nakedsubset','hiddensubset','blocklineinteraction',
                         'lineblockinteraction','blockblockinteraction'])
        self.reducecandidates()
        self.loopgroups(['complement'])
        self.logfile = open(self.logname,'a')
        self.logfile.write('number of remaining candidates '+str(self.ncands)+'\n')
        self.logfile.close()
        while self.ncands < ncands:
            ncands = self.ncands
            self.loopgroups(['nakedsubset','hiddensubset','blocklineinteraction',
                         'lineblockinteraction','blockblockinteraction'])
            self.reducecandidates()
            self.loopgroups(['complement'])
            self.logfile = open(self.logname,'a')
            self.logfile.write('number of remaining candidates: '+str(self.ncands)+'\n')
            self.logfile.close()
        self.logfile = open(self.logname,'a')
        self.logfile.write('Advanced methods finished.\n')
        self.logfile.close()
        (outputcode,message) = self.terminate()
        if outputcode!=0: return (outputcode,message)
        # STEP 3: hyperadvanced methods
        self.logfile = open(self.logname,'a')
        self.logfile.write('Start using hyperadvanced methods...\n')
        self.logfile.close()
        self.swordfishcolumns()
        self.swordfishrows()
        self.xywing()
        if userecursive: self.forcingchain()
        self.loopgroups(['nakedsubset','hiddensubset','blocklineinteraction',
                         'lineblockinteraction','blockblockinteraction'])
        self.reducecandidates()
        self.loopgroups(['complement'])
        self.logfile = open(self.logname,'a')
        self.logfile.write('number of remaining candidates: '+str(self.ncands)+'\n')
        self.logfile.close()
        (outputcode,message) = self.terminate()
        if outputcode!=0: return (outputcode,message)
        while self.ncands < ncands:
            ncands = self.ncands
            self.swordfishcolumns()
            self.swordfishrows()
            self.xywing()
            if userecursive: self.forcingchain()
            self.loopgroups(['nakedsubset','hiddensubset','blocklineinteraction',
                             'lineblockinteraction','blockblockinteraction'])
            self.reducecandidates()
            self.loopgroups(['complement'])
            self.logfile = open(self.logname,'a')
            self.logfile.write('number of remaining candidates: '+str(self.ncands)+'\n')
            self.logfile.close()
        self.logfile = open(self.logname,'a')
        self.logfile.write('Hyperadvanced methods finished.\n')
        self.logfile.close()
        (outputcode,message) = self.terminate()
        if outputcode!=0: return (outputcode,message)
        self.logfile = open(self.logname,'a')
        self.logfile.write('Unable to solve sudoku with presently implemented methods...\n')
        self.logfile.write('Got up to this point: \n')
        self.logfile.write(self.tostring())
        if not userecursive: return (outputcode,message)
        # STEP 4: brute force methods
        self.logfile.write('Starting brute force methods...\n')
        self.logfile.close()
        (outcode,message) = self.solvebruteforce()
        return (outcode,message)

    def solvebruteforce(self):
        # fill a cell by random guessing and recursively call solver
        rowmin = 0; colmin = 0; candmin = self.size+1
        for i in range(self.size):
            for j in range(self.size):
                ncands = len(self.candidates[i][j])
                if(ncands<candmin and ncands>=2):
                    candmin = len(self.candidates[i][j])
                    rowmin = i; colmin = j
        allinvalid = True
        for cand in self.candidates[rowmin][colmin]:
            self.logfile = open(self.logname,'a')
            message = 'row and column indices of cell with least candidates: '
            message += str(rowmin)+','+str(colmin)+'\n'
            message += 'candidates are: '+str(self.candidates[rowmin][colmin])+'\n'
            message += 'now trying: '+str(cand)+'\n'
            self.logfile.write(message)
            self.logfile.close()
            S = self.copy(self.logname,newlogfile=False)
            S.setcell(rowmin,colmin,cand)
            (outcode,message) = S.solve()
            if outcode==1: 
                self.set(S)
                return (outcode,message)
        if allinvalid: return (-1,'All options invalid, go one step back...')
        
    def terminate(self):
        # check termination conditions and print final output to screen
        # output codes:
        #       -1: invalid sudoku detected, stop processing
        #       0: sudoku partially solved, continue processing
        #       1: sudoku fully solved, stop processing
        self.logfile = open(self.logname,'a')
        if not self.isvalid():
            message = 'ERROR: sudoku is invalid \n'
            message += '-> when running in brute force mode, this is part of the standard workflow \n'
            message += '-> if not, check solving methods for bugs or input for typos!\n'
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
        self.logfile.close()
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
