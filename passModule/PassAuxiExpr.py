#! /usr/bin/python3
# coding=UTF-8 

import random
from pycparser import parse_file, c_ast, c_generator, c_parser
from graphviz import Digraph
from enum import Enum
import os

class NodeType(Enum):
    DeclNode = 0        # int x = 0;
    ConditionNode = 1   # (x == i)  废弃
    AssignmentNode = 2  # x = 1;
    ReturnNode = 3      # return 0;
    DummyNode = 4       # N*
    AssertNode = 5      # assert()
    LabelNode = 6       # Label: XX  废弃
    ErrorNode = 7       # 
    WhileHeadNode = 8   # while()
    IfHeadNode = 9      # if()

class EdgeType(Enum):
    NormalType = 0
    DummyType = 1

class AssertType(Enum):
    Rem = 0     # x % 2 == 0|1
    Exact = 8   # x / 2 == 0
    Equ = 1     # x == y
    Blt = 2     # x < 10
    Ble = 3     # x <= 10
    Bgt = 4     # x > 10
    Bge = 5     # x >= 10
    Nequ = 6    # x != 0
    Other = 7

class IntNumber(Enum):
    MinNumber = "-2147483648"
    MaxNumber = "2147483647"

class BigNumberType(Enum):
    BigEven = 1 # 大偶数
    BigOdd  = 2 # 大奇数

class Expression(object):
    def __init__(self, type) -> None:
        self.type = type
    
    # 表达式以文本显示
    def getCode(self) -> str:
        pass

    # 带有类型的文本
    def __str__(self) -> str:
        return self.getCode()
        # return "[type: " + self.type + "] {" + self.getCode() +"}"

# 变量类
class VariableExpression(Expression):
    def __init__(self, name : str) -> None:
        super().__init__("Var")
        self.name = name
    
    # 变量前后有一个空格
    def getCode(self) -> str:
        return " " + self.name +" "

# 常数类
class NumberExpression(Expression):
    def __init__(self, number : str) -> None:
        super().__init__("Number")
        self.number = number

    # 前后有一个空格
    def getCode(self) -> str:
        return " " + self.number + " "

class BinaryExpression(Expression):
    def __init__(self, lhs, rhs, op) -> None:
        super().__init__("Binary")
        self.lvalue = lhs
        self.rvalue = rhs
        self.op = op

    def getCode(self) -> str:
        return "(" + self.lvalue.getCode() + self.op + self.rvalue.getCode() + ")"

class LabelExpression(Expression):
    def __init__(self, name) -> None:
        super().__init__("Label")
        self.name = name
    
    def getCode(self) -> str:
        return 'Label :' + self.name.getCode()

class ReturnExpression(Expression):
    # ret 有多种可能
    # return 0; 或者 return a;
    # return callFunc 
    # 将来如果出现了这样的就添加虚拟dummy边和结点
    # 目前只处理常量和变量
    def __init__(self, var, pIsError = False) -> None:
        super().__init__("Return")
        self.var = var
        self.isError = pIsError

    def getCode(self) -> str:
        return "Return :" + self.var.getCode()

class SpecialExpression(Expression):
    def __init__(self, name) -> None:
        super().__init__("SPecial")
        self.name = name
    
    def getCode(self) -> str:
        return self.name

class UnaryExpression(Expression):
    def __init__(self, expr, unaryType) -> None:
        super().__init__("Unary")
        self.expr = expr
        self.unaryType = unaryType

    def getCpde(self) -> str:
        return self.unaryType + " " + self.expr.getCode()    

class CFANode(object):
    ID = 1
    def __init__(self, expr : Expression, pAst : c_ast.Node, pNodeType = NodeType.AssignmentNode) -> None:
        self.id = CFANode.ID
        # 虚拟结点的名字带有'*'号标记
        self.enteringEdges = []
        self.leavingEdges = []
        self.code = str(expr)
        self.expr = expr
        self.function = None
        self.nodeType = pNodeType
        self.name = "N" + str(self.id) + "*" if self.nodeType == NodeType.DummyNode else "N" + str(self.id)
        self.ast = pAst         # c_ast.Node() 指向ast结点
        CFANode.ID += 1
    
    def getCode(self, condtion = True) -> str:
        # 将普通结点视为条件真的结点
        # 对于循环头默认输出左边
        if condtion:
            return self.code
        else:
            return str(reverseExpr(self.expr))

    def __str__(self) -> str:
        return "[Node] " + self.name  + " " + self.getCode() + " " + self.nodeType.name

class AssertCFANode(CFANode):
    def __init__(self, expr: Expression, pAst: c_ast.Node, pNodeType=NodeType.AssignmentNode) -> None:
        super().__init__(expr, pAst, pNodeType=pNodeType)
        self.assertType = AssertType.Equ

class CFAEdge(object):
    ID = 1
    def __init__(self, predecessor=None, successor=None, condition=True, pEdgeType=EdgeType.NormalType) -> None:
        self.id = CFAEdge.ID
        self.predecessor = predecessor
        self.successor = successor
        self.edgeType = pEdgeType
        self.condition = condition
        self.expr = predecessor.expr if condition else reverseExpr(predecessor.expr)
        self.code = str(self.expr) 
        self.description = self.code
        CFAEdge.ID += 1

    def getCode(self) -> str:
        return self.code

    def __str__(self) -> str:
        prefix = "[Edge*] " if self.edgeType == EdgeType.DummyType else "[Edge] "
        return prefix + self.predecessor.name +" -{ " + self.getCode() + " }- " + self.successor.name

    def initDescription(self) -> str:
        suffix = " *" if self.edgeType == EdgeType.DummyType else " "
        self.description = self.code + suffix

