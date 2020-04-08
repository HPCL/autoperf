import sys
import math

class _Error(Exception):
    """Base class for exceptions in this module"""
    pass

class UnresolvedSymbolError(_Error):
    def __init__(self, symbol):
        self.symbol = symbol

    def __str__(self):
        return "Unresolved symbol: `%s`" % self.symbol

class MathExp:
    # token types
    OP  = 0
    VAR = 1
    NUM = 2
    LP  = 3
    RP  = 4
    FUNC = 5
    COMMA = 6

    # associativity
    LR = 0
    RL = 1

    delimiter = "(),=+-*/%^ \t"

    operators = {
        # (precedence, associativity, argc, op)
        '=': (0, RL, 2, lambda a,b: b),
        '+': (1, LR, 2, lambda a,b: a+b),
        '-': (1, LR, 2, lambda a,b: a-b),
        '*': (2, LR, 2, lambda a,b: a*b),
        '/': (2, LR, 2, lambda a,b: a/b),
        '%': (2, LR, 2, lambda a,b: a%b),
        '^': (3, RL, 2, lambda a,b: pow(a,b)),
    }

    functions = {
        # (argc, op)
        'abs'  : (1, lambda a:    abs(a)),
        'min'  : (2, lambda a, b: min(a, b)),
        'max'  : (2, lambda a, b: max(a, b)),
        'pow'  : (2, lambda a, b: math.pow(a, b)),
        'exp'  : (1, lambda a:    math.exp(a)),
        'log'  : (2, lambda a, b: math.log(a, b)),
        'log10': (1, lambda a:    math.log10(a)),
        'sqrt' : (1, lambda a:    math.sqrt(a)),
        'acos' : (1, lambda a:    math.acos(a)),
        'asin' : (1, lambda a:    math.asin(a)),
        'atan' : (1, lambda a:    math.atan(a)),
        'cos'  : (1, lambda a:    math.cos(a)),
        'sin'  : (1, lambda a:    math.sin(a)),
        'tan'  : (1, lambda a:    math.tan(a)),
    }

    def __init__(self, exp):
        """
        Parse infix notation mathematical expressions to reverse
        polish notation (RPN) using shunting-yard algorithm.

        See http://en.wikipedia.org/wiki/Shunting-yard_algorithm
        """

        # infix notation math exp
        self.exp       = exp.strip()

        # operator stack
        self.opstack   = [ ]

        # output queue
        self.rpn       = [ ]

        # variable symbol table
        self.variables = set()

        # while there are tokens to be read, read a token
        for token in self.gen_tokens():
            # if the token is a number, then add it to the output
            # queue
            if token[0] == MathExp.NUM:
                self.rpn.append(token)

            # if the token is a variable, then add it to the output
            # queue
            elif token[0] == MathExp.VAR:
                self.rpn.append(token)
                self.variables.add(token[1])

            # if the token is a function, then push it onto the stack
            elif token[0] == MathExp.FUNC:
                self.opstack.append(token)

            # if the token is a function argument separator (e.g. a
            # comma)
            elif token[0] == MathExp.COMMA:
                get_lp = False
                # until the token at the top of the stack is a left
                # parenthesis, pop operators off the stack onto the
                # ouput queue
                while (len(self.opstack) > 0):
                    if self.opstack[-1][0] != MathExp.LP:
                        self.rpn.append(self.opstack.pop())
                    else:
                        get_lp = True
                        break

                # if no left parentheses are encountered, either the
                # separator was misplaced or parentheses were
                # mismatched
                if not get_lp:
                    raise Exception("Syntax error")

            # if the token is an operator o1, then
            elif token[0] == MathExp.OP:
                o1 = token[1]

                # while there is an operator token, o2, at the top of
                # the operator stack ...
                while (len(self.opstack) > 0) and \
                      (self.opstack[-1][0] == MathExp.OP):
                    o2 = self.opstack[-1][1]

                    # ... and either o1 is left-associative and its
                    # precedence is less than or equal to that of o2,
                    # or o1 has precedence less than that of o2
                    if ((self.operators[o1][1] == MathExp.LR) and            \
                        (self.operators[o1][0] <= self.operators[o2][0])) or \
                       (self.operators[o1][0] < self.operators[o2][0]):
                        # pop o2 of the stack, onto the ouput queue
                        self.rpn.append(self.opstack.pop())
                    else:
                        break

                # push o1 onto the stack
                self.opstack.append(token)

            # if the token is a left parenthesis, then push it onto
            # the stack
            elif token[0] == MathExp.LP:
                self.opstack.append(token)

            # if the token is a right parenthesis
            elif token[0] == MathExp.RP:
                get_lp = False;
                while len(self.opstack) > 0:
                    # until the token at the top of the stack is a
                    # left parenthesis, pop operators off the stack on
                    # to the output queue
                    if self.opstack[-1][0] != MathExp.LP:
                        self.rpn.append(self.opstack.pop())
                    # pop the left parenthesis from the stack, but not
                    # onto the output queue
                    else:
                        self.opstack.pop()
                        get_lp = True
                        break

                # if the stack runs out without finding a left
                # parenthesis, then there are mismatched parentheses
                if not get_lp:
                    raise Exception("Mispatched parentheses")

                # if the token at the top of the stack is a function
                # token, pop it onto the ouput queue
                if (len(self.opstack) > 0) and \
                   (self.opstack[-1][0] == MathExp.FUNC):
                    self.rpn.append(self.opstack.pop())

        # when there are no more tokens to read
        # while there are still operator tokens in the stack
        while len(self.opstack) > 0:
            # if the operator token on the top of the stack is a
            # parenthesis, then there are mismatched parentheses
            if (self.opstack[-1][0] == MathExp.LP) or \
               (self.opstack[-1][0] == MathExp.RP):
                raise Exception("Mispatched parentheses")

            # pop the operator onto the ouput queue
            self.rpn.append(self.opstack.pop())

    def get_type(self, token):
        """
        Get the type of the token
        """
        if token == '(':
            return MathExp.LP

        if token == ')':
            return MathExp.RP

        if token == ',':
            return MathExp.COMMA

        if token in self.operators.keys():
            return MathExp.OP

        if token in self.functions.keys():
            return MathExp.FUNC

        try:
            val = float(token)
        except ValueError:
            return MathExp.VAR
        else:
            return MathExp.NUM

    def get_token(self):
        """
        Return next token in the mathematical expression
        """
        for i in range(len(self.exp)):
            if self.exp[i] in self.delimiter:
                if i == 0:
                    rv = (self.get_type(self.exp[i]), self.exp[i])
                    self.exp = self.exp[1:].strip()
                else:
                    rv = (self.get_type(self.exp[:i]), self.exp[:i])
                    self.exp = self.exp[i:].strip()

                return rv

        rv = (self.get_type(self.exp), self.exp)
        self.exp = ''
        return rv

    def gen_tokens(self):
        """
        Generator. Generate all tokens in the methematical expression
        """
        while len(self.exp) > 0:
            yield self.get_token()

    def resolve_symbol(self, symtab, token):
        if token[0] == MathExp.NUM:
            return float(token[1])
        elif token[0] == MathExp.VAR:
            if token[1] in symtab.keys():
                return symtab[token[1]]
            else:
                raise UnresolvedSymbolError(token[1])
        else:
            raise Exception("Fatal error: bug encountered")

    def apply_operator(self, symtab, stack, op):
        argv = [ ]
        argc = MathExp.operators[op][2]
        oper = MathExp.operators[op][3]

        # sanity check
        if len(stack) < argc:
            raise Exception("Syntax error")

        # get typed arguments
        for i in range(argc):
            argv.insert(0, stack.pop())

        # resolve argv[0]
        if op is '=':
            # special treatment for op=
            if argv[0][0] != MathExp.VAR:
                raise Exception("Syntax error")
            else:
                argv[0] = argv[0][1]
        else:
            # normal case
            argv[0] = self.resolve_symbol(symtab, argv[0])

        # now resolve remaining argv[1:]
        for i in range(1, argc):
            argv[i] = self.resolve_symbol(symtab, argv[i])

        # FIXME: avoid divide-by-zero exception. Should we do it here?
        # Or should we even do it?
        if op is '/' and argv[1] == 0:
            argv[1] = 1

        # apply the operation and update the stack
        stack.append((MathExp.NUM, oper(*argv)))

        # update symbal table for op=
        if op is '=':
            symtab[argv[0]] = argv[1]

    def apply_function(self, symtab, stack, f):
        argv = [ ]
        argc = MathExp.functions[f][0]
        func = MathExp.functions[f][1]

        # sanity check
        if len(stack) < argc:
            raise Exception("Syntax error")

        # get typed arguments
        for i in range(argc):
            argv.insert(0, self.resolve_symbol(symtab, stack.pop()))

        stack.append((MathExp.NUM, func(*argv)))

    def eval(self, symtab={}):
        """
        Eval the RPN expression.

        See http://en.wikipedia.org/wiki/Reverse_Polish_notation
        """
        eval_stack = [ ]

        for token in self.rpn:
            if token[0] == MathExp.NUM:
                eval_stack.append(token)

            elif token[0] == MathExp.VAR:
                eval_stack.append(token)

            elif token[0] == MathExp.OP:
                self.apply_operator(symtab, eval_stack, token[1])

            elif token[0] == MathExp.FUNC:
                self.apply_function(symtab, eval_stack, token[1])

        if len(eval_stack) == 1:
            return self.resolve_symbol(symtab, eval_stack[0])
        else:
            raise Exception('Syntax error')

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print ("Usage: python MathExp.py <input_file>")
        exit(1)

    symtab = {'pi': math.pi, 'e': math.e}

    with open(sys.argv[1], 'r') as f:
        for line in f:
            line = line.strip()

            # ignore empty line
            if len(line) == 0:
                continue

            # ignore comments
            if line[0] is '#':
                continue

            print (line)
            exp = MathExp(line)
            rv = exp.eval(symtab)

    print ("rv = %f" % rv)
