import parsing
   
class Interpreter(object):    
    
    def __init__(self, builtins=None, preprocess_table=None):
        if builtins is None:
            builtins = {"define" : self.handle_define, "def" : self.handle_def,
                        "foreign" : self.handle_foreign, "for" : self.handle_for,
                        
                        "print" : self.handle_print, "call" : self.handle_call,                          
                        "=" : self.handle_equals, "+" : self.handle_plus,
                        "if" : self.handle_if, ";" : self.handle_semicolon,
                        "__stack__" : []}                      
        self.builtins = builtins                     
     
    def run(self, source, context=None, stack=None, preprocessor=None):
        program = self.compile(source)
        return self.execute(program, context, stack, preprocessor)
        
    def compile(self, source):        
        return parsing.parse_string(source)
        
    def execute(self, program, context=None, stack=None, preprocessor=None):        
        context = context if context is not None else self.builtins.copy()
        context["__stack__"] = stack if stack is not None else []
        context["__preprocessor__"] = preprocessor if preprocessor is not None else dict()
        program = program[:]               
        output = self.evaluate(program, context)

        if parsing.is_word(output):
            try:
                output = context[output]
            except KeyError:
                raise NameError("{} not found".format(output))
            
        if context["__stack__"]: 
            raise ValueError("Stack not empty when program finished: {}".format(context["__stack__"]))        
        return output
        
    def evaluate(self, program, context):
        _builtins = self.builtins.values()
        _program = program[:]
        
        while program:                                                
            name = parsing.parse_next_value(program)      
            token = self.resolve_next_value(name, context)    
            if token is None:
                continue
            if token in _builtins:                  
                token(program, context)             
            else:                                                
                self.handle_unrecognized_token((''.join(name), token), program, context)
        try:                      
            return context["__stack__"].pop(-1)[1]
        except IndexError:
            return None
        
    def resolve_next_value(self, next_name, context):               
        if next_name is None or not next_name:
            return None        
        
        if len(next_name) == 1:             
            next_name_value = self.resolve_name(next_name[0], context)          
        else:
            if next_name[0] in parsing.STRING_INDICATORS:          
                next_token = ''.join(parsing.parse_next_value(next_name))         
                next_name_value = self.resolve_name(next_token, context)                         
                if next_name:         
                    context["__stack__"].append((next_token, next_name_value))
                    
            if next_name:                         
                next_name_value = self.resolve_block(next_name[1:-1], context)            
                            
        if parsing.is_integer(next_name_value):
            next_name_value = int(next_name_value)
        
        return next_name_value
                
    def resolve_name(self, next_name, context):                                   
        try:
            next_name = context["__preprocessor__"][next_name]
        except KeyError:
            pass    
        else:                
            try:
                block = self.compile(next_name)                             
            except TypeError:
                pass
            else:                        
                if len(block) > 1 and block[0] not in parsing.STRING_INDICATORS:
                    block = block[1:-1]                                   
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
        next_item = parsing.parse_next_value(program)
        true_or_false = self.resolve_next_value(next_item, context)            
        if true_or_false == True:
            
            next_item = parsing.parse_next_value(program)
            result = self.resolve_next_value(next_item, context)
            if result is not None:
                context["__stack__"].append((None, result))
            
            if program:
                _else = parsing.parse_next_value(program)
             
                while _else[0] == "elif":          
                    _conditional = parsing.parse_next_value(program)             
                    _block = parsing.parse_next_value(program)
               
                    if program:
                        _else = parsing.parse_next_value(program)
                    else:
                        return
                                    
                if _else[0] == "else":
                    _block = parsing.parse_next_value(program)
                else:                    
                    program[:] = _else + program
        else:
            _previous_block = parsing.parse_next_value(program)
            
            _else = parsing.parse_next_value(program)   
            if _else[0] == "elif":
                result = self.handle_if(program, context)                
            elif _else[0] == "else":     
                next_block = parsing.parse_next_value(program)
                result = self.resolve_next_value(next_block, context)
                if result is not None:
                    context["__stack__"].append((None, result))
            else:
                program[:] = _else + program
   
    def handle_for(self, program, context):        
        names = parsing.parse_next_value(program)
        if names[0] in parsing.BLOCK_INDICATORS:
            names = names[1:-1]
        _names = []
        while names:
            _names.append(parsing.parse_next_value(names)[0])
        names = _names        
        
        _in = parsing.parse_next_value(program)
        if _in[0] != "in":
            raise SyntaxError("Expected '{}'".format("in"))
                
        next_item = self.resolve_next_value(parsing.parse_next_value(program), context)
        assert next_item[0] in parsing.BLOCK_INDICATORS, next_item
        
        iterator = iter(next_item[1:-1])
        loop_body = parsing.parse_next_value(program)    
        running = True        
        while running:
            try:
                next_item = next(iterator)
            except StopIteration:
                running = False
                break
            else:                
                if len(names) > 1:                
                    for index, name in enumerate(names):                        
                        context[name] = next_item[index]  
                else:                    
                    context[names[0]] = next_item            
            self.resolve_block(loop_body[:], context)
        
    def handle_foreign(self, program, context):   
        language = ''.join(parsing.parse_next_value(program))        
        if language.lower() == "python":
            python_source = ''.join(parsing.parse_next_value(program))[1:-1]            
            python_code = compile(python_source, "foreign_function_interface", "exec")
            _context = context.copy()
            exec(python_code, _context, _context)            
        else:
            raise NotImplementedError("Foreign language '{}' not implemented".format(language))
        
    def handle_define(self, program, context):                  
        name_token = parsing.parse_next_value(program)
      #  function_name = self.resolve_next_value(name_token, context)        
        body_token = parsing.parse_next_value(program)
        context["__preprocessor__"][''.join(name_token)] = ''.join(body_token)        
        
    def handle_def(self, program, context):        
        function_name = parsing.parse_next_value(program)
        arguments = parsing.parse_next_value(program)        
        arguments = [item for item in arguments if parsing.is_word(item)]
        body = parsing.parse_next_value(program)       
        context[''.join(function_name)] = (arguments, body)       
        
    def handle_call(self, program, context):                        
        function_name = ''.join(parsing.parse_next_value(program))
        
        try:
            arguments, body = context[function_name]
        except KeyError:
            raise NameError("{} not found".format(function_name))
        except TypeError:
            raise TypeError("{} is not callable".format(function_name))
        
        preprocess_table = context["__preprocessor__"]
        backup = []
        prune = []        
        for argument in arguments:                     
            del program[0]                   
            if argument in preprocess_table:
                backup.append((argument, preprocess_table[argument]))
            else:
                prune.append(argument)
            next_token = parsing.parse_next_value(program)
            preprocess_table[argument] = self.resolve_next_value(next_token, context)            
        
        _context = context.copy()                    
        value = self.evaluate(body[:], _context)        
        
        for item, _backup in backup:
            preprocess_table[item] = _backup
        for item in prune:
            del preprocess_table[item]
                    
    def handle_print(self, program, context):          
        next_token = parsing.parse_next_value(program)                        
        print self.resolve_next_value(next_token, context)        
                
    def handle_plus(self, program, context):             
        try:
            last_name_value = context["__stack__"].pop(-1)[1]              
        except IndexError:
            raise SyntaxError("Unable to load left hand operand for '+' operation ({}) ({})".format(program[:8], context["__stack__"]))

        next_name = parsing.parse_next_value(program)
        next_name_value = self.resolve_next_value(next_name[:], context)                       
        
        try:
            if last_name_value[0] in parsing.STRING_INDICATORS:
                last_name_value = last_name_value[:-1]
                assert next_name_value[0] in parsing.STRING_INDICATORS
                next_name_value = next_name_value[1:]
            elif next_name_value[0] in parsing.STRING_INDICATORS:
                next_name_value = next_name_value[1:-1]
            else:                                   
                value = last_name_value + next_name_value     
        except (IndexError, TypeError):     
            pass
                
        value = last_name_value + next_name_value                     
        context["__stack__"].append((None, value))
        
    def handle_equals(self, program, context):                                
        name = context["__stack__"].pop(-1)[0]             
        next_token = parsing.parse_next_value(program)        
        value = self.resolve_next_value(next_token, context)         
        context[name] = value                         
        
    def handle_operator(self, operator, program, context):        
        left_hand_operand = context["__stack__"].pop(-1)[1]
        right_hand_operand = self.resolve_next_value(program, context)
        result = getattr(left_hand_operand, "__{}__".format(self.operator_name[operator]))(right_hand_operand)
        context["__stack__"].append((None, result))
        
    def handle_unrecognized_token(self, token, program, context):                
        context["__stack__"].append(token)
             
    def handle_semicolon(self, program, context):
        pass
        
    @classmethod
    def unit_test(cls):
        interpreter = cls()
        
        for file_name in ("assignment", "preprocessorprinting", "functions", "foreign", "branching"):  
            with open("./unittesting/{}.txt".format(file_name), 'r') as _file:
                test_source = _file.read()
            print "\nNext program" + ('-' * (79 - len("\nNext program")))
            print '*' * 79
            print test_source
            print
            print '*' * 79            
            print "Executing..."
            print                            
            program = interpreter.compile(test_source)
            output = interpreter.execute(program)
            if output is not None:
                print "Obtained output: ", output            
            
if __name__ == "__main__":
    Interpreter.unit_test()
    