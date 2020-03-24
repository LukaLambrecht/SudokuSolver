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
        hint = ''
        if resdict['method']=='reducecandidates':
            hint = 'Candidate '+str(resdict['value'])+' can be erased from cell '+str(resdict['cell'])+'\n'
            hint += 'because it is already present in the '+resdict['label']+'\n'
        elif resdict['method']=='complement':
            hint = 'The value '+str(resdict['value'])+' can be assigned to cell '+str(resdict['cell'])+'\n'
            hint += 'because it is the only place in the '+resdict['label']+' where it can go.\n'
        elif resdict['method']=='nakedsubset':
            hint = 'There is an unexploited naked subset in '+resdict['grouplabel']+' '
            hint += str(resdict['groupindex'])+':\n'
            hint += 'the indices '+str(resdict['indices'])+' contain the candidates '+str(resdict['values'])+'\n'
            hint += 'You can remove those candidates from all other cells in the '+resdict['grouplabel']+'\n'
        elif resdict['method']=='hiddensubset':
            hint = 'There is an unexploited hidden subset in '+resdict['grouplabel']+' '
            hint += str(resdict['groupindex'])+':\n'
            hint += 'the candidates '+str(resdict['values'])+' only occur in the indices '
            hint += str(resdict['indices'])+'\n'
            hint += 'You can remove all other candidates from those cells in the '+resdict['grouplabel']+'\n'
        elif resdict['method']=='blocklineinteraction':
            hint = 'There is an unexploited block-line interaction\n(i.e. candidates within a block align)\n'
            hint += 'between block '+str(resdict['blockindex'])+' and '+resdict['linelabel']
            hint += ' '+str(resdict['lineindex'])+'\n'
            hint += '(check candidate '+str(resdict['value'])+')\n'
        elif resdict['method']=='lineblockinteraction':
            hint = 'There is an unexploited line-block interaction\n(i.e. candidates within a line are blocked)\n'
            hint += 'between '+resdict['linelabel']+' '+str(resdict['lineindex'])+' and block'
            hint += str(resdict['blockindex'])+'\n'
            hint += '(check candidate '+str(resdict['value'])+')\n'
        else: # to complet later on
            hint = 'method: '+resdict['method']
            for key in resdict['infokeys']:
                hint += ', '+key+': '+str(resdict[key])
            hint += '\n'
        return hint
