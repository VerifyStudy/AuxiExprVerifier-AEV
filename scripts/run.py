#! /usr/bin/python3
# coding=UTF-8 

import os
import getopt
import sys
from concurrent.futures import ThreadPoolExecutor

current_dir = os.getcwd()
sys.path.append(current_dir)
from passModule.PassManager import PassManager

from passModule.PassPyParse import PassPyParse
from passModule.PassFuncRet import PassFuncRet
from passModule.PassWhileLoop import PassWhileLoop
from passModule.PassSimplyExpr import PassSimplyExpr
from passModule.PassCompleteBlock import PassCompleteBlock
from passModule.PassAuxiExpr import PassAuxiExpr


def exec(orgDir, preDir, tmpDir, file):
    PM = PassManager(orgDir, preDir, tmpDir, file)
    PM.add(PassPyParse)
    PM.add(PassCompleteBlock)
    PM.add(PassWhileLoop)
    PM.add(PassSimplyExpr)
    # PM.add(PassFuncRet)
    PM.add(PassAuxiExpr)
    result = PM.run()
    print("exec success!\t[" + result + "]")
        
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

if __name__ == '__main__':
    args = sys.argv[1:]
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hi:o:", ["help"])
    except getopt.GetoptError:
      print('./sripts/run.py -i .../loop-acceleration -o .../loop-acceleration-auxi or')
      print('./sripts/run.py -i .../loop-invariants -o .../loop-invariants-auxi or')
      print('./sripts/run.py -i .../benchmark -o .../benchmark or')
      sys.exit(2)
    sourcePath = ''
    outputPath = ''
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print('./sripts/run.py -i .../loop-acceleration -o .../loop-acceleration-auxi or')
            print('./sripts/run.py -i .../loop-invariants -o .../loop-invariants-auxi or')
            print('./sripts/run.py -i .../benchmark -o .../benchmark or')
            sys.exit()
        elif opt == '-i':
            sourcePath = arg
        elif opt == '-o':
            outputPath = arg
    if sourcePath == '':
        print('expect argument -i, but None')
        sys.exit(2)
    if outputPath == '':
        print('expect argument -o, but None')
        sys.exit(2)

    # 输入目录必须是loop-*
    if "loop-" not in sourcePath:
        print('problem about argument `-i`, sourcePath must start with `loop-`')
        sys.exit(2)

    current_dir = os.getcwd()
    # 所有路径都使用绝对路径表示，如果是相对的就转化了
    if not isabs(sourcePath):
        sourceDir = os.path.join(current_dir, sourcePath)
    if not isabs(outputPath):
        outputDir = os.path.join(current_dir, outputPath)
    
    # 判断输出目录是否已经存在，不存在就创建该目录和临时目录
    if not os.path.exists(outputDir): os.mkdir(outputDir)
    if not os.path.exists(outputDir + "tmp/"): os.mkdir(outputDir + "tmp/")
    print('sourceDir ', sourceDir)
    print('outputDir ', outputDir)
    print('tmpDir ', outputDir + "tmp/")

    # 获取源目录下所有验证文件
    files = [file for file in os.listdir(sourceDir) if file.endswith('.c')]
    orgDirs = [sourceDir] * len(files)
    preDirs = [outputDir] * len(files)
    tmpDirs = [outputDir + "tmp/"] * len(files)
    
    # Worker数量
    N = 4
    # 建立线程池
    with ThreadPoolExecutor(max_workers = N) as pool:
        pool = ThreadPoolExecutor(max_workers = N)
        results = pool.map(exec, orgDirs,  preDirs, tmpDirs, files)
        # for result in results:
        #     print(result)
    sys.exit()
