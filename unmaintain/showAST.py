from pycparser import c_generator, c_ast, c_parser, parse_file, plyparser
ast = parse_file(r'loop-invariants/even.c', use_cpp=False)
# assert isinstance(ast, c_ast.FileAST)
# compound = None
# for ext, node in ast.children():
#     if isinstance(node, c_ast.FuncDef):
#         for ext, node in node.children():
#             if isinstance(node, c_ast.Compound):
#                 compound = node
#                 break
# # compound.show()
# tmpDecl = None
# for ext, node in compound.children():
#     if isinstance(node, c_ast.Decl):
#         tmpDecl = node
#         break
# tmpDecl.show()
# print("name :", tmpDecl.name, type(tmpDecl.name))
# name : x <class 'str'>
# print("quals :", tmpDecl.quals, type(tmpDecl.quals))
# quals : [] <class 'list'>
# print("storage :", tmpDecl.storage, type(tmpDecl.storage))
# storage : [] <class 'list'>
# print("funcspec :", tmpDecl.funcspec, type(tmpDecl.funcspec))
# funcspec : [] <class 'list'>
# print("type :", tmpDecl.type, type(tmpDecl.type))
# print("init :", tmpDecl.init, type(tmpDecl.init))
# print("bitsize :", tmpDecl.bitsize, type(tmpDecl.bitsize))
# bitsize : None <class 'NoneType'>
# print("coord :", tmpDecl.coord, type(tmpDecl.coord))
# coord : test5.c:2:15 <class 'pycparser.plyparser.Coord'>
# newCoord = plyparser.Coord(tmpDecl.coord.file, tmpDecl.coord.line + 1)
# print(newCoord)
# newTypeDecl = c_ast.TypeDecl(declname="z", quals=[],type=c_ast.IdentifierType(names=['unsigned', 'int']))
# newConstant = c_ast.Constant(type="int", value="0")
# newDecl = c_ast.Decl(name="z", quals=[], storage=[], funcspec=[], type=newTypeDecl, init=newConstant, bitsize=None, coord = newCoord)
# newDecl.show()
ast.show()

# for ext, node in ast.children():
#     if isinstance(node, c_ast.FuncDef):
#         for ext, node in node.children():
#             if isinstance(node, c_ast.Compound):
#                 compound.block_items.insert(0,newDecl)
# print(c_generator.CGenerator().visit(ast))
"""
FileAST: 
  Decl: abort, [], ['extern'], []
    FuncDecl: 
      ParamList: 
        Typename: None, []
          TypeDecl: None, []
            IdentifierType: ['void']
      TypeDecl: abort, []
        IdentifierType: ['void']
  Decl: __assert_fail, [], ['extern'], []
    FuncDecl: 
      ParamList: 
        Typename: None, ['const']
          PtrDecl: []
            TypeDecl: None, ['const']
              IdentifierType: ['char']
        Typename: None, ['const']
          PtrDecl: []
            TypeDecl: None, ['const']
              IdentifierType: ['char']
        Typename: None, []
          TypeDecl: None, []
            IdentifierType: ['unsigned', 'int']
        Typename: None, ['const']
          PtrDecl: []
            TypeDecl: None, ['const']
              IdentifierType: ['char']
      TypeDecl: __assert_fail, []
        IdentifierType: ['void']
  FuncDef: 
    Decl: reach_error, [], [], []
      FuncDecl: 
        TypeDecl: reach_error, []
          IdentifierType: ['void']
    Compound: 
      FuncCall: 
        ID: __assert_fail
        ExprList: 
          Constant: string, "0"
          Constant: string, "even.c"
          Constant: int, 3
          Constant: string, "reach_error"
  Decl: __VERIFIER_nondet_int, [], ['extern'], []
    FuncDecl: 
      TypeDecl: __VERIFIER_nondet_int, []
        IdentifierType: ['int']
  FuncDef: 
    Decl: __VERIFIER_assert, [], [], []
      FuncDecl: 
        ParamList: 
          Decl: cond, [], [], []
            TypeDecl: cond, []
              IdentifierType: ['int']
        TypeDecl: __VERIFIER_assert, []
          IdentifierType: ['void']
    Compound: 
      If: 
        UnaryOp: !
          ID: cond
        Compound: 
          Label: ERROR
            Compound: 
              FuncCall: 
                ID: reach_error
              FuncCall: 
                ID: abort
      Return: 
  FuncDef: 
    Decl: main, [], [], []
      FuncDecl: 
        ParamList: 
          Typename: None, []
            TypeDecl: None, []
              IdentifierType: ['void']
        TypeDecl: main, []
          IdentifierType: ['int']
    Compound: 
      Decl: x, [], [], []
        TypeDecl: x, []
          IdentifierType: ['unsigned', 'int']
        Constant: int, 0
      While: 
        FuncCall: 
          ID: __VERIFIER_nondet_int
        Compound: 
          Assignment: +=
            ID: x
            Constant: int, 2
      FuncCall: 
        ID: __VERIFIER_assert
        ExprList: 
          UnaryOp: !
            BinaryOp: %
              ID: x
              Constant: int, 2
      Return: 
        Constant: int, 0
"""