class ARG(object):

    def __init__(self, name, pRootAst) -> None:
        self.nodes = []
        self.edges = []
        self.name = name
        self.dot = Digraph(self.name)
        self.rootAst = pRootAst
        self.removeNodeNumber = 0
        self.assertId = -1
        self.assertType = AssertType.Equ
        self.assertNode = None
        self.functions = {}

        self.endNode = CFANode(SpecialExpression("End"), self.rootAst, NodeType.DummyNode)
        self.nodes.append(self.endNode)

        # 一些预定义功能
        self.declNodes = None # 指向所有声明结点
        self.varDeclParentAst = None
        self.mainFuncAst = None
        self.vars = []
        self.numbers = []

    def showNodes(self):
        # 所有结点按照id排序
        self.nodes.sort(key=lambda node: node.id, reverse=False)
        # assert len(self.nodes) + 1 == CFANode.ID - self.removeNodeNumber, \
        #     '请检查是否存在未被添加到arg的结点'+str(len(self.nodes) +1 ) + " ? " + str(CFANode.ID - self.removeNodeNumber)
        print("######## ShowNodes Start ################")
        for node in self.nodes:
            print(node)
        print("######## ShowNodes End ##################\n")

    def showEdges(self):
        # 所有边按照id排序
        self.edges.sort(key=lambda node: node.predecessor.id, reverse=False)
        assert len(self.edges) == CFAEdge.ID, '请检查是否存在未被添加到arg的边'
        print("######## showEdges Start ################")
        for edge in self.edges:
            print(edge)
        print("######## showEdges End ##################\n")

    def showCFG(self):
        for node in self.nodes:
            self.dot.node(name=node.name, label=node.name)
        for edge in self.edges:
            self.dot.edge(edge.predecessor.name, edge.successor.name, edge.description)
        self.dot.render(os.path.join('tmp', self.name[:-2], self.name[:-2]), view=False)

    def insertFuncDeclAst(self, insertAst):
        self.rootAst.ext.insert(0, insertAst)

    # 断言结构统一转化为if(assertConditon){ret 1}
    # 其中 return 1 会被标记为Assert结点
    # 寻找带有条件的assert结点需要向上搜索
    def initAssertType(self):
        assert self.assertNode == None, '断言结点只允许调用一次'
        for node in self.nodes:
            if node.nodeType == NodeType.AssertNode:
                self.assertNode = node 
                break
                
        # if isinstance(self.assertNode.ast, c_ast.BinaryOp):
        #     pass
        # else:
        #     stack = [self.assertNode]
        #     findFlag = False
        #     while not findFlag:
        #         oneNode = stack.pop()
        #         edges = oneNode.enteringEdges
        #         for edge in edges:
        #             node = edge.predecessor
        #             if isinstance(node.expr, BinaryExpression):
        #                 self.assertNode = node
        #                 findFlag = True
        #             else:
        #                 stack.append(node)
        ops = extractOps(self.assertNode.expr)
        # if isinstance(self.assertNode.expr, BinaryExpression):
        #     expr = self.assertNode.expr
        #     if expr.op == "==":
        #         self.assertType = AssertType.Equ
        #         if hasattr(expr.lvalue, 'op') and expr.lvalue.op == "%":
        #             self.assertType = AssertType.Rem
        #     elif expr.op == "!=":
        #         self.assertType = AssertType.Nequ
        #         if hasattr(expr.lvalue, 'op') and expr.lvalue.op == "%":
        #             self.assertType = AssertType.Rem
            
        if "==" in ops  : self.assertType = AssertType.Equ
        if "<" in ops   : self.assertType = AssertType.Blt
        if "<=" in ops  : self.assertType = AssertType.Ble
        if ">" in ops   : self.assertType = AssertType.Bgt
        if ">=" in ops  : self.assertType = AssertType.Bge
            
        if "%" in ops or "&" in ops: self.assertType = AssertType.Rem
        if "/" in ops: self.assertType = AssertType.Exact

        print("Pass info: PassAuxiExpr find assert node ", self.assertNode.name, "type:", self.assertType.name, " ops:", ", ".join(ops))

    def initRelationInfo(self):
        for edge in self.edges:
            edge.predecessor.leavingEdges.append(edge)
            edge.successor.enteringEdges.append(edge)
        for node in self.nodes:
            if node.nodeType == NodeType.DummyNode:
                # for enterEdge in node.enteringEdges:
                #     enterEdge.edgeType = EdgeType.DummyType
                for leavingEdge in node.leavingEdges:
                    leavingEdge.edgeType = EdgeType.DummyType
        for edge in self.edges:
            edge.initDescription()

    def initVarsInfo(self):
        assert len(self.vars) == 0, "不要重复初始化变量"
        result = []
        for node in self.nodes:
            if node.nodeType == NodeType.DeclNode:
                result += getVars(node.expr)
        self.vars = set(result)

    def initMainFuncAstInfo(self):
        assert self.mainFuncAst is None, '不要重复初始化mainAst信息'
        for _ext in self.rootAst.ext:
            if isinstance(_ext, c_ast.FuncDef) and _ext.decl.name == "main":
                self.mainFuncAst = _ext
                return

    def initVarDeclAstInfo(self):
        assert self.varDeclParentAst is None, '不能重复初始化声明信息'
        assert self.mainFuncAst is not None, '需要调用initMainFuncAstInfo()'
        self.varDeclParentAst = self.mainFuncAst

    # 与自定义的程序尾结点链接
    def addEndEdge(self, node : CFANode):
        edge = CFAEdge(node, self.endNode)
        self.edges.append(edge)
        
    def injectVarDeclAst(self, declAst : c_ast.Decl):
        cur = -1
        for index, ast in enumerate(self.varDeclParentAst.body.block_items):
            if isinstance(ast, c_ast.Decl):
                cur = index
        assert cur != -1, 'main函数中没有找到声明语句'
        self.varDeclParentAst.body.block_items.insert(cur + 1, declAst)

    # 返回声明结点集合
    def getDeclNodes(self) -> list:
        if self.declNodes is None:
            self.declNodes= []
            for node in self.nodes:
                if node.nodeType == NodeType.DeclNode:
                    self.declNodes.append(node)
            return self.declNodes
        else:
            return self.declNodes

    # 沿着CFG，从pNode向上找一个循环头
    # 找不到 返回None
    def findOneWhileNode(self, pNode : CFANode) -> CFANode:
        stack = pNode.enteringEdges
        while len(stack) > 0:
            edge = stack.pop()
            node = edge.predecessor
            if node.nodeType == NodeType.WhileHeadNode:
                return node
            else:
                stack += node.enteringEdges
        return None

    def getWhileBodyNodes(self, node):
        assert node.nodeType == NodeType.WhileHeadNode
        head = node
        whileBodyNodes = []
        stack = [edge for edge in node.leavingEdges if edge.condition == False]
        while len(stack) > 0:
            edge = stack.pop()
            succ = edge.successor
            if succ != head:
                whileBodyNodes.append(succ)
                stack += succ.leavingEdges
            else:
                pass
        return whileBodyNodes

    def getWhileBodyAssignmentNodes(self, node : CFANode) -> list:
        assert node.nodeType == NodeType.WhileHeadNode
        head = node
        whileBodyAssignmentNodes = []
        stack = [edge for edge in node.leavingEdges if edge.condition == True]
        while len(stack) > 0:
            edge = stack.pop()
            succ = edge.successor
            if succ != head:
                if succ.nodeType == NodeType.AssignmentNode:
                    whileBodyAssignmentNodes.append(succ)
                stack += succ.leavingEdges
            else:
                pass
        return whileBodyAssignmentNodes

    def getAssignmentNodes(self, compoundNode):

        for node in self.nodes:
            pass
        pass

    def getRandomVar(self, prefix = "auxi"):
        randomNumber = random.randint(0,9)
        varName = prefix + str(randomNumber)
        if varName in self.vars : return self.getRandomVar()
        else: return varName

    def clearCache(self):
        self.nodes = []
        self.edges = []
        CFANode.ID = 0
        CFAEdge.ID = 0
        self.removeNodeNumber = -1
        self.dot = Digraph(self.name)
        self.endNode = CFANode(SpecialExpression("End"), self.rootAst, NodeType.DummyNode)
        self.nodes.append(self.endNode)
        self.vars = []
        self.numbers = []
