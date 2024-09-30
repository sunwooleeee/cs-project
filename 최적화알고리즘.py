import simpy
import random
import numpy as np

# Process times and coefficients
time_A = [15, 15, 15, 15, 15]
time_B = [[5, 40, 25, 25, 5], [10, 10, 5, 10, 15]]
coeff_A = [4, 9, 8, 8, 5.5]
coeff_B = [4, 9, 8, 8, 5.5]

def production_process_A(env, k, material, factory_A, input_buffers_A, completed_products, finished_products, usage_times):
    for i in range(2):
        for j in range(5):
            priority = 1 if i == 1 else 2
            resource = factory_A[j]

            yield input_buffers_A[j].get()

            with resource.request(priority=priority) as req:
                yield req
                material[k][i][j] = 1
                if j == 4 and random.random() < 0.5:
                    material[k][i][j] = 0
                    if i == 1:
                        completed_products['Product A'] += 1
                        finished_products.append((f"Product A_{k}", env.now))
                        material[k][i][5] = 1
                    yield input_buffers_A[0].put(1)
                    continue
                yield env.timeout(time_A[j])
                usage_times[resource]['busy_time'] += time_A[j]
                material[k][i][j] = 0
                if j == 4 and i == 1:
                    completed_products['Product A'] += 1
                    finished_products.append((f"Product A_{k}", env.now))
                    material[k][i][5] = 1

            if j < 4:
                yield input_buffers_A[j + 1].put(1)
            elif i == 0:
                yield input_buffers_A[0].put(1)

            if env.now >= max_time:
                return
        if env.now >= max_time:
            return

def production_process_B(env, k, material, factory_B, input_buffers_B, completed_products, finished_products, usage_times):
    for i in range(2):
        for j in range(5):
            priority = 1 if i == 1 else 2
            resource = factory_B[j]

            yield input_buffers_B[j].get()

            with resource.request(priority=priority) as req:
                yield req
                material[k][i][j] = 1
                if j == 4 and random.random() < 0.5:
                    material[k][i][j] = 0
                    if i == 1:
                        completed_products['Product B'] += 1
                        finished_products.append((f"Product B_{k}", env.now))
                        material[k][i][5] = 1
                    yield input_buffers_B[0].put(1)
                    continue
                yield env.timeout(time_B[i][j])
                usage_times[resource]['busy_time'] += time_B[i][j]
                material[k][i][j] = 0
                if j == 4 and i == 1:
                    completed_products['Product B'] += 1
                    finished_products.append((f"Product B_{k}", env.now))
                    material[k][i][5] = 1

            if j < 4:
                yield input_buffers_B[j + 1].put(1)
            elif i == 0:
                yield input_buffers_B[0].put(1)

            if env.now >= max_time:
                return
        if env.now >= max_time:
            return

def calculate_profit(material_A, material_B, finished_products, max_time, fac_A, fac_B):
    completed_A = sum(1 for product, time in finished_products if product.startswith("Product A") and time <= max_time)
    completed_B = sum(1 for product, time in finished_products if product.startswith("Product B") and time <= max_time)
    min_completed = min(completed_A, completed_B)
    total_fac = sum(f * c for f, c in zip(fac_A, coeff_A)) + sum(f * c for f, c in zip(fac_B, coeff_B))
    return (100 * min_completed) - total_fac if total_fac > 0 else 0, completed_A, completed_B

def evaluate(fac_A, fac_B, max_time, n_products=200):
    env = simpy.Environment()
    completed_products = {'Product A': 0, 'Product B': 0}
    finished_products = []
    material_A = [[[0 for _ in range(6)] for _ in range(2)] for _ in range(n_products)]
    material_B = [[[0 for _ in range(6)] for _ in range(2)] for _ in range(n_products)]
    factory_A = [simpy.PriorityResource(env, capacity=fac_A[j]) for j in range(5)]
    factory_B = [simpy.PriorityResource(env, capacity=fac_B[j]) for j in range(5)]
    input_buffers_A = [simpy.Store(env, capacity=simpy.core.Infinity) if j == 0 else simpy.Store(env, capacity=fac_A[j]) for j in range(5)]
    input_buffers_B = [simpy.Store(env, capacity=simpy.core.Infinity) if j == 0 else simpy.Store(env, capacity=fac_B[j]) for j in range(5)]

    for _ in range(n_products):
        input_buffers_A[0].put(1)
        input_buffers_B[0].put(1)

    usage_times = {resource: {'busy_time': 0, 'total_time': max_time * resource.capacity} for resource in factory_A + factory_B}

    for k in range(n_products):
        env.process(production_process_A(env, k, material_A, factory_A, input_buffers_A, completed_products, finished_products, usage_times))
        env.process(production_process_B(env, k, material_B, factory_B, input_buffers_B, completed_products, finished_products, usage_times))

    env.run(until=max_time)

    profit, completed_A, completed_B = calculate_profit(material_A, material_B, finished_products, max_time, fac_A, fac_B)
    return profit, completed_A, completed_B

# 고정된 Fac A와 B 값을 사용하여 100번의 시뮬레이션 실행
fac_A = [3, 3, 3, 3, 2]
fac_B = [2, 5, 3, 4, 1]
max_time = 24 * 60
n_simulations = 100

profits = []
completed_A_totals = []
completed_B_totals = []

for _ in range(n_simulations):
    profit, completed_A, completed_B = evaluate(fac_A, fac_B, max_time)
    profits.append(profit)
    completed_A_totals.append(completed_A)
    completed_B_totals.append(completed_B)

# 평균 및 표준편차 계산
mean_profit = np.mean(profits)
std_dev_profit = np.std(profits)
mean_completed_A = np.mean(completed_A_totals)
std_dev_completed_A = np.std(completed_A_totals)
mean_completed_B = np.mean(completed_B_totals)
std_dev_completed_B = np.std(completed_B_totals)

print(f"평균 이익: {mean_profit}")
print(f"이익의 표준편차: {std_dev_profit}")
print(f"A의 평균 생산량: {mean_completed_A}")
print(f"A의 생산량 표준편차: {std_dev_completed_A}")
print(f"B의 평균 생산량: {mean_completed_B}")
print(f"B의 생산량 표준편차: {std_dev_completed_B}")
