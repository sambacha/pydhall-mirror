[![coverage report](https://gitlab.com/lisael/pydhall/badges/master/coverage.svg)](https://gitlab.com/lisael/pydhall/-/commits/master)

# Pydhall

Python Dhall implementation

## Project Goals

By priority

1. Standard compliant
2. Pythonic interface
   - `pydhall.[dump|load]s(src: str)` to mimic json an yaml libs)
   - (un)marshalling python objects, maybe using django models-like metaclasses
3. Time and memory efficient

## WIP

At the moment it's more a proof of concept than a usable thing.

That said, here's a quick showcase:

```
$ pydhall normalize <<<('2')              
2
$ pydhall normalize <<<('let a = 2 in a')
2
$ pydhall normalize <<<('if True then 1 else 2')
1
$ pydhall normalize <<<('if True then 1 else True')
Error: ❰if❱ branches must have matching types
$ pydhall hash <<<('let a = 2 in a')   
sha256:4caf97e8c445d4d4b5c5b992973e098ed4ae88a355915f5a59db640a589bc9cb
$ pydhall hash <<<('let a = _ in _')   
sha256:4caf97e8c445d4d4b5c5b992973e098ed4ae88a355915f5a59db640a589bc9cb
$ ## sha256 are compatible with the specs
$ dhall hash <<<('let _ = 2 in _') 
sha256:4caf97e8c445d4d4b5c5b992973e098ed4ae88a355915f5a59db640a589bc9cb
```

### Done

1. Global code design from parsing to SHA256 hash
2. Parsing of the 16.0.0 grammar
   - Missing:
      - [ ] http imports
      - [ ] using
3. Terms are created out of the parsed expression
4. Type checking
5. Evaluation
6. Quote values
7. CBOR-encoding and hashing

Most of the standard tests pass, except [these](https://gitlab.com/lisael/pydhall/-/blob/master/pydhall/tests/spec/__init__.py).

Pydhall can import, normalize and hash the Prelude, except for one assert in `Text/show`
and a broken implementation of IntegerToDouble (and hence a broken sha256 for this
package).

### TODO

1. Binary decoding (WIP)
1. HTTP import
2. Content-addressable FS cache
3. Pythonic interface
4. Documentation

## Installation - Development

The project is not fully packaged at the moment. For experimentations and
developements, use local package install in a virtualenv. Get in touch
with me opening an issue, or on [Dhall discourse](https://discourse.dhall-lang.org/)
if you need detailed instrucions.

Quick start (for python devs):

In a Python 3.8 environment (should work with 3.7 and 3.9 but it's not tested yet):

```
git clone https://gitlab.com/lisael/pydhall.git
pip install -r requirements.txt
pip install -e .
```

Running the test

```
pip install -r requirements_dev.txt
git submodule update --init
make test
```

## Technical Overview

Pydhall is modeled on [dhall-golang](https://github.com/philandstuff/dhall-golang),
and as such, implements [normalization by evaluation](http://davidchristiansen.dk/tutorials/nbe/)
techniques.

It's rather slow (~15s to import `Prelude/JSON/renderAs`, my nemesis). It's
about 7 times slower than dhall-haskell. It tends to use less memory, though
(40Mo vs 70Mo importing the prelude). 

Mandatory disclaimer: don't trust random benchmarks from the internet, try it,
and see if it fits your needs.

The bright side is that albeit slow, Python allows fancy tricks such as [using
the parser to type builtin functions](https://gitlab.com/lisael/pydhall/-/blob/c57689700982b54d1f0eb2e39ef1b095e3a6fb53/pydhall/ast/list_/builtins.py#L16).
Adding a builtin is a simple as:

```python
class ListHead(Builtin):
    _literal_name = "List/head"
    _type = "∀(a : Type) → List a → Optional a"

    def __call__(self, type , x):
        if isinstance(x, EmptyListValue):
            return NoneOf(type)
        if isinstance(x, NonEmptyListValue):
            return SomeValue(x.content[0])
```

Behind the scene, a metaclass handles the boring work of translating the dhall type into
an internal value and of currying the applications.

Once the parser allows to re-define the builtins at runtime (WIP), it's easy for the
user to define custom builtins.
 
## Related work

[dhall-python](https://github.com/SupraSummus/dhall-python): another pure python
dhall implementation.

## License

Well, I'm refaining from applying AGPL on this work, but I'm not sure at the moment which
one to pick.
By sending a contribution to the project you allow me to license your work with any free
software license (i.e. somewhere between AGPL and WTFPL).

## Credits

Shameless self-credit: the PEG parser is created using [fastidious](https://github.com/lisael/fastidious/),
a port of pigeon in python I coded a couple of years ago. The huge benefit of
fastidious is that it can create standalone parsers, without any runtime dependency, limiting
pydhall dependencies to cbor alone. (not implemented yet)

This is a port of [dhall-golang](https://github.com/philandstuff/dhall-golang),
with huge procedural -> OOP translation. The PEG parser is  almost a verbatim
copy of dhall-golang parser(or should be, as soon as fastidious is more pigeon-compatible)

This package was created with Cookiecutter and the `audreyr/cookiecutter-pypackage` project template.
