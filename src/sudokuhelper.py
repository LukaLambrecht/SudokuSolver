# imports
from sudoku import Sudoku
import copy as cp

class SudokuHelper(Sudoku):

    def __init__(self,grid,candidates,logfilename,newlogfile=True):
        super(SudokuHelper,self).__init__(grid,logfilename,newlogfile)
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
        return 'No hint could be found!'

    def showhint(self,resdict):
        hint = '[hint:] '
        cells = []
        if resdict['method']=='reducecandidates':
            hint += 'Candidate '+str(resdict['value'])+' can be erased from cell '+str(resdict['cell'])+'\n'
            hint += '        because it is already present in the '+resdict['label']+'.\n\n'
            cells = [resdict['cell']]
        elif resdict['method']=='complement':
            hint += 'The value '+str(resdict['value'])+' can be assigned to cell '+str(resdict['cell'])+'\n'
            hint += '        because it is the only place in the '+resdict['label']+' where it can go.\n\n'
            cells = [resdict['cell']]
        elif resdict['method']=='nakedsubset':
            hint += 'There is an unexploited naked subset in '+resdict['grouplabel']+' '
            hint += str(resdict['groupindex'])+':\n'
            hint += '        the indices '+str(resdict['indices'])+' contain the candidates '
            hint += str(resdict['values'])+'.\n'
            hint += '        You can remove those candidates from all other cells in the '
            hint += resdict['grouplabel']+'.\n\n'
            cells = resdict['cells']
        elif resdict['method']=='hiddensubset':
            hint += 'There is an unexploited hidden subset in '+resdict['grouplabel']+' '
            hint += str(resdict['groupindex'])+':\n'
            hint += '        the candidates '+str(resdict['values'])+' only occur in the indices '
            hint += str(resdict['indices'])+'.\n'
            hint += '        You can remove all other candidates from those cells in the '
            hint += resdict['grouplabel']+'.\n\n'
            cells = ['cells']
        elif resdict['method']=='blocklineinteraction':
            hint += 'There is an unexploited block-line interaction\n'
            hint += '        (i.e. candidates within a block align)\n'
            hint += '        between block '+str(resdict['blockindex'])+' and '+resdict['linelabel']
            hint += ' '+str(resdict['lineindex'])+'.\n'
            hint += '        Check candidate '+str(resdict['value'])+'.\n\n'
            cells = resdict['cells']
        elif resdict['method']=='lineblockinteraction':
            hint += 'There is an unexploited line-block interaction\n'
            hint += '        (i.e. candidates within a line are blocked)\n'
            hint += '        between '+resdict['linelabel']+' '+str(resdict['lineindex'])+' and block'
            hint += str(resdict['blockindex'])+'.\n'
            hint += '        Check candidate '+str(resdict['value'])+'.\n\n'
            cells = resdict['cells']
        elif resdict['method']=='blockblockhorizontalinteraction':
            hint += 'There is an unexploited horizontal block-block interaction\n'
            hint += '        (i.e. candidate appears in two rows within two horizontally aligned blocks).\n'
            hint += '        Check candidate '+str(resdict['value'])+' in blocks '+str(resdict['block1index'])
            hint += ' and '+str(resdict['block2index'])+'.\n\n'
            cells = resdict['cells']
        elif resdict['method']=='blockblockverticalinteraction':
            hint += 'There is an unexploited vertical block-block interaction\n'
            hint += '        (i.e. candidate appears in two columns in two vertically aligned blocks).\n'
            hint += '        Check candidate '+str(resdict['value'])+' in blocks '+str(resdict['block1index'])
            hint += ' and '+str(resdict['block2index'])+'.\n\n'
            cells = resdict['cells']
        elif resdict['method']=='swordfishcolumns':
            hint += 'There is a column-wise swordfish pattern.\n'
            hint += '        Check candidate '+str(resdict['value'])+' in the following cells:\n'
            for c in resdict['pattern']: hint += '        '+str(c)+'\n'
            hint += '        You can remove this candidate from all rows in the pattern\n'
            hint += '        except for the cells belonging to the swordfish pattern.\n\n'
            cells = resdict['pattern']
        elif resdict['method']=='swordfishrows':
            hint += 'There is a row-wise swordfish pattern.\n'
            hint += '        Check candidate '+str(resdict['value'])+' in the following cells:\n'
            for c in resdict['pattern']: hint += '        '+str(c)+'\n'
            hint += '        You can remove this candidate from all columns in the pattern\n'
            hint += '        except for the cells belonging to the swordfish pattern.\n\n'
            cells = resdict['pattern']
        else:
            hint = 'Oops, something went wrong, the hint cannot be shown...\n\n'
        return (hint,cells)
