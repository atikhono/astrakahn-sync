#!/usr/bin/env python3

import os
from . import ast
from . import coord
from . import exception as exn
from . import symtab
from . import types

precedence = (
    ('left', 'LOR', 'LAND', 'BOR', 'BAND', 'BXOR'),
    ('left', 'LE', 'GE', 'GEQ', 'LEQ', 'EQ', 'NEQ'),
    ('nonassoc', 'NOT'),
    ('left', 'MULT', 'DIVIDE', 'MOD', 'SHL', 'SHR'),
    ('right', 'UMINUS'),
)

configs = None
config_nodes = {}

intab = symtab.Symtab(None)
outtab = symtab.Symtab(None)
top = symtab.Symtab(None)
saved = top

def p_sync(p):
    '''
    sync : SYNCH VID LPAREN input_list BOR output_list RPAREN \
           LBRACE decl_list_opt state_list RBRACE
    '''
    p[0] = ast.Sync(p[2], ast.PortList(p[4], intab), ast.PortList(p[6], outtab),
                    p[9], ast.StateList(p[10]), None)


def p_VID(p):
    '''
    VID : ID
    '''
    c = coord.Coord(p.lineno(1), p.lexpos(1))
    if p[1] in configs:
        term = ast.ID(configs[p[1]], coord=c)
        config_nodes[p[1]].append(term)
    else:
        term = ast.ID(p[1], coord=c)
    p[0] = term


def p_VNUMBER(p):
    '''
    VNUMBER : ID
            | NUMBER
    '''
    if p[1] in configs:
        term = ast.NUMBER(configs[p[1]])
        config_nodes[p[1]].append(term)
    else:
        if type(p[1]) is not int:
            raise ValueError("ID instead of NUMBER, or undeclared macros.")
        else:
            term = ast.NUMBER(p[1])
    p[0] = term


def p_VTERM(p):
    '''
    VTERM : ID
    '''
    c = coord.Coord(p.lineno(1), p.lexpos(1))
    if p[1] in configs:
        term = ast.TERM(configs[p[1]], coord=c)
        config_nodes[p[1]].append(term)
    else:
        term = ast.ID(p[1], coord=c)
    p[0] = term


def p_id_list(p):
    '''
    id_list : VID
            | id_list COMMA VID
    '''
    p[0] = [p[1]] if len(p) == 2 else p[1] + [p[3]]


def p_input_list(p):
    '''
    input_list : input
               | input_list COMMA input
    '''
    p[0] = [p[1]] if len(p) == 2 else p[1] + [p[3]]


def p_input(p):
    '''
    input : VID
          | VID COLON VID
          | VID COLON VNUMBER
    '''
    if len(p) == 4:
        depth = p[3]
    else:
        depth = ast.DepthNone()

    tmp = intab.put(p[1].value,
            symtab.Entry(type=types.Choice(variants={}, tails=[types.Variable()]), ast=p[1]))
    if tmp is not None:
        raise exn.DuplicatesError("Channel '%s' was previously declared" %
                p[1].value, p[1].coord, tmp.ast.coord)

    p[0] = ast.Port(p[1], depth)


def p_output_list(p):
    '''
    output_list : output
                | output_list COMMA output
    '''
    p[0] = [p[1]] if len(p) == 2 else p[1] + [p[3]]


def p_output(p):
    '''
    output : VID
           | VID COLON depth_exp
    '''
    tmp = outtab.put(p[1].value,
            symtab.Entry(type=types.Choice(variants={}, tails=[types.Variable()]), ast=p[1]))
    if tmp is not None:
        raise exn.DuplicatesError("Channel '%s' was previously declared"
                % p[1].value, p[1].coord, tmp.ast.coord)

    p[0] = ast.Port(p[1], (ast.DepthNone() if len(p) == 2 else p[3]))


def p_depth_exp(p):
    '''
    depth_exp : VNUMBER
              | VID
              | VID PLUS VNUMBER
              | VID MINUS VNUMBER
    '''
    if len(p) == 2:
        p[0] = p[1]

    else:
        p[0] = ast.DepthExp(p[1], p[2], p[3])


def p_decl_list_opt(p):
    '''
    decl_list_opt : decl_list
                  | empty
    '''
    p[0] = ast.DeclList(p[1], top) if p[1] != '' else ast.DeclList([], top)


def p_decl_list(p):
    '''
    decl_list : decl
              | decl_list decl
    '''
    decl_list = p[1] if len(p) == 2 else p[1] + p[2]
    p[0] = decl_list


def p_decl_store(p):
    '''
    decl : STORE store_type id_list SCOLON
    '''
    for n in p[3]:
        tmp = top.put(n.value, symtab.Entry(type=types.Record(labels={}, tails=[]), ast=n))
        if tmp is not None:
            raise exn.DuplicatesError("Store variable '%s' was previously declared"
                    % n.value, n.coord, tmp.ast.coord)

    p[0] = [ast.StoreVar(n, p[2]) for n in p[3]]