arg = None

# 结点必须是c_ast定义的AST结点
def recursiveTraversal(astNode : c_ast.FileAST):
    assert isinstance(astNode, c_ast.FileAST), '根节点类型需要FileAST'
    for _, ast in astNode.children():
        if isinstance(ast, c_ast.FuncDef) and ast.decl.name == "main":
            recursiveTraversalFunction(ast)
        elif isinstance(ast, c_ast.Decl):
            pass

def recursiveTraversalFunction(funcDef : c_ast.FuncDecl):
    funcDecl = funcDef.decl.name
    funcBody = funcDef.body
    
    functionHead = CFANode(SpecialExpression(funcDecl), funcDef, NodeType.DummyNode)
    arg.nodes.append(functionHead)
    
    compoundHead, compoundEnds = recursiveTraversalCompound(funcBody, "Function")
    headEdge = CFAEdge(functionHead, compoundHead)
    arg.edges.append(headEdge)
    for node in compoundEnds:
        edge = CFAEdge(node, functionHead)
        arg.edges.append(edge)

def recursiveTraversalCompound(compoundAst : c_ast.Compound, name : str):
    NodeQueue = []
    compoundHead = CFANode(SpecialExpression(name + " Compound Start"), compoundAst, NodeType.DummyNode)
    NodeQueue.append([compoundHead])
    
    for _, ast in compoundAst.children():
        if isinstance(ast, c_ast.Decl):         # int x = 0;
            expr = parseDeclAst(ast)
            declNode = buildDeclNode(expr, ast)
            NodeQueue.append([declNode])
        elif isinstance(ast, c_ast.UnaryOp):    # x++;
            expr = parseUnaryAst(ast)
            unaryNode = buildAssignmentNode(expr, ast)
            NodeQueue.append([unaryNode])
        elif isinstance(ast, c_ast.Assignment): # assignment
            expr = parseAssignmentAst(ast)
            assignNode = buildAssignmentNode(expr, ast)
            NodeQueue.append([assignNode])
        elif isinstance(ast, c_ast.While):      # while
            whileHead = parseWhileStatement(ast)
            # whileHead.expr = reverseExpr(whileHead.expr)
            NodeQueue.append([whileHead])
        elif isinstance(ast, c_ast.FuncCall):   # function call
            # funcHead, funcEnd = parseFuncCallAst(ast)
            funcNode = parseFuncCallAst(ast)
            NodeQueue.append([funcNode])
            # buildQueueTrans(NodeQueue)
            # NodeQueue.pop()
            # NodeQueue.append([funcEnd])
        elif isinstance(ast, c_ast.If):         # if
            ifHeadNode, ifTrueEnd, ifFalseEnd = parseIfStatement(ast)
            NodeQueue.append([ifHeadNode])
            buildQueueTrans(NodeQueue)
            NodeQueue.pop()     # 弹出ifHead
            NodeQueue.append(ifFalseEnd + ifTrueEnd)
        elif isinstance(ast, c_ast.Label):      # label[ERROR:]
            expr = parseLabelAst(ast)
            rerNode = buildReturnNode(expr, ast) # * 看成return 情况
            NodeQueue.append([rerNode])
            buildQueueTrans(NodeQueue)
            arg.addEndEdge(rerNode)
            return compoundHead, []
        elif isinstance(ast, c_ast.Return):     # return
            expr = parseReturnAst(ast)
            retNode = buildReturnNode(expr, ast)
            NodeQueue.append([retNode])
            buildQueueTrans(NodeQueue)
            arg.addEndEdge(retNode)
            return compoundHead, []

            

    compoundEnd = CFANode(SpecialExpression(name + " Compound End"), compoundAst, NodeType.DummyNode)
    NodeQueue.append([compoundEnd])

    assert len(NodeQueue) > 1   # 一定有一个Start结点或者IfEnds结点+CompoundEnd结点
    buildQueueTrans(NodeQueue)

    assert len(NodeQueue) == 1, '最后剩下一个虚拟尾结点'
    # if compoundEnd is not None: arg.nodes.append(compoundEnd)  # 只需要添加尾部虚拟结点
    # else: arg.removeNodeNumber += 1
    return compoundHead, NodeQueue.pop()    # 使用pop弹出最后一个元素，释放资源

