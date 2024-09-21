<?php

define('ERR_OK', 0);
define('ERR_PARAM', 10);
define('ERR_HEADER', 21);
define('ERR_OPCODE', 22);
define('ERR_OTHER', 23);

ini_set('display_errors', 'stderr');

$order = 1;
$header = false;

// Create XMLWriter object, set indent and start new document
$xml = new XMLWriter();
$xml->openMemory();
$xml->setIndent(true);
$xml->startDocument('1.0', 'UTF-8');

// Check arguments
if ($argc === 2)
{
  // In case of --help, print it
  if ($argv[1] == "--help")
  {
    print_help();
    exit();
  }
  else
  {
    print_err(ERR_PARAM);
  }
}
elseif ($argc !== 1)
{
  print_err(ERR_PARAM);
}

// Main loop
while ($line = fgets(STDIN))
{

  // Strip comments
  $line_divided = explode('#', $line);
  $line = $line_divided[0];

  // Trim line of any spaces on each side
  $line = trim($line);

  // Remove excess whitespaces
  $line = preg_replace('/\s+/', ' ', $line);

  // Check and continue for lines with comments only or overall empty lines
  if (preg_match("/^\s*(?:#.*)?$/", $line))
  {
    continue;
  }

  // Check for header
  if(!$header)
  {
    if (preg_match("/^\s*\.IPPcode23\s*(?:#.*)?$/", $line))
    {
      // Start element 'program'
      $xml->startElement('program');
      $xml->writeAttribute('language', 'IPPcode23');

      $header = true;
    }
    else
    {
      print_err(ERR_HEADER);
    }
  }
  else
  {
    // Explode line into "words"
    $splitted = explode(' ', trim($line, "\n"));

    // Trim each "word" of extra spaces
    foreach ($splitted as $word)
    {
      $word = trim($word);
    }

    // Switch based on the first word (instruction)
    switch(strtoupper($splitted[0]))
    {
      // No argument
      case 'CREATEFRAME':
      case 'PUSHFRAME':
      case 'POPFRAME':
      case 'RETURN':
      case 'BREAK':
        xml_no_arg($splitted, $xml);
        break;

      // One argument - <var>
      case 'DEFVAR':
      case 'POPS':
        xml_var_arg($splitted, $xml);
        break;
      
      // One argument - <symb>
      case 'PUSHS':
      case 'WRITE':
      case 'EXIT':
      case 'DPRINT':
        xml_symb_arg($splitted, $xml);
        break;

      // One argument - <label>
      case 'CALL':
      case 'LABEL':
      case 'JUMP':
        xml_label_arg($splitted, $xml);
        break;

      // Two arguments - <var> <symb>
      case 'MOVE':
      case 'INT2CHAR':
      case 'STRLEN':
      case 'TYPE':
      case 'NOT':
        xml_var_symb_arg($splitted, $xml);
        break;

      // Two arguments - <var> <type>
      case 'READ':
        xml_var_type_arg($splitted, $xml);
        break;

      // Three arguments - <var> <symb> <symb>
      case 'ADD':
      case 'SUB':
      case 'MUL':
      case 'IDIV':
      case 'LT':
      case 'GT':
      case 'EQ':
      case 'AND':
      case 'OR':
      case 'STRI2INT':
      case 'CONCAT':
      case 'GETCHAR':
      case 'SETCHAR':
        xml_var_symb_symb_arg($splitted, $xml);
        break;

      // Three arguments - <label> <symb> <symb>
      case 'JUMPIFEQ':
      case 'JUMPIFNEQ':
        xml_label_symb_symb_arg($splitted, $xml);
        break;
      
      // No known argument
      default:
        print_err(ERR_OPCODE);
        break;
    }
  }
}

// End element 'program'
$xml->endElement();

// End document
$xml->endDocument();

// Output xml
echo $xml->outputMemory();

//----------------- FUNCTIONS -----------------//
// Output the given error
function print_err(int $err_code)
{
  fwrite(STDERR, strval($err_code));
  exit($err_code);
}

// Print help
function print_help()
{
  echo "name:         parse.php\n";
  echo "\n";
  echo "usage:        php8.1 parse.php [--help]\n";
  echo "\n";
  echo "description:  syntactic and lexical analysis of IPPcode23 source code\n";
  echo "\n";
  echo "optional\narguments:    --help, print this help message and exit\n";
}

