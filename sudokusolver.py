# imports
import sys
import numpy as np
sys.path.insert(0,'./src')
from sudoku import Sudoku
try: import Tkinter as tk
except ImportError: import tkinter as tk

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
        initstring += '- Click on the cells in the grid above to set the intial values \n'
        initstring += '  or press "Load" to load a previously saved grid.\n'
        initstring += '- (Optional:) Save the grid you filled in by pressing "Save" \n'
        initstring += '  (this will overwrite any previously saved grid)\n'
        initstring += '- Solve your sudoku by pressing "Solve"!\n\n'
        self.messages_text.insert(tk.INSERT,initstring)
        
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
        np.savetxt('./fls/sudokusave.txt',grid,fmt='%.1i')
        message =  '[notification:] Current grid saved successfully.\n'
        message += '                You can load it in future runs using the "Load" button.\n\n'
        self.messages_text.insert(tk.INSERT,message)
        self.messages_text.see(tk.END)
        
    def load(self):
        try:
            grid = np.loadtxt('./fls/sudokusave.txt')
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