def p_store_type(p):
    '''
    store_type : QM VID DOT VID
               | VID
    '''
    if len(p) == 2:
        p[0] = ast.StoreType(ast.ID('uniq'), p[1])
    else:
        p[0] = ast.StoreType(p[2], p[4])


def p_decl_state(p):
    '''
    decl : STATE state_type statevar_list SCOLON
    '''
    if isinstance(p[2], ast.IntType):
        for n in p[3]:
            tmp = top.put(n[0].value,
                    symtab.Entry(type=types.Int(p[2].size.value), ast=n[0]))
            if tmp is not None:
                raise exn.DuplicatesError("'%s' was previously declared"
                    % n[0].value, n[0].coord, tmp.ast.coord)
    else:
        e = [l.value for l in p[2].labels]
        for n in p[3]:
            tmp = top.put(n[0].value,
                    symtab.Entry(type=types.Enum(e), ast=n[0]))
            if tmp is not None:
                raise exn.DuplicatesError("'%s' was previously declared"
                    % n[0].value, n[0].coord, tmp.ast.coord)

    p[0] = [ast.StateVar(n[0], p[2], n[1]) for n in p[3]]


def p_state_type(p):
    '''
    state_type : INT LPAREN VNUMBER RPAREN
               | ENUM LPAREN id_list RPAREN
    '''
    if p[1] == 'int':
        p[0] = ast.IntType(p[3])
    else:
        for n in p[3]:
            tmp = top.put(n.value, symtab.Entry(type=types.Int(),
                ast=ast.IntExp('n0', [],
                    {'n0': ast.NUMBER(p[3].index(n), coord=n.coord)}),
                ro=True))
            if tmp is not None:
                raise exn.DuplicatesError("'%s' was previously declared"
                        % n.value, n.coord, tmp.ast.coord)

        p[0] = ast.EnumType(p[3])


def p_statevar_list(p):
    '''
    statevar_list : statevar
                  | statevar_list COMMA statevar
    '''
    p[0] = [p[1]] if len(p) == 2 else p[1] + [p[3]]


def p_statevar(p):
    '''
    statevar : ID
             | ID ASSIGN VNUMBER
    '''
    c = coord.Coord(p.lineno(1), p.lexpos(1))
    p[0] = (ast.ID(p[1], coord=c), ast.NUMBER(0) if len(p) == 2 else p[3])


def p_state_list(p):
    '''
    state_list : state
               | state_list state
    '''
    p[0] = [p[1]] if len(p) == 2 else p[1] + [p[2]]


def p_state(p):
    '''
    state : VID LBRACE on_scope elseon_scope_list_opt RBRACE
    '''
    p[0] = ast.State(p[1], [p[3]] + p[4])


def p_on_scope(p):
    '''
    on_scope : ON COLON trans_list
    '''
    p[0] = ast.TransOrder(p[3])


def p_elseon_scope_list_opt(p):
    '''
    elseon_scope_list_opt : elseon_scope_list
                          | empty
    '''
    p[0] = p[1] if p[1] != '' else []


def p_elseon_scope_list(p):
    '''
    elseon_scope_list : elseon_scope
                      | elseon_scope_list elseon_scope
    '''
    p[0] = [p[1]] if len(p) == 2 else p[1] + [p[2]]


def p_elseon_scope(p):
    '''
    elseon_scope : ELSEON COLON trans_list
    '''
    p[0] = ast.TransOrder(p[3])


def p_trans_list(p):
    '''
    trans_list : trans_stmt
               | trans_list trans_stmt
    '''
    p[0] = [p[1]] if len(p) == 2 else p[1] + [p[2]]


def p_trans_stmt(p):
    '''
    trans_stmt : trans_port condition_opt guard_opt action_list
    '''
    global saved, top
    t = ast.Trans(p[1], p[2], p[3], p[4], top)
    top = saved
    p[0] = t


def p_trans_port(p):
    '''
    trans_port : VID
    '''
    global saved, top
    saved = top
    top = symtab.Symtab(top)
    p[0] = p[1]


def p_condition_opt(p):
    '''
    condition_opt : DOT cond_segmark
                  | DOT cond_datamsg
                  | DOT cond_else
                  | empty
    '''
    if len(p) == 2:
        p_ast = ast.CondEmpty()
        top.put('this',
            symtab.Entry(type=types.Record(labels={}, tails=[]),
                         ast=p_ast, ro=False))
        p[0] = p_ast
    else:
        top.put('this',
            symtab.Entry(type=types.Record(labels={}, tails=[]),
                         ast=p[2], ro=False))
        p[0] = p[2]


