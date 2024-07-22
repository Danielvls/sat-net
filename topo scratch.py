import random
import matplotlib.pyplot as plt

# 模拟参数
num_nodes = 1000  # 节点数量
num_steps = 100  # 时间步数量
max_routes = 50  # 每个节点的最大路由数量

# 初始化节点的路由表
nodes = {i: set() for i in range(num_nodes)}

def update_routes(nodes):
    """随机更新节点的路由表"""
    num_converged = 0
    for node in nodes:
        if len(nodes[node]) < max_routes:
            # 随机选择一个新的路由目标
            new_route = random.randint(0, num_nodes - 1)
            # 更新路由表
            nodes[node].add(new_route)
        else:
            num_converged += 1
    return num_converged

# 记录每个时间步收敛的节点数
convergence_log = []

# 模拟收敛过程
for step in range(num_steps):
    converged_this_step = update_routes(nodes)
    convergence_log.append(converged_this_step)

# 绘制收敛曲线
plt.figure(figsize=(10, 6))
plt.plot(convergence_log, marker='o', linestyle='-')
plt.title("Network Convergence Over Time")
plt.xlabel("Time Step")
plt.ylabel("Number of Converged Nodes")
plt.grid(True)
plt.show()
