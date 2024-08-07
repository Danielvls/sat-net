# -*- coding: utf-8 -*-
# @Time    : 2024/8/6 20:51
# @Author  : DanielFu
# @Email   : daniel_fys@163.com
# @File    : test.py

import cProfile
import pstats
import io

def some_function_to_profile():
    print("Processing...")
    # 这里放入你需要分析的代码块

def main():
    some_function_to_profile()

# 创建一个 Profile 对象
profiler = cProfile.Profile()
profiler.enable()  # 开始监控

main()  # 执行你的主函数或者需要分析的代码

profiler.disable()  # 停止监控
s = io.StringIO()
sortby = 'cumulative'  # 可以选择不同的排序方式，如'cumulative', 'time'
ps = pstats.Stats(profiler, stream=s).sort_stats(sortby)
ps.print_stats()
print(s.getvalue())
