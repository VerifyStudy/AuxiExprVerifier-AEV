#!/usr/bin/python3

import random
from pycparser import parse_file, c_ast, c_generator


# 作用 补充函数返回表达
# 只关注作为条件的部分，如 if(*), while(*), assert(* )
'''
    if (isExist()){...}
    tmp_0 = isExist();
    if (tmp_0){...}

    注意：因未构建完整函数调用图，所以无法获取函数返回类型，暂定使用int
'''

usedFuncRetVar = []

# 结点必须是c_ast定义的AST结点
def recursiveTraversal(astNode : c_ast.FileAST):
    assert isinstance(astNode, c_ast.FileAST), '根节点类型需要FileAST'
    for _, ast in astNode.children():
        if isinstance(ast, c_ast.FuncDef):
            parseCompoundAst(ast.body)

def parseCompoundAst(compoundAst : c_ast.Compound):
    for _, ast in compoundAst.children():
        if isinstance(ast, c_ast.UnaryOp):      # x++;
            pass
        elif isinstance(ast, c_ast.Assignment): # assignment
            insertAsts = parseAssignmentAst(ast)
            if len(insertAsts) == 0: continue
            pasentAst = getattr(compoundAst, 'block_items')
            for __, _ast in compoundAst.children():
                if _ast == ast:
                    curIndex = int(__[12:-1])
                    for insertAst in reversed(insertAsts):
                        pasentAst.insert(curIndex, insertAst)
        elif isinstance(ast, c_ast.For):        # For
            print("发现For结点，请使用LoopPass消除For结点")
        elif isinstance(ast, c_ast.Switch):     # switch
            print("发现Switch结点，请使用BrenchPass消除Switch结点")
        elif isinstance(ast, c_ast.While):      # while
            insertAsts = parseWhileAst(ast)
            if len(insertAsts) == 0: continue
            pasentAst = getattr(compoundAst, 'block_items')
            for __, _ast in compoundAst.children():
                if _ast == ast:
                    curIndex = int(__[12:-1])
                    for insertAst in reversed(insertAsts):
                        pasentAst.insert(curIndex, insertAst)
        elif isinstance(ast, c_ast.If):         # if
            insertAsts = parseIfAst(ast)
            if len(insertAsts) == 0: continue
            pasentAst = getattr(compoundAst, 'block_items')
            for __, _ast in compoundAst.children():
                if _ast == ast:
                    curIndex = int(__[12:-1])
                    for insertAst in reversed(insertAsts):
                        pasentAst.insert(curIndex, insertAst)
        elif isinstance(ast, c_ast.FuncCall):   # FuncCall
            insertAsts = parseFuncCallAst(ast)
            if len(insertAsts) == 0: continue
            pasentAst = getattr(compoundAst, 'block_items')
            for __, _ast in compoundAst.children():
                if _ast == ast:
                    curIndex = int(__[12:-1])
                    for insertAst in reversed(insertAsts):
                        pasentAst.insert(curIndex, insertAst)

# Assignment
# 只考虑了x = func() 情况
# 此外还有x = func() + 2 
def parseAssignmentAst(assignmentAst : c_ast.Assignment):
    insertAsts = []
    if isinstance(assignmentAst.rvalue, c_ast.FuncCall):    # 特殊
        tmpFuncRetVar = getRandomVar(assignmentAst.rvalue.name.name)
        localDecl = createDeclAst(["int"], tmpFuncRetVar, {"type":"int", "value":"0"}) # insertAst1
        insertAsts.append(localDecl)
        tmpVar = c_ast.ID(tmpFuncRetVar)
        newCond = c_ast.BinaryOp('!=', tmpVar, c_ast.Constant('int', '0'))          # insertAst2
        tmpFuncRetVar.cond = newCond
        tmpAst = c_ast.Assignment('=', tmpVar, tmpFuncRetVar)
        insertAsts.append(tmpAst)        
        return insertAsts
    return insertAsts

# While
def parseWhileAst(whileAst : c_ast.While):
    cond = whileAst.cond
    insertAsts = []
    if isinstance(cond, c_ast.FuncCall):
        tmpVarName = tmpVarName = getRandomVar(cond.name.name)
        localDecl = createDeclAst(["int"], tmpVarName, {"type":"int", "value":"0"}) # insertAst1
        insertAsts.append(localDecl)
        tmpVar = c_ast.ID(tmpVarName)
        newCond = c_ast.BinaryOp('!=', tmpVar, c_ast.Constant('int', '0'))          # insertAst2
        whileAst.cond = newCond
        tmpAst = c_ast.Assignment('=', tmpVar, cond)
        insertAsts.append(tmpAst)

    whileBody = whileAst.stmt

    if isinstance(whileBody, c_ast.Compound):
        parseCompoundAst(whileBody)
    
    return insertAsts

