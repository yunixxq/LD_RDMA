# 双数据中心 Fat-Tree 拓扑 + DCI
k_fat = 4
oversubscript = 1
link_rate = 100  # Gbps
link_latency = 1000  # ns

dci_rate = 400  # Gbps
dci_latency = 3_000_000  # ns（600km传播）

assert k_fat % 2 == 0
filename = "two_dc_fat_k{}_OS{}_DCI.txt".format(k_fat, oversubscript)
num_link = 0

# 一个数据中心内元信息
n_core = int(k_fat / 2 * k_fat / 2)
n_pod = k_fat
print("Number of Core: {}".format(n_core))
print("Number of pods: {}".format(n_pod))

n_agg_per_pod = int(k_fat / 2)
print("Number of Agg per pod: {}, total: {}".format(n_agg_per_pod, n_agg_per_pod * k_fat))

n_tor_per_pod = int(k_fat / 2)
print("Number of ToR per pod: {}, total: {}".format(n_tor_per_pod, n_tor_per_pod * k_fat))

n_server_per_pod = int(k_fat / 2 * k_fat / 2 * oversubscript)
n_server_per_tor = int(k_fat / 2 * oversubscript)
print("Number of servers per ToR: {} (oversubscript:{})".format(n_server_per_tor, oversubscript))
print("Number of servers per pod: {}, total: {}".format(n_server_per_pod, n_server_per_pod * k_fat))

n_server_total = n_server_per_pod * k_fat
n_tor_total = n_tor_per_pod * k_fat
n_agg_total = n_tor_per_pod * k_fat
n_core_total = n_core

with open(filename, "w") as f:

    dc_nodes = []  # 存每个数据中心的节点编号偏移量

    for dc_id in range(2):  # DC A (0), DC B (1)
        node_offset = dc_id * 100  # 确保编号不冲突，偏移量为1万
        dc_nodes.append(node_offset)

        i_server = node_offset
        i_tor = i_server + n_server_total
        i_agg = i_tor + n_tor_total
        i_core = i_agg + n_agg_total
        i_dci = i_core + n_core_total  # 每个 DC 的 DCI 交换机编号

        # Server–ToR 连接
        for p in range(n_tor_total):
            for i in range(n_server_per_tor):
                id_server = i_server + p * n_server_per_tor + i
                id_tor = i_tor + p
                f.write(f"{id_server} {id_tor} {link_rate}Gbps {link_latency}ns 0.000000\n")
                num_link += 1

        # ToR–Agg 连接
        for i in range(n_pod):
            for j in range(n_tor_per_pod):
                for l in range(n_agg_per_pod):
                    id_tor = i_tor + i * n_tor_per_pod + j
                    id_agg = i_agg + i * n_agg_per_pod + l
                    f.write(f"{id_tor} {id_agg} {link_rate}Gbps {link_latency}ns 0.000000\n")
                    num_link += 1

        # Agg–Core 连接
        n_jump = k_fat // 2
        for i in range(n_pod):
            for j in range(n_agg_per_pod):
                for l in range(k_fat // 2):
                    id_agg = i_agg + i * n_agg_per_pod + j
                    id_core = i_core + j * n_jump + l
                    f.write(f"{id_agg} {id_core} {link_rate}Gbps {link_latency}ns 0.000000\n")
                    num_link += 1

        # Core–DCI 连接（连接本地核心到 DCI）
        for i in range(n_core_total):
            id_core = i_core + i
            id_dci = i_dci
            f.write(f"{id_core} {id_dci} {link_rate}Gbps {link_latency}ns 0.000000\n")
            num_link += 1

    # 跨数据中心：DCI–DCI 连接（双向）
    dci_a = dc_nodes[0] + (k_fat**3 // 4 + k_fat * k_fat // 2 + k_fat * k_fat // 2 + (k_fat//2)**2)
    dci_b = dc_nodes[1] + (k_fat**3 // 4 + k_fat * k_fat // 2 + k_fat * k_fat // 2 + (k_fat//2)**2)

    f.write(f"{dci_a} {dci_b} {dci_rate}Gbps {dci_latency}ns 0.000000\n")
    f.write(f"{dci_b} {dci_a} {dci_rate}Gbps {dci_latency}ns 0.000000\n")
    num_link += 2

    # 总节点数 = 2个DC节点总数 + 2个 DCI 节点
    total_node = 2 * ((k_fat // 2 * oversubscript * k_fat * k_fat // 2) + (k_fat * k_fat // 2) * 2 + (k_fat // 2)**2) + 2
    total_switch = total_node - 2 * (k_fat // 2 * oversubscript * k_fat * k_fat // 2)

    # 写入 switch ID（第二行）
    id_switch_all = ""
    server_total = 2 * (k_fat // 2 * oversubscript * k_fat * k_fat // 2)
    for i in range(server_total, total_node):
        if i == total_node - 1:
            id_switch_all += f"{i}\n"
        else:
            id_switch_all += f"{i} "
    # prepender
    def line_prepender(filename, line):
        with open(filename, "r+") as f:
            content = f.read()
            f.seek(0, 0)
            f.write(line.rstrip('\r\n') + '\n' + content)
# prepend metadata
line_prepender(filename, id_switch_all)
line_prepender(filename, f"{total_node} {total_switch} {num_link}")