#
# FIT VUT 2023 - IPP Project Implemenation part 2
# Interpret of IPPcode23 language
#
# File: interpret.py
# Author(s): xpauli08
#

import sys
import argparse
import xml.etree.ElementTree as ElementTree
import re

ERR_OK = 0
ERR_PARAM = 10
ERR_IN_FILE = 11
ERR_OUT_FILE = 12
ERR_XML_FORMAT = 31
ERR_XML_STRUCT = 32
ERR_SEMANTIC = 52
ERR_BAD_TYPE = 53
ERR_VAR_MISSING = 54
ERR_FRAME_MISSING = 55
ERR_VALUE_MISSING = 56
ERR_OPERAND_VALUE = 57
ERR_STRING = 58
ERR_INTERNAL = 99

opcodes_and_args = [
   ['MOVE', 2],
   ['CREATEFRAME', 0],
   ['PUSHFRAME', 0],
   ['POPFRAME', 0],
   ['DEFVAR', 1],
   ['CALL', 1],
   ['RETURN', 0],
   ['PUSHS', 1],
   ['POPS', 1],
   ['ADD', 3],
   ['SUB', 3],
   ['MUL', 3],
   ['IDIV', 3],
   ['LT', 3],
   ['GT', 3],
   ['EQ', 3],
   ['AND', 3],
   ['OR', 3],
   ['NOT', 2],
   ['INT2CHAR', 2],
   ['STRI2INT', 3],
   ['READ', 2],
   ['WRITE', 1],
   ['CONCAT', 3],
   ['STRLEN', 2],
   ['GETCHAR', 3],
   ['SETCHAR', 3],
   ['TYPE', 2],
   ['LABEL', 1],
   ['JUMP', 1],
   ['JUMPIFEQ', 3],
   ['JUMPIFNEQ', 3],
   ['EXIT', 1],
   ['DPRINT', 1],
   ['BREAK', 0],
   ['CLEARS', 0],
   ['ADDS', 0],
   ['SUBS', 0],
   ['MULS', 0],
   ['IDIVS', 0],
   ['LTS', 0],
   ['GTS', 0],
   ['EQS', 0],
   ['ANDS', 0],
   ['ORS', 0],
   ['NOTS', 0],
   ['INT2CHARS', 0],
   ['STRI2INTS', 0],
   ['JUMPIFEQS', 1],
   ['JUMPIFNEQS', 1],
   ['INT2FLOAT', 2],
   ['FLOAT2INT', 2]
]

# List of all program instructions
instructions = []

# Frames
global_frame = {}
local_frames = []
temporary_frame = {}

# Counter for the READ function
read_line_number = 0

# Bool for keeping track of temporary frame status
tf_not_created = True

# Stack and call stack
stack = []
call_stack = []

################################# CLASSES ###################################

class Argument:
  
   def __init__(self, arg_tag: str, arg_type: str, value):
      self.set_order(arg_tag)
      self.set_type(arg_type)
      self.set_value(value)

   def set_order(self, arg_tag):
      if arg_tag == "arg1":
         self._order = 1
      elif arg_tag == "arg2":
         self._order = 2
      elif arg_tag == "arg3":
         self._order = 3
      else:
         print_error('Error: invalid instruction argument', ERR_XML_STRUCT)

   def set_type(self, arg_type):
      self._type = arg_type
    
   def set_value(self, arg_value):
      self._value = arg_value
   
   def get_order(self):
      return self._order

   def get_type(self):
      return self._type

   def get_value(self):
      return self._value

class Instruction:

   def __init__(self, opcode: str, order: int):
      self.set_opcode(opcode)
      self.set_order(order)
      self._args = []

   def set_opcode(self, opcode):
      self._opcode = opcode

   def set_order(self, order):
      self._order = order

   def get_opcode(self):
      return self._opcode.upper()

   def get_order(self):
      return self._order     

   def add_arg(self, arg_tag, arg_type, value):
      self._args.append(Argument(arg_tag, arg_type, value))

   # Used when I need to sort the arguments
   def set_args(self, args):
      self._args = args

   def get_args(self):
      return self._args
   
class Variable:

   # Access to global variables
   global global_frame
   global local_frames
   global temporary_frame
   global tf_not_created

   def __init__(self, name, value, frame):
      self._name = name
      self._value = value
      self._frame = frame
      self._type = None
   
   def get_name(self):
      return self._name

   def get_value(self):
      return self._value
   
   # DEFVAR
   def create(self):

      frame = self.get_frame()

      # If variable already exists print an error
      if self._name in frame:
         print_error(f'Redefinition of variable: {self._name}', ERR_SEMANTIC)
      
      # Assing it's value and type to chosen frame
      frame[self._name] = [self._value, self._type]
   
   # Assign value to the variable
   def set(self):

      frame = self.get_frame()

      # If variable exists, set it's value and type
      if self._name in frame:
         frame[self._name] = [self._value, self._type]
      else:
            print_error(f'Error: undefined variable {self._name}', ERR_VAR_MISSING)

   def get_value(self):

      frame = self.get_frame()
      
      # If variable exists, get it's value, if it's unset, raise an error
      if self._name in frame:
         self._value = frame[self._name][0]
         if self._value == None:
            print_error(f'Error: unset variable value {self._name}', ERR_VALUE_MISSING)
         else:
            return self._value
      else:
         print_error('Error: undefined variable', ERR_VAR_MISSING)
   
   # Same as get_value() but without the 'unset variable' check
   # Used in SETCHAR and TYPE instructions
   def get_value_unset(self):

      frame = self.get_frame()

      # If variable exists, retrieve it's value, even if it's unset
      if self._name in frame:
         self._value = frame[self._name][0]
         return self._value
      else:
         print_error('Error: undefined variable', ERR_VAR_MISSING)

   def set_type(self, type):
      self._type = type   

   def get_type(self):

      frame = self.get_frame()

      # If variable exists, retrieve it's type
      if self._name in frame:
         self._type = frame[self._name][1]
         if self._type == None:
            self._type = get_variable_type(self.get_value())
         
         return self._type
      else:
         print_error('Error: undefined variable', ERR_VAR_MISSING)
   
   # Same as get_type(), but without the 'unset variable' check
   # Used in the TYPE instruction
   def get_type_unset(self):

      frame = self.get_frame()

      # If variable exists, retrieve it's type
      if self._name in frame:
         self._type = frame[self._name][1]
         if self._type == None:
            self._type = get_variable_type(self.get_value_unset())
         
         return self._type
      else:
         print_error('Error: undefined variable', ERR_VAR_MISSING)

   def get_frame(self):
      
      # Choose a frame
      frame = None
      if self._frame == 'GF':
         frame = global_frame
      
      elif self._frame == 'TF':
         if tf_not_created == True:
            print_error('Error: DEFVAR - undefined temporary frame', ERR_FRAME_MISSING)
         frame = temporary_frame
      
      elif self._frame == 'LF':
         if len(local_frames) ==  0:
            print_error('Error: DEFVAR - undefined local frame', ERR_FRAME_MISSING)
         frame = local_frames[-1]
      
      return frame



################################# FUNCTIONS ###################################

def print_error(err_message, err_code):
   sys.stderr.write(err_message + '\n')
   exit(err_code)

# Check program input arguments
def check_input_arguments():
   # Help message
   help_message = "Interpret of the IPPcode23 language.\n\nArguments:\n  --source SOURCE  File with the XML representation of the source code.\n  --input INPUT    File with the inputs for the actual interpretation of the given source code."

   # Create an instance of ArgumentParser and set the help message
   parser = argparse.ArgumentParser(description=help_message)

   # Define arguments
   parser.add_argument('--source', type=str, help='file with the XML representation of the source code')
   parser.add_argument('--input', type=str, help='file with the inputs for the actual interpretation of the given source code')

   # Parse the command line arguments
   args = parser.parse_args()

   # At least one parameter needs to be present
   if not args.source and not args.input:
      print_error('At least one of --source or --input must be present, ERR_PARAM')
   
   return args.source, args.input

# Sorts a list of arguments
def sort_arguments(arguments):

   # There can be instructions with no arguments
   if len(arguments) == 0:
      return []

   # Check that there are no duplicate tags
   if len(set(arg.get_order() for arg in arguments)) != len(arguments):
      print_error('Error: duplicate argument tags', ERR_XML_STRUCT)

   # Check list length and order values
   if len(arguments) == 1:
         if arguments[0].get_order() != 1:
            print_error('Error: wrong argument numbers', ERR_XML_STRUCT)
   elif len(arguments) == 2:
         if not all([arg.get_order() in [1, 2] for arg in arguments]) or sorted([arg.get_order() for arg in arguments]) != [1, 2]:
            print_error('Error: wrong argument numbers', ERR_XML_STRUCT)
   elif len(arguments) == 3:
         if not all([arg.get_order() in [1, 2, 3] for arg in arguments]) or sorted([arg.get_order() for arg in arguments]) != [1, 2, 3]:
            print_error('Error: wrong argument numbers', ERR_XML_STRUCT)

   # If everything is ok, return the sorted list
   return sorted(arguments, key=lambda arg: arg.get_order())

# Check instruction attributes
def check_instruction_attributes(list: Instruction):
   
   # Create the seen instruction orders set
   seen_inst = set()
   for inst in list:
      # Check number of opcode attribute + number of arguments
      valid = False

      # Loop through the global opcodes_and_args list
      # and find the opcode and argument numbers combination
      for op in opcodes_and_args:
         if inst.get_opcode().upper() == op[0] and len(inst.get_args()) == op[1]:
            valid = True
            break
      if not valid:
         print_error('Error: wrong opcode value or wrong number of instruction arguments', ERR_XML_STRUCT)
         
      # Check order attribute
      try:
         order = int(inst.get_order())
      except:
         print_error('Error: order must be an integer', ERR_XML_STRUCT)
      
      # More order checks
      if order < 1:
         print_error('Error: negative order', ERR_XML_STRUCT)
      if order in seen_inst:
         print_error('Error: duplicate instruction order', ERR_XML_STRUCT)
      seen_inst.add(order)

# Not really used, but if anything goes wrong with the
# get_type() Variable function, this is the replacement
def get_variable_type(value):

   if value == None:
      return 'nil'
   
   if isinstance(value, int):
      return 'int'
   
   elif isinstance(value, str):
      if value in ['true', 'false']:
         return 'bool'
      if value == 'nil':
         return 'nil'
      return 'string'

# Find and replace all escape sequences in a string   
def replace_escape_sequences(text):

   if text != None:
      # Use regular expression to find escape sequences
      pattern = re.compile(r"\\(\d\d\d)")
      matches = pattern.findall(text)
      
      # Replace escape sequences with corresponding ascii characters
      for match in matches:
         text = text.replace("\\" + match, chr(int(match)))
      
   return text

################################ BODY ###################################

