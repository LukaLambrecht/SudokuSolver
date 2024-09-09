### imports

# external modules
import sys
import os
import numpy as np
try:
    import Tkinter as tk
    import ScrolledText as scrtxt
    import tkFileDialog as fldlg
except ImportError: 
    import tkinter as tk
    import tkinter.scrolledtext as scrtxt
    import tkinter.filedialog as fldlg

# local modules
sys.path.insert(0, os.path.abspath('./src'))
from sudoku import Sudoku
from sudokuhelper import SudokuHelper


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


def bflayout(bf):
    ### helper function for setting the layout of a button frame
    bf.config(
      width = 250,
      pady = 5,
      padx = 5,
      #borderwidth = 1,
      #relief = tk.RIDGE
    )


class SudokuSolverGUI:
    
    def __init__(self, master):
        self.master = master
        master.title("SudokuSolver GUI")
		
        # non-widget attributes
        self.sudoku = None
        self.logfilename = 'logs/currentlog.txt'

        # set global geometry parameters
        self.grid_frame_nrow = 5
        self.grid_frame_ncol = 1
        self.candidate_frame_nrow = 1
        self.candidate_frame_ncol = 1
        self.messages_text_nrow = 1
        self.messages_text_ncol = 3
        self.bpadx = 20
        self.bpady = 10
        self.bwidth = 10
        self.bheight = 1

        # define a frame for the sudoku cells
        self.grid_frame = tk.Frame(master,width=200)
        self.grid_frame.grid(row=0,column=0,
                             rowspan=self.grid_frame_nrow,columnspan=self.grid_frame_ncol,
                             padx=10,pady=10)
        # build frame for the candidate cells
        self.candidate_frame = tk.Frame(master,height=30,width=200)
        self.candidate_frame.grid(row=self.grid_frame_nrow,column=0,
                                  rowspan=self.candidate_frame_nrow,
                                  columnspan=self.candidate_frame_ncol,
                                  padx=10,pady=10)
        
        self.gridsize = 9 # default, can be changed with a button
        self.gridsize_var = tk.IntVar(master, value=self.gridsize)
        self.blocksize = int(np.sqrt(int(self.gridsize)))
        self.blockframes = []
        self.gridcells = []
        self.candidatecells = []
        self.buildgrid(master=master)

        # define several frames for the action buttons
        # overall frame to group all sub-frames with buttons
        self.buttons_frame = tk.Frame(master, width=200)
        self.buttons_frame.grid(row=0, column=1, rowspan=self.grid_frame_nrow)

        # frame for mode button
        self.mode_frame = tk.Frame(self.buttons_frame)
        bflayout(self.mode_frame)
        self.mode_frame.grid(row=0, column=0)
        
        self.mode = tk.StringVar()
        self.mode.set("A")
        
        self.mode_frame_label = tk.Label(self.mode_frame, text='Mode')
        self.mode_frame_label.grid(row=0, column=0, columnspan=2)
        
        self.auto_button = tk.Radiobutton(self.mode_frame, text='Automatic', indicatoron=False,
                                variable=self.mode, value="A", command=self.setmode,
                                width=self.bwidth, height=self.bheight)
        self.auto_button.grid(row=1, column=0, ipadx=self.bpadx, ipady=self.bpady)
        
        self.inter_button = tk.Radiobutton(self.mode_frame, text='Interactive', indicatoron=False,
                                variable=self.mode, value="I", command=self.setmode,
                                width=self.bwidth, height=self.bheight)
        self.inter_button.grid(row=1,column=1, ipadx=self.bpadx, ipady=self.bpady)

        # frame for solving or related actions (depending on automatic or interactive mode)
        self.solve_frame = tk.Frame(self.buttons_frame)
        bflayout(self.solve_frame)
        self.solve_frame.grid(row=1, column=0)

        self.solve_frame_label = tk.Label(self.solve_frame, text='Solving')
        self.solve_frame_label.grid(row=0, column=0, columnspan=2)

        self.solve_button = tk.Button(self.solve_frame, text='Solve', command=self.solve)
        self.solve_button.grid(row=1, column=0, ipadx=self.bpadx, ipady=self.bpady)
		
        self.abort_button = tk.Button(self.solve_frame, text='Abort', command=self.abort)
        self.abort_button.grid(row=1, column=1, ipadx=self.bpadx, ipady=self.bpady)
       
        self.hint_button = tk.Button(self.solve_frame,text='Hint',command=self.hint)

        self.reduce_button = tk.Button(self.solve_frame,text='Reduce',command=self.reduce)

        self.show_candidate_window_button = tk.Button(self.solve_frame,text='Show candidates',
                                                      command=self.show_candidate_window)

        # frame for saving and loading
        self.io_frame = tk.Frame(self.buttons_frame)
        bflayout(self.io_frame)
        self.io_frame.grid(row=2, column=0)

        self.io_frame_label = tk.Label(self.io_frame, text='Saving / loading')
        self.io_frame_label.grid(row=0, column=0, columnspan=2)

        self.save_button = tk.Button(self.io_frame, text='Save', command=self.save)
        self.save_button.grid(row=1, column=0, ipadx=self.bpadx, ipady=self.bpady)
        
        self.load_button = tk.Button(self.io_frame, text='Load', command=self.load)
        self.load_button.grid(row=1, column=1, ipadx=self.bpadx, ipady=self.bpady)

        # frame for clearing and closing
        self.close_frame = tk.Frame(self.buttons_frame)
        bflayout(self.close_frame)
        self.close_frame.grid(row=3, column=0)

        self.close_frame_label = tk.Label(self.close_frame, text='Change / clear / close')
        self.close_frame_label.grid(row=0, column=0, columnspan=2)

        self.change_size_button = tk.Button(self.close_frame,
                text='Change size', command=self.open_change_size_window)
        self.change_size_button.grid(row=1, column=0, columnspan=2, ipadx=self.bpadx, ipady=self.bpady)


        self.clear_button = tk.Button(self.close_frame, text='Clear', command=self.clear)
        self.clear_button.grid(row=2, column=0, ipadx=self.bpadx, ipady=self.bpady)
        
        self.close_button = tk.Button(self.close_frame, text='Close', command=master.destroy)
        self.close_button.grid(row=2, column=1, ipadx=self.bpadx, ipady=self.bpady)

        # make window for log text
        self.messages_text = scrtxt.ScrolledText(master, width=75, height=25)
        self.messages_text.grid(row=self.grid_frame_nrow+self.candidate_frame_nrow, column=0,
                            columnspan=3)
        initstring = 'Welcome to the Sudoku Solver!\n'
        initstring += '- Click on the cells in the grid above to set the intial values \n'
        initstring += '  or press "Load" to load a previously saved grid.\n'
        initstring += '- (Optional:) Save the grid you filled in by pressing "Save" \n'
        initstring += '  (this will overwrite any previously saved grid)\n'
        initstring += '- Solve your sudoku by pressing "Solve"!\n\n'
        self.messages_text.insert(tk.INSERT,initstring)

    def buildgrid(self, master=None):

        # remove previous widgets
        for wid in self.grid_frame.grid_slaves(): wid.grid_forget()
        for wid in self.candidate_frame.grid_slaves(): wid.grid_forget()

        # build grid frames
        self.blockframes = []
        for i in range(self.gridsize):
            self.blockframes.append(tk.LabelFrame(self.grid_frame,text='',
                                    relief='solid',borderwidth=1))
            self.blockframes[i].grid(row=divmod(i,self.blocksize)[0],
                                     column=divmod(i,self.blocksize)[1])
        
        # build grid cells
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

        # build candidate cells
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

    def setmode(self):
        ### change mode from automatic to interactive or the other way around
        mode = self.mode.get()
        if mode=='A':
            # switch from interactive to automatic
            try:
                self.hint_button.grid_forget()
                self.reduce_button.grid_forget()
                self.show_candidate_window_button.grid_forget()
                for wid in self.candidate_frame.grid_slaves():
                    wid.grid_forget()
            except: pass
            self.solve_button.grid(row=1, column=0, ipadx=self.bpadx, ipady=self.bpady)
            self.abort_button.grid(row=1, column=1, ipadx=self.bpadx, ipady=self.bpady)
        elif mode=='I':
            # switch from automatic to interactive
            try:
                self.solve_button.grid_forget()
                self.abort_button.grid_forget()
            except: pass
            self.hint_button.grid(row=1, column=0, ipadx=self.bpadx, ipady=self.bpady)
            self.reduce_button.grid(row=1, column=1, ipadx=self.bpadx, ipady=self.bpady)
            self.show_candidate_window_button.grid(row=2, column=0, columnspan=2,
                    ipadx=self.bpadx, ipady=self.bpady)
            self.gridcells[0][0].focus()
            for k in range(self.gridsize): self.candidatecells[0][0][k]['button'].grid(row=0, column=k)

    def open_change_size_window(self):
        self.change_size_window = tk.Toplevel(self.master)
        self.change_size_window.title("Choose grid size")
        # size choosing widgets
        size_frame = tk.Frame(self.change_size_window)
        size_frame.grid(row=0, column=0)
        label = tk.Label(size_frame, text="Grid size:")
        label.grid(row=0, column=0)
        size_options = [4, 9, 16]
        size_widget = tk.OptionMenu(size_frame, self.gridsize_var, *size_options)
        size_widget.grid(row=0, column=1)
        # buttons for accepting or canceling
        buttons_frame = tk.Frame(self.change_size_window)
        buttons_frame.grid(row=1, column=0)
        ok_button = tk.Button(buttons_frame, text='Ok', command=self.change_size)
        ok_button.grid(row=0, column=0, ipadx=self.bpadx, ipady=self.bpady)
        cancel_button = tk.Button(buttons_frame, text='Cancel', command=self.close_change_size_window)
        cancel_button.grid(row=0, column=1, ipadx=self.bpadx, ipady=self.bpady)

    def close_change_size_window(self):
        self.change_size_window.destroy()

    def change_size(self):
        newgridsize = int(self.gridsize_var.get())
        newblocksize = int(np.sqrt(newgridsize))
        self.clear()
        if newgridsize==self.gridsize: return
        self.gridsize = newgridsize
        self.blocksize = newblocksize
        self.buildgrid()
        self.change_size_window.destroy()

    def showcandidates(self,event,i,j):
        if self.mode.get()=='A': return None
        for wid in self.candidate_frame.grid_slaves():
            wid.grid_forget()
        for k,buttondict in enumerate(self.candidatecells[i][j]):
            buttondict['button'].grid(row=0,column=k)

    def show_candidate_window(self):
        ### open a separate window with all remaining candidates nicely shown
        # create a window
        window = tk.Toplevel(self.master)
        window.title('Remaining candidates')
        # create a frame
        candidates_frame = tk.Frame(window, width=200)
        candidates_frame.grid(row=0,column=0)
        # create the frames (for solid lines around boxes)
        blockframes = []
        for i in range(self.gridsize):
            blockframes.append(tk.LabelFrame(candidates_frame,
                                 text='',
                                 relief='solid',
                                 borderwidth=1))
            blockframes[i].grid(row=divmod(i,self.blocksize)[0],
                                column=divmod(i,self.blocksize)[1])
        # get candidates and find maximum length
        candidates = self.getcandidates()
        lens = []
        for i in range(self.gridsize):
            for j in range(self.gridsize):
                lens.append(len(candidates[i][j]))
        maxlen = max(lens)
        txtlen = maxlen*2-1
        # make and fill the text boxes
        for i in range(self.gridsize):
            for j in range(self.gridsize):
                blockn = divmod(i,self.blocksize)[0]*self.blocksize + divmod(j,self.blocksize)[0]
                label = tk.Text(blockframes[blockn], font="Calibri 15", height=1, width=txtlen)
                thiscandidates = candidates[i][j]
                cstr = ' '.join([str(el) for el in thiscandidates])
                label.insert(tk.END, cstr)
                label.config(state=tk.DISABLED)
                label.grid(row=divmod(i,self.blocksize)[1],column=divmod(j,self.blocksize)[1])

    def getgrid(self):
        grid = np.zeros((self.gridsize,self.gridsize))
        for i in range(self.gridsize):
            for j in range(self.gridsize):
                val = self.gridcells[i][j].get()
                if(val==''): continue
                if(val=='_'): continue
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
        self.sudoku = Sudoku(grid,logfilename=self.logfilename)
        (outputcode,message) = self.sudoku.solve()
        # reset sys.stdout
        sys.stdout = stdout
        #self.readlog()
        message = '\n\n[notification:] '+message+'\n\n'
        self.messages_text.insert(tk.INSERT,message)
        self.messages_text.see(tk.END)
        self.setgrid(self.sudoku.grid,markfilled=True,markunfilled=True)
		
    def abort(self):
        if self.sudoku is None: return
        if not isinstance(self.sudoku,Sudoku): return
        self.sudoku.setbreak()
 
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
            newgridsize = int(len(grid))
            newblocksize = int(np.sqrt(newgridsize))
        except:
            message = '[notification:] ERROR: grid could not be loaded from file.\n\n'
            self.messages_text.insert(tk.INSERT,message)
            self.messages_text.see(tk.END)
            return None
        # if file loading was successfull, clear any previous grid
        # before setting the new one
        self.clear()
        # special care is needed when grid size is different
        if newgridsize!=self.gridsize:
            self.gridsize = newgridsize
            self.blocksize = newblocksize
            self.buildgrid()
        # set the new grid
        self.setgrid(grid)
        message =  '[notification:] Grid loaded successfully.\n\n'
        self.messages_text.insert(tk.INSERT,message)
        self.messages_text.see(tk.END)

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