def p_cond_segmark(p):
    '''
    cond_segmark : AT VID
    '''
    p[0] = ast.CondSegmark(p[2])


def p_cond_datamsg(p):
    '''
    cond_datamsg : QM VID
                 | LPAREN id_list tail_opt RPAREN
                 | QM VID LPAREN id_list tail_opt RPAREN
    '''
    if len(p) == 3:
        p[0] = ast.CondDataMsg(p[2], [], ast.TERM(None))

    elif len(p) == 5:
        for n in p[2]:
            tmp = top.put(n.value,
                    symtab.Entry(type=types.Variable(),#types.Record(labels={n.value:types.Variable()}),
                                 ast=n, ro=True))
            if tmp is not None:
                # tail_opt is parsed earlier than this rule hits
                if n.value == p[3].value:
                    raise exn.DuplicatesError("'%s' was previously declared"
                            % n.value, tmp.ast.coord, n.coord)
                raise exn.DuplicatesError("'%s' was previously declared"
                        % n.value, n.coord, tmp.ast.coord)

        p[0] = ast.CondDataMsg(ast.TERM(None), p[2], p[3])

    elif len(p) == 7:
        for n in p[4]:
            tmp = top.put(n.value,
                    symtab.Entry(type=types.Variable(),#types.Record(labels={n.value:types.Variable()}),
                                 ast=n, ro=True))
            if tmp is not None:
                # tail_opt is parsed earlier than this rule hits
                if n.value == p[5].value:
                    raise exn.DuplicatesError("'%s' was previously declared"
                            % n.value, tmp.ast.coord, n.coord)
                raise exn.DuplicatesError("'%s' was previously declared"
                        % n.value, n.coord, tmp.ast.coord)

        p[0] = ast.CondDataMsg(p[2], p[4], p[5])


def p_tail_opt(p):
    '''
    tail_opt : LOR VID
             | empty
    '''
    if len(p) == 3:
        tmp = top.put(p[2].value,
            symtab.Entry(type=types.Variable(),#types.Record(labels={}, tails=[types.Variable()]), #types.Record(labels={p[2].value:types.Variable()}),
                         ast=p[2], ro=True))
        if tmp is not None:
            raise exn.DuplicatesError("'%s' was previously declared"
                % p[2].value, p[2].coord, tmp.ast.coord)

    p[0] = p[2] if len(p) == 3 else ast.TERM(None)


def p_cond_else(p):
    '''
    cond_else : ELSE
    '''
    p[0] = ast.CondElse()


def p_guard_opt(p):
    '''
    guard_opt : BAND int_exp
              | empty
    '''
    if p[1] == '':
        p[0] = ast.IntExp('True', [], {})

    else:
        p[0] = p[2]


def p_action_list(p):
    '''
    action_list : LBRACE set_stmt_opt send_stmt_opt goto_stmt_opt RBRACE
    '''
    p[0] = p[2] + p[3] + p[4]


def p_set_stmt_opt(p):
    '''
    set_stmt_opt : SET assign_list SCOLON
                 | empty
    '''
    p[0] = p[2] if len(p) == 4 else []


def p_assign_list(p):
    '''
    assign_list : assign
                | assign_list COMMA assign
    '''
    p[0] = [p[1]] if len(p) == 2 else p[1] + [p[3]]


def p_assign_int_exp(p):
    '''
    assign : VID ASSIGN int_exp
    '''
    tmp = top.put(p[1].value, symtab.Entry(type=types.Int(), ast=p[3]))
    p[0] = ast.Assign(p[1], p[3])


def p_assign_data_exp(p):
    '''
    assign : VID ASSIGN data_exp
    '''
    p[0] = ast.Assign(p[1], p[3])


def p_data_exp(p):
    '''
    data_exp : data
             | LPAREN data RPAREN
    '''
    data = p[1] if len(p) == 2 else p[2]
    p[0] = ast.DataExp(data)


def p_data(p):
    '''
    data : item
         | data LOR item
    '''
    p[0] = [p[1]] if len(p) == 2 else p[1] + [p[3]]


def p_item(p):
    '''
    item : THIS
         | VID
         | APOSTR VID
         | VID COLON rhs
    '''
    if len(p) == 2:
        if p[1] == 'this':
            p[0] = ast.ItemThis()
        else:
            p[0] = ast.ItemVar(p[1])

    elif len(p) == 3:
        p[0] = ast.ItemExpand(p[2])

    elif len(p) == 4:
        p[0] = ast.ItemPair(p[1], p[3])
    else:
        raise ValueError("Something Wrong!")


def p_rhs(p):
    '''
    rhs : VID
        | int_exp
    '''
    p[0] = p[1]


