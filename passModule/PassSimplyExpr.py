#!/usr/bin/python3

from pycparser import parse_file, c_ast, c_generator

# 作用 
# 前提：while都有大括号，+=已经被消除
# 预处理3，保存在tmp/filename文件夹下
# 1. 扩展自增符号
# 2. 集中单元声明位置

# 结点必须是c_ast定义的AST结点
def recursiveTraversal(astNode : c_ast.FileAST):
    assert isinstance(astNode, c_ast.FileAST), '根节点类型需要FileAST'
    for _, ast in astNode.children():
        if isinstance(ast, c_ast.FuncDef):
            parseCompoundAst(ast.body)

def parseCompoundAst(compoundAst : c_ast.Compound):

    for _, ast in compoundAst.children():
        if isinstance(ast, c_ast.UnaryOp):    # x++;
            replaceAst = parseUnaryOpAst(ast)
            pasentAst = getattr(compoundAst, 'block_items')
            for __, _ast in compoundAst.children():
                if _ast == ast:
                    curIndex = int(__[12:-1])
                    pasentAst[curIndex] = replaceAst
        elif isinstance(ast, c_ast.Assignment): # assignment
            parseAssignmentAst(ast)
        elif isinstance(ast, c_ast.While):      # while
            assert isinstance(ast.stmt, c_ast.Compound)
            parseCompoundAst(ast.stmt)
        elif isinstance(ast, c_ast.If):         # if
            assert isinstance(ast.iftrue, c_ast.Compound)
            parseCompoundAst(ast.iftrue)
            if ast.iffalse is None: continue
            assert isinstance(ast.iffalse, c_ast.Compound)
            parseCompoundAst(ast.iffalse)
        elif isinstance(ast, c_ast.For):        # For
           print("发现For结点，请使用PassWhileLoop消除后再次使用该通道")
        elif isinstance(ast, c_ast.Switch):     # switch
            print("发现Switch结点，请先使用PassIfBrench消除后再次使用该通道")


# x++; => x = x + 1;    
def parseUnaryOpAst(unaryAst : c_ast.UnaryOp):
    if unaryAst.op == 'p++' or unaryAst.op == '++':
        # x++ 表达式一定是ID
        assert isinstance(unaryAst.expr, c_ast.ID)
        return  c_ast.Assignment('=', 
                    unaryAst.expr, 
                    c_ast.BinaryOp('+', unaryAst.expr, c_ast.Constant('int', '1'))
                )
# x += 2; => x = x + 2;
def parseAssignmentAst(assignAst : c_ast.Assignment):
    op = assignAst.op
    if op in ['+=', '-=', '*=', '/=']:
        rvalue = assignAst.rvalue
        if isinstance(rvalue, c_ast.Constant):
            newBinaryOp = c_ast.BinaryOp(op[0], assignAst.lvalue, rvalue)
            assignAst.rvalue = newBinaryOp
            assignAst.op = '='
# For
def parseForAst(forAst : c_ast.For):
    forBody = forAst.stmt

    if isinstance(forBody, c_ast.Compound):
        parseCompoundAst(forBody)
    else:
        forCompoundAst = c_ast.Compound(block_items = [forBody])
        forAst.stmt = forCompoundAst
    if isinstance(forAst.next, c_ast.UnaryOp):
        replaceAst = parseUnaryOpAst(forAst.next)
        forAst.stmt.block_items.append(replaceAst)
    elif forAst is None:
        pass
    newWhile = c_ast.While(cond=forAst.cond, stmt=forAst.stmt)

    if isinstance(forAst.init, c_ast.DeclList):
        declList = parseDeclListAst(forAst.init)
        return declList + [newWhile]
    elif isinstance(forAst.init, c_ast.Assignment):
        return [forAst.init, newWhile]
    elif forAst.init is None:
        return [newWhile]

def parseDeclListAst(declListAst : c_ast.DeclList):
    return declListAst.decls

def parse(filePath):
    ast = parse_file(filePath, use_cpp=True, cpp_args=['-E', r'-Ifake_libc_include'])
    return ast

def PassSimplyExpr(parseFilePath):

    # 简化表达
    # 集中声明语句
    '''
    :param parseFilePath: 提供文件的据对路径，不建议使用相对路径
    :return renderResult: 返回处理后的文本
    Org. x++;
    Pre. x = x + 1;
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