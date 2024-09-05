# -*- coding: utf-8 -*-
# @Time    : 2024/8/6 20:51
# @Author  : DanielFu
# @Email   : daniel_fys@163.com
# @File    : test.py

from multiprocessing import Manager, Process

def modify_graph(graph_proxy):
    graph_proxy['new_edge'] = (1, 2)
    print("Modified graph in process.")

if __name__ == "__main__":
    with Manager() as manager:
        # 创建一个代理字典来模拟图操作
        graph_proxy = manager.dict()
        graph_proxy['edge'] = (1, 2)

        p = Process(target=modify_graph, args=(graph_proxy,))
        p.start()
        p.join()

        print(graph_proxy)  # 查看修改后的图

