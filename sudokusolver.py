# imports
import sys
import os
import numpy as np
sys.path.insert(0,'./src')
from sudoku import Sudoku
from sudokuhelper import SudokuHelper
try:
    import Tkinter as tk
    import ScrolledText as scrtxt
    import tkFileDialog as fldlg
except ImportError: 
    import tkinter as tk
    import tkinter.scrolledtext as scrtxt
    import tkinter.filedialog as fldlg

class StdOutRedirector:
    ### helper class to redirect print output to GUI widget
    # use as follows:
    #   stdout = sys.stdout
    #   sys.stdout = StdOutRedirector(<some widget>)
    #   ... <some code execution containing print statements>
    #   sys.stdout = stdout

    def __init__(self,tk_text_widget,tk_root_object):
        self.text_dump = tk_text_widget
        self.root = tk_root_object

    def write(self,text):
        self.text_dump.insert(tk.INSERT, text)
        self.text_dump.see(tk.END)
        self.root.update()

class SudokuSolverGUI:
    
    def __init__(self,master):
        self.master = master
        master.title("SudokuSolver GUI")

        # set global geometry parameters
        self.grid_frame_nrow = 5
        self.grid_frame_ncol = 1
        self.candidate_frame_nrow = 1
        self.candidate_frame_ncol = 1
        self.messages_text_nrow = 1
        self.messages_text_ncol = 3
        self.bwidth=20
        self.bheight=10

        # define a frame for the sudoku cells and fill the grid        
        self.grid_frame = tk.Frame(master,width=200)
        self.grid_frame.grid(row=0,column=0,
                             rowspan=self.grid_frame_nrow,columnspan=self.grid_frame_ncol,
                             padx=10,pady=10)
        
        self.gridsize = 9
        self.blocksize = 3
        self.blockframes = []
        for i in range(self.gridsize): 
            self.blockframes.append(tk.LabelFrame(self.grid_frame,text='',
                                    relief='solid',borderwidth=1))
            self.blockframes[i].grid(row=divmod(i,self.blocksize)[0],
                                     column=divmod(i,self.blocksize)[1])
        self.gridcells = []
        for i in range(self.gridsize):
            self.gridcells.append([])
            for j in range(self.gridsize):
                blockn = divmod(i,self.blocksize)[0]*self.blocksize + divmod(j,self.blocksize)[0]
                cell_entry = tk.Entry(self.blockframes[blockn],font="Calibri 20",
                                        justify='center',width=2)
                cell_entry.grid(row=divmod(i,self.blocksize)[1],column=divmod(j,self.blocksize)[1])
                self.gridcells[i].append(cell_entry)
                self.gridcells[i][j].bind("<1>",lambda event,row=i,col=j : 
                                            self.showcandidates(event,row,col))
        
        # define a frame for the candidate cells and create a 3D list
        self.candidate_frame = tk.Frame(master,height=20,width=200)
        self.candidate_frame.grid(row=self.grid_frame_nrow,column=0,
                                  rowspan=self.candidate_frame_nrow,
                                  columnspan=self.candidate_frame_ncol,
                                  padx=10,pady=10)

        self.candidatecells = []
        for i in range(self.gridsize):
            self.candidatecells.append([])
            for j in range(self.gridsize):
                self.candidatecells[i].append([])
                for k in range(self.gridsize):
                    var = tk.IntVar(value=1)
                    candidate_rbutton = tk.Checkbutton(self.candidate_frame,text=str(k+1),
                            font="Calibri 20",justify='center',width=2,indicatoron=False,
                            var=var,background="red",selectcolor='green')
                    self.candidatecells[i][j].append({'button':candidate_rbutton,'var':var})

        # set focus to (0,0) and show corresponding candidates
        #self.gridcells[0][0].focus()
        #for k in range(self.gridsize): self.candidatecells[0][0][k]['button'].grid(row=0,column=k)

        # define mode button 
        self.mode = tk.StringVar()
        self.mode.set("A")
        self.auto_button = tk.Radiobutton(master,text='Automatic',indicatoron=False,
                                variable=self.mode,value="A",command=self.setmode)
        self.auto_button.grid(row=0,column=1,ipadx=self.bwidth,ipady=self.bheight)
        self.inter_button = tk.Radiobutton(master,text='Interactive',indicatoron=False,
                                variable=self.mode,value="I",command=self.setmode)
        self.inter_button.grid(row=0,column=2,ipadx=self.bwidth,ipady=self.bheight)

        # define a frame for the buttons and fill it                
        self.options_frame = tk.Frame(master,width=200)
        self.options_frame.grid(row=1,column=1,rowspan=self.grid_frame_nrow-1,columnspan=2)

        self.logfilename = 'logs/currentlog.txt'
        
        self.solve_button = tk.Button(self.options_frame,text='Solve',command=self.solve)
        self.solve_button.grid(row=0,column=0,columnspan=2,ipadx=self.bwidth,ipady=self.bheight)
        
        self.save_button = tk.Button(self.options_frame,text='Save',command=self.save)
        self.save_button.grid(row=1,column=1,ipadx=self.bwidth,ipady=self.bheight)
        
        self.load_button = tk.Button(self.options_frame,text='Load',command=self.load)
        self.load_button.grid(row=1,column=0,ipadx=self.bwidth,ipady=self.bheight)

        self.delete_button = tk.Button(self.options_frame,text='Delete',command=self.delete)
        self.delete_button.grid(row=2,column=1,ipadx=self.bwidth,ipady=self.bheight)
        
        self.clear_button = tk.Button(self.options_frame,text='Clear',command=self.clear)
        self.clear_button.grid(row=2,column=0,ipadx=self.bwidth,ipady=self.bheight)
        
        self.close_button = tk.Button(self.options_frame,text='Close',command=master.destroy)
        self.close_button.grid(row=3,column=0,columnspan=2,ipadx=self.bwidth,ipady=self.bheight)

        self.hint_button = tk.Button(self.options_frame,text='Hint',command=self.hint)

        self.reduce_button = tk.Button(self.options_frame,text='Reduce',command=self.reduce)
        
        self.messages_text = scrtxt.ScrolledText(master,width=75,height=30)
        self.messages_text.grid(row=self.grid_frame_nrow+self.candidate_frame_nrow,column=0,
                            columnspan=3)
        initstring = 'Welcome to the Sudoku Solver!\n'
        initstring += '- Click on the cells in the grid above to set the intial values \n'
        initstring += '  or press "Load" to load a previously saved grid.\n'
        initstring += '- (Optional:) Save the grid you filled in by pressing "Save" \n'
        initstring += '  (this will overwrite any previously saved grid)\n'
        initstring += '- Solve your sudoku by pressing "Solve"!\n\n'
        self.messages_text.insert(tk.INSERT,initstring)

    def setmode(self):
        mode = self.mode.get()
        if mode=='A':
            try:
                self.hint_button.grid_forget()
                self.reduce_button.grid_forget()
                for wid in self.candidate_frame.grid_slaves():
                    wid.grid_forget()
            except: pass
            self.solve_button.grid(row=0,column=0,columnspan=2,ipadx=self.bwidth,ipady=self.bheight)
        elif mode=='I':
            try:
                self.solve_button.grid_forget()
            except: pass
            self.hint_button.grid(row=0,column=0,ipadx=self.bwidth,ipady=self.bheight)
            self.reduce_button.grid(row=0,column=1,ipadx=self.bwidth,ipady=self.bheight)
            self.gridcells[0][0].focus()
            for k in range(self.gridsize): self.candidatecells[0][0][k]['button'].grid(row=0,column=k)

    def showcandidates(self,event,i,j):
        if self.mode.get()=='A': return None
        for wid in self.candidate_frame.grid_slaves():
            wid.grid_forget()
        for k,buttondict in enumerate(self.candidatecells[i][j]):
            buttondict['button'].grid(row=0,column=k)

    def getgrid(self):
        grid = np.zeros((self.gridsize,self.gridsize))
        for i in range(self.gridsize):
            for j in range(self.gridsize):
                val = self.gridcells[i][j].get()
                if(val==''): continue
                message =  '[notification:] ERROR: invalid value found in input grid: '+str(val)+'\n\n'
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

    def getcandidates(self):
        candidates = []
        for i in range(self.gridsize):
            candidates.append([])
            for j in range(self.gridsize):
                candidates[i].append([])
                for k in range(self.gridsize):
                    if self.candidatecells[i][j][k]['var'].get() == 1: candidates[i][j].append(k+1)
        return candidates

    def setgrid(self,grid,markfilled=False,markunfilled=False):
        for i in range(self.gridsize):
            for j in range(self.gridsize):
                val = self.gridcells[i][j].get()
                if(val==''):
                    newval = int(grid[i,j])
                    if newval==0:
                        if markunfilled:
                            self.gridcells[i][j].insert(0,'_')
                            self.gridcells[i][j].config(foreground='red')
                    else:
                        self.gridcells[i][j].insert(0,str(newval))
                        if markfilled: self.gridcells[i][j].config(foreground='green')

    def setcandidates(self,candidates):
        for i in range(self.gridsize):
            for j in range(self.gridsize):
                for k in range(self.gridsize):
                    if(not k+1 in candidates[i][j] and self.candidatecells[i][j][k]['var'].get() == 1):
                        self.candidatecells[i][j][k]['var'].set(0)

    def allcellswhite(self):
        for i in range(self.gridsize):
            for j in range(self.gridsize):
                self.gridcells[i][j].config({'background':'white'})
        
    def solve(self):
        self.allcellswhite()
        # display a message that solving will start
        message =  '[notification:] Now solving...\n'
        message += '                You can find the full log file below when done.\n\n'
        self.messages_text.insert(tk.INSERT,message)
        self.messages_text.see(tk.END)
        root.update() # needed for displaying text synchronously
        self.makelog()
        grid = self.getgrid()
        if grid is None: return None
        # redirect sys.stdout to text widget
        stdout = sys.stdout
        sys.stdout = StdOutRedirector(self.messages_text,root)
        # make a Sudoku object and solve it
        S = Sudoku(grid,logfilename=self.logfilename)
        (outputcode,message) = S.solve()
        # reset sys.stdout
        sys.stdout = stdout
        #self.readlog()
        message = '\n\n[notification:] '+message+'\n\n'
        self.messages_text.insert(tk.INSERT,message)
        self.messages_text.see(tk.END)
        self.setgrid(S.grid,markfilled=True,markunfilled=True)           
 
    def save(self):
        self.allcellswhite()
        abspath = os.path.abspath(os.path.dirname(__file__))
        fullpath = os.path.join(abspath,'fls')
        filename = fldlg.asksaveasfilename(initialdir=fullpath,
                    title='Save sudoku')
        filename = filename.rstrip('.txt')+'.txt'
        grid = self.getgrid()
        np.savetxt(filename,grid,fmt='%.1i')
        message =  '[notification:] Current grid saved successfully.\n'
        message += '                You can load it in future runs using the "Load" button.\n\n'
        self.messages_text.insert(tk.INSERT,message)
        self.messages_text.see(tk.END)
        
    def load(self):
        self.allcellswhite()
        abspath = os.path.abspath(os.path.dirname(__file__))
        fullpath = os.path.join(abspath,'fls')
        filename = fldlg.askopenfilename(initialdir=fullpath,
                    title='Select sudoku to load',
                    filetypes=(('txt files','*.txt'),('all files','*.*')))
        try:
            grid = np.loadtxt(filename)
            self.gridsize = len(grid)
            self.setgrid(grid)
            message =  '[notification:] Grid loaded successfully.\n\n'
            self.messages_text.insert(tk.INSERT,message)
            self.messages_text.see(tk.END)
        except:
            message = '[notification:] ERROR: grid could not be loaded from file.\n\n'
            self.messages_text.insert(tk.INSERT,message)
            self.messages_text.see(tk.END)
            return None

    def delete(self):
        self.allcellswhite()
        abspath = os.path.abspath(os.path.dirname(__file__))
        fullpath = os.path.join(abspath,'fls')
        filename = fldlg.askopenfilename(initialdir=fullpath,
                    title='Select sudoku to remove',
                    filetypes=(('txt files','*.txt'),('all files','*.*')))
        filename = str(filename)
        if len(filename)==0: return None
        try:
            os.system('rm '+filename)
            message = '[notification:] File successfully deleted.\n\n'
            self.messages_text.insert(tk.INSERT,message)
            self.messages_text.see(tk.END)
        except:
            message = '[notification:] ERROR: file could not be deleted.\n\n'
            self.messages_text.insert(tk.INSERT,message)
            self.messages_text.see(tk.END)
    
    def clear(self):
        self.allcellswhite()
        for i in range(self.gridsize):
            for j in range(self.gridsize):
                self.gridcells[i][j].delete(0,tk.END)
                self.gridcells[i][j].config(foreground='black')
                for k in range(self.gridsize):
                    self.candidatecells[i][j][k]['var'].set(1)
        message = '[notification:] Current grid cleared. \n\n'
        self.messages_text.insert(tk.INSERT,message)
        self.messages_text.see(tk.END)

    def makelog(self):
        abspath = os.path.abspath(os.path.dirname(__file__))
        fullpath = os.path.join(abspath,self.logfilename)
        if os.path.exists(fullpath): os.system('rm '+fullpath)
        fname = fullpath[fullpath.rfind('/')+1:]
        dirname = fullpath[:fullpath.rfind('/')]
        if not os.path.exists(dirname): os.makedirs(dirname)
        os.chdir(dirname)
        lf = open(fname,'w')
        lf.close()
        os.chdir(abspath)    

    def readlog(self):
        lf = open(self.logfilename,'r')
        message = lf.read()
        self.messages_text.insert(tk.INSERT,message)
        self.messages_text.see(tk.END)

    def hint(self):
        self.allcellswhite()
        grid = self.getgrid()
        candidates = self.getcandidates()
        S = SudokuHelper(grid,candidates,logfilename=self.logfilename,appendlogfile=True)
        (message,cells) = S.hint()
        self.messages_text.insert(tk.INSERT,message)
        self.messages_text.see(tk.END)
        for c in cells: self.gridcells[c[0]][c[1]].config({'background':'cyan'})

    def reduce(self):
        self.allcellswhite()
        grid = self.getgrid()
        candidates = self.getcandidates()
        S = SudokuHelper(grid,candidates,logfilename=self.logfilename,appendlogfile=True)
        ncands= S.ncands
        S.reducecandidates()
        self.setgrid(S.grid,markfilled=True,markunfilled=False)
        self.setcandidates(S.candidates)
        if S.issolved():
            (outputcode,message) = S.terminate()
            message = '\n\n[notification:] '+message+'\n\n'
            self.messages_text.insert(tk.INSERT,message)
            self.messages_text.see(tk.END)
            return 
        ncandsnew = S.ncands
        message = '[reduce:] '
        if ncandsnew < ncands:
            message += 'number of candidates erased: '+str(ncands-ncandsnew)+'\n\n'
        else:
            message += 'no additional candidates could be erased!\n\n'
        self.messages_text.insert(tk.INSERT,message)
        self.messages_text.see(tk.END)
        
        

root = tk.Tk()
gui = SudokuSolverGUI(root)
root.mainloop()