# queue中所有结点都被记录，所有边都被记录，所有点都被记录
# len(queue) > 0 最后queue会剩一个
def buildQueueTrans(queue : list) -> None:
    while len(queue) > 1:
        startNodes = queue.pop(0)
        for startNode in startNodes:
            if not startNode in arg.nodes: arg.nodes.append(startNode)
            
            for endNode in queue[0]:
                if startNode.nodeType == NodeType.WhileHeadNode or startNode.nodeType == NodeType.AssertNode:
                    edge = CFAEdge(startNode, endNode, False)
                else:
                    edge = CFAEdge(startNode, endNode)
                arg.edges.append(edge)
    for node in queue[0]:
        arg.nodes.append(node)

def buildAssertNode(assertCallAst : c_ast.FuncCall):
    args = assertCallAst.args
    assert isinstance(args, c_ast.ExprList)
    exprList = []
    for expr in args.exprs:
        if isinstance(expr, c_ast.UnaryOp):
            exprList.append(parseUnaryAst(expr))
        if isinstance(expr, c_ast.BinaryOp):
            exprList.append(parseBinaryAst(expr))
    assertNode = CFANode(exprList[0], assertCallAst.args, NodeType.AssertNode)
    # arg.nodes.append(assertNode)

    ret = CFANode(
        ReturnExpression(NumberExpression("1"), True),
        assertCallAst.args, NodeType.DummyNode)
    arg.nodes.append(ret)
    edge = CFAEdge(assertNode, ret, True, EdgeType.DummyType)
    arg.edges.append(edge)
    arg.addEndEdge(ret)
    
    return assertNode

# function call
def parseFuncCallAst(funcCallAst : c_ast.FuncCall):
    retValue = None
    if funcCallAst.name.name =='__VERIFIER_nondet_int':
        retValue = VariableExpression("__VERIFIER_nondet_int")
    elif funcCallAst.name.name =='__VERIFIER_nondet_uint':
        retValue = VariableExpression("__VERIFIER_nondet_uint")
    elif funcCallAst.name.name =='__VERIFIER_nondet_uchar':
        retValue = VariableExpression("__VERIFIER_nondet_uchar")
    elif funcCallAst.name.name =='__VERIFIER_assert':
        retValue = buildAssertNode(funcCallAst)
    # assert retValue != None, '存在未被解析结点'
    return retValue

# while
def parseWhileStatement(whileAst : c_ast.While):
    whileHead = None
    whileCond = whileAst.cond
    whileBody = whileAst.stmt
    expr = None

    if isinstance(whileCond, c_ast.BinaryOp):
        expr = parseBinaryAst(whileCond)
    elif isinstance(whileCond, c_ast.ID):           # while(x)
        expr = BinaryExpression(parseIdAst(whileCond), NumberExpression("0"), "!=")
    elif isinstance(whileCond, c_ast.UnaryOp):
        expr = parseUnaryAst(whileCond)
    elif isinstance(whileCond, c_ast.FuncCall):
        retValue = parseFuncCallAst(whileCond)
        expr = BinaryExpression(retValue, NumberExpression("0"), "!=")

    assert expr is not None, 'expr 表达式为空，可能存在未识别的ast结点'
    whileHead = buildConditionNode(expr, whileAst, NodeType.WhileHeadNode)

    assert isinstance(whileBody, c_ast.Compound), 'while体一定有大括号'
    try:
        compoundHead, compoundEnds = recursiveTraversalCompound(whileBody, "While")
        # whileHead - whileBodyHead
        headEdge = CFAEdge(whileHead, compoundHead)
        arg.edges.append(headEdge)

        #whileBodyEdns - whileHead
        for node in compoundEnds:
            edge = CFAEdge(node, whileHead, True)
            arg.edges.append(edge)
        return whileHead
    except Exception as e:
        print("Exception on parseWhileStatement[WhileBody part]")
        print(e)

