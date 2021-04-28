import rating
import declare_server
import time
import block
import blockchain
import socket
import json
import math
import threading
import random
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style

class Server:
    def __init__(self, node):
        self.node = node
        self.rating = rating.RatingBase()
        self.work_time = time.time()
        self.blockchain = blockchain.Blockchain()
        self.amount_of_valid = 0
        self.validators = dict()
        self.threads = []
        self.start_listen()
        self.time_for_vote = None
        self.graph = nx.Graph()
        self.figure = plt.figure()
        self.show_plot()


    def __str__(self):
        return f"(node={self.node.host}, port = {self.node.port}, rating = {self.rating})"

    def __repr__(self):
        return str(self)

    def get_connected_users(self):
        print(self.node.connected_id)

    def show_block_chain(self):
        print(self.blockchain.chain)

    def update_valid_amount(self, users):
        self.amount_of_valid = math.ceil(len(users) * 0.15)

    def choose_rating(self):
        self.validators.clear()
        users = declare_server.get_nodes(self.node, True)
        self.update_valid_amount(users)
        print(users)
        for user in users[:self.amount_of_valid]:
            self.validators[user.port] = user.ip_address
        self.send_valid()

    def send_valid(self):
        for node in self.node.nodes_outbound:
            try:
                self.validators[node.port] == node.host
            except KeyError:
                pass
            else:
                self.node.send_to_node(node, json.dumps(
                    {"command": "-send_rep"}))
                self.announce_gen_block()
        print(self.validators)

    def disconnect_to_all(self):
        users = self.node.nodes_outbound.copy()
        for user in users:
            self.node.send_to_node(user, json.dumps({"command": "-s"}))
            self.node.disconnect_with_node(user)
        declare_server.disconnect(self.node)
        self.node.stop()

    def countdown(self, t):
        while t:
            time.sleep(1)
            t -= 1
        self.close_survey()


    def submit_textarea(self):
        author = self.node.id
        questionid = "1"
        question = "1"
        answersList = "Yes|No".split("|")
        opening_time = 120
        answers = {}
        timestamp = time.time()
        for answer in answersList:
            answers[answer] = []

        post_object = {
            'type': 'open',
            'content': {
                'questionid': questionid,
                'question': question,
                'answers': answers,
                'opening_time': opening_time,
                'status': 'opening',
                'author': author,
                'timestamp': timestamp,
                'amount_of_people': 5
            }
        }
        vote_thread = threading.Thread(target=self.countdown, args=(opening_time,),daemon=True)
        vote_thread.start()
        vote_thread.name = "Vote time"
        self.threads.append(vote_thread)
        self.time_for_vote = timestamp
        self.choose_rating()

        self.new_transaction(post_object)


        # print(new_tx_address)

        return True

    def close_survey(self):
        """
        Endpoint to create a new transaction via our application.
        """
        author = self.node.id
        questionid = self.blockchain.unconfirmed_transactions[-1]['content']['questionid']

        post_object = {
            'type': 'close',
            'content': {
                'questionid': questionid,
                'author': author,
                'timestamp': time.time()
            }
        }
        print(post_object)
        # Submit a transaction
        self.new_transaction(post_object)

        return True

    def ping_users(self):
        while True:
            if self.node.nodes_outbound:
                for node in self.node.nodes_outbound:
                    result = self.node.send_to_node(node, json.dumps({"command": "p"}))
                    self.node.delete_closed_connections()
                    if not result:
                        declare_server.disconnect_other(node)
                    else:
                        declare_server.update(node)
            else:
                nodes = declare_server.get_nodes(self.node)
                for node in nodes:
                    declare_server.disconnect_other(node, by_p2p=False)

    def get_block(self):
        while True:
            time.sleep(5)
            if self.blockchain.chain:
                if self.node.recieved_block:
                    self.validate_and_add_block()

    def start_listen(self):
        get_ping = threading.Thread(target=self.ping_users)
        get_ping.name = "Ping"
        get_graph = threading.Thread(target=self.plot_graph)
        get_graph.name ="Graph"
        get_graph.start()
        # get_block = threading.Thread(target=self.get_block)
        # get_block.name = "Get block"
        # get_block.start()
        get_ping.start()
        self.threads.extend([get_ping])

    def plot_graph(self):
        while True:
            time.sleep(5)
            if self.node.recieved_graph:
                for graph in self.node.recieved_graph:
                    graph_new_node = graph.get('id')
                    graph_conn_id = graph.get('conn_nodes')
                    if graph_new_node not in self.graph:
                        self.graph.add_node(graph_new_node)
                        for edge in graph_conn_id:
                            if not self.graph.has_edge(graph_new_node, edge):
                                self.graph.add_edge(graph_new_node, edge)

    def do_something_plot(self, i):
        plt.clf()
        plt.cla()
        nx.draw_shell(self.graph, with_labels = True)

    def show_plot(self):
        ani = animation.FuncAnimation(self.figure, self.do_something_plot, interval=1000)
        plt.ion()
        plt.show()
        plt.pause(0.001)

    def new_transaction(self, post):
        tx_data = post
        required_fields = ["type", "content"]

        for field in required_fields:
            if not tx_data.get(field):
                return "Invalid transaction data"

        tx_data["timestamp"] = time.time()

        self.blockchain.add_new_transaction(tx_data)

        self.announce_new_transaction(tx_data)

    def announce_new_transaction(self, data):
        if not data:
            return "Invalid data at announce_new_block", 400
        data_to_send = json.dumps(data)
        for peer in self.validators:
            try:
                time.sleep(random.randint(1, 3))
                self.node.send_to_node(peer, json.dumps(
                    {"command": "-send", "data": data_to_send}))
            except socket.error:
                print("something wrong")
        for peer in self.node.nodes_outbound:
            try:
                time.sleep(random.randint(1, 3))
                self.node.send_to_node(peer, json.dumps(
                    {"command": "-send", "data": data_to_send}))
            except socket.error:
                print("something wrong")
        return "Success", 201

    def announce_new_block(self, data):
        bloc = block.Block.fromDict(data)
        if not bloc:
            return "Invalid data at announce_new_block", 400
        block_to_send = json.dumps(bloc.__dict__)
        for peer in self.node.nodes_outbound:
            try:
                self.node.send_to_node(peer, json.dumps(
                    {"command": "-send_block", "data": block_to_send}))
            except socket.error:
                print("something wrong")
        return "Success", 201

    def announce_gen_block(self):
        data = self.blockchain.chain[0]
        for peer in self.node.nodes_outbound:
            try:
                self.validators[peer.port] == peer.host
            except KeyError:
                pass
            else:
                try:
                    self.node.send_to_node(peer, json.dumps(
                        {"command": "-send_gen", "data": data.__dict__}))
                except socket.error:
                    print("something wrong")
        return "Success", 201

    def get_transaction(self):
        required_fields = ["type", "content", "timestamp"]

        for field in required_fields:
            if not self.node.recieved_data.get(field):
                return "Invalid transaction data", 404

        self.blockchain.add_new_transaction(self.node.recieved_data)
        self.node.recieved_data = None
        print(self.blockchain.unconfirmed_transactions)
        return "Success"

    def validate_and_add_block(self):
        block_data = self.node.recieved_block

        bloc = block.Block(block_data["index"],
                      block_data["transactions"],
                      block_data["timestamp"],
                      block_data["previous_hash"],
                      block_data["nonce"])
        tmp_open_surveys = self.blockchain.open_surveys
        tmp_chain_code = self.blockchain.chain_code

        if not self.compute_open_surveys(bloc, tmp_open_surveys):
            return "The block was discarded by the node"

        self.blockchain.open_surveys = tmp_open_surveys
        self.blockchain.chain_code = tmp_chain_code

        proof = block_data['hash']
        added = self.blockchain.add_block(bloc, proof)
        if not added:
            return "The block was discarded by the node"
        return "Block added to the chain"

    def compute_open_surveys(self, block, open_surveys):
        for transaction in block.transactions:
            if transaction['type'].lower() == 'open':
                questionid = transaction['content']['questionid']
                if questionid not in open_surveys:
                    open_surveys[questionid] = transaction['content']
                    return True
            elif transaction['type'].lower() == 'close':
                questionid = transaction['content']['questionid']
                if questionid in open_surveys and open_surveys[questionid]['author'] == transaction['content'][
                    'author'] and open_surveys[questionid]['status'] == 'opening':
                    open_surveys[questionid]['status'] = 'closed'
                    return True
            elif transaction['type'].lower() == 'vote':
                questionid = transaction['content']['questionid']
                if questionid in open_surveys and open_surveys[questionid]['status'] == 'opening':
                    vote = transaction['content']['vote']
                    author = transaction['content']['author']
                    if author not in open_surveys[questionid]['answers'][vote]:
                        open_surveys[questionid]['answers'][vote].append(author)
                        return True
            else:
                return True
            return False
        return True


if __name__ == '__main__':
    server = declare_server.connect(serv=True)
    if server is not None:
        serv = Server(server)
        serv.blockchain.create_genesis_block(None)
        while True:

            try:
                answer = int(input('''  
                Press 2 to show users
                Press 4 for new servers
                Press 5 to disconnect
                Press 9 to close servers
                '''))
            except ValueError:
                print("Invalid input")
            else:
                if answer == 2:
                    serv.get_connected_users()
                if answer == 4:
                    serv.submit_textarea()
                if answer == 5:
                    serv.disconnect_to_all()
                    break
                if answer == 7:
                    serv.validate_and_add_block()
                if answer == 8:
                    print(serv.blockchain.chain)
                if answer == 9:
                    serv.close_survey()