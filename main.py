#!/usr/bin/python3

from passModule.PassManager import PassManager

from passModule.PassPyParse import PassPyParse
from passModule.PassFuncRet import PassFuncRet
from passModule.PassWhileLoop import PassWhileLoop
from passModule.PassSimplyExpr import PassSimplyExpr
from passModule.PassCompleteBlock import PassCompleteBlock
from passModule.PassAuxiExpr import PassAuxiExpr


orgDir = "/home/liangle/verifier/CFG-dupath-of-C/"
preDir = "/home/liangle/verifier/CFG-dupath-of-C/tmp/"
tmpDir = "/home/liangle/verifier/CFG-dupath-of-C/tmp/"
file = "test.c"
PM = PassManager(orgDir, preDir, tmpDir, file)
PM.add(PassPyParse)
PM.add(PassCompleteBlock)
PM.add(PassWhileLoop)
PM.add(PassSimplyExpr)
# PM.add(PassFuncRet)
PM.add(PassAuxiExpr)
PM.run()