# if
def parseIfStatement(ifAst : c_ast.If):
    ifCond = ifAst.cond
    ifTrue = ifAst.iftrue
    ifFalse = ifAst.iffalse
    ifHead = None
    trueEnd = None
    falseEnd = None

    if isinstance(ifCond, c_ast.BinaryOp):
        expr = parseBinaryAst(ifCond)
    elif isinstance(ifCond, c_ast.ID):          # if(x)
        expr = BinaryExpression(parseIdAst(ifCond), NumberExpression("0"), "!=")
    elif isinstance(ifCond, c_ast.UnaryOp):
        expr = parseUnaryAst(ifCond)
    elif isinstance(ifCond, c_ast.FuncCall):
        retValue = parseFuncCallAst(ifCond)
        expr = BinaryExpression(retValue, NumberExpression("0"), "!=")

    assert expr is not None, 'expr 表达式为空，可能存在未识别的ast结点'
    ifHead = buildConditionNode(expr, ifCond, NodeType.IfHeadNode)

    assert isinstance(ifTrue, c_ast.Compound)
    try:
        trueHead, trueEnd = recursiveTraversalCompound(ifTrue, "IfTrue")
    except Exception as e:
        print("Exception on parseIfStatement[True part]")
        print(e)
    edge = CFAEdge(ifHead, trueHead)
    arg.edges.append(edge)
      

    if isinstance(ifFalse, c_ast.Compound):
        try:
            falseHead, falseEnd = recursiveTraversalCompound(ifFalse, "IfFalse")
        except:
            print("Exception on parseIfStatement[False part]")
            print(e)
        edge = CFAEdge(ifHead, falseHead)
        arg.edges.append(edge)
    else:
        dummyNode = CFANode(reverseExpr(ifHead.expr), ifHead, NodeType.DummyNode)
        arg.nodes.append(dummyNode)
        edge = CFAEdge(ifHead, dummyNode, False, EdgeType.DummyType)
        arg.edges.append(edge)
        falseEnd = [dummyNode]

    return ifHead, trueEnd, falseEnd

# Return BinaryExpression
def parseDeclAst(declAst : c_ast.Decl) -> BinaryExpression:
    # unsigned int x = 0;
    # Decl.name 变量名字
    # Decl.init(Constant) 初始常数类型
    # Constant{"type":"int","value":"0"}
    # Decl.type(TypeDecl) 声明类型
    # TypeDecl("declname":"x","type.names","unsigned int")
    lvalue = VariableExpression(declAst.name)
    if isinstance(declAst.init, c_ast.ID): rvalue = parseIdAst(declAst.init)
    if isinstance(declAst.init, c_ast.Constant): rvalue = parseConstantAst(declAst.init)
    if isinstance(declAst.init, c_ast.BinaryOp): rvalue = parseBinaryAst(declAst.init)
    if isinstance(declAst.init, c_ast.FuncCall): rvalue = parseFuncCallAst(declAst.init)
    declExp = BinaryExpression(lvalue, rvalue, "=")
    return declExp

# Return DeclNode
def buildDeclNode(expr : BinaryExpression, declAst : c_ast.Decl) -> CFANode:
    assert isinstance(expr, BinaryExpression), '构建声明结点的表达式应该是赋值语句'
    return CFANode(expr, declAst, NodeType.DeclNode)

# Return ConditionNode
def buildConditionNode(expr : BinaryExpression, condAst : c_ast.Node, nodeType = NodeType.WhileHeadNode) -> CFANode:
    assert isinstance(expr, BinaryExpression), '构建条件结点的表达式应该是条件语句'
    return CFANode(expr, condAst, nodeType)

# Return AssignmentNode
def buildAssignmentNode(expr : BinaryExpression, assignAst : c_ast.Node) -> CFANode:
    assert isinstance(expr, BinaryExpression)
    return CFANode(expr, assignAst, NodeType.AssignmentNode)

# Return ReturnNode
def buildReturnNode(expr : ReturnExpression, retAst : c_ast.Return) -> CFANode:
    assert isinstance(expr, ReturnExpression)
    return CFANode(expr, retAst, NodeType.ReturnNode)

# Return BinaryExpression
def parseBinaryAstWithoutConvert(binaryAst: c_ast.BinaryOp) -> BinaryExpression:
    lvalue = binaryAst.left
    rvalue = binaryAst.right
    op = binaryAst.op
    if isinstance(lvalue, c_ast.BinaryOp):  lhs = parseBinaryAst(lvalue)
    if isinstance(lvalue, c_ast.ID):        lhs = parseIdAst(lvalue)
    if isinstance(lvalue, c_ast.Constant):  lhs = parseConstantAst(lvalue)

    if isinstance(rvalue, c_ast.BinaryOp):  rhs = parseBinaryAst(rvalue)
    if isinstance(rvalue, c_ast.ID):        rhs = parseIdAst(rvalue)
    if isinstance(rvalue, c_ast.Constant):  rhs = parseConstantAst(rvalue)
    expr = BinaryExpression(lhs, rhs, op)
    return expr

# Return BinaryExpression
# x % 2 => (x % 2) != 0 废弃，因为(x & 2) == 3 会变成 ((x & 2) == 0) ==3
# 原格式返回
def parseBinaryAst(binaryAst: c_ast.BinaryOp) -> BinaryExpression:
    lvalue = binaryAst.left
    rvalue = binaryAst.right
    op = binaryAst.op

    if isinstance(lvalue, c_ast.BinaryOp):  lhs = parseBinaryAst(lvalue)
    if isinstance(lvalue, c_ast.ID):        lhs = parseIdAst(lvalue)
    if isinstance(lvalue, c_ast.Constant):  lhs = parseConstantAst(lvalue)

    if isinstance(rvalue, c_ast.BinaryOp):  rhs = parseBinaryAst(rvalue)
    if isinstance(rvalue, c_ast.ID):        rhs = parseIdAst(rvalue)
    if isinstance(rvalue, c_ast.Constant):  rhs = parseConstantAst(rvalue)

    if op in ["=", "==", "!=", "<", "<=", ">", ">=", "%", "&", "/", "+", "-", "*", "&&", "||"]:
        expr = BinaryExpression(lhs, rhs, op)
        return expr
    raise 'expr 为空，二元表达式解析错误'
    # if op in ["&&", "&", "||", "|"]:
    #     expr1 = BinaryExpression(lhs, rhs, op)
    #     expr2 = BinaryExpression(expr1, NumberExpression("0"), "!=")
    #     return expr2

    # return CFANode(expr, condition, NodeType.ConditionNode)

