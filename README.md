[![coverage report](https://gitlab.com/lisael/pydhall/badges/master/coverage.svg)](https://gitlab.com/lisael/pydhall/-/commits/master)

# Pydhall

Python Dhall implementation

## Project Goals

By priority

1. Standard compliant (v1.0)
2. Pythonic interface
   - `pydhall.[dump|load]s(src: str)` to mimic json an yaml libs)
   - (un)marshalling python objects, maybe using django models-like metaclasses
3. Time and space efficient

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
$ ## sha256 are compatible with dhall-haskell
$ dhall hash <<<('let _ = 2 in _') 
sha256:4caf97e8c445d4d4b5c5b992973e098ed4ae88a355915f5a59db640a589bc9cb
```

### Done

1. Global code design from parsing to SHA256 hash
2. Full parsing of the 15.0.0 grammar
3. Many terms are created out of the parsed expression
   - notably missing:
     - imports
     - lambdas
4. Some of those terms (3.) are type-checked
5. Some of those terms (4.) are evaluated
6. Some of those values (5.) are quoted
7. Some of those terms (4.) are CBOR-encoded and hashed (dhall-haskell compatible hashes)

### TODO

1. lambdas
2. import
3. cache
4. pythonic interface

## Installation - Development

The project is not fully packaged at the moment. For experimentations and
developements, use local package install in a virtualenv. Get in touch
with me opening an issue, or on [Dhall discourse](https://discourse.dhall-lang.org/)
if you need detailed instrucions.

TODO: instructions

## Related work

[dhall-python](https://github.com/SupraSummus/dhall-python): another pure python
dhall implementation.

## Credits

Shameless self-credit: the PEG parser is created using [fastidious](https://github.com/lisael/fastidious/),
a port of pigeon in python I coded a couple of years ago. The huge benefit of
fastidious is that it can create standalone parsers, without any runtime dependency, limiting
pydhall dependencies to cbor alone. (not implemented yet)

This is a port of [dhall-golang](https://github.com/philandstuff/dhall-golang),
with huge procedural -> OOP translation. The PEG parser is  almost a verbatim
copy of dhall-golang parser(or should be, as soon as fastidious is more pigeon-compatible)

This package was created with Cookiecutter and the `audreyr/cookiecutter-pypackage` project template.
