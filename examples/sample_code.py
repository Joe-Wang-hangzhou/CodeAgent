# 这是一个待审查的代码样本
def calculate_sum(arr):
    # 坏味道：变量命名不规范，没有类型提示，可改用内置 sum 函数
    s = 0
    for i in range(len(arr)):
        s = s + arr[i]
    return s

def read_file(path):
    # Bug：文件没有关闭，没有异常处理
    f = open(path, 'r')
    content = f.read()
    return content

print(calculate_sum([1, 2, 3]))