# Return BinaryExpression
def parseUnaryAst(unaryAst : c_ast.UnaryOp) -> BinaryExpression:
    operator = unaryAst.op
    if operator == "!":
        if isinstance(unaryAst.expr, c_ast.BinaryOp):
            expr = parseBinaryAst(unaryAst.expr)
            return BinaryExpression(expr, NumberExpression("0"), "!=")
        elif isinstance(unaryAst.expr, c_ast.ID):
            return BinaryExpression(VariableExpression(unaryAst.expr.name), NumberExpression("0"), "!=")
    elif operator == "p++":
        lhs = unaryAst.expr.name
        lhsVarExpr1 = VariableExpression(lhs)
        lhsVarExpr2 = VariableExpression(lhs)
        oneVarExpr = NumberExpression("1")
        op = unaryAst.op[1]
        expr = BinaryExpression(lhsVarExpr1, BinaryExpression(lhsVarExpr2, oneVarExpr, op), "=")
        # return CFANode(expr, unaryOp, NodeType.AssignmentNode)
        return expr

# Return BinaryExpression
def parseAssignmentAst(assignAst : c_ast.Assignment) -> BinaryExpression:
    op = assignAst.op
    lvalue = assignAst.lvalue
    rvalue = assignAst.rvalue
    assert isinstance(lvalue, c_ast.ID), '赋值语句左边似乎只能是变量'
    
    if isinstance(lvalue, c_ast.ID) :       lhs = parseIdAst(lvalue)
    
    if isinstance(rvalue, c_ast.ID) :       rhs = parseIdAst(rvalue)
    if isinstance(rvalue, c_ast.Constant):  rhs = parseConstantAst(rvalue)
    if isinstance(rvalue, c_ast.BinaryOp) : rhs = parseBinaryAstWithoutConvert(rvalue)
    if isinstance(rvalue, c_ast.FuncCall):  rhs = parseFuncCallAst(rvalue)    
    # TODO 赋值右边还可能有别的形式


    if op in ["-=", "+=", "*=", "/="]:
        return BinaryExpression(
            lhs,
            BinaryExpression(lhs, rhs, op[0]),
            "="
        )

    elif op == "=":
        return BinaryExpression(lhs, rhs, "=")

# Return VariableExpression
def parseIdAst(idAst : c_ast.ID) -> VariableExpression:
    return VariableExpression(idAst.name)

# Return NumberExpression
def parseConstantAst(constantAst : c_ast.Constant) -> VariableExpression:
    return NumberExpression(constantAst.value)

# Return ReturnExpression 我们暂时把Label看成特殊的Return
def parseLabelAst(label : c_ast.Label) -> ReturnExpression:
    labelName = label.name
    # lVarExpr = VariableExpression(labelName)
    if labelName == "ERROR":
        labelTo = label.stmt
        assert isinstance(labelTo, c_ast.Return), '暂时只考虑 ERROR : return XXX; 这样的语句'
        expr = parseReturnAst(labelTo)
        expr.isError = True
        return expr
    #     ReturnExpression()
    #     labelNode = CFANode(LabelExpression(lVarExpr), label, NodeType.ErrorNode)
    # else:
    #     labelNode = CFANode(LabelExpression(lVarExpr), label, NodeType.LabelNode)

    # labelTo = label.stmt
    # if isinstance(labelTo, c_ast.Return):
    #     retNode = parseReturnStatement(labelTo)
    #     arg.nodes.append(retNode)
    #     edge = CFAEdge(labelNode, retNode)
    #     arg.edges.append(edge)
    #     arg.addEndEdge(retNode)
    # return labelNode

def parseReturnAst(returnAst : c_ast.Return) -> ReturnExpression:
    returnExpr = returnAst.expr
    if isinstance(returnExpr, c_ast.Constant):
        rVarExpr = VariableExpression(returnExpr.value)
        # returnNode = CFANode(ReturnExpression(rVarExpr), returnAst, NodeType.ReturnNode)
        return ReturnExpression(rVarExpr)
    elif isinstance(returnExpr, c_ast.BinaryOp):
        binaryExpr = parseBinaryAst(returnExpr)
        return ReturnExpression(binaryExpr)
    else:
        raise 'return 类型为解析'

def reverseExpr(expr : BinaryExpression) -> Expression:
    reverseDict = {'>': '<=', '>=': '<',
            '<': '>=', '<=': '>',
            '==': '!=', '!=': '=='}
    if expr.op in reverseDict.keys():
        reverseOp = reverseDict[expr.op]
        return BinaryExpression(expr.lvalue, expr.rvalue, reverseOp)
    if expr.op in ['%', '/', '+', '-', '*']:
        return BinaryExpression(expr, NumberExpression('0'), '!=')

# IdentifierType[int] TypeDecl[x] = Constant[0]
# pType : ["unsigned", "int"] 声明类型
# pVarname : "z"
# pConstant : {"type": int, "value": 0} 常数类型
# int z = 0;
def createDeclAst(pType : list, pVarName : str, pInit) -> c_ast.Decl:
    type = c_ast.IdentifierType(names=pType)
    varName = c_ast.TypeDecl(declname=pVarName, quals=[], type=type)
    declStatement = c_ast.Decl(name=pVarName, quals=[], storage=[], funcspec=[], type=varName, init=pInit, bitsize=None)
    # decl.show()
    return declStatement

