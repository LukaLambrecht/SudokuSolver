# Tests for swordfish pattern recognition

Examples from here: https://www.learn-sudoku.com/x-wing.html and here: https://www.learn-sudoku.com/swordfish.html.

Check by using the GUI.
Load one of the examples and perform basic reduction until no further candidates can be erased.
Then ask for a hint, it should hopefully show the swordfish pattern (potentially after a few other hints)...

Results (as of 06/09/2024):
`example_xwing.txt`: succes
`example_swordfish.txt`: not so clear. Another swordfish pattern than the one given in the example is found, but it seems to be correct as well. In fully automatic mode, this example cannot be solved without forcing chain, but in interactive mode it can; there must be some inefficiency in fully automatic solving.
