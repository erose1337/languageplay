NUMBER_SYMBOLS = bytes(bytearray(range(48, 58)))
TOKEN_SYMBOLS = bytes(bytearray(range(65, 91))) + bytes(bytearray(range(97, 97 + 26))) + NUMBER_SYMBOLS + '_'
OPERATOR_SYMBOLS = bytes(bytearray(range(48))) + bytes(bytearray(range(58, 65))) + bytes(bytearray(range(91, 97))) + bytes(bytearray(range(123, 256)))
BLOCK_INDICATORS = {'{' : '}', '[' : ']', '(' : ')',
                    "'" : "'", '"' : '"', """'''""" : """'''""", '''"""''' : '''"""''',}                    
STRING_INDICATORS = ["'", '"', "'''", '"""']
IGNORE_TOKENS = (' ', '\n')

def parse_string(_bytes):    
    program = []
    token = []
    for symbol in _bytes:
        if symbol in TOKEN_SYMBOLS:            
            token.append(symbol)
        else:            
            if token:
                program.append(''.join(token))            
            program.append(symbol)
            token = []
    if token:
        program.append(''.join(token))
    return program
            
def parse_for_block(program, block_indicators=BLOCK_INDICATORS):    
    end_of_block = []    
    if program[0] in block_indicators:                    # if the current symbol opens a block
        end_of_block.append(block_indicators[program[0]]) # then store the corresponding end block token and search for it in the program
        for index, piece in enumerate(program[1:]):             
            if piece == end_of_block[-1]:       
                del end_of_block[-1]
                if not end_of_block:
                    return index + 2
            elif piece in block_indicators:       
                end_of_block.append(block_indicators[piece])                              
        else:      
            raise SyntaxError("Block is missing a closing delimiter {}".format(''.join(program[:index + 2])))
         
def parse_next_value(program, ignore_tokens=IGNORE_TOKENS, string_indicators=STRING_INDICATORS):        
    try:
        while program[0] in ignore_tokens:
            del program[0]
    except IndexError:
        return None    
    
    end_of_block = parse_for_block(program)
    if end_of_block is None:
        next_name = [program[0]]                 
        del program[0]                    
    else:            
        while program[0] in ignore_tokens:
            del program[0]
      
        if program[0] not in string_indicators:                       
            next_name = program[:end_of_block]#[1:end_of_block - 1]            
            del program[:end_of_block]             
        else:            
            next_name = program[:end_of_block]
            del program[:end_of_block]
    return next_name

        
def is_integer(_bytes, _set=set(NUMBER_SYMBOLS)):
    try:
        value = int(_bytes)
    except (TypeError, ValueError):
        return False
    else:
        return True
        
def is_word(_bytes, _set=set(TOKEN_SYMBOLS), _set2=set(NUMBER_SYMBOLS)):
    # determine whether or not _bytes is a word like "def" or "variable_name1", or something like ";" or " "  or '10234'   
    try:
        if not len(_set.union(_bytes)) > len(_set) and not is_integer(_bytes):
            return True
    except TypeError:
        pass
    return False
                         
def is_operator(_bytes, _set=set(OPERATOR_SYMBOLS)):
    if not set(_bytes).difference(_set):
        return True
    else:
        return False
            
def test_parse_string():    
    test_input = "def test_function(arguments){for item in range(10){print item}}"
    parse_string(test_input)
    #for token in parse_string(test_input):
    #    print token
    
def test_parse_for_block():
    test_input = b"'{define test_parse_string HEADER(){\n\"printf('testin \"ur\" limitz')\";}}'"
    program = parse_string(test_input)
    #print ''.join(program)
    first_block = parse_for_block(program)
    print ''.join(program[:first_block])
    
    result = parse_for_block("testing")
    assert result is None
    
if __name__ == "__main__":
    test_parse_string()
    test_parse_for_block()    
    