# 创建辅助结点
# y = k*x + b
def createAuxiAst(y, k, x, op, b) -> c_ast.Assignment:
    k_x = c_ast.BinaryOp("*", k, x)
    k_x_op_b = c_ast.BinaryOp(op, k_x, b)
    assignment = c_ast.Assignment("=", y, k_x_op_b)
    return assignment

# 创建__VERIFIER_assume定义
# void __VERIFIER_assume(int expression) { 
#   if (!expression) { 
#     LOOP: goto LOOP; }
#     return; 
# }
def createAssumtDeclAst() -> c_ast.Decl:
    code = """
            void __VERIFIER_assume(int expression) { \
                if (!expression) { \
                    LOOP: goto LOOP; \
                } \
                return; \
            }"""
    tmpParser = c_parser.CParser()
    assumtAst = tmpParser.parse(code)
    del tmpParser
    return assumtAst.ext[0] # 根节点是FileAst 只有一个子节点

# 创建随机值函数声明
# extern int __VERIFIER_nondet_XXXX();
# XXX 类型 {int, uint, char}
def createNondetDeclAst(type : str):
    code = "extern int __VERIFIER_nondet_" + type + "();"
    tmpParser = c_parser.CParser()
    assumtAst = tmpParser.parse(code)
    del tmpParser
    return assumtAst.ext[0] # 根节点是FileAst 只有一个子节点

# 断言计数，断言偶数
# type = {"odd":1, "even":2} 注意，字符串形式
# eg. odd => (var % 1)
def assumeNumberTypeAst(var, type):
    # code = "__VERIFIER_assume(" + var + " % " + type +");"
    # print(code)
    # tmpParser = c_parser.CParser()
    # assumtAst = tmpParser.parse(code)
    # del tmpParser
    # return assumtAst.ext[0] # 根节点是FileAst 只有一个子节点
    if type == "odd":
        return c_ast.FuncCall(name=c_ast.ID("__VERIFIER_assume"),
                args=c_ast.ExprList([c_ast.BinaryOp("%", c_ast.ID(var), c_ast.Constant("int", "1"))]))
    if type == "even":
        return c_ast.FuncCall(name=c_ast.ID("__VERIFIER_assume"),
                args=c_ast.ExprList([c_ast.BinaryOp("%", c_ast.ID(var), c_ast.Constant("int", "0"))]))
    
# 判断大数类型
def getBigNumberType(number : str):
    if number == "0x0fffffff":
        return "odd"
    if number == "0x0ffffffe":
        return "even"
    print("不知道数据类型")
    exit(1)

# 创建一元符号
# i++
def createUnaryAst(op, exprAst) -> c_ast.UnaryOp:
    return c_ast.UnaryOp(op, exprAst)

def parse(filePath) -> c_ast.FileAST:
    ast = parse_file(filePath, use_cpp=True, cpp_args=['-E', r'-Ifake_libc_include'])
    return ast

# 返回表达式中变量集合(可能重复)
# example:  getNumber(x = y + 2) 
# return:   ["x", "y"]
def getVars(expr : Expression) -> list:
    result = []
    if isinstance(expr.lvalue, VariableExpression):
        result.append(expr.lvalue.name)
    elif isinstance(expr.lvalue, BinaryExpression):
        result += getVars(expr.lvalue)

    if isinstance(expr.rvalue, VariableExpression):
        result.append(expr.rvalue.name)
    elif isinstance(expr.rvalue, BinaryExpression):
        result += getVars(expr.rvalue)
    return result

# 获取该表达式所有符号， 允许重复
def extractOps(expr : Expression) -> list:
    if isinstance(expr, VariableExpression): return []
    if isinstance(expr, SpecialExpression): return []
    if isinstance(expr, LabelExpression): return []
    if isinstance(expr, ReturnExpression): return []
    if isinstance(expr, NumberExpression): return []
    if isinstance(expr, BinaryExpression):
        ops = extractOps(expr.lvalue)
        ops = ops + extractOps(expr.rvalue)
        return ops + [expr.op]

# 返回表达式中常量的集合(可能重复)
# example:  getNumber(x = 1 + 2) 
# return:   ["1", "2"]
def getNumber(expr : Expression) -> list:
    result = []
    if isinstance(expr.lvalue, NumberExpression):
        result.append(expr.lvalue.number)
    elif isinstance(expr.lvalue, BinaryExpression):
        result += getVars(expr.lvalue)

    if isinstance(expr.rvalue, NumberExpression):
        result.append(expr.rvalue.number)
    elif isinstance(expr.rvalue, BinaryExpression):
        result += getVars(expr.rvalue)
    return result

# (x + 1) => (y + 1) in ast
def substitute(y, x, ast):
    if isinstance(ast, c_ast.UnaryOp):
        substitute(y, x, ast.expr)
    if isinstance(ast, c_ast.BinaryOp):
        substitute(y, x, ast.left)
        substitute(y, x, ast.right)
    if isinstance(ast, c_ast.ID):
        if ast.name == x: ast.name = y

