# Documentation of Project Implementation for IPP 2022/2023 part 1

Name and surname: Kryštof Paulík

Login: xpauli08

## Libraries

In the first part of the project, I used only one library to make outputting XML easier:

- _[XMLWriter](https://www.php.net/manual/en/book.xmlwriter.php)_

## Functions

- **Syntax** - for checking the correct syntax of arguments, I used regular expressions, which in my opinion made the program more lightweight, because it allowed me to check more complex expressions with just a few lines of code
- **XML** - based on the number and type of arguments, I have created functions generating different instructions. Before generating the instruction, each function always checks the number of operands and type of operands.

## Program structure - parse.php

Because I'm not so familiar with PHP and did not want to complicate things, I decided to put all functions as well as the main body of the program into one file.

Among other things, the program starts by creating a XMLWriter object which is then used to generate XML, then the arguments get checked and eventually the help can be printed. Then the main program loop begins.

In each iteration of the loop, one line is read from the stdin, it is trimmed of all the comments and in case of an empty line, it is removed completely.

Each line is "exploded" into words and a switch is used to determine what XML to generate based on the first word, which should always be the instruction. If everything goes well, the program moves onto the next line.

# Documentation of Project Implementation for IPP 2022/2023 part 2

Name and surname: Kryštof Paulík

Login: xpauli08

## Introduction

The assigment was to crate a `interpret.py` script in the language Python 3.10.
Script `interpret.py` would analyze and interpret an XML file with the actual program.

## Modules

The script uses the following modules:

- _[sys](https://docs.python.org/3/library/sys.html)_
- _[argparse](https://docs.python.org/3/library/argparse.html)_
- _[xml.etree.ElementTree](https://docs.python.org/3/library/xml.etree.elementtree.html)_
- _[re](https://docs.python.org/3/library/re.html)_

## Implementation

The script `interpret.py` reads the XML represetation and the input from files or from standard input based on the script arguments. The output (if there is any) is written on the standard output, any error messages are written on the standard error output.

The script starts by checking program arguments. For that, an `argparse` library is used. The function `check_input_arguments()` validates the arguments and sets the corresponding variables.

The next thing is loading the XML file. For that `xml.etree.ElementTree` is used. Once the XML file is loaded, the script goes through the elements and checks their attributes. If everything went right, the next step is to load each instruction along with it's arguments.

The class `Instruction` is used to save individual instructions, which are then stored into a global list `instructions`. Before saving the instruction to the list, the script also needs to loop through it's arguments and add them to the instruction. Arguments have their own `Argument` class. The arguments of each instruction are then sorted using the `sort_arguments()` function and the instruction is finally added to the list.

Before the interpretations begin, the script goes through the `instructions` list, finds all the labels and saves their name and position in the global `labels` list.

The interpretation is in the form of a loop. During each cycle, one instruction is being interpreted. Variables have their own `Variable` class, which is for all kinds of stuff, such as getting the variable type, value, defining the variable and so on.

The interpretation ends with an error or with depleting the instructions to interpret and the program ends with a return code of 0.
