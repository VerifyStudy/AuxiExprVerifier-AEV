#!/usr/bin/python3

from PassManager import PassManager

from PassPyParse import PassPyParse
from PassFuncRet import PassFuncRet
from PassWhileLoop import PassWhileLoop
from PassSimplyExpr import PassSimplyExpr
from PassCompleteBlock import PassCompleteBlock

orgDir = "/home/liangle/verifier/AuxiExprVerifier-AEV/"
preDir = "/home/liangle/verifier/AuxiExprVerifier-AEV/tmp/"
tmpDir = "/home/liangle/verifier/AuxiExprVerifier-AEV/tmp/"
file = "test.c"
PM = PassManager(orgDir, preDir, tmpDir, file)
PM.add(PassPyParse)
PM.add(PassCompleteBlock)
PM.add(PassWhileLoop)
PM.add(PassSimplyExpr)
PM.add(PassFuncRet)
PM.run()