# 无边界: 单无边界， 双无边界
# 双无边界
def unBound():
    auxiVarName = arg.getRandomVar(prefix='auxi')       # y
    countName = arg.getRandomVar(prefix="count")        # x
    bigRandomNumber = arg.getRandomVar(prefix='bigNumber')  # nondet

    nondetUintAst =  createNondetDeclAst("uint")        # extern int __VERIFIER_nondet_uint();
                                                        # unsigned int bigNumber = __VERIFIER_nondet_uint();
    bigRandomNumberAst = createDeclAst(["unsigned", "int"], bigRandomNumber, 
            c_ast.FuncCall(name=c_ast.ID(nondetUintAst.name), args=None))
    assumeFuncDeclAst = createAssumtDeclAst()           # void __VERIFIER_assume(int expression);
                                                        # __VERIFIER_assume(bigNumber % 1)
    assumeCallAst = assumeNumberTypeAst(bigRandomNumber, "odd")

    # 1.1) 断言必须是x%2或者x&2的形式
    if arg.assertType != AssertType.Rem: return
    vars = getVars(arg.assertNode.expr)
    
    # 1.2) 一个变量 
    if len(vars) != 1: return
    var = vars[0]
    del vars

    # 2.1 寻找循环头
    whileHead = arg.findOneWhileNode(arg.assertNode)
    assert whileHead is not None, '没有找到循环头'
    whileExpr = whileHead.expr
    whileAst = whileHead.ast

    # 2.2 判断循环条件类型
    if isinstance(whileAst.cond, c_ast.BinaryOp):
        if whileExpr.rvalue.number == '0x0fffffff':
            whileAst.cond.right = c_ast.ID(bigRandomNumber)
            arg.insertFuncDeclAst(assumeFuncDeclAst)
            arg.insertFuncDeclAst(nondetUintAst)
            arg.injectVarDeclAst(assumeCallAst)
            arg.injectVarDeclAst(bigRandomNumberAst)
            singleUnBound(whileAst, whileHead, auxiVarName, countName, var)

    if isinstance(whileAst.cond, c_ast.FuncCall):
        if whileAst.cond.name.name =='__VERIFIER_nondet_int': 
            singleUnBound(whileAst, whileHead, auxiVarName, countName, var)

# 无边界: 单无边界， 双无边界
# 单边界
def singleUnBound(whileAst, whileHead, auxiVarName, countName, var):
    # 2) 循环头包含随机数
    if isinstance(whileAst.cond, c_ast.FuncCall):
        if whileAst.cond.name.name !='__VERIFIER_nondet_int': return
    if isinstance(whileAst.cond, c_ast.BinaryOp):
        pass
    # 3) 验证变量线性变化
    assignments = arg.getWhileBodyAssignmentNodes(whileHead)
    assert len(assignments) > 0, '循环体内没有找到赋值语句'
    for assignment in assignments:
        if assignment.expr.lvalue.name == var:
            assigNode = assignment
            break

    # 4.1) 是线性变化，获取op和k    
    op = assigNode.expr.rvalue.op
    if op in ["+", "-"]:
        k = assigNode.expr.rvalue.rvalue

    # 4.2) 获取b 断言变量的初始值
    decls = arg.getDeclNodes()
    for node in decls:
        if node.expr.lvalue.name == var:
            b = node.expr.rvalue
            break

    # 4.3) 构建辅助表达式 y = kx op b
    # k 增长量 x 是控制变量 b 是初始量
    assignmentAst = createAuxiAst(
                        c_ast.ID(auxiVarName),
                        c_ast.Constant("int", k.number),
                        c_ast.ID(countName),
                        op,
                        c_ast.Constant("int", b.number)
                    )

    # 4.4) 创建 y[] 和 x 的声明 
    countDecl = createDeclAst(["unsigned", "int"], countName, c_ast.Constant('int', '0'))
    auxiVarDecl = createDeclAst(["unsigned", "int"], auxiVarName, c_ast.ID(var))

    # 4.5) 插入 y(auxiVarDecl)和x(countDecl) 的声明
    arg.injectVarDeclAst(auxiVarDecl)
    arg.injectVarDeclAst(countDecl)

    # 4.6) 创建 x 的自增控制表达式
    countAst = createUnaryAst("p++", c_ast.ID(countName))

    insertIndex = -1
    for index, ast in enumerate(whileHead.ast.stmt.block_items):
        assigNode.ast== ast
        insertIndex = index

    # 4.7) 插入辅助表达式和 x 的自增控制表达式
    whileHead.ast.stmt.block_items.insert(insertIndex + 1, countAst)
    whileHead.ast.stmt.block_items.insert(insertIndex + 1, assignmentAst)

    # 5) 使用辅助变量替换断言表达式
    for ast in arg.assertNode.ast.exprs:
        substitute(auxiVarName, var, ast)

# 绝对路径的识别        
def _get_sep(path):
    if isinstance(path,bytes):
        return b'/'
    else:
        return '/'

def isabs(path):
    s = os.fspath(path)  #判断path类型是否str或bytes,否抛出异常
    sep = _get_sep(s)
    return s.startswith(sep)

def preprocess(parseFilePath):
    global arg
    rootAst = parse(parseFilePath)

    file = parseFilePath.split("/")[-1]
    arg = ARG(file, rootAst)
    recursiveTraversal(rootAst)

    arg.initRelationInfo()
    arg.initVarsInfo()
    arg.initAssertType()
    arg.initMainFuncAstInfo()
    arg.initVarDeclAstInfo()
    arg.clearCache()

    recursiveTraversal(rootAst)
    # arg.showNodes()
    # arg.showEdges()
    # arg.showCFG()
    # arg.renderCode(outputDir + fileName)
    unBound()
    cGenerator =  c_generator.CGenerator()
    renderResult = cGenerator.visit(rootAst)

    return renderResult

def PassAuxiExpr(parseFilePath) -> str:

    # Papar 通道
    """
    :param parseFilePath: 提供文件的据对路径，不建议使用相对路径
    :return renderResult: 返回处理后的文本
    """

    renderResult = preprocess(parseFilePath)

    return renderResult

if __name__ == '__main__':

    parseFilePath = './test.c'
    renderResult = preprocess(parseFilePath)
    print(renderResult)
