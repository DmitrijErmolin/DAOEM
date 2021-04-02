import rating
import declare_server
import time
import block
import blockchain
import socket
import json
import math

class Server:
    def __init__(self, node):
        self.node = node
        self.rating = rating.RatingBase()
        self.work_time = time.time()
        self.blockchain = blockchain.Blockchain()
        self.amount_of_valid = 0
        self.validators = dict()

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
                print(node.host, node.port)
        print(self.validators)


    def update_users(self):
        users = declare_server.get_nodes(self.node)
        for user in users:
            if user.port != self.node.host:
                declare_server.get_connect(user.ip_address, user.port, self.node)
        for node in self.node.nodes_outbound:
            self.node.send_to_node(node, json.dumps(
                {"command": "-c", "host": self.node.host, "port": self.node.port}))

    def disconnect_to_all(self):
        users = self.node.nodes_outbound.copy()
        for user in users:
            self.node.send_to_node(user, json.dumps({"command": "-s"}))
            self.node.disconnect_with_node(user)
        declare_server.disconnect(self.node)
        self.node.stop()

    def submit_textarea(self):
        author = self.node.id
        questionid = input("Please input question ID")
        question = input("Please input the question")
        answersList = input("Please input the answers separated by |").split('|')
        opening_time = int(input("Please input vote time")) * 60
        answers = {}

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
                'timestamp': time.time()
            }
        }

        self.new_transaction(post_object)

        # print(new_tx_address)

        return True

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
        print(data)
        for peer in self.node.nodes_outbound:
            try:
                self.node.send_to_node(peer, json.dumps(
                    {"command": "-send", "data": data}))
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
        print(bloc)
        tmp_open_surveys = self.blockchain.open_surveys
        tmp_chain_code = self.blockchain.chain_code

        if not self.compute_open_surveys(bloc, tmp_open_surveys):
            return "The block was discarded by the node"

        self.blockchain.open_surveys = tmp_open_surveys
        self.blockchain.chain_code = tmp_chain_code

        proof = block_data['hash']
        added = self.blockchain.add_block(bloc, proof)
        print(added)
        if not added:
            return "The block was discarded by the node"
        print(self.blockchain.chain)
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
    server = declare_server.connect(True)
    if server is not None:
        serv = Server(server)
        while True:
            try:
                answer = int(input('''  
                Press 1 to update users
                Press 2 to show users
                Press 3 to choose validator users
                Press 4 for new servers
                Press 5 to disconnect
                '''))
            except ValueError:
                print("Invalid input")
            else:
                if answer == 1:
                   serv.update_users()
                if answer == 2:
                    serv.get_connected_users()
                if answer == 3:
                    serv.choose_rating()
                if answer == 4:
                    serv.submit_textarea()
                if answer == 5:
                    serv.disconnect_to_all()
                if answer == 6:
                    serv.get_transaction()
                if answer == 7:
                    serv.validate_and_add_block()