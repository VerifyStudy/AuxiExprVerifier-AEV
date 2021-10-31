#!/usr/bin/python3

# 管理通道，调度和销毁
# pass 是python关键字，使用_pass表示
import os
import shutil

class PassManager(object):

    """
    @param orgDir: 处理文件的目录
    @param preDir: 结构保存目录
    @param tmpDir：临时文件保存目录
    @param file: 文件名字
    """
    def __init__(self, orgDir, preDir, tmpDir, file) -> None:
        self.orgDir = orgDir
        self.preDir = preDir
        self.tmpDir = tmpDir
        self.file = file
        self.passPool = []

    def add(self, _pass):
        self.passPool.append(_pass)

    def size(self) -> int:
        return len(self.passPool)
    
    def pop(self):
        self.passPool.pop(0)
    
    def clear(self):
        del self.passPool
        self.passPool = []
    
    def checkPath(self) -> bool:
        orgPath = os.path.join(self.orgDir, self.file)
        if not os.path.isdir(self.orgDir): return False
        if os.path.isdir(self.tmpDir): 
            subTmpDir = os.path.join(self.tmpDir, self.file[:-2])
            if not os.path.isdir(subTmpDir): 
                os.mkdir(subTmpDir)
        else :return False
        if not os.path.isdir(self.preDir): return False
        if not os.path.isfile(orgPath): return False
        return True

    def run(self) -> str:
        """
        #return : 返回结果的绝对路径
        """
        
        if not self.checkPath():
            print("路径有问题")
            print("orgDir\t", self.orgDir)
            print("preDir\t", self.preDir)
            print("tmpDir\t", self.tmpDir)

        orgPath = os.path.join(self.orgDir, self.file)
        prePath = os.path.join(self.preDir, self.file)
        for _pass in self.passPool:

            renderResult = _pass(orgPath)
            returnFilePath = os.path.join(self.tmpDir, self.file[:-2] + "/",  _pass.__name__ + "_" + self.file)
            with open(returnFilePath, 'w', encoding='utf-8') as f:
                f.write(renderResult)
            print("Pass info:", _pass.__name__ , "finish! saving to: ", returnFilePath)
            orgPath = returnFilePath
        shutil.copyfile(orgPath, prePath)
        print("PassManager info: All pass finished, result file save to ", prePath)
        return prePath