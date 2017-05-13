import pprint
import parsing

class InvalidToken(Exception): pass
   
class Interpreter(object):    
    
    def __init__(self, builtins=None):
        if builtins is None:
            builtins = {"handle_define" : self.handle_define, "handle_def" : self.handle_def,                      
                        "handle_ " : self.handle_space, "handle_\n" : self.handle_newline,
                        "handle_print" : self.handle_print, 
                        "handle_=" : self.handle_equals, "handle_+" : self.handle_plus,
                        "__stack__" : []}                      
        self.builtins = builtins             
        self.preprocess_table = {}
        
    def compile(self, source):
        return parsing.parse_string(source)
        
    def execute(self, program, context=None):        
        context = context if context is not None else self.builtins.copy()
        program = program[:]               
        self.evaluate(program, context)
        if context["__stack__"]: 
            raise ValueError("Stack not empty when program finished: {}".format(context["__stack__"]))
            
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
        if end_of_string is None:
            _text = program[0]
            del program[0]
        else:
            _text = program[:end_of_string]         
            del program[:end_of_string]
        try:
            _text = self.preprocess_table[_text]
        except KeyError:            
            pass
        if _text in context:
            _text = context[_text]
        print _text            
        
    def handle_plus(self, program, context):
        assert program[0] == ' '
        del program[0]        
        last_name = context["__stack__"].pop(-1)
        last_name_value = context[last_name] if parsing.is_word(last_name) else last_name
        next_name_value = self.resolve_next_value(program, context)               
        context["__stack__"].append(last_name_value + next_name_value)
            
    def resolve_next_value(self, program, context):
        end_of_block = parsing.parse_for_block(program)
        if end_of_block is None:
            next_name = program[0]
            print "Next item is a single item: ", next_name
            del program[0]
            try:
                next_name = self.preprocess_table[next_name]
            except KeyError:
                pass            
            if parsing.is_word(next_name):
                next_name_value = context[next_name]
            else:
                next_name_value = next_name            
        else:
            block = program[1:end_of_block - 1]
            del program[:end_of_block]
            _context = context.copy()
            print "Evaluating block: ", block
            self.evaluate(block, _context)                    
            next_name_value = _context["__stack__"].pop(-1)
        return next_name_value
        
    def handle_equals(self, program, context):                
        assert program[0] == ' '
        del program[0]        
        name = context["__stack__"].pop(-1)        
        value = self.resolve_next_value(program, context)
        #end_of_block = parsing.parse_for_block(program)
        #if end_of_block is None:
        #    value = program[0]
        #    del program[0]
        #else:
        #    _program = program[:end_of_block][1:-1]
        #    del program[:end_of_block]
        #    _context = context.copy()
        #    self.evaluate(_program, _context)
        #    value = _context["__stack__"].pop(-1)
            
        print "Assigning", name, value, context["__stack__"]
        context[name] = value
        
    def evaluate(self, program, context):
        while program:
            token = program[0]                   
            if token in self.preprocess_table:
                token = self.preprocess_table[token]
            try:
                handler = context["handle_{}".format(token)]
            except KeyError:                      
                print "Storing name: ", token
                context["__stack__"].append(token)
                del program[0]
                #self.invalid_token(program, context)
            else:                
                del program[0]            
                print "Handling: ", token            
                handler(program, context)          
        
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
        
        test_input = "define takeitfurther \'Ok now I am REALLY happy! :D\'\nprint takeitfurther"
        program = interpreter.compile(test_input)        
        interpreter.execute(program)
        
        #test_input = "define item_count 10 for item in range(item_count){print item}"
        #program = interpreter.compile(test_input)        
        #interpreter.execute(program)
                
        test_input = "test_value = 1\ntest_value = {test_value + test_value}"
        program = interpreter.compile(test_input)
        interpreter.execute(program)
        
        print "\nNext program"
        test_input = "define item_a 10\ndefine item_b 20\ntest_value = {item_a + {item_b + item_b}}\nprint test_value"
        program = interpreter.compile(test_input)
        interpreter.execute(program)
        
        
if __name__ == "__main__":
    Interpreter.unit_test()
    