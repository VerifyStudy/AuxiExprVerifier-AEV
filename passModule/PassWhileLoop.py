#!/usr/bin/python3

from pycparser import parse_file, c_ast, c_generator

# 作用 使用统一使用While作为循环表达
# 1. For 转化为 While
# 2. Do-While 转化为 While
# Note: 暂时不支持嵌套

# 结点必须是c_ast定义的AST结点
def recursiveTraversal(astNode : c_ast.FileAST):
    assert isinstance(astNode, c_ast.FileAST), '根节点类型需要FileAST'
    for _, ast in astNode.children():
        if isinstance(ast, c_ast.FuncDef):
            parseCompoundAst(ast.body)

def parseCompoundAst(compoundAst : c_ast.Compound):

    for _, ast in compoundAst.children():
        if isinstance(ast, c_ast.While):      # while
            assert isinstance(ast.stmt, c_ast.Compound)
            parseCompoundAst(ast.stmt)
        elif isinstance(ast, c_ast.If):         # if
            assert isinstance(ast.iftrue, c_ast.Compound)
            parseCompoundAst(ast.iftrue)
            if ast.iffalse is None: continue
            assert isinstance(ast.iffalse, c_ast.Compound)
            parseCompoundAst(ast.iffalse)
        elif isinstance(ast, c_ast.For):        # For
            insertAsts = parseForAst(ast)
            pasentAst = getattr(compoundAst, 'block_items')
            for __, _ast in compoundAst.children():
                if _ast == ast:
                    curIndex = int(__[12:-1])
                    del pasentAst[curIndex]
                    for insertAst in reversed(insertAsts):
                        pasentAst.insert(curIndex, insertAst)
        elif isinstance(ast, c_ast.DoWhile):
            insertAsts = parseDoWhileAst(ast)
            for __, _ast in compoundAst.children():
                if _ast == ast:
                    curIndex = int(__[12:-1])
                    del pasentAst[curIndex]
                    for insertAst in reversed(insertAsts):
                        pasentAst.insert(curIndex, insertAst)

# For
def parseForAst(forAst : c_ast.For):
    forBody = forAst.stmt

    if isinstance(forBody, c_ast.Compound):
        parseCompoundAst(forBody)
    else:
        forCompoundAst = c_ast.Compound(block_items = [forBody])
        forAst.stmt = forCompoundAst

    if forAst.next is not None:
        forAst.stmt.block_items.append(forAst.next)
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

# Do-While
def parseDoWhileAst(doAst : c_ast.DoWhile):
    doBody = doAst.stmt
    assert isinstance(doBody, c_ast.Compound)
    insertAst = doBody.block_items
    newWhile = c_ast.While(doAst.cond, doBody)
    return insertAst + [newWhile]

def parseDeclListAst(declListAst : c_ast.DeclList):
    return declListAst.decls

def parse(filePath):
    ast = parse_file(filePath, use_cpp=True, cpp_args=['-E', r'-Ifake_libc_include'])
    return ast

def PassWhileLoop(parseFilePath):

    # 使用统一使用While作为循环表达
    '''
    :param parseFilePath: 提供文件的据对路径，不建议使用相对路径
    :return renderResult: 返回处理后的文本
    Org. do{ x++; } while(x<0)
    Pre. x++; while(x<0){x++;}
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