# If 可能会返回临时结点
def parseIfAst(ifAst : c_ast.If):
    cond = ifAst.cond
    insertAsts = []

    if isinstance(cond, c_ast.FuncCall):
        tmpVarName = getRandomVar(cond.name.name)
        localDecl = createDeclAst(["int"], tmpVarName, {"type":"int", "value":"0"}) # insertAst1
        insertAsts.append(localDecl)
        tmpVar = c_ast.ID(tmpVarName)
        newCond = c_ast.BinaryOp('!=', tmpVar, c_ast.Constant('int', '0'))          # insertAst2
        ifAst.cond = newCond
        tmpAst = c_ast.Assignment('=', tmpVar, cond)
        insertAsts.append(tmpAst)
    else:
        print('未考虑if(func()>0)情况')

    ifTrue = ifAst.iftrue
    ifFalse = ifAst.iffalse
    
    if isinstance(ifTrue, c_ast.Compound):
        parseCompoundAst(ifTrue)
    if ifFalse is None: return insertAsts
    if isinstance(ifFalse, c_ast.Compound):
        parseCompoundAst(ifFalse)
    return insertAsts

def parseFuncCallAst(funcCallAst : c_ast.FuncCall):
    insertAsts = []
    args = funcCallAst.args
    if len(args.exprs) != 1: return insertAsts # 只考虑一个参数的
    exprAst = args.exprs[0]
    if isinstance(exprAst, c_ast.FuncCall):
        tmpVarName = getRandomVar(exprAst.name.name)
        localDecl = createDeclAst(["int"], tmpVarName, {"type":"int", "value":"0"}) # insertAst1
        insertAsts.append(localDecl)
        tmpVar = c_ast.ID(tmpVarName)
        newCond = c_ast.BinaryOp('!=', tmpVar, c_ast.Constant('int', '0'))          # insertAst2
        args = [newCond]
        tmpAst = c_ast.Assignment('=', tmpVar, exprAst)
        insertAsts.append(tmpAst)
    pass
    return insertAsts


def getRandomVar(prefix = "auxi"):
    randomNumber = random.randint(0,9)
    varName = prefix + "__ret__" + str(randomNumber)
    if varName in usedFuncRetVar: return getRandomVar(prefix)
    else : 
        usedFuncRetVar.append(varName)
        return varName

def parse(filePath):
    ast = parse_file(filePath, use_cpp=True, cpp_args=['-E', r'-Ifake_libc_include'])
    return ast

# pType : ["unsigned", "int"] 声明类型，["char", "const"]
# pVarname : "z"    变量名字
# pConstant : {"type": int, "value": 0}     常数类型，int可能是由一个，如果是unsigned int类型会不是列表类型
def createDeclAst(pType : list, pVarName : str, pConstant) -> c_ast.Decl:
    pInit = c_ast.Constant(pConstant['type'], pConstant['value'])
    type = c_ast.IdentifierType(names=pType)
    varName = c_ast.TypeDecl(declname=pVarName, quals=[], type=type)
    declStatement = c_ast.Decl(name=pVarName, quals=[], storage=[], funcspec=[], type=varName, init=pInit, bitsize=None)
    return declStatement

def PassFuncRet(parseFilePath) -> str:
    # 补充函数返回值
    '''
    :param parseFilePath: 提供文件的据对路径，不建议使用相对路径
    :return renderResult: 返回处理后的文本
    Org. if(isExist()){...}
    Pre. isExist__0 = isExist();
        if(isExist__0 != 0){...}
    '''
    # 返回处理后的文本
    rootAst = parse(parseFilePath)
    recursiveTraversal(rootAst)
    cGenerator =  c_generator.CGenerator()
    renderResult = cGenerator.visit(rootAst)

    return renderResult


if __name__ == '__main__':

    parseFilePath = './test.c'
    rootAst = parse(parseFilePath)
    recursiveTraversal(rootAst)
    cGenerator =  c_generator.CGenerator()
    renderResult = cGenerator.visit(rootAst)
    print(renderResult)