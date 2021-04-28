import json
import time
import networkx as nx
import client
import declare_server
users = []
graph = nx.Graph()
if __name__ == '__main__':
    with open("test.txt", "r") as read_file:
        for line in read_file.readlines():
            s = json.loads(line)
            user = declare_server.connect(s.get('login'), s.get('password'))
            clint = client.Client(user)
            users.append(clint)
            graph.add_node(clint.node.port)
            users.append(clint)









