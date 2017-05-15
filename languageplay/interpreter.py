import parsing

class InvalidToken(Exception): pass
   
class Interpreter(object):    
    
    def __init__(self, builtins=None, preprocess_table=None, ignore_tokens=(' ', '\n')):
        if builtins is None:
            builtins = {"define" : self.handle_define, "def" : self.handle_def,
                        "foreign" : self.handle_foreign,
                        "print" : self.handle_print, "call" : self.handle_call,                          
                        "=" : self.handle_equals, "+" : self.handle_plus,
                        "if" : self.handle_if,
                        "__stack__" : []}                      
        self.builtins = builtins             
        self.preprocess_table = {} if preprocess_table is None else preprocess_table
        self.ignore_tokens = ignore_tokens
        
    def compile(self, source):
        return parsing.parse_string(source)
        
    def execute(self, program, context=None):        
        context = context if context is not None else self.builtins.copy()
        program = program[:]               
        output = self.evaluate(program, context)
        if parsing.is_word(output) and output not in context:
            raise NameError("{} not found".format(output))
        if context["__stack__"]: 
            raise ValueError("Stack not empty when program finished: {}".format(context["__stack__"]))
        return output
        
    def evaluate(self, program, context):
        _builtins = self.builtins.values()
        while program:                                    
            #print "Resolving: ", program
            token = self.resolve_next_value(program, context)    
            if token is None:
                break
            if token in _builtins:            
                token(program, context)             
            else:                
                self.handle_unrecognized_token(token, program, context)
        try:            
            return context["__stack__"].pop(-1)
        except IndexError:
            return None
        
    def resolve_next_value(self, program, context):
        next_name = self.parse_next_value(program)
        if next_name is None:
            return None
            
        if len(next_name) == 1:          
            next_name_value = self.resolve_name(next_name[0], context)           
        elif next_name[0] not in parsing.STRING_INDICATORS:
            assert next_name           
            next_name_value = self.resolve_block(next_name, context)
        else:           
            next_name_value = ''.join(next_name)
            
        if parsing.is_integer(next_name_value):
            next_name_value = int(next_name_value)
                     
        return next_name_value
        
    def parse_next_value(self, program):        
        try:
            while program[0] in self.ignore_tokens:
                del program[0]
        except IndexError:
            return None
            
        end_of_block = parsing.parse_for_block(program)
        if end_of_block is None:
            next_name = [program[0]]         
            del program[0]            
        else:            
            while program[0] in self.ignore_tokens:
                del program[0]
          
            if program[0] not in parsing.STRING_INDICATORS:                       
                next_name = program[1:end_of_block - 1]            
                del program[:end_of_block] 
                          
            else:            
                next_name = program[:end_of_block]
                del program[:end_of_block]
        return next_name
        
    def resolve_name(self, next_name, context):                   
        try:
            next_name = self.preprocess_table[next_name]
        except KeyError:
            pass    
        else:
            # if a block was defined, then evaluate the block now   
            try:
                block = self.compile(next_name)                             
            except TypeError:
                pass
            else:
                if next_name[0] not in parsing.STRING_INDICATORS:                                                            
                    next_name = self.resolve_block(block, context)             
        try:
            next_name_value = context[next_name]
        except KeyError:
            next_name_value = next_name             
        return next_name_value

    def resolve_block(self, block, context):
        _context = context.copy()  
        return self.evaluate(block, _context)                            
                    
    def handle_if(self, program, context):
        true_or_false = self.resolve_next_value(program, context)
        if true_or_false == True:
            
            result = self.resolve_next_value(program, context)
            if result is not None:
                context["__stack__"].append(result)
            
            if program:
                _else = self.parse_next_value(program)
             
                while _else[0] == "elif":          
                    _conditional = self.parse_next_value(program)             
                    _block = self.parse_next_value(program)
               
                    if program:
                        _else = self.parse_next_value(program)
                    else:
                        return
                                    
                if _else[0] == "else":
                    _block = self.parse_next_value(program)
                else:                    
                    program[:] = _else + program
        else:
            _previous_block = self.parse_next_value(program)
            
            _else = self.parse_next_value(program)   
            if _else[0] == "elif":
                result = self.handle_if(program, context)                
            elif _else[0] == "else":            
                result = self.resolve_next_value(program, context)
                if result is not None:
                    context["__stack__"].append(result)                    
            else:
                program[:] = _else + program
   
    def handle_foreign(self, program, context):
        language = self.resolve_next_value(program, context)        
        if language.lower() == "python":
            python_source = self.resolve_next_value(program, context)[1:-1]  
            print "Compiling python source: ", python_source
            python_code = compile(python_source, "foreign_function_interface", "exec")
            _context = context.copy()
            exec(python_code, _context, _context)            
        else:
            raise NotImplementedError("Foreign language '{}' not implemented".format(language))
        
    def handle_define(self, program, context):          
        token = self.resolve_next_value(program, context)               
        value = self.parse_next_value(program)
        self.preprocess_table[token] = ''.join(value)
                
    def handle_def(self, program, context):        
        function_name = self.parse_next_value(program)
        arguments = self.parse_next_value(program)        
        arguments = [item for item in arguments if parsing.is_word(item)]
        body = self.parse_next_value(program)       
        context[''.join(function_name)] = (arguments, body)       
        
    def handle_call(self, program, context):                        
        function_name = ''.join(self.parse_next_value(program))
        try:
            arguments, body = context[function_name]
        except KeyError:
            raise NameError("{} not found".format(function_name))
        
        preprocess_table = self.preprocess_table        
        backup = []
        prune = []        
        for argument in arguments:                     
            del program[0]                   
            if argument in preprocess_table:
                backup.append((argument, preprocess_table[argument]))
            else:
                prune.append(argument)
            preprocess_table[argument] = self.resolve_next_value(program, context)            
            
        _context = context.copy()                
        value = self.evaluate(body, _context)        
        
        for item, _backup in backup:
            preprocess_table[item] = _backup
        for item in prune:
            del preprocess_table[item]
                    
    def handle_print(self, program, context):                           
        print self.resolve_next_value(program, context)        
                
    def handle_plus(self, program, context):                        
        try:
            last_name = context["__stack__"].pop(-1)                
        except IndexError:
            raise SyntaxError("Unable to load left hand operand for '+' operation ({})".format(program[:8]))
                
        last_name_value = self.resolve_name(last_name, context)                
        next_name_value = self.resolve_next_value(program, context)                       
        try:
            value = last_name_value[:-1] + next_name_value[1:]
        except TypeError:
            value = last_name_value + next_name_value
        context["__stack__"].append(value)
                    
    def handle_equals(self, program, context):                                
        name = context["__stack__"].pop(-1)        
        value = self.resolve_next_value(program, context)        
        context[name] = value                 
        
    def handle_operator(self, operator, program, context):        
        left_hand_operand = context["__stack__"].pop(-1)
        right_hand_operand = self.resolve_next_value(program, context)
        result = getattr(left_hand_operand, "__{}__".format(self.operator_name[operator]))(right_hand_operand)
        context["__stack__"].append(result)
        
    def handle_unrecognized_token(self, token, program, context):        
        context["__stack__"].append(token)
             
    @classmethod
    def unit_test(cls):
        interpreter = cls()
        
        for test_source in ("define takeitfurther \'Ok now I am REALLY happy! :D\'\n" + 
                            "print takeitfurther",
                            
                            "test_value1 = 1\n" + 
                            "test_value2 = {test_value1 + test_value1}\n" +
                            "print test_value2",
                            
                            "define item_a {10 + 1 + 2}\n" + 
                            "item_b = 20\n" + 
                            "test_value = {item_a + {item_b + item_b + item_b}}\n" + 
                            "print test_value",
                            
                            "print {\'testing \' + \'testing further\'}",
                            
                            "def test_function(thing1 thing2){print {thing1 + thing2}}\n" + 
                            "call test_function 'I love you so much ' ':D!'\n" +
                            "print 'and you even more ;)'",
                            
                            "define test_value '10'\n" + 
                            "test_string = {test_value + 'test1 ' + 'test2 ' + {'test3 ' + 'test4 ' + 'test5 '}}\n" +
                            "print test_string",
                            
                            "define implicit_reference {variable1 + variable2}\n" +
                            "variable1\n=\n1\n" +
                            "variable2\n=\n2\n" +
                            "print\nimplicit_reference\n" +
                            "variable1\n=\n{1 + 5}\n" +
                            "implicit_reference",
                            
                            "x = 10 y = 20 z = {x + y} print (z) z",
                            
                            "x = 0\n" + 
                            "y = 0\n" + 
                            "if (x){\n" +
                            "    print 'x is True!'}\n" +
                            "elif (y){\n" +
                            "    print 'y is True!'}\n" +
                            "elif (0){}\n" + 
                            "elif (1){print '1 is 1!'}\n" + 
                            "else{\n" + 
                            "    print 'x and y are False!'}\n" +
                            "print 'good happy success'\n  " +
                            "def wow(x y){print {x + y}}\n" + 
                            "call wow 1 2\n" + 
                            " 1  ",
                            
                            "foreign python \"import this; __stack__.append('python was here')\""
                            ):
                           
                            #"define item_count 10\n" +
                            #"for item in range(item_count){print 'item'}"):        
            print "\nNext program" + ('-' * (79 - len("\nNext program")))
            #print '*' * 79
            #print test_source
            #print
            #print '*' * 79            
            #print "Executing..."
            #print                            
            program = interpreter.compile(test_source)
            output = interpreter.execute(program)
            if output is not None:
                print "Obtained output: ", output
        
if __name__ == "__main__":
    Interpreter.unit_test()
    