#!/usr/bin/env python3

from . import lexer as sync_lexer


def macro_subst(code, macros):
    code_final = ''

    lexer = sync_lexer.build()
    lexer.input(code)

    while True:
        t = lexer.token()

        if t is None:
            break

        if t.type == 'ID' and t.value in macros:
            code_final += str(macros[t.value])
        else:
            code_final += str(t.value)

    return code_final


def parse(code, macros={}):
    global sync_lexer

    #if macros:
    #    code = macro_subst(code, macros)

    lexer = sync_lexer.build()

    return lexer
