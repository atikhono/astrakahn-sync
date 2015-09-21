The concepts of the new coordination language __AstraKahn__ are described in [[1]](http://arxiv.org/abs/1306.6029). The language defines the coordination behaviour of asynchronous stateless components (_boxes_) and their orderly interconnection via stream-carrying channels with finite capacity. __AstraKahn__ structures the interconnect using a fixed set of wiring primitives, viz. serial and parallel composition, wrap-around connection and serial replication. Boxes are connected to the network with one or two input channels and one or more output channels. A stateless box does not synchronise data on its input channels; to this end, __AstraKahn__ provides a synchronisation facility called _synchroniser_. Synchronisers are finite state machines for joining messages and sending them on to the output channels. A synchroniser is connected to the network with one or more input and output channels. __AstraKahn__ provides a dedicated language to define synchronisers. The grammar of the language is given in [[1]](http://arxiv.org/abs/1306.6029).

__This repository holds the up-to-date synchroniser compiler implementation.__


### Communication passport
An __AstraKahn__ component, either a box or a synchroniser, is both a consumer and a producer for some other components in the network. The static correctness of a connection demands that the statically guaranteed properties of an output message be sufficient to satisfy the static requirements of its recipients. In order to check the static correctness over the network, a component can be abstracted with respect to its data-transformation behaviour as a so-called communication passport _p ⇒ P_, where _p_ is the conjunction of all the requirements and _P_ is the conjunction of all the guarantees. Synchronisers are fully analysable by __AstraKahn__ and their passports can be extracted from the source code exclusively by program analysis. Such an analysis is implemented as a part of the synchroniser compiler.


## What is implemented so far
* Lexical analyser (with [PLY](http://www.dabeaz.com/ply/))
* Syntax analyser (with [PLY](http://www.dabeaz.com/ply/))
* Abstract syntax tree (using [cpyparser](https://github.com/eliben/pycparser) AST generatpr)
* Symbol tables and management
* Types and type checker
* Input/output passport extraction
* Tests (with unittest)

For the implementation details see Chapter 4 of [my thesis](https://github.com/atikhono/uhmt).


The tool is written in _python3_. It works in a bundle with the [__AstraKahn__ runtime](https://bitbucket.org/mkuznets/astrakahn-runtime) and also can run on its own (see sync_compiler.py):

```python
import sync

with open('path/to/sync/code', 'r') as f:
    src_code = f.read()

assert(sync.process(src_code))
```

To test the tool, run:
```bash
python3 sync/tests/tests.py
```
