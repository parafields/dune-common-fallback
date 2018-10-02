""" Generator module:

    The module provides the main class for on the fly generation of pybind11
    Python wrappers for implementations of a gives interface. The necessary
    details for each implementation (the C++ typedef and the includes) are
    provided by python dictonaries stored in files.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import logging

from . import builder

logger = logging.getLogger(__name__)

class SimpleGenerator(object):
    def __init__(self, typeName, namespace, pythonname=None, filename=None):
        if not (isinstance(typeName,list) or isinstance(typeName,tuple)):
            self.single = True
            typeName = [typeName]
        else:
            self.single = False
        self.typeName = typeName
        if namespace:
            self.namespace = namespace+"::"
        else:
            self.namespace = ""
        if pythonname is None:
          self.pythonName = typeName
        else:
          self.pythonName = pythonname
        self.fileName = filename

    def pre(self, includes, duneType, moduleName, defines=[], preamble=None):
        source = '#include <config.h>\n\n'
        source += '#define USING_DUNE_PYTHON 1\n\n'
        source += ''.join(["#define " + d + "\n" for d in defines])
        source += ''.join(["#include <" + i + ">\n" for i in includes])
        source += '\n'
        source += '#include <dune/python/common/typeregistry.hh>\n'
        source += '#include <dune/python/pybind11/pybind11.h>\n'
        source += '#include <dune/python/pybind11/stl.h>\n'
        source += '\n'

        if self.fileName is not None:
            with open(self.fileName, "r") as include:
                source += include.read()
            source += "\n"
        if preamble is not None:
            source += preamble
            source += "\n"

        if self.namespace == "":
            source += "void register" + self.typeName[0] + "( ... ) {}\n"
        source += "PYBIND11_MODULE( " + moduleName + ", module )\n"
        source += "{\n"
        return source

    def main(self, nr, includes, duneType, *args,
            options=[], bufferProtocol=False, dynamicAttr=False ):
        source = "  using pybind11::operator\"\"_a;\n"
        if not bufferProtocol: # kwargs.get("bufferProtocol", False):
            clsParams = []
        else:
            clsParams = ['pybind11::buffer_protocol()']
        if dynamicAttr:
            clsParams += ['pybind11::dynamic_attr()']

        if nr == 0:
            source += '  pybind11::module cls0 = module;\n'

        source += '  {\n'
        source += "    typedef " + duneType + " DuneType;\n"
        source += '    auto cls = Dune::Python::insertClass' +\
                       '< ' + duneType +\
                       ', '.join([""]+options) + ' >' +\
                       '( cls0, "' + self.typeName[nr] + '"' +\
                       ','.join(['']+clsParams) +\
                       ', Dune::Python::GenerateTypeName("' + duneType + '")' +\
                       ', Dune::Python::IncludeFiles{' + ','.join(['"' + i + '"' for i in includes]) + '}' +\
                       ").first;\n"
        source += "    " + self.namespace + "register" + self.typeName[nr] + "( cls0, cls );\n"

        for arg in args:
            if arg:
                source += "".join("    " + s + "\n" for s in str(arg).splitlines())
        source += '  }\n'
        return source

    def post(self, moduleName, source):
        source += "}\n"
        module = builder.load(moduleName, source, self.typeName[0])
        return module

    def load(self, includes, typeName, moduleName, *args,
            defines=[], preamble=None,
            options=[], bufferProtocol=False, dynamicAttr=False ):
        if self.single:
            typeName = (typeName,)
            options = (options,)
            bufferProtocol = (bufferProtocol,)
            dynamicAttr = (dynamicAttr,)
            args = (args,)
        else:
            if args == ():
                args=((),)*2
            else:
                args = args[0]
        if options == ():
            options = ((),)*len(typeName)
        if not bufferProtocol:
            bufferProtocol = (False,)*len(typeName)
        if not dynamicAttr:
            dynamicAttr = (False,)*len(typeName)
        source  = self.pre(includes, typeName[0], moduleName, defines, preamble)
        for nr, (tn, a, o, b, d)  in enumerate( zip(typeName, args, options, bufferProtocol, dynamicAttr) ):
            source += self.main(nr, includes, tn, *a, options=o, bufferProtocol=b, dynamicAttr=d)
        return self.post(moduleName, source)

from dune.common.hashit import hashIt
def simpleGenerator(inc, baseType, namespace, pythonname=None, filename=None):
    generator = SimpleGenerator(baseType, namespace, pythonname, filename)
    def load(includes, typeName, *args):
        includes = includes + inc
        moduleName = namespace + "_" + baseType + "_" + hashIt(typeName)
        return generator.load(includes, typeName, moduleName, *args)
    return load

from . import Method as Method_
from . import Constructor as Constructor_
from dune.deprecate import deprecated
@deprecated("import from dune.generator directly")
class Method(Method_):
    pass
@deprecated("import from dune.generator directly")
class Constructor(Constructor_):
    pass
