LanguagePlay (Name subject to change)
--------
A computer programming language that currently supports the following:
    
- strings and integers
    - addition operation is currently the only available operator
- preprocessor macros
- print
- expressions
- if/elif/else
- define/call functions
- foreign function interface
    - currently only supports python
    
The syntax is very flexible and customizable.
The only example (or even existing) code is for the Interpreter unit test. Consequently it was written more to stress edge cases then read well.
Each space separates a program. Some programs print something, other programs ultimately return a value:

```
"define takeitfurther \'Ok now I am REALLY happy! :D\'\n" + 
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

"x = 10 y = 20 z = {x + y} print (z) z", # print z and then return z

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
" 1  ", # returns 1

"foreign python \"import this; __stack__.append('python was here')\"" # returns 'python was here'!
```





 Why?
----
Fun.