def p_send_stmt_opt(p):
    '''
    send_stmt_opt : SEND dispatch_list SCOLON
                  | empty
    '''
    p[0] = p[2] if len(p) == 4 else []


def p_dispatch_list(p):
    '''
    dispatch_list : dispatch
                  | dispatch_list COMMA dispatch
    '''
    p[0] = [p[1]] if len(p) == 2 else p[1] + [p[3]]


def p_dispatch(p):
    '''
    dispatch : msg_exp TO VID
    '''
    p[0] = ast.Send(p[1], p[3])


def p_msg_exp(p):
    '''
    msg_exp : AT int_exp
            | AT VID
            | data_msg
            | NIL
    '''
    if len(p) == 2:
        p[0] = ast.MsgNil() if p[1] == 'nil' else p[1]
    else:
        depth = p[2]
        p[0] = ast.MsgSegmark(depth)


def p_data_msg(p):
    '''
    data_msg : data_exp
             | QM VID data_exp
    '''
    if len(p) == 2:
        p[0] = ast.MsgData(None, p[1])
    else:
        p[0] = ast.MsgData(p[2], p[3])


def p_goto_stmt_opt(p):
    '''
    goto_stmt_opt : GOTO id_list SCOLON
                  | empty
    '''
    states = [n for n in p[2]] if len(p) == 4 else []
    p[0] = [ast.Goto(states)]


def p_empty(p):
    'empty :'
    p[0] = ''

###############################
# INTEXP

intexp_args = []
terms = {}
terms_cnt = 1


def p_int_exp(p):
    '''
    int_exp : LBRACKET intexp_raw RBRACKET
    '''
    global intexp_args, terms, terms_cnt

    p[0] = ast.IntExp(p[2], intexp_args, terms)

    # Cleanup globals
    intexp_args = []
    terms = {}
    terms_cnt = 0


def p_intexp_raw(p):
    '''
    intexp_raw : NUMBER
           | exp_term
           | LPAREN intexp_raw RPAREN
           | intexp_raw PLUS intexp_raw
           | intexp_raw MINUS intexp_raw
           | intexp_raw MULT intexp_raw
           | intexp_raw DIVIDE intexp_raw
           | intexp_raw MOD intexp_raw
           | intexp_raw SHL intexp_raw
           | intexp_raw SHR intexp_raw
           | intexp_raw BOR intexp_raw
           | intexp_raw BAND intexp_raw
           | intexp_raw BXOR intexp_raw
           | MINUS intexp_raw %prec UMINUS
           | intexp_raw LE intexp_raw
           | intexp_raw GE intexp_raw
           | intexp_raw EQ intexp_raw
           | intexp_raw NEQ intexp_raw
           | intexp_raw LEQ intexp_raw
           | intexp_raw GEQ intexp_raw
           | NOT intexp_raw
           | intexp_raw LAND intexp_raw
           | intexp_raw LOR intexp_raw
    '''
    global terms, terms_cnt

    if len(p) == 2:
        t = ('n%d' if type(p[1]) is int else 't%d') % terms_cnt
        terms_cnt += 1
        # Ugly hack. Need to make a separate rule for wrapping a number.
        terms[t] = ast.NUMBER(p[1]) if type(p[1]) is int else p[1]
        p[0] = '{%s}' % t

    else:
        if p[2] == '&&': p[2] = ' and '
        if p[2] == '||': p[2] = ' or '
        if p[1] == '!': p[1] = ' not '

        p[0] = ''.join(str(t) for t in list(p)[1:])


def p_exp_term(p):
    '''
    exp_term : VTERM
    '''
    global intexp_args
    intexp_args.append(p[1].value)
    p[0] = p[1]

###############################


def p_error(p):
    if p:
        raise exn.ParseError("Syntax error at '%s'"
                % p.value, coord.Coord(p.lineno, p.lexpos))
    else:
        raise exn.ParseError("Syntax error")


import ply.yacc as yacc
from . import lexer


def init():
    global intab, outtab, top, saved
    intab = symtab.Symtab(None)
    outtab = symtab.Symtab(None)
    top = symtab.Symtab(None)
    saved = top


def build():
    init()
    tokens = lexer.tokens
    tab_path = '/tmp/tmp-sync-tab'
    return yacc.yacc(start='sync', debug=0, tabmodule=tab_path)


import inspect
import sys


def linenumber_of_member(m):
    try:
        return m[1].__code__.co_firstlineno
    except AttributeError:
        return -1


def print_grammar():
    rules = []

    members = inspect.getmembers(sys.modules[__name__])
    members = sorted(members, key=linenumber_of_member)

    for name, obj in members:
        if inspect.isfunction(obj) and name[:2] == 'p_'\
                and obj.__doc__ is not None:
            rule = str(obj.__doc__).strip()
            rules.append(rule)

    print("\n\n".join(rules))
