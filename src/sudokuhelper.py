# imports
from sudoku import Sudoku
import copy as cp

class SudokuHelper(Sudoku):

    def __init__(self, grid, candidates,
            verbose=True, logfilename=None, appendlogfile=False):
        super(SudokuHelper,self).__init__(grid,
                verbose=verbose, logfilename=logfilename, appendlogfile=appendlogfile)
        self.candidates = cp.deepcopy(candidates)
        self.ncands = 0
        for i in range(self.size):
            for j in range(self.size):
                if not self.grid[i,j]==0: 
                    self.candidates[i][j] = [grid[i,j]]
                self.ncands += len(self.candidates[i][j])

    def hint(self):
        # STEP 1: basic methods
        res = self.reducecandidates(solve=False)
        if len(res)>0: return self.showhint(res[0])
        res = self.loopgroups(['complement'],solve=False)
        if len(res)>0: return self.showhint(res[0])
        # STEP 2: advanced methods
        for method in (['nakedsubset','hiddensubset','blocklineinteraction',
                        'lineblockinteraction','blockblockinteraction']):
            res = self.loopgroups([method],solve=False)
            if len(res)>0: return self.showhint(res[0])
        # STEP 3: hyperadvanced methods
        res = self.swordfishcolumns(solve=False)
        if len(res)>0: return self.showhint(res[0])
        res = self.swordfishrows(solve=False)
        if len(res)>0: return self.showhint(res[0])
        res = self.xywing(solve=False)
        if len(res)>0: return self.showhint(res[0])
        #res = self.uniquerectangle(solve=False)
        #if len(res)>0: return self.showhint(res[0])
        res = self.forcingchain(solve=False)
        if len(res)>0: return self.showhint(res[0])
        return ('No hint could be found!\n\n',[])

    def printcell(self,cell):
        # return a string of cell coordinates (givan as tuple) in suitable format
        return str((cell[0]+1,cell[1]+1))

    def showhint(self,resdict):
        hint = '[hint:] '
        cells = []
        if resdict['method']=='reducecandidates':
            hint += 'Candidate '+str(resdict['value'])+' can be erased from cell '
            hint += self.printcell(resdict['cell'])+'\n'
            hint += '        because it is already present in the '+resdict['label']+'.\n\n'
            cells = [resdict['cell']]
        
        elif resdict['method']=='complement':
            hint += 'The value '+str(resdict['value'])+' can be assigned to cell '
            hint += self.printcell(resdict['cell'])+'\n'
            hint += '        because it is the only place in the '+resdict['label']+' where it can go.\n\n'
            cells = [resdict['cell']]
        
        elif resdict['method']=='nakedsubset':
            hint += 'There is an unexploited naked subset in '+resdict['grouplabel']+' '
            hint += str(resdict['groupindex']+1)+':\n'
            hint += '        the indices '+str([f+1 for f in resdict['indices']])+' contain the candidates '
            hint += str(resdict['values'])+'.\n'
            hint += '        You can remove those candidates from all other cells in the '
            hint += resdict['grouplabel']+'.\n\n'
            cells = resdict['cells']
        
        elif resdict['method']=='hiddensubset':
            hint += 'There is an unexploited hidden subset in '+resdict['grouplabel']+' '
            hint += str(resdict['groupindex'])+':\n'
            hint += '        the candidates '+str(resdict['values'])+' only occur in the indices '
            hint += str([f+1 for f in resdict['indices']])+'.\n'
            hint += '        You can remove all other candidates from those cells in the '
            hint += resdict['grouplabel']+'.\n\n'
            cells = resdict['cells']
        
        elif resdict['method']=='blocklineinteraction':
            hint += 'There is an unexploited block-line interaction\n'
            hint += '        (i.e. candidates within a block align)\n'
            hint += '        between block '+str(resdict['blockindex']+1)+' and '+resdict['linelabel']
            hint += ' '+str(resdict['lineindex']+1)+'.\n'
            hint += '        Check candidate '+str(resdict['value'])+'.\n\n'
            cells = resdict['cells']
        
        elif resdict['method']=='lineblockinteraction':
            hint += 'There is an unexploited line-block interaction\n'
            hint += '        (i.e. candidates within a line are blocked)\n'
            hint += '        between '+resdict['linelabel']+' '+str(resdict['lineindex']+1)+' and block'
            hint += str(resdict['blockindex']+1)+'.\n'
            hint += '        Check candidate '+str(resdict['value'])+'.\n\n'
            cells = resdict['cells']
        
        elif resdict['method']=='blockblockhorizontalinteraction':
            hint += 'There is an unexploited horizontal block-block interaction\n'
            hint += '        (i.e. candidate appears in two rows within two horizontally aligned blocks).\n'
            hint += '        Check candidate '+str(resdict['value'])+' in blocks '+str(resdict['block1index']+1)
            hint += ' and '+str(resdict['block2index']+1)+'.\n\n'
            cells = resdict['cells']
        
        elif resdict['method']=='blockblockverticalinteraction':
            hint += 'There is an unexploited vertical block-block interaction\n'
            hint += '        (i.e. candidate appears in two columns in two vertically aligned blocks).\n'
            hint += '        Check candidate '+str(resdict['value'])+' in blocks '+str(resdict['block1index']+1)
            hint += ' and '+str(resdict['block2index']+1)+'.\n\n'
            cells = resdict['cells']
        
        elif resdict['method']=='swordfishcolumns':
            hint += 'There is a column-wise swordfish pattern.\n'
            hint += '        Check candidate '+str(resdict['value'])+' in the following cells:\n'
            for c in resdict['pattern']: hint += '        '+self.printcell(c)+'\n'
            hint += '        You can remove this candidate from all rows in the pattern\n'
            hint += '        except for the cells belonging to the swordfish pattern.\n\n'
            cells = resdict['pattern']
        
        elif resdict['method']=='swordfishrows':
            hint += 'There is a row-wise swordfish pattern.\n'
            hint += '        Check candidate '+str(resdict['value'])+' in the following cells:\n'
            for c in resdict['pattern']: hint += '        '+self.printcell(c)+'\n'
            hint += '        You can remove this candidate from all columns in the pattern\n'
            hint += '        except for the cells belonging to the swordfish pattern.\n\n'
            cells = resdict['pattern']
        
        elif resdict['method']=='xywing':
            hint += 'There is an XY-wing pattern.\n'
            hint += '        The base is cell '+self.printcell(resdict['cells'][0])+' and the wings are\n'
            hint += '        cells '+self.printcell(resdict['cells'][1])+' and '
            hint += self.printcell(resdict['cells'][2])+'.\n'
            hint += '        You can remove candidate '+str(resdict['value'])+' from all cells that share\n'
            hint += '        a group (row, column or block) with both wings.\n\n'
            cells = resdict['cells']
        
        elif resdict['method']=='uniquerectangle':
            hint += 'There is a unique rectangle pattern.\n'
            hint += '        The base cells are '+self.printcell(resdict['cells'][0])
            hint += ', '+self.printcell(resdict['cells'][1])
            hint += ' and '+self.printcell(resdict['cells'][2])+'\n'
            hint += '        You can remove candidates '+str(resdict['values'])
            hint += ' from target cell '+self.printcell(resdict['target'])+'.\n\n'
            cells = resdict['cells']
        
        elif resdict['method']=='forcingchain':
            hint += 'A forcing chain method was used.\n'
            hint += '        Cell '+self.printcell(resdict['cell'])+' can hold different numbers,\n'
            hint += '        but all choices result in the removal of the following candidates:\n'
            for c in resdict['results']:
                hint += '        candidate '+str(c[2])+' in cell '+self.printcell((c[0],c[1]))+'\n'
            hint += '\n'
            cells = resdict['results']
        
        else:
            hint = 'Oops, something went wrong, the hint cannot be shown...\n\n'
        
        return (hint,cells)
