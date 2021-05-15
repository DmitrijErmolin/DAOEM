import rating
import random
import declare_server
import time
import datetime
import blockchain
import socket
import json
import block
import threading
import logging
import sys
import coloredlogs
from collections import deque

class Client:
    def __init__(self, node):
        self.node = node
        self.rating = rating.RatingBase()
        self.work_time = time.time()
        self.blockchain = blockchain.Blockchain()
        self.node.sock.settimeout(5)
        self.server_not_found = True
        self.amount = 0
        self.have_gen_block = False
        self.voted = False
        self.open = False
        self.count_votes = 0
        self.votes = 0
        self.connect_to_server()
        self.start_listen()

    def __str__(self):
        return f"(node={self.node.host}, port = {self.node.port}, rating = {self.rating})"

    def __repr__(self):
        return str(self)

    def conn_people(self):
        print(f"{self.node.id} connected to {self.node.connected_id}")

    def get_time(self, start_time):
        end_time = time.time()
        return round(end_time - start_time)

    def connect_to_server(self):
        while self.server_not_found:
            node_server = declare_server.get_server()
            if node_server is not None:
                logger = logging.getLogger()
                coloredlogs.install(level='Info', stream=sys.stdout, logger=logger)
                logging.info("%s Success connected to server", self.node.id)
                self.node.connect_with_node(node_server.ip_address, node_server.port)
                for serv_node in self.node.nodes_outbound:
                    if serv_node.host == node_server.ip_address and serv_node.port == node_server.port:
                        self.node.send_to_node(serv_node, json.dumps(
                    {"command": "-c", "host": self.node.host, "port": self.node.port, "started": self.work_time}))
                self.server_not_found = False
            else:
                logger = logging.getLogger()
                coloredlogs.install(level='Info', stream=sys.stdout, logger=logger)
                logging.info("User %s cannot find server", self.node.id)

    def get_connect_to_user(self):
        if self.node.base:
            while len(self.node.connected_id) < 3 and len(self.node.nodes_inbound) < 2:
                random_connect_numb = random.randint(1, 2)
                users = self.node.base
                for i in range(random_connect_numb):
                    time.sleep(1)
                    if users:
                        random_user = random.choice(users)
                        if int(random_user[0]) not in self.node.connected_id:
                            declare_server.get_connect(random_user[1], int(random_user[2]), self.node)
                            for node in self.node.nodes_outbound:
                                if random_user[1] == node.host and int(random_user[2]) == node.port:
                                    logger = logging.getLogger()
                                    coloredlogs.install(level='Info', stream=sys.stdout, logger=logger)
                                    logging.info("User %s connected to user %s", self.node.id, int(random_user[0]))
                                    self.node.send_to_node(node, json.dumps(
                                        {"command": "-c", "host": self.node.host, "port": self.node.port}))
        for node in self.node.nodes_outbound:
            if node.host == "localhost" and node.port == 49001:
                self.node.send_to_node(node, json.dumps(
                    {"command": "-g", "id": self.node.id, "conn_nodes": list(self.node.connected_id)}))

    def disconnect_to_all(self):
        users = self.node.nodes_outbound.copy()
        for user in users:
            self.node.send_to_node(user, json.dumps({"command": "-s"}))
            self.node.disconnect_with_node(user)
        declare_server.disconnect(self.node)
        self.node.stop()

    def get_transaction(self):
        while self.node.recieved_data:
            dat = json.loads(self.node.recieved_data.popleft())
            required_fields = ["type", "content", "timestamp"]
            for field in required_fields:
                if not dat.get(field):
                   print("Invalid transaction data", 404)
            if self.node.set_validation_user is False:
                if dat['type'].lower() == 'open':
                    if not self.voted:
                        self.vote(dat)
                        self.voted = True
                if dat['type'].lower() == 'vote':
                    if dat not in self.blockchain.unconfirmed_transactions:
                        self.blockchain.add_new_transaction(dat)
                        self.announce_new_transaction(dat)
            else:
                if dat['type'].lower() == 'open':
                    logger_open = logging.getLogger()
                    logger_open.propagate = False
                    coloredlogs.install(level='Info', stream=sys.stdout, logger=logger_open)
                    logging.info("User %s get transaction %s", self.node.id, dat)
                    self.amount = dat['content']['amount_of_people']
                    self.open = True
                    self.blockchain.add_new_transaction(dat)
                if dat['type'].lower() == 'vote':
                    if self.open:
                        if dat not in self.blockchain.unconfirmed_transactions:
                            logger_vote = logging.getLogger()
                            logger_vote.propagate = False
                            coloredlogs.install(level='Info', stream=sys.stdout, logger=logger_vote)
                            logging.info("User %s get transaction %s", self.node.id, dat)
                            self.blockchain.add_new_transaction(dat)
                            self.count_votes += 1
                            self.votes += 1
                            logger_vote.info(f"Total votes {self.node.id} - {self.votes} ")
                        if self.count_votes == self.amount:
                            self.mine_unconfirmed_transactions()
                            self.count_votes = 0

    def listen(self):
        while True:
            time.sleep(1)
            self.get_transaction()
            if self.node.set_validation_user and self.have_gen_block is False:
                self.get_gen_block()
                self.have_gen_block = True

    def start_listen(self):
        get_tranc_t = threading.Thread(target=self.listen)
        get_tranc_t.start()

    def get_gen_block(self):
        if self.node.set_validation_user is True:
            if not self.blockchain.chain:
                if self.node.recieved_gen:
                    block_data = block.Block.fromDict(self.node.recieved_gen)
                    self.blockchain.chain.append(block_data)

    def vote(self, data):
        if self.node.set_validation_user is False:
            answer = ["Yes", "No"]
            author = self.node.id
            questionid = data['content']['questionid']
            answer = random.choice(answer)

            post_object = {
                'type': 'vote',
                'content': {
                    'questionid': questionid,
                    'author': author,
                    'vote': answer,
                    'timestamp': time.time()
                }
            }
            self.new_transaction(post_object)


    def new_transaction(self, post):
        required_fields = ["type", "content"]
        for field in required_fields:
            if not post.get(field):
                return "Invalid transaction data"

        post["timestamp"] = time.time()
        if self.node.set_validation_user:
            self.blockchain.add_new_transaction(post)

        self.announce_new_transaction(post)

    def announce_new_transaction(self, data):
        if not data:
            return "Invalid data at announce_new_block", 400
        data_to_send = json.dumps(data)
        for peer in self.node.nodes_outbound:
            try:
                time.sleep(random.randint(1, 3))
                self.node.send_to_node(peer, json.dumps(
                    {"command": "-send", "data": data_to_send}))
            except socket.error:
                print("something wrong")

    def announce_new_block(self, data):
        bloc = block.Block.fromDict(data)
        if not bloc:
            return "Invalid data at announce_new_block", 400
        block_to_send = json.dumps(bloc.__dict__)
        print(block_to_send)
        for peer in self.node.nodes_outbound:
            try:
                self.node.send_to_node(peer, json.dumps(
                    {"command": "-send_block", "data": data}))
            except socket.error:
                print("something wrong")
        return "Success"

    def mine_unconfirmed_transactions(self):
        if not self.blockchain.unconfirmed_transactions:
            return {"response": "None transactions 0x001"}

        last_block = self.blockchain.last_block
        new_block = block.Block(index=last_block.index + 1,
                          transactions=[],
                          timestamp=time.time(),
                          previous_hash=last_block.hash)

        for transaction in self.blockchain.unconfirmed_transactions:

            if not self.validate_transaction(transaction):
                continue

            new_block.transactions.append(transaction)

        blockchain.unconfirmed_transactions = []

        if (len(new_block.transactions) == 0):
            return "None transactions 0x002"

        proof = self.blockchain.proof_of_work(new_block)
        self.blockchain.add_block(new_block, proof)
        self.announce_new_block(new_block.__dict__)
        result = new_block.index

        if not result:
            return "None transactions to mine 0x003"
        print("NEW BLOCK", new_block)
        return "Block #{} is mined.".format(result)

    def validate_transaction(self, transaction):
        if transaction['type'].lower() == 'open':
            questionid = transaction['content']['questionid']
            if questionid in self.blockchain.open_surveys:
                return False
            self.blockchain.open_surveys[questionid] = transaction['content']
            return True
        elif transaction['type'].lower() == 'close':
            questionid = transaction['content']['questionid']
            if questionid in self.blockchain.open_surveys and self.blockchain.open_surveys[questionid]['author'] == \
                    transaction['content']['author'] and self.blockchain.open_surveys[questionid]['status'] == 'opening':
                self.blockchain.open_surveys[questionid]['status'] = 'closed'
                return True
            return False
        elif transaction['type'].lower() == 'vote':
            questionid = transaction['content']['questionid']
            if questionid in self.blockchain.open_surveys and self.blockchain.open_surveys[questionid]['status'] == 'opening':
                vote = transaction['content']['vote']
                author = transaction['content']['author']
                if author not in self.blockchain.open_surveys[questionid]['answers'][vote]:
                    self.blockchain.open_surveys[questionid]['answers'][vote].append(author)
                    return True
                return False

    def validate_and_add_block(self):
        block_data = json.loads(self.node.recieved_block)
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
    while True:
        try:
            answer = int(input('''
            Press 1 to sigIn \n
            Press 2 to logIn\n
            Press 3 to exit\n
            '''))
        except ValueError:
            print("Invalid input")
        else:
            if answer == 1:
                declare_server.register()
            elif answer == 2:
                user = declare_server.connect()
                if user is not None:
                    client = Client(user)
                    while True:
                        try:
                            if client.rating.parameters['rang'] == 'Common':
                                answer = int(input('''
                                Press 2 to show time in system
                                Press 4 to show available users
                                Press 5 to disconnect and close connection
                                '''))
                            elif client.rating.parameters['rang'] == 'Valid_note':
                                answer = int(input('''
                                Press 2 to show time in system
                                Press 4 to show available users
                                Press 5 to disconnect and close connection
                                Press 9 to mine unconfirmed transactions
                                Press 10 to show blockchain
                                Press 11 to get genesis_block
                                '''))
                        except ValueError:
                            print("Invalid input")
                        else:
                            if answer == 2:
                                work_time = client.get_time(client.work_time)
                                print("You are in the system for ", str(datetime.timedelta(seconds=work_time)))
                            if answer == 3:
                                print(round(client.rating.user_rating, 6))
                            if answer == 5:
                                client.disconnect_to_all()
                                break
                            if answer == 7:
                                print(client.blockchain.unconfirmed_transactions)
                            if answer == 9:
                                print(client.mine_unconfirmed_transactions())
                            if answer == 10:
                                print(client.blockchain.chain)
                            if answer == 11:
                                client.get_gen_block()

            elif answer == 3:
                break

