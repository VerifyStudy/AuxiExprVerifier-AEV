#!/usr/bin/python3

import random
from pycparser import parse_file, c_ast, c_generator

# 作用 给部分语句补充大括号
# 1. 作用范围While, If 和 Switch(未完成)
# 2. 赋初值 （可能有问题）

# 结点必须是c_ast定义的AST结点
def recursiveTraversal(astNode : c_ast.FileAST):
    assert isinstance(astNode, c_ast.FileAST), '根节点类型需要FileAST'
    for _, ast in astNode.children():
        if isinstance(ast, c_ast.FuncDef):
            parseCompoundAst(ast.body)

def parseCompoundAst(compoundAst : c_ast.Compound):

    for _, ast in compoundAst.children():
        if isinstance(ast, c_ast.Decl):         # int x = 0;
            parseDeclAst(ast)
        elif isinstance(ast, c_ast.While):      # while
            parseWhileAst(ast)
        elif isinstance(ast, c_ast.For):        # For
            parseForAst(ast)
        elif isinstance(ast, c_ast.If):         # if
            parseIfAst(ast)
        elif isinstance(ast, c_ast.DoWhile):    # do-while
            parseDoWhile(ast)

# 声明语句赋初始值
def parseDeclAst(declAst : c_ast.Decl):
    if declAst.init is None:
        initConstant = c_ast.Constant(type="int", value="0")
        declAst.init = initConstant

# While
def parseWhileAst(whileAst : c_ast.While):
    whileBody = whileAst.stmt

    if isinstance(whileBody, c_ast.Compound):
        parseCompoundAst(whileBody)
    else:
        whileCompoundAst = c_ast.Compound(block_items = [whileBody])
        whileAst.stmt = whileCompoundAst

# For
def parseForAst(forAst : c_ast.For):
    forBody = forAst.stmt

    if isinstance(forBody, c_ast.Compound):
        parseCompoundAst(forBody)
    else:
        forCompoundAst = c_ast.Compound(block_items = [forBody])
        forAst.stmt = forCompoundAst

# If
def parseIfAst(ifAst : c_ast.If):
    ifTrue = ifAst.iftrue
    ifFalse = ifAst.iffalse
    
    if isinstance(ifTrue, c_ast.Compound):
        parseCompoundAst(ifTrue)
    else:
        ifTrueBody = c_ast.Compound(block_items=[ifTrue])
        ifAst.iftrue = ifTrueBody
        
    if ifFalse is None: return
    if isinstance(ifFalse, c_ast.Compound):
        parseCompoundAst(ifFalse)
    else:
        ifFalseBody = c_ast.Compound(block_items=[ifFalse])
        ifAst.iffalse = ifFalseBody

# Do While
def parseDoWhile(doWhileAst : c_ast.DoWhile):
    doBody = doWhileAst.stmt

    if isinstance(doBody, c_ast.Compound):
        parseCompoundAst(doBody)
    else:
        doCompoundAst = c_ast.Compound(block_items = [doBody])
        doWhileAst.stmt = doCompoundAst

def parse(filePath):
    ast = parse_file(filePath, use_cpp=True, cpp_args=['-E', r'-Ifake_libc_include'])
    return ast

def getRandomVar(prefix='__tmp__'):
    randomNumber = random.randint(0, 20)
    return prefix + str(randomNumber)

def PassCompleteBlock(parseFilePath) -> str:

    # 给While, If 和Switch 补充块结构
    # 给没有赋初值的变量添加初始状态
    '''
    :param parseFilePath: 提供文件的据对路径，不建议使用相对路径
    :return renderResult: 返回处理后的文本
    Org. if(*) x++;
    Pre. if(*) { x++; }
    '''
    
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