#!/usr/bin/python3

# 作用 适配pycparse扩展库
# 1. 删除 #include 部分
# 2. 删除 // 注释
# 3. 删除 __attribute__

def preprocess(parseFilePath):
    assert parseFilePath.endswith('.c'), '输入文件需要是*.c文件'

    with open(parseFilePath, encoding='utf-8') as f:
        txt_list = f.readlines()
        txt = ''
        for each in txt_list:
            if each.find('#include') != -1 or each.find('using') == 0:
                continue
            elif each.find('//') != -1:
                txt += each[:each.find('//')] + '\n' # 把注释都删了
            elif each.find('__attribute__') != -1:
                txt += each[:each.find('__attribute__')] + ';\n' # 把__attribute__删了
            else:
                txt += each

        return txt

def PassPyParse(parseFilePath) -> str:

    # 适配pycparse扩展库
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