// Check if string is of type <var>, if not, raise an error
function check_var(string $str)
{
  if (preg_match("/^(LF|GF|TF)@[a-zA-Z_$&%*!?-][a-zA-Z0-9_$&%*!?-]*/", $str))
    return true;
  
  print_err(ERR_OTHER);
}

// Check if string is of type <var>
function is_var(string $str)
{
  if (preg_match("/^(LF|GF|TF)@[a-zA-Z_$&%*!?-][a-zA-Z0-9_$&%*!?-]*/", $str))
    return true;
  
  return false;
}

// Check if string is of type <symb>, if not, raise an error
function check_symb(string $str)
{
  // Check for variables, than constants - bool, nil, int and string
  if (preg_match("/^(LF|GF|TF)@[a-zA-Z_$&%*!?-][a-zA-Z0-9_$&%*!?-]*/", $str) ||
      preg_match("/^bool@(true|false)/", $str) || preg_match("/^nil@nil$/", $str) ||
      preg_match("/^int@((-?|\+?)[0-9]\d*)/", $str) ||
      preg_match("/^string@(?:[^\s\\\\]|\\\\[0-9]{3})*$/", $str))
  {
    return true;
  }
  
  print_err(ERR_OTHER);
}

// Check if string is of type <symb>
function is_symb(string $str)
{
  // Check for variables, than constants - bool, nil, int and string
  if (preg_match("/^(LF|GF|TF)@[a-zA-Z_$&%*!?-][a-zA-Z0-9_$&%*!?-]*/", $str) ||
      preg_match("/^bool@(true|false)$/", $str) || preg_match("/^nil@nil$/", $str) ||
      preg_match("/^int@(((-|\+)?(0[xX][0-9a-fA-F]+(_[0-9a-fA-F]+)*)|(0[oO]?[0-7]+(_[0-7]+)*)|((0[bB][01]+(_[01]+)*))|([1-9]\d*)))\b/", $str) ||
      preg_match("/^string@(?:[^\s\\\\]|\\\\[0-9]{3})*$/", $str))
  {
    return true;
  }
  
  return false;
}

// Check if string is of type <label>, if not, raise an error
function check_label(string $str)
{
  if (!is_var($str) && !is_type($str) && !is_symb($str)
      && preg_match("/^[a-zA-Z_$&%*!?-][a-zA-Z0-9_$&%*!?-]*/", $str))
  {
    return true;
  }

  print_err(ERR_OTHER);
}

// Check if string is of type <label>
function is_label(string $str)
{
  if (preg_match("/^[a-zA-Z_$&%*!?-][a-zA-Z0-9_$&%*!?-]*/", $str))
  {
    return true;
  }
  
  return false;
}

// Check if string is of type <type>, if not, raise an error
function check_type(string $str)
{
  if (preg_match("/^(int|string|bool)$/", $str))
    return true;

  print_err(ERR_OTHER);
}

// Check if string is of type <type>
function is_type(string $str)
{
  if (preg_match("/^(int|string|bool)$/", $str))
    return true;
  
  return false;
}

// Check if the number of operands is correct, if not, raise an error
function check_operands(array $arr, int $expected)
{
  if (sizeof($arr) === $expected)
    return true;
  
  print_err(ERR_OTHER);
}

// Get type from <symb>
function get_type(string $str)
{
  if (preg_match('/^(GF|LF|TF)@/', $str)) {
    return "var";
  } else if (preg_match('/^bool@/', $str)) {
    return "bool";
  } else if (preg_match('/^int@/', $str)) {
    return "int";
  } else if (preg_match('/^nil@/', $str)) {
    return "nil";
  } else if (preg_match('/^string@/', $str)) {
    return "string";
  } else {
    print_err(ERR_OTHER);
  }
}

// Create <argX> element
function xml_arg(int $arg, string $type, string $value, XMLWriter $xml)
{
  // Check if it's a var, bool, int or string and if needed, remove the prefix
  if ($type === 'symb')
  {
    $type = get_type($value);
    if ($type !== 'var')
    {
      $parts = explode('@', $value, 2);
      $value = $parts[1];
    }
  }

  // Determine the name of the element
  switch($arg)
  {
    case 1:
      $xml->startElement('arg1');
      break;
    case 2:
      $xml->startElement('arg2');
      break;
    case 3:
      $xml->startElement('arg3');
      break;
  }
  
  // Add attribute and value
  $xml->writeAttribute('type', $type);
  $xml->text($value);
  $xml->endElement();
}

// Start an <instruction> element
function start_instruction_element(string $opcode, XMLWriter $xml)
{
  global $order;
  $xml->startElement('instruction');
  $xml->writeAttribute('order', strval($order++));
  $xml->writeAttribute('opcode', strtoupper($opcode));
}

// Generate given instruction with no arguments
function xml_no_arg(array $splitted, XMLWriter $xml)
{
  // Check operands
  check_operands($splitted, 1);

  // Element 'instruction'
  start_instruction_element($splitted[0], $xml);
  $xml->endElement();
}

// Generate given instruction with one argument - <var>
function xml_var_arg(array $splitted, XMLWriter $xml)
{
  // Check operands
  check_operands($splitted, 2);

  // Start element 'instruction'
  start_instruction_element($splitted[0], $xml);

  // Arguments
  if (check_var($splitted[1]))
  {
    xml_arg(1, 'var', $splitted[1], $xml);
  }

  // End element 'instruction'
  $xml->endElement();
}

// Generate given instruction with one argument - <symb>
function xml_symb_arg(array $splitted, XMLWriter $xml)
{
  // Check operands
  check_operands($splitted, 2);

  // Start element 'instruction'
  start_instruction_element($splitted[0], $xml);

  // Arguments
  if (check_symb($splitted[1]))
    xml_arg(1, 'symb', $splitted[1], $xml);

  // End element 'instruction'
  $xml->endElement();
}

// Generate given instruction with one argument - <label>
function xml_label_arg(array $splitted, XMLWriter $xml)
{
  // Check operands
  check_operands($splitted, 2);

  // Start element 'instruction'
  start_instruction_element($splitted[0], $xml);

  // Arguments
  if (check_label($splitted[1]))
    xml_arg(1, 'label', $splitted[1], $xml);

  // End element 'instruction'
  $xml->endElement();
}

// Generate given instruction with two arguments - <var> <symb>
function xml_var_symb_arg(array $splitted, XMLWriter $xml)
{
  // Check operands
  check_operands($splitted, 3);

  // Start element 'instruction'
  start_instruction_element($splitted[0], $xml);

  // Arguments
  if (check_var($splitted[1]))
    xml_arg(1, 'var', $splitted[1], $xml);
  if (check_symb($splitted[2]))
    xml_arg(2, 'symb', $splitted[2], $xml);

  // End element 'instruction'
  $xml->endElement();
}

// Generate given instruction with two arguments - <var> <type>
function xml_var_type_arg(array $splitted, XMLWriter $xml)
{
  // Check operands
  check_operands($splitted, 3);

  // Start element 'instruction'
  start_instruction_element($splitted[0], $xml);

  // Arguments
  if (check_var($splitted[1]))
    xml_arg(1, 'var', $splitted[1], $xml);
  if (check_type($splitted[2]))
    xml_arg(2, 'type', $splitted[2], $xml);

  // End element 'instruction'
  $xml->endElement();
}

// Generate given instruction with three arguments - <var> <symb> <symb>
function xml_var_symb_symb_arg(array $splitted, XMLWriter $xml)
{
  // Check operands
  check_operands($splitted, 4);

  // Start element 'instruction'
  start_instruction_element($splitted[0], $xml);

  // Arguments
  if (check_var($splitted[1]))
    xml_arg(1, 'var', $splitted[1], $xml); 
  if (check_symb($splitted[2]))
    xml_arg(2, 'symb', $splitted[2], $xml);
  if (check_symb($splitted[3]))
    xml_arg(3, 'symb', $splitted[3], $xml);

  // End element 'instruction'
  $xml->endElement();
}

// Generate given instruction with three arguments - <label> <symb> <symb>
function xml_label_symb_symb_arg(array $splitted, XMLWriter $xml)
{
  // Check operands
  check_operands($splitted, 4);

  // Start element 'instruction'
  start_instruction_element($splitted[0], $xml);

  // Arguments
  if (check_label($splitted[1]))
    xml_arg(1, 'label', $splitted[1], $xml);
  if (check_symb($splitted[2]))
    xml_arg(2, 'symb', $splitted[2], $xml);
  if (check_symb($splitted[3]))
    xml_arg(3, 'symb', $splitted[3], $xml);

  // End element 'instruction'
  $xml->endElement();
}
?>