def main():

   # Global variables
   global instructions
   global temporary_frame
   global local_frames
   global stack
   global call_stack

   # Get the source and input file names
   source_name, input_name = check_input_arguments()

   # This is where the source will be parsed
   tree = None
   # This is where the input will be
   input_file = None

   # Load the tree and input file variables based on the input arguments
   if source_name is not None:
      # Load XML
      try:
         tree = ElementTree.parse(source_name)
      except ElementTree.ParseError:
         print_error('Error: invalid XML format', ERR_XML_FORMAT)
   
   if input_name is not None:
      input_file = open(input_name).read()

   # If stdin input is needed, read it into the appropriate variable
   if input_file is None:
      input_file = sys.stdin.read()
   
   if tree is None:
      # Load XML
      try:
         tree = ElementTree.parse(sys.stdin)
      except ElementTree.ParseError:
         print_error('Error: invalid XML format', ERR_XML_FORMAT)   

   # End of 'Load the tree and input file variables'     

   root = tree.getroot()

   # Check XML
   root_attributes = list(root.attrib.keys())

   # Check program attributes
   if not((set(root_attributes) == {'language'}) or (set(root_attributes) == {'language', 'description'}) or (set(root_attributes) == {'language', 'name'}) or (set(root_attributes) == {'language', 'name', 'description'})):
      print_error('Error: wrong program attributes', ERR_XML_STRUCT)

   # Check program attribute 'language'
   if root.attrib['language'].upper() != 'IPPCODE23':
      print_error('Error: wrong program code, should be IPPcode23', ERR_XML_STRUCT)

   # Child is instruction in this case
   for child in root:

      if child.tag != 'instruction':
         print_error('Error: unexpected XML structure', ERR_XML_STRUCT)

      # Each instruction must have an order and opcode
      child_attributes = list(child.attrib.keys())
      if not(set(child_attributes) == {'order', 'opcode'}):
         print_error('Error: unexpected XML structure', ERR_XML_STRUCT)

      # Sub element means arguments of instruction
      for sub_element in child:
         sub_element_attributes = list(sub_element.attrib.keys())

         # Each argument must have a type
         if not(set(sub_element_attributes) == {'type'}):
            print_error('Error: unexpected XML structure', ERR_XML_STRUCT)

         # Check type value
         if not(sub_element.attrib['type'] in ['int', 'bool', 'string', 'nil', 'label', 'type', 'var', 'float', 'symb']):
            print_error('Error: unexpected XML structure', ERR_XML_STRUCT)

         # Check the tag itself
         if not(re.match(r"\b(arg1|arg2|arg3)\b", sub_element.tag)):
            print_error('Error: wrong argument numbers', ERR_XML_STRUCT)
    
   # Put all instructions in one list
   for child in root:
      instruction = Instruction(child.attrib['opcode'], child.attrib['order'])

      # For each instruction, add it's arguments
      for sub_element in child:
         sub_text = None
         if sub_element.text != None:
            sub_text = sub_element.text.strip()
            
         instruction.add_arg(sub_element.tag, sub_element.attrib['type'], sub_text)

      # Sort the arguments of each instruction and then add it to the list
      instruction.set_args(sort_arguments(instruction.get_args()))
      instructions.append(instruction)

   # Sort instructions list
   try:
      instructions = sorted(instructions, key=lambda inst: int(inst.get_order()))
   except:
      print_error('Error: string order', ERR_XML_STRUCT)
   
   # For each instruction in the list, check its attributes
   check_instruction_attributes(instructions)
      
       
   #for i in instructions:
   #   print(str(i.get_order()) + " " + str(i.get_opcode()))
    
   # Interpret instructions
   # for i in instructions:
   #      interpret(i)

   labels = {}

   # Save all labels and check duplicity
   i = 0
   for inst in instructions:
      if inst.get_opcode() == 'LABEL':
         value = inst.get_args()[0].get_value()
         if value in labels:
            print_error(f'Error: duplicate label: {value}', ERR_SEMANTIC)
         
         labels[value] = i
      i += 1
   
   # Switch
   i = 0
   while i < len(instructions):
      inst = instructions[i]
      global tf_not_created

      opcode = inst.get_opcode().upper()
      
      if opcode == "MOVE":
         
         arg1 = inst.get_args()[0]
         arg2 = inst.get_args()[1]

         value = None
         var_type = None

         # Check for type compatibility and get the value from either a constant or another variable
         if (arg1.get_type() != 'var'):
            print_error('Error: first argument of MOVE must be of type var', ERR_BAD_TYPE)

         if (arg2.get_type() in ['int', 'bool', 'string', 'nil', 'float']):
            value = arg2.get_value()
            var_type = arg2.get_type()
            if arg2.get_type() == 'string' and value == None:
               value = ""
         elif (arg2.get_type() == 'var'):
            var2_frame, var2_name = arg2.get_value().split('@')
            var2 = Variable(var2_name, None, var2_frame)
            value = var2.get_value()
            var_type = var2.get_type()
         else:
            print_error('Error: second argument of MOVE must be of type symb', ERR_BAD_TYPE)

         # Get the var frame and var name
         var_frame, var_name = arg1.get_value().split('@')

         # Create a new Variable object and try to set it's value
         var = Variable(var_name, value, var_frame)
         var.set_type(var_type)
         var.set()

      elif opcode == "CREATEFRAME":
         
         # Create TF
         temporary_frame = {}
         tf_not_created = False

      elif opcode == "PUSHFRAME":
         
         # If TF exists, move it to the LF stack, else error
         if tf_not_created == False:
            local_frames.append(temporary_frame)
            tf_not_created = True
            temporary_frame = {}
         else:
            print_error('Error: undefined temporary frame', ERR_FRAME_MISSING)

      elif opcode == "POPFRAME":
         
         if len(local_frames) == 0:
            print_error('Error: no local frame to be popped', ERR_FRAME_MISSING)

         # Pop the topmost LF into TF 
         temporary_frame = local_frames.pop()
         tf_not_created = False

      elif opcode == "DEFVAR":
         
         arg1 = inst.get_args()[0]

         # Check types
         if (arg1.get_type() != 'var'):
            print_error('Error: first argument of DEFVAR must be of type var', ERR_BAD_TYPE)

         # Get the var frame and var name and create a Variable object with these parameters
         var_frame, var_name = arg1.get_value().split('@')
         var = Variable(var_name, None, var_frame)
         
         # Define the variable
         var.create()

      elif opcode == "CALL":
         
         # Add current position to call stack
         call_stack.append(i)

         arg1 = inst.get_args()[0]

         # Check types
         if (arg1.get_type() != 'label'):
            print_error(f'Error: first argument of {opcode} must be of type label', ERR_BAD_TYPE)

         # Search for the label position and jump there
         label_name = arg1.get_value()
         if label_name in labels:
            i = labels[label_name] # jump
         else:
            print_error('Error: undefined label', ERR_SEMANTIC)

      elif opcode == "RETURN":
         
         # Get the previous position from the call stack and jump there
         if len(call_stack) > 0:
            i = call_stack.pop() # jump
         else:
            print_error('Error: call stack empty', ERR_VALUE_MISSING)

      elif opcode == "PUSHS":
         
         arg1 = inst.get_args()[0]

         value = None
         value_type = None

         # Check types and retrieve the value and type
         if (arg1.get_type() in ['int', 'string', 'bool', 'nil']):
            value = arg1.get_value()
            value_type = arg1.get_type()
         elif (arg1.get_type() == 'var'):
            var_frame, var_name = arg1.get_value().split('@')
            var = Variable(var_name, None, var_frame)
            value = var.get_value()
            value_type = var.get_type()
         else:
            print_error(f'Error: second and third argument of {opcode} must be of type symb', ERR_BAD_TYPE)

         # Push the results onto the stack
         stack.append([value_type, value])

      elif opcode == "POPS":
         
         arg1 = inst.get_args()[0]

         value = None
         var_type = None

         # Check types
         if (arg1.get_type() != 'var'):
            print_error('Error: first argument of MOVE must be of type var', ERR_BAD_TYPE)

         # Get the var frame and var name
         var_frame, var_name = arg1.get_value().split('@')

         # Try to retrieve the value and type from the stack
         try:
            value_type, value = stack.pop()
         except:
            print_error('Error: empty stack', ERR_VALUE_MISSING)

         # Create a new Variable object and try to set it's value
         var = Variable(var_name, value, var_frame)
         var.set_type(value_type)
         var.set()

      elif opcode in ["ADD", "SUB", "MUL", "IDIV"]:
         
         arg1 = inst.get_args()[0]
         arg2 = inst.get_args()[1]
         arg3 = inst.get_args()[2]

         value = None
         value_1 = None
         value_2 = None

         # Check types and retrieve the value and type
         if (arg1.get_type() != 'var'):
            print_error(f'Error: first argument of {opcode} must be of type var', ERR_BAD_TYPE)

         if (arg2.get_type() == 'int'):
            value_1 = arg2.get_value()
         elif (arg2.get_type() == 'var'):
            var2_frame, var2_name = arg2.get_value().split('@')
            var2 = Variable(var2_name, None, var2_frame)
            value_1 = var2.get_value()
            if var2.get_type() != 'int':
               print_error(f'Error: second and third argument of {opcode} must be of type symb', ERR_BAD_TYPE)

         else:
            print_error(f'Error: second and third argument of {opcode} must be of type symb', ERR_BAD_TYPE)

         if (arg3.get_type() == 'int'):
            value_2 = arg3.get_value()
         elif (arg3.get_type() == 'var'):
            var3_frame, var3_name = arg3.get_value().split('@')
            var3 = Variable(var3_name, None, var3_frame)
            value_2 = var3.get_value()
            if var3.get_type() != 'int':
               print_error(f'Error: second and third argument of {opcode} must be of type symb', ERR_BAD_TYPE)

         else:
            print_error(f'Error: second and third argument of {opcode} must be of type symb', ERR_BAD_TYPE)

         # Check for missing values
         if value_1 == None or value_2 == None:
            print_error('Error: missing value', ERR_VALUE_MISSING)

         # Try to convert values to int
         try:
            value_1 = int(value_1)
            value_2 = int(value_2)
         except:
            print_error('Error: wrong integer value', ERR_XML_STRUCT)

         # Calculate the value
         if opcode == "ADD":
            value = value_1 + value_2
         elif opcode == "SUB":
            value = value_1 - value_2
         elif opcode == "MUL":
            value = value_1 * value_2
         else:
            if value_2 == 0:
               print_error('Error: division by 0', ERR_OPERAND_VALUE)
            value = value_1 // value_2

         # Get the var frame and var name
         var_frame, var_name = arg1.get_value().split('@')

         # Create a new Variable object and try to set it's value
         var = Variable(var_name, value, var_frame)
         var.set_type('int')
         var.set()

      elif opcode in ["LT", "GT", "EQ"]:
         
         arg1 = inst.get_args()[0]
         arg2 = inst.get_args()[1]
         arg3 = inst.get_args()[2]

         value = None
         value_1 = None
         value_2 = None
         value_1_type = None
         value_2_type = None

         # Check types and retrieve the value and type
         if (arg1.get_type() != 'var'):
            print_error(f'Error: first argument of {opcode} must be of type var', ERR_BAD_TYPE)

         if (arg2.get_type() in ['int', 'string', 'bool', 'nil']):
            value_1 = arg2.get_value()
            value_1_type = arg2.get_type()
         elif (arg2.get_type() == 'var'):
            var2_frame, var2_name = arg2.get_value().split('@')
            var2 = Variable(var2_name, None, var2_frame)
            value_1 = var2.get_value()
            value_1_type = var2.get_type()
            
         else:
            print_error(f'Error: second and third argument of {opcode} must be of type symb', ERR_BAD_TYPE)

         if (arg3.get_type() in ['int', 'string', 'bool', 'nil']):
            value_2 = arg3.get_value()
            value_2_type = arg3.get_type()
         elif (arg3.get_type() == 'var'):
            var3_frame, var3_name = arg3.get_value().split('@')
            var3 = Variable(var3_name, None, var3_frame)
            value_2 = var3.get_value()
            value_2_type = var3.get_type()

         else:
            print_error(f'Error: second and third argument of {opcode} must be of type symb', ERR_BAD_TYPE)

         # Correct the values of empty strings
         if value_1 == None and value_1_type == 'string':
            value_1 = ""
         
         if value_2 == None and value_2_type == 'string':
            value_2 = ""

         # If they're still none, they have not been set
         if value_1 == None or value_2 == None:
            print_error('Error: missing value', ERR_VALUE_MISSING)

         # Can compare nils with EQ instruction
         if (value_1_type == 'nil' or value_2_type == 'nil') and opcode == 'EQ':
            pass
         elif value_1_type != value_2_type:
            print_error(f'Error: second and third argument of {opcode} must be of the same type', ERR_BAD_TYPE)
         
         # Cannot compare nils with LT and GT instructions
         if (value_1_type == 'nil' or value_2_type == 'nil') and opcode != 'EQ':
            print_error('Error: nil can only be compared using the EQ instruction', ERR_BAD_TYPE)

         # Calculate the value for each instruction and type combination
         try:
            if opcode == "LT":
               if value_1_type == 'int':
                  value = bool(int(value_1) < int(value_2))
               elif value_1_type == 'string':
                  value_1 = replace_escape_sequences(value_1)
                  value_2 = replace_escape_sequences(value_2)        
                  value = bool(value_1 < value_2)
               else:
                  if value_1 == 'false' and value_2 == 'true':
                     value = True
                  else:
                     value = False
            elif opcode == "GT":
               if value_1_type == 'int':
                  value = bool(int(value_1) > int(value_2))
               elif value_1_type == 'string':    
                  value_1 = replace_escape_sequences(value_1)
                  value_2 = replace_escape_sequences(value_2)       
                  value = bool(value_1 > value_2)
               else:
                  if value_1 == 'true' and value_2 == 'false':
                     value = True
                  else:
                     value = False
            elif opcode == "EQ":
               if value_1_type == 'nil':
                  if value_2_type == 'nil':
                     value = True
                  else:
                     value = False
               elif value_2_type == 'nil':
                  if value_1_type == 'nil':
                     value = True
                  else:
                     value = False
               elif value_1_type == 'int':
                  value = bool(int(value_1) == int(value_2))
               elif value_1_type == 'string':
                  value_1 = replace_escape_sequences(value_1)
                  value_2 = replace_escape_sequences(value_2)           
                  value = bool(value_1 == value_2)
               else:
                  if value_1 == value_2:
                     value = True
                  else:
                     value = False
         except:
            print_error(f'Error: {opcode} - typeerror', ERR_BAD_TYPE)
         
         # In case of booleans, set the actual value
         if value is True:
            value = 'true'
         elif value is False:
            value = 'false'

         # Get the var frame and var name
         var_frame, var_name = arg1.get_value().split('@')

         # Create a new Variable object and try to set it's value
         var = Variable(var_name, value, var_frame)
         var.set_type('bool')
         var.set()

      elif opcode in ["AND", "OR", "NOT"]:
         
         arg1 = inst.get_args()[0]
         arg2 = inst.get_args()[1]
         if opcode != "NOT":
            arg3 = inst.get_args()[2]

         value = None
         value_1 = None
         value_2 = None

         # Check types and retrieve the value and type
         if (arg1.get_type() != 'var'):
            print_error(f'Error: first argument of {opcode} must be of type var', ERR_BAD_TYPE)

         if (arg2.get_type() not in ['bool', 'var']):
            print_error(f'Error: second argument of {opcode} must be of type symb', ERR_BAD_TYPE)

         if (opcode != "NOT") and (arg3.get_type() not in ['bool', 'var']):
            print_error(f'Error: third argument of {opcode} must be of type symb', ERR_BAD_TYPE)

         if (arg2.get_type() == 'bool'):
            value_1 = arg2.get_value()
         else:
            var2_frame, var2_name = arg2.get_value().split('@')
            var2 = Variable(var2_name, None, var2_frame)

            if var2.get_type() != 'bool':
               print_error(f'Error: second argument of {opcode} must be of type symb', ERR_BAD_TYPE)

            value_1 = var2.get_value()

         if (opcode != "NOT"):
            if (arg3.get_type() == 'bool'):
               value_2 = arg3.get_value()
            else:
               var3_frame, var3_name = arg3.get_value().split('@')
               var3 = Variable(var3_name, None, var3_frame)

               if var3.get_type() != 'bool':
                  print_error(f'Error: third argument of {opcode} must be of type symb', ERR_BAD_TYPE)

               value_2 = var3.get_value()

         # Convert 'strings' to booleans
         if value_1 == 'true':
            value_1 = True
         if value_1 == 'false':
            value_1 = False
         if value_2 == 'true':
            value_2 = True
         if value_2 == 'false':
            value_2 = False

         # Perform the instruction
         if opcode == "AND":
            value = value_1 and value_2
         elif opcode == "OR":
            value = value_1 or value_2
         elif opcode == "NOT":
            value = not value_1

         # Convert the value back
         if value is True:
            value = 'true'
         else:
            value = 'false'

         # Get the var frame and var name
         var_frame, var_name = arg1.get_value().split('@')

         # Create a new Variable object and try to set it's value
         var = Variable(var_name, value, var_frame)
         var.set_type('bool')
         var.set()

      elif opcode == "INT2CHAR":
         
         arg1 = inst.get_args()[0]
         arg2 = inst.get_args()[1]

         value = None
         value_1 = None
         value_1_type = None

         # Check types and retrieve the value and type
         if (arg1.get_type() != 'var'):
            print_error(f'Error: first argument of {opcode} must be of type var', ERR_BAD_TYPE)

         if (arg2.get_type() == 'int'):
            value_1 = arg2.get_value()
            value_1_type = arg2.get_type()
         elif (arg2.get_type() == 'var'):
            var2_frame, var2_name = arg2.get_value().split('@')
            var2 = Variable(var2_name, None, var2_frame)
            if var2.get_type() != 'int':
               print_error(f'Error: second argument of {opcode} must be of type int', ERR_BAD_TYPE)
            value_1 = var2.get_value()
         else:
            print_error(f'Error: second argument of {opcode} must be of type int', ERR_BAD_TYPE)
         
         # Try to get the actual char value
         try:
            value = chr(int(value_1))
         except:
            print_error(f'Error: {opcode} - cannot convert integer to char', ERR_STRING)

         # Get the var frame and var name
         var_frame, var_name = arg1.get_value().split('@')

         # Create a new Variable object and try to set it's value
         var = Variable(var_name, value, var_frame)
         var.set_type('string')
         var.set()

      elif opcode == "STRI2INT":
         
         arg1 = inst.get_args()[0]
         arg2 = inst.get_args()[1]
         arg3 = inst.get_args()[2]

         value = None
         value_1 = None
         value_2 = None

         # Check types and retrieve the value and type
         if (arg1.get_type() != 'var'):
            print_error(f'Error: first argument of {opcode} must be of type var', ERR_BAD_TYPE)

         if (arg2.get_type() == 'string'):
            value_1 = arg2.get_value()
         elif (arg2.get_type() == 'var'):
            var2_frame, var2_name = arg2.get_value().split('@')
            var2 = Variable(var2_name, None, var2_frame)
            if var2.get_type() != 'string':
               print_error(f'Error: second argument of {opcode} must be of type string', ERR_BAD_TYPE)
            value_1 = var2.get_value()
         else:
            print_error(f'Error: second argument of {opcode} must be of type string', ERR_BAD_TYPE)

         if (arg3.get_type() == 'int'):
            value_2 = arg3.get_value()
         elif (arg3.get_type() == 'var'):
            var3_frame, var3_name = arg3.get_value().split('@')
            var3 = Variable(var3_name, None, var3_frame)
            if var3.get_type() != 'int':
               print_error(f'Error: third argument of {opcode} must be of type int', ERR_BAD_TYPE)
            value_2 = var3.get_value()
         else:
            print_error(f'Error: third argument of {opcode} must be of type int', ERR_BAD_TYPE)

         # Check value range
         if int(value_2) < 0:
            print_error(f'Error: {opcode} - index out of range', ERR_STRING)

         # Get the integer value
         try:
            value = ord(value_1[int(value_2)])
         except:
            print_error(f'Error: {opcode} - index out of range', ERR_STRING)

         # Get the var frame and var name
         var_frame, var_name = arg1.get_value().split('@')

         # Create a new Variable object and try to set it's value
         var = Variable(var_name, value, var_frame)
         var.set_type('int')
         var.set()

      elif opcode == "READ":

         global read_line_number
         value = None
         var_type = None

         arg1 = inst.get_args()[0]
         arg2 = inst.get_args()[1]

         # Check types
         if (arg1.get_type() != 'var'):
            print_error(f'Error: first argument of {opcode} must be of type var', ERR_BAD_TYPE)

         if (arg2.get_type() != 'type'):
            print_error(f'Error: second argument of {opcode} must be of type \'type\'', ERR_BAD_TYPE)

         var_type = arg2.get_value()

         # Split the input by '\n' and read one line on index 'read_line_number'
         input_lines = input_file.split('\n')
         try:
            line = input_lines[read_line_number]
         except:
            value = 'nil'
            var_type = 'nil'
         
         read_line_number += 1
         
         # Retrieve the value based on possible types
         if var_type == 'bool':
            if line.upper() == 'TRUE':
               value = 'true'
            else:
               value = 'false'

         elif var_type == 'int':
            try:
               value = int(line)
            except:
               value = 'nil'
               var_type = 'nil'
         
         elif var_type == 'string':
            try:
               value = str(line)
            except:
               value = 'nil'
               var_type = 'nil'
         else:
            value = 'nil'
            var_type = 'nil'

         # Get the var frame and var name
         var_frame, var_name = arg1.get_value().split('@')

         # Create a new Variable object and try to set it's value
         var = Variable(var_name, value, var_frame)
         var.set_type(var_type)
         var.set()         

      elif opcode == "WRITE":
         
         arg1 = inst.get_args()[0]

         # Check types and retrieve the value and type
         if (arg1.get_type() in ['int', 'bool', 'string', 'float', 'nil']):
            value = arg1.get_value()
            typ = arg1.get_type()

         elif (arg1.get_type() == 'var'):
            var_frame, var_name = arg1.get_value().split('@')
            var = Variable(var_name, None, var_frame)
            value = var.get_value()
            typ = var.get_type()

         else:
            print_error('Error: second argument of MOVE must be of type symb', ERR_XML_STRUCT)

         value = replace_escape_sequences(str(value))

         # Change the value if it's 'nil'
         if value == 'nil' and typ != 'string':
            value = ""
         print(value, end='')

      elif opcode == "CONCAT":

         arg1 = inst.get_args()[0]
         arg2 = inst.get_args()[1]
         arg3 = inst.get_args()[2]

         value = None
         value_1 = None
         value_2 = None

         # Check types and retrieve the value and type
         if (arg1.get_type() != 'var'):
            print_error(f'Error: first argument of {opcode} must be of type var', ERR_BAD_TYPE)

         if (arg2.get_type() not in ['string', 'var']):
            print_error(f'Error: second argument of {opcode} must be of type string', ERR_BAD_TYPE)

         if (arg2.get_type() == 'string'):
            value_1 = arg2.get_value()
            value_1_type = arg2.get_type()
         else:
            var2_frame, var2_name = arg2.get_value().split('@')
            var2 = Variable(var2_name, None, var2_frame)

            if var2.get_type() != 'string':
               print_error(f'Error: second argument of {opcode} must be of type string', ERR_BAD_TYPE)

            value_1 = var2.get_value()
            value_1_type = var2.get_type()

         if (arg3.get_type() not in ['string', 'var']):
            print_error(f'Error: third argument of {opcode} must be of type string', ERR_BAD_TYPE)

         if (arg3.get_type() == 'string'):
            value_2 = arg3.get_value()
            value_2_type = arg3.get_type()
         else:
            var3_frame, var3_name = arg3.get_value().split('@')
            var3 = Variable(var3_name, None, var3_frame)

            if var3.get_type() != 'string':
               print_error(f'Error: third argument of {opcode} must be of type string', ERR_BAD_TYPE)

            value_2 = var3.get_value()
            value_2_type = var3.get_type()

         # Correct the values of empty strings
         if value_1 == None and value_1_type == 'string':
            value_1 = ""
         if value_2 == None and value_2_type == 'string':
            value_2 = ""   

         value = str(value_1) + str(value_2)

         # Get the var frame and var name
         var_frame, var_name = arg1.get_value().split('@')

         # Create a new Variable object and try to set it's value
         var = Variable(var_name, value, var_frame)
         var.set_type('string')
         var.set()
         
      elif opcode == "STRLEN":
         
         arg1 = inst.get_args()[0]
         arg2 = inst.get_args()[1]

         value = None
         value_1 = None

         # Check types and retrieve the value and type
         if (arg1.get_type() != 'var'):
            print_error(f'Error: first argument of {opcode} must be of type var', ERR_BAD_TYPE)

         if (arg2.get_type() == 'string'):
            value_1 = arg2.get_value()
         elif (arg2.get_type() == 'var'):
            var2_frame, var2_name = arg2.get_value().split('@')
            var2 = Variable(var2_name, None, var2_frame)
            if var2.get_type() != 'string':
               print_error(f'Error: second argument of {opcode} must be of type string', ERR_BAD_TYPE)
            value_1 = var2.get_value()
         else:
            print_error(f'Error: second argument of {opcode} must be of type string', ERR_BAD_TYPE)

         # Strlen of empty string is 0
         if value_1 == None:
            value = 0
         else:
            value = len(replace_escape_sequences(value_1))

         # Get the var frame and var name
         var_frame, var_name = arg1.get_value().split('@')

         # Create a new Variable object and try to set it's value
         var = Variable(var_name, value, var_frame)
         var.set_type('int')
         var.set()

      elif opcode == "GETCHAR":

         arg1 = inst.get_args()[0]
         arg2 = inst.get_args()[1]
         arg3 = inst.get_args()[2]

         # Check types and retrieve the value and type
         if (arg1.get_type() != 'var'):
            print_error(f'Error: first argument of {opcode} must be of type var', ERR_BAD_TYPE)

         if (arg2.get_type() == 'string'):
            value_1 = arg2.get_value()
         elif (arg2.get_type() == 'var'):
            var2_frame, var2_name = arg2.get_value().split('@')
            var2 = Variable(var2_name, None, var2_frame)
            if var2.get_type() != 'string':
               print_error(f'Error: second argument of {opcode} must be of type string', ERR_BAD_TYPE)
            value_1 = var2.get_value()
         else:
            print_error(f'Error: second argument of {opcode} must be of type string', ERR_BAD_TYPE)

         if (arg3.get_type() == 'int'):
            value_2 = arg3.get_value()
         elif (arg3.get_type() == 'var'):
            var3_frame, var3_name = arg3.get_value().split('@')
            var3 = Variable(var3_name, None, var3_frame)
            if var3.get_type() != 'int':
               print_error(f'Error: third argument of {opcode} must be of type int', ERR_BAD_TYPE)
            value_2 = var3.get_value()
         else:
            print_error(f'Error: third argument of {opcode} must be of type int', ERR_BAD_TYPE)
         
         # Check value range
         if int(value_2) < 0:
            print_error(f'Error: {opcode} - index out of range', ERR_STRING)
         
         # Try to get the actual value
         try:
            value = value_1[int(value_2)]
         except:
            print_error(f'Error: {opcode} - index out of range', ERR_STRING)

         # Get the var frame and var name
         var_frame, var_name = arg1.get_value().split('@')

         # Create a new Variable object and try to set it's value
         var = Variable(var_name, value, var_frame)
         var.set_type('string')
         var.set()

      elif opcode == "SETCHAR":
         
         arg1 = inst.get_args()[0]
         arg2 = inst.get_args()[1]
         arg3 = inst.get_args()[2]

         value = None
         value_1 = None
         value_2 = None

         # Check types and retrieve the value and type
         if (arg1.get_type() != 'var'):
            print_error(f'Error: first argument of {opcode} must be of type var', ERR_BAD_TYPE)
         
         var1_frame, var1_name = arg1.get_value().split('@')
         var1 = Variable(var1_name, None, var1_frame)
         if var1.get_type() != 'string':
            print_error(f'Error: first argument of {opcode} must be of type string', ERR_BAD_TYPE)
         

         if (arg2.get_type() == 'int'):
            value_1 = arg2.get_value()
         elif (arg2.get_type() == 'var'):
            var2_frame, var2_name = arg2.get_value().split('@')
            var2 = Variable(var2_name, None, var2_frame)
            if var2.get_value_unset() == None:
               print_error(f'Error: {opcode} - missing value', ERR_VALUE_MISSING)
            if var2.get_type() != 'int':
               print_error(f'Error: second argument of {opcode} must be of type int', ERR_BAD_TYPE)
            value_1 = var2.get_value()
         else:
            print_error(f'Error: second argument of {opcode} must be of type int', ERR_BAD_TYPE)

         if (arg3.get_type() == 'string'):
            value_2 = arg3.get_value()
         elif (arg3.get_type() == 'var'):
            var3_frame, var3_name = arg3.get_value().split('@')
            var3 = Variable(var3_name, None, var3_frame)
            if var3.get_value_unset() == None:
               print_error(f'Error: {opcode} - missing value', ERR_VALUE_MISSING)
            if var3.get_type() != 'string':
               print_error(f'Error: third argument of {opcode} must be of type string', ERR_BAD_TYPE)
            value_2 = var3.get_value()
         else:
            print_error(f'Error: third argument of {opcode} must be of type string', ERR_BAD_TYPE)

         # Get the var frame and var name
         var_frame, var_name = arg1.get_value().split('@')

         var_tmp = Variable(var_name, value, var_frame)
         value = var_tmp.get_value()
         
         # Check value range
         if int(value_1) < 0 or int(value_1) >= len(value):
            print_error(f'Error: {opcode} - index out of range', ERR_STRING)

         value = replace_escape_sequences(value)
         value_2 = replace_escape_sequences(value_2)

         # Try to get the actual value
         try:
            value = value[:int(value_1)] + value_2[0] + value[int(value_1)+1:]
         except:
            print_error(f'Error: {opcode} - index out of range', ERR_STRING)

         # Create a new Variable object and try to set it's value
         var = Variable(var_name, value, var_frame)
         var.set_type('string')
         var.set()

      elif opcode == "TYPE":
        
         arg1 = inst.get_args()[0]
         arg2 = inst.get_args()[1]

         value = None

         # Check types and retrieve the value and type
         if (arg1.get_type() != 'var'):
            print_error(f'Error: first argument of {opcode} must be of type var', ERR_BAD_TYPE)

         if (arg2.get_type() == 'var'):
            var2_frame, var2_name = arg2.get_value().split('@')
            var2 = Variable(var2_name, None, var2_frame)
            if var2.get_value_unset() == None:
               value = ""
            else:
               value = var2.get_type_unset()
            
         else:
            value = arg2.get_type()

         # Get the var frame and var name
         var_frame, var_name = arg1.get_value().split('@')

         # Create a new Variable object and try to set it's value
         var = Variable(var_name, value, var_frame)
         var.set_type('string')
         var.set()

      elif opcode == "LABEL":
         # LABEL are already dealt with at the beginning
         pass

      elif opcode == "JUMP":
         
         arg1 = inst.get_args()[0]

         # Check type
         if (arg1.get_type() != 'label'):
            print_error(f'Error: first argument of {opcode} must be of type label', ERR_BAD_TYPE)

         # Find the label index and jump
         label_name = arg1.get_value()
         if label_name in labels:
            i = labels[label_name] # jump
         else:
            print_error('Error: undefined label', ERR_SEMANTIC)

      elif opcode == "JUMPIFEQ":
         
         arg1 = inst.get_args()[0]
         arg2 = inst.get_args()[1]
         arg3 = inst.get_args()[2]

         # Check if label exists
         if arg1.get_value() not in labels:
            print_error('Error: undefined label', ERR_SEMANTIC)

         # Default is false
         value = False

         # Check types and retrieve the value and type
         if (arg1.get_type() != 'label'):
            print_error(f'Error: first argument of {opcode} must be of type label', ERR_BAD_TYPE)

         if (arg2.get_type() in ['int', 'string', 'bool', 'nil']):
            value_1 = arg2.get_value()
            value_1_type = arg2.get_type()
         elif (arg2.get_type() == 'var'):
            var2_frame, var2_name = arg2.get_value().split('@')
            var2 = Variable(var2_name, None, var2_frame)
            value_1 = var2.get_value()
            value_1_type = var2.get_type()
            
         else:
            print_error(f'Error: second and third argument of {opcode} must be of type symb', ERR_BAD_TYPE)

         if (arg3.get_type() in ['int', 'string', 'bool', 'nil']):
            value_2 = arg3.get_value()
            value_2_type = arg3.get_type()
         elif (arg3.get_type() == 'var'):
            var3_frame, var3_name = arg3.get_value().split('@')
            var3 = Variable(var3_name, None, var3_frame)
            value_2 = var3.get_value()
            value_2_type = var3.get_type()

         else:
            print_error(f'Error: second and third argument of {opcode} must be of type symb', ERR_BAD_TYPE)

         # nils can be compared
         if (value_1_type == 'nil' or value_2_type == 'nil'):
            pass
         elif value_1_type != value_2_type:
            print_error(f'Error: second and third argument of {opcode} must be of the same type', ERR_BAD_TYPE)

         # Set the value in case of different types
         try:
            if value_1_type == 'nil':
               if value_2_type == 'nil':
                  value = True
               else:
                  value = False
            elif value_2_type == 'nil':
               if value_1_type == 'nil':
                  value = True
               else:
                  value = False
            elif value_1_type == 'int':
               value = bool(int(value_1) == int(value_2))
            elif value_1_type == 'string':
               value_1 = replace_escape_sequences(value_1)
               value_2 = replace_escape_sequences(value_2)           
               value = bool(value_1 == value_2)
            else:
               if value_1 == value_2:
                  value = True
               else:
                  value = False
         except:
            print_error(f'Error: {opcode} - typeerror', ERR_BAD_TYPE)

         # If the condition is true, jump
         if value == True:
            label_name = arg1.get_value()
            if label_name in labels:
               i = labels[label_name] # jump
            else:
               print_error('Error: undefined label', ERR_SEMANTIC)

      elif opcode == "JUMPIFNEQ":
         
         arg1 = inst.get_args()[0]
         arg2 = inst.get_args()[1]
         arg3 = inst.get_args()[2]

         # Check is label exists
         if arg1.get_value() not in labels:
            print_error('Error: undefined label', ERR_SEMANTIC)

         # Default is false
         value = False

         # Check types and retrieve the value and type
         if (arg1.get_type() != 'label'):
            print_error(f'Error: first argument of {opcode} must be of type label', ERR_BAD_TYPE)

         if (arg2.get_type() in ['int', 'string', 'bool', 'nil']):
            value_1 = arg2.get_value()
            value_1_type = arg2.get_type()
         elif (arg2.get_type() == 'var'):
            var2_frame, var2_name = arg2.get_value().split('@')
            var2 = Variable(var2_name, None, var2_frame)
            value_1 = var2.get_value()
            value_1_type = var2.get_type()
            
         else:
            print_error(f'Error: second and third argument of {opcode} must be of type symb', ERR_BAD_TYPE)

         if (arg3.get_type() in ['int', 'string', 'bool', 'nil']):
            value_2 = arg3.get_value()
            value_2_type = arg3.get_type()
         elif (arg3.get_type() == 'var'):
            var3_frame, var3_name = arg3.get_value().split('@')
            var3 = Variable(var3_name, None, var3_frame)
            value_2 = var3.get_value()
            value_2_type = var3.get_type()

         else:
            print_error(f'Error: second and third argument of {opcode} must be of type symb', ERR_BAD_TYPE)

         # nils can be compared
         if (value_1_type == 'nil' or value_2_type == 'nil'):
            pass
         elif value_1_type != value_2_type:
            print_error(f'Error: second and third argument of {opcode} must be of the same type', ERR_BAD_TYPE)

         # Set the value in case of different types
         try:
            if value_1_type == 'nil':
               if value_2_type == 'nil':
                  value = True
               else:
                  value = False
            elif value_2_type == 'nil':
               if value_1_type == 'nil':
                  value = True
               else:
                  value = False
            elif value_1_type == 'int':
               value = bool(int(value_1) == int(value_2))
            elif value_1_type == 'string':
               value_1 = replace_escape_sequences(value_1)
               value_2 = replace_escape_sequences(value_2)           
               value = bool(value_1 == value_2)
            else:
               if value_1 == value_2:
                  value = True
               else:
                  value = False
         except:
            print_error(f'Error: {opcode} - typeerror', ERR_BAD_TYPE)

         # If value is false, jump
         if value == False:
            label_name = arg1.get_value()
            if label_name in labels:
               i = labels[label_name] # jump
            else:
               print_error('Error: undefined label', ERR_SEMANTIC)

      elif opcode == "EXIT":

         arg1 = inst.get_args()[0]

         # Check types and retrieve the value
         if (arg1.get_type() == 'int'):
            value = arg1.get_value()
         elif (arg1.get_type() == 'var'):
            var_frame, var_name = arg1.get_value().split('@')
            var = Variable(var_name, None, var_frame)
            if var.get_type() != 'int':
               print_error(f'Error: first argument of {opcode} must be of type int', ERR_BAD_TYPE)
            value = var.get_value()
         else:
            print_error(f'Error: first argument of {opcode} must be of type int', ERR_BAD_TYPE)

         # Check value range
         if int(value) < 0 or int(value) > 49:
            print_error(f'Error: {opcode} - invalid error value', ERR_OPERAND_VALUE) 

         # Exit with the given value
         sys.exit(int(value))        

      # Just acknowledge these and ignore them
      elif opcode == "DPRINT":
         pass

      elif opcode == "BREAK":
         pass

      # DON'T NEED TO DO THESE
      elif opcode == "CLEARS":
         # handle EQ instruction with 0 arguments
         pass
      elif opcode == "ADDS":
         # handle AND instruction with 0 arguments
         pass
      elif opcode == "SUBS":
         # handle OR instruction with 0 arguments
         pass
      elif opcode == "MULS":
         # handle NOT instruction with 0 arguments
         pass
      elif opcode == "IDIVS":
         # handle INT2CHAR instruction with 0 arguments
         pass
      elif opcode == "LTS":
         # handle STRI2INT instruction with 0 arguments
         pass
      elif opcode == "GTS":
         # handle READ instruction with 2 arguments
         pass
      elif opcode == "EQS":
         # handle WRITE instruction with 1 argument
         pass
      elif opcode == "ANDS":
         # handle CONCAT instruction with 0 arguments
         pass
      elif opcode == "ORS":
         # handle GT instruction with 0 arguments
         pass
      elif opcode == "NOTS":
         # handle EQ instruction with 0 arguments
         pass
      elif opcode == "INT2CHARS":
         # handle AND instruction with 0 arguments
         pass
      elif opcode == "STRI2INTS":
         # handle OR instruction with 0 arguments
         pass
      elif opcode == "JUMPIFEQS":
         # handle NOT instruction with 0 arguments
         pass
      elif opcode == "JUMPIFNEQS":
         # handle INT2CHAR instruction with 0 arguments
         pass
      
      # Increment the instruction counter
      i += 1
      
if __name__ == '__main__':
   main()