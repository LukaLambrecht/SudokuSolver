# SudokuSolver
Simple, lightweight and easy-to-use python program (with GUI) to solve sudokus.  
Both interactive and fully automatic solving modes are available.  
Version March 2021. 

# How to use this program?
- Prerequisites:  
  -- You will need the python programming language.  
     This project was developed and tested using python 2.7, but it should work with python 3 as well (tested in 3.8).
  -- The following python modules must be installed: numpy, itertools, os, sys, Tkinter, copy  
     (all except numpy are in the standard library so should be installed if you have python).
- Clone or download the files in this repository onto your local computer.  
  (If you don't know how to do this, the easiest option is probably to click the green button that says ' Code ', then ' Download ZIP ', then move the downloaded zip file to wherever you want this program to be located, then unzip it using any unzipping tool.)  
  No further compilation or installation is required.
- Open a terminal and navigate to the ' SudokuSolver ' folder (depends on where you downloaded/moved/unzipped it) and run the program using the command ' python sudokusolver.py '. Alternatively, start your favorite python IDE and open and run the file ' sudokusolver.py ' in the ' SudokuSolver ' folder. Note that the folder might also be called ' SudokuSolver-master ' instead of ' SudokuSolver ' depending on how you downloaded the project.
- The previous step will pop up a window with an empty sudoku.  
  In order to fill a cell, click it and type the number that is supposed to go in it.  
  Fill all the cells whose content is known at the start.
- Click the ' Solve ' button. 
- There is also an ' Interactive ' mode which instead of solving will show you hints.  
  Either fill a cell by clicking on it and typing the correct number, or remove a candidate number for a given cell by clicking on it and then clicking on the candidate number in the line at the bottom (it should turn red). Click the ' Reduce ' button to make the program perform the most basic operations for you and the ' Hint ' button whenever you need a new hint.

# Main references for the implemented methods
https://www.kristanix.com/sudokuepic/sudoku-solving-techniques.php  
https://www.learn-sudoku.com/advanced-techniques.html
