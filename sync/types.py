from string import digits, ascii_lowercase
from random import choice


class Term(object):
    def show(self): pass


class Number(Term):
    '''
    Represents term NUMBER.
    '''
    pass


class Int(Number):
    '''
    Represents the type of an integer variable.

    Attributes:
        size (int): the size of an integer; [0, 2^size-1] is the integer's value
        range.

    %size% defines the synchroniser state space. size=0 indicates that such
    variable is of integer type but it's not a state variable (expression alias,
    enum members).
    '''
    def __init__(self, s=0):
        self.size = s

    def show(self):
        return ("Int(%s)" % self.size)


class Enum(Number):
    '''
    Represents enum type of a state variable.

    Attributes:
        enum (dict): enum members' identifiers.
        size (int): number of elements in the %enum% dict.
    '''
    def __init__(self, e):
        self.enum = e
        self.size = len(e)

    def show(self):
        return "Enum(%s)" % self.enum


class Variable(Term):
    '''
    Represents term VARIABLE. Variable name is generated on instantiation.
    '''
    def __init__(self):
        self.label = '__var_' + ''.join(choice(digits + ascii_lowercase)
                for i in range(6))

    def show(self):
        return "$%s" % self.label


class Record(Term):
    '''
    Represents term RECORD.

    Attributes:
        labels (dict of str:<Term>): label-term pairs of the record.
        tails (list of <Variable>): records' tails (might be more than 1).
    '''
    def __init__(self, labels={}, tails=[]):
        self.labels = labels
        self.tails = tails

    def merge(self, other):
        '''
        Merge two records into one.

        { {a:Int, b:$v}, [$t] }.merge({ {a:$w}, [$z] })
            = { {a:Union(Int, $w), b:$v}, [$t, $z] } 
        '''
        assert(isinstance(other, Record))
        for l in other.labels:
            if l in self.labels:
                if self.labels[l] != other.labels[l]:
                    self.labels[l] = rep_union(self.labels[l], other.labels[l])
            else:
                self.labels[l] = other.labels[l]
        #FIXME add uniq check
        for t in other.tails:
            if t not in self.tails:
                self.tails.append(t)

    def update(self, other):
        assert(isinstance(other, Record))
        for l in other.labels:
            self.labels[l] = other.labels[l]

        for t in other.tails:
            if t not in self.tails:
                self.tails.append(t)

    def show(self):
        '''
        Pretty print records.

        { {a:$a}, [$z] }
            # printed as { 'a':$a | $z }
        { {a:$a}, [] }
            # printed as { 'a':$a }
        { {}, [$z] }
            # printed as $z
        { {}, [] }
            # printed as { }
        '''
        l_str = ''
        t_str = ''
        if self.labels:
            for l in self.labels:
                l_str += "'%s':%s, " % (l, self.labels[l].show())
            l_str = l_str[:-2]
            if not self.tails:
                return "{ %s }" % l_str

        if self.tails:
            for t in self.tails:
                t_str += " %s |" % t.show()
            t_str = t_str[:-2]
            if not self.labels:
                return "{%s }" % t_str
            else:
                return "{%s |%s }" % (l_str, t_str)

        return "{ }"


class Choice(Term):
    '''
    Represents term CHOICE.

    Attributes:
        variants (dict of str:<Record>): label-record pairs of the choice.
        tails (list of <Variable>): choices' tails (might be more than 1,
        in theory).
    '''
    def __init__(self, variants={}, tails=[]):
        for v in variants:
            assert(isinstance(variants[v], Record))
        self.variants = variants
        self.tails = tails

    def merge(self, other):
        '''
        Merge two choices in one, similar to Record.merge.
        '''
        assert(isinstance(other, Choice))

        for v in other.variants:
            if v in self.variants:
                self.variants[v].merge(other.variants[v])
            else:
                self.variants[v] = other.variants[v]

        for t in other.tails:
            if t not in self.tails:
                self.tails.append(t)


    def show(self):
        '''
        Pretty print choices, similar to Record.show.

        (: {a:{}}, [$z] :)
            # printed as (: 'a':{ } | $z :)
        (: {a:{}}, [] :)
            # printed as (: 'a':{ } :)
        (: {}, [$z] :)
            # printed as $z
        (: {}, [] :)
            # printed as (: :)
        '''
        v_str = ''
        t_str = ''
        if self.variants:
            for v in self.variants:
                v_str += "'%s':%s, " % (v, self.variants[v].show())
            v_str = v_str[:-2]
            if not self.tails:
                return "(: %s :)" % v_str

        if self.tails:
            for t in self.tails:
                t_str += "%s |" % t.show()
            t_str = t_str[:-2]
            if not self.variants:
                return "(: %s :)" % t_str
            else:
                return "(: %s | %s :)" % (v_str, t_str)

        return "(: :)"


class Union(object):
    '''
    Represents an OR of two label-value pairs with the same label.

    Attributes:
        val_[1|2] (<Term>): values to be put in the union.
    '''
    def __init__(self, val_1, val_2):
        self.val_1 = val_1
        self.val_2 = val_2

    def show(self):
        return "union(%s, %s)" % (self.val_1.show(), self.val_2.show())

def rep_union(r1, r2):
    if isinstance(r1, Variable) and not isinstance(r2, Variable):
        return r2
    if not isinstance(r1, Variable) and isinstance(r2, Variable):
        return r1
    if isinstance(r1, Variable) and isinstance(r2, Variable):
        return Union(r1, r2)
    if r1.__class__.__name__ != r2.__class__.__name__:
        raise TypeError
    return Union(r1, r2)
