import pprint
import parsing

class InvalidToken(Exception): pass
   
class Interpreter(object):    
    
    def __init__(self, builtins=None):
        if builtins is None:
            builtins = {"handle_define" : self.handle_define, "handle_def" : self.handle_def,                      
                        "handle_ " : self.handle_space, "handle_\n" : self.handle_newline,
                        "handle_print" : self.handle_print, "handle_+" : "handle_plus"}                      
        self.builtins = builtins             
        self.preprocess_table = {}
        
    def compile(self, source):
        return parsing.parse_string(source)
        
    def execute(self, program, context=None):        
        context = context if context is not None else self.builtins.copy()
        program = program[:]
        context["__stack__"] = stack = []        
        while program:
            token = program[0]                                            
            print "Executing: ", token
            try:
                handler = context["handle_{}".format(token)]
            except KeyError:                
                self.invalid_token(program, context)
            del program[0]            
            handler(program, context)            
                
    def handle_define(self, program, context):
        # define token expression        
        assert program[0] == ' '
        token = program[1]
        assert program[2] == ' '
        del program[:3]
        block_end = parsing.parse_for_block(program)
        if block_end is None:
            value = program[0]
            del program[0]
        else:
            value = program[:block_end]
            del program[:block_end]
        self.preprocess_table[token] = ''.join(value)
        print "Defined: ", token, ''.join(value)
        
    def handle_def(self, program, context):        
        assert program[0] == ' '
        function_name = program[1]
        del program[:2]
                
        end_of_arguments = parsing.parse_for_block(program)
        if end_of_arguments is None:
            raise ValueError("Invalid function header ...{}...".format(''.join(program[:8])))
        else:
            arguments = program[:end_of_arguments]
            del program[:end_of_arguments]
        
        end_of_body = parsing.parse_for_block(program)
        if end_of_body is None:
            raise ValueError("Invalid function body ...{}...".format(''.join(program[:8])))
        else:
            body = program[:end_of_body]
            del program[:end_of_body]
        function_name = ''.join(function_name)      
        context[function_name] = (arguments, body)
       # context["__functions"]
       # context["handle_function"] = (arguments, body)
                     
    def handle_space(self, program, context):
        pass
        
    def handle_newline(self, program, context):
        pass
        
    def handle_print(self, program, context):   
        assert program[0] == ' '
        del program[0]        
        end_of_string = parsing.parse_for_block(program)        
        assert end_of_string is not None, program
        _text = program[:end_of_string]
         
        try:
            _text = self.preprocess_table[_text]
        except KeyError:            
            pass
        print _text    
        del program[:end_of_string]
        
    def handle_plus(self, program, context):
        print "Plussing: ", program
        
        
    def invalid_token(self, program, context):
        print("Exception" + ('*' * (79 - len("Exception"))))
        print("Program: {}".format(program[:8]))
        program[0] += " <--- Invalid Token"
        _display = program[:5]
        pprint.pprint(_display, width=1)
        #print("Invalid Token: ->{} {}".format(program[0], program[1:]))
        raise InvalidToken("Invalid token")
             
    @classmethod
    def unit_test(cls):
        interpreter = cls()
        
        test_input = "def test_function(something){print something}"                                     
        program = interpreter.compile(test_input)  
        interpreter.execute(program)
        
        test_input = "define takeitfurther \'Ok now I am REALLY happy! :D\'\nprint takeitfurther {oh}"
        program = interpreter.compile(test_input)        
        interpreter.execute(program)
        
        #test_input = "define item_count 10 for item in range(item_count){print item}"
        #program = interpreter.compile(test_input)        
        #interpreter.execute(program)
        
        test_input = "define item_a 10\ndefine item_b 20\ndefine item_a {item_a + item_b}\nprint item_a"
        program = interpreter.compile(test_input)
        interpreter.execute(program)
        
        
if __name__ == "__main__":
    Interpreter.unit_test()
    