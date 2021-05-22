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
import argparse
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
        self.sending = False
        self.get_people = False
        self.get_valid = False
        self.votes = 0
        self.people_voted = set()
        self.already_send = set()
        self.connect_to_server()
        self.start_listen()
        self.node.recieved_block.clear()

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
                            self.node.connect_with_node(random_user[1], int(random_user[2]))
                            for node in self.node.nodes_outbound:
                                if random_user[1] == node.host and int(random_user[2]) == node.port:
                                    logger = logging.getLogger()
                                    coloredlogs.install(level='Info', stream=sys.stdout, logger=logger)
                                    logging.info("User %s connected to user %s", self.node.id, int(random_user[0]))
                                    self.node.send_to_node(node, json.dumps(
                                        {"command": "-c", "host": self.node.host, "port": self.node.port}))
        self.get_people = True
        for node in self.node.nodes_outbound:
            if node.host == "localhost" and node.port == 49001:
                self.node.send_to_node(node, json.dumps(
                    {"command": "-g", "id": self.node.id, "conn_nodes": list(self.node.connected_id)}))

    def get_connect_to_validators(self):
        users = self.node.base
        for user in users:
            if user[2] in self.node.other_validators and int(user[0]) not in self.node.connected_id:
                self.node.connect_with_node(user[1], int(user[2]))
                for node in self.node.nodes_outbound:
                    if user[1] == node.host and int(user[2]) == node.port:
                        logger_other_val = logging.getLogger()
                        coloredlogs.install(level='Info', stream=sys.stdout, logger=logger_other_val)
                        logging.info("Validator %s connected to validator %s", self.node.id, int(user[0]))
                        self.node.send_to_node(node, json.dumps(
                            {"command": "-c", "host": self.node.host, "port": self.node.port}))
        self.get_valid = True

    def disconnect_to_all(self):
        users = self.node.nodes_outbound.copy()
        for user in users:
            self.node.send_to_node(user, json.dumps({"command": "-s"}))
            self.node.disconnect_with_node(user)
        declare_server.disconnect(self.node)
        self.node.stop()

    def get_transaction(self):
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
            if dat['type'].lower() == 'close':
                if self.voted:
                    self.voted = False
        else:
            if dat['type'].lower() == 'open':
                logger_open = logging.getLogger()
                logger_open.propagate = False
                coloredlogs.install(level='Info', stream=sys.stdout, logger=logger_open)
                logging.info("User %s get open transaction", self.node.id)
                self.amount = dat['content']['amount_of_people']
                self.open = True
                self.validate_transaction(dat)
                # self.blockchain.add_new_transaction(dat)
            if dat['type'].lower() == 'vote':
                if self.open:
                    if dat not in self.blockchain.unconfirmed_transactions:
                        if dat['content']['author'] not in self.people_voted:
                            logger_vote = logging.getLogger()
                            logger_vote.propagate = False
                            coloredlogs.install(level='Info', stream=sys.stdout, logger=logger_vote)
                            logging.info("User %s get vote transaction", self.node.id)
                            self.people_voted.add(dat['content']['author'])
                            self.blockchain.add_new_transaction(dat)
                            self.votes += 1
                    if len(self.blockchain.unconfirmed_transactions) >= round(0.15 * self.amount):
                        self.mine_unconfirmed_transactions()
                    elif len(self.people_voted) == self.amount:
                        self.mine_unconfirmed_transactions()
                        self.votes = 0

    def listen(self):
        while True:
            time.sleep(0.5)
            if self.node.set_validation_user is False and self.blockchain.unconfirmed_transactions and self.sending is False:
                send_tranc = threading.Thread(target=self.send_transaction)
                send_tranc.start()
                self.sending = True
            if self.node.recieved_data:
                self.get_transaction()
            if self.node.set_validation_user and self.have_gen_block is False:
                self.get_gen_block()
                self.have_gen_block = True
            if self.node.all_conn and not self.get_people:
                self.get_connect_to_user()

    def send_transaction(self):
        while True:
            if self.blockchain.unconfirmed_transactions:
                time.sleep(0.5)
                transaction_to_send = random.choice(self.blockchain.unconfirmed_transactions)
                transaction_to_add = str(transaction_to_send)
                if transaction_to_add not in self.already_send:
                    self.already_send.add(transaction_to_add)
                    self.blockchain.unconfirmed_transactions.remove(transaction_to_send)
                    self.announce_new_transaction(transaction_to_send)

    def get_block(self):
        while True:
            time.sleep(1)
            if self.blockchain.chain and self.node.set_validation_user is True:
                if not self.get_valid:
                    self.get_connect_to_validators()
                if self.node.recieved_block:
                    self.check_transaction()

    def start_listen(self):
        get_tranc_t = threading.Thread(target=self.listen)
        get_tranc_t.start()
        get_block = threading.Thread(target=self.get_block)
        get_block.name = "Get block"
        get_block.start()


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
                self.node.send_to_node(peer, json.dumps(
                    {"command": "-send", "data": data_to_send}))
            except socket.error:
                print("something wrong")

    def announce_new_block(self, data):
        bloc = block.Block.fromDict(data)
        if not bloc:
            return "Invalid data at announce_new_block", 400
        block_to_send = json.dumps(bloc.__dict__)
        for peer in self.node.nodes_outbound:
            if peer.port in self.node.other_validators:
                time.sleep(random.randint(0, 2))
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

        self.blockchain.unconfirmed_transactions = []

        if (len(new_block.transactions) == 0):
            return "None transactions 0x002"

        proof = self.blockchain.proof_of_work(new_block)
        self.blockchain.add_block(new_block, proof)
        logger_chain = logging.getLogger()
        logger_chain.propagate = False
        coloredlogs.install(level='Warning', stream=sys.stdout, logger= logger_chain)
        logging.warning(f"User {self.node.id} added block to chain {self.blockchain.chain}")
        self.announce_new_block(new_block.__dict__)
        result = new_block.index

        if not result:
            return "None transactions to mine 0x003"

        return "Block #{} is mined.".format(result)

    def check_transaction(self):
        block_data = self.node.recieved_block.popleft()
        bloc = block.Block(block_data["index"],
                           block_data["transactions"],
                           block_data["timestamp"],
                           block_data["previous_hash"],
                           block_data["nonce"])
        for transaction in bloc.transactions:
            if transaction['type'].lower() == "vote":
                if transaction['content']['author'] not in self.people_voted:
                    self.people_voted.add(transaction['content']['author'])

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
        block_data = self.node.recieved_block.popleft()
        bloc = block.Block(block_data["index"],
                      block_data["transactions"],
                      block_data["timestamp"],
                      block_data["previous_hash"],
                      block_data["nonce"])
        tmp_open_surveys = self.blockchain.open_surveys
        tmp_chain_code = self.blockchain.chain_code
        if not self.compute_open_surveys(bloc, tmp_open_surveys):
            logger_discarded_block_open = logging.getLogger()
            logger_discarded_block_open.propagate = False
            coloredlogs.install(level='Info', stream=sys.stdout, logger=logger_discarded_block_open)
            logging.info("User %s discarded block open", self.node.id)
            return "The block was discarded by the node"

        self.blockchain.open_surveys = tmp_open_surveys
        self.blockchain.chain_code = tmp_chain_code

        proof = block_data['hash']
        added = self.blockchain.add_block(bloc, proof)
        if not added:
            logger_discarded_block = logging.getLogger()
            logger_discarded_block.propagate = False
            coloredlogs.install(level='Info', stream=sys.stdout, logger=logger_discarded_block)
            logging.info("User %s discarded block", self.node.id)
            return "The block was discarded by the node"
        logger_add_block = logging.getLogger()
        logger_add_block.propagate = False
        coloredlogs.install(level='Info', stream=sys.stdout, logger=logger_add_block)
        logging.info("User %s added block", self.node.id)
        return "Block added to the chain"

    def compute_open_surveys(self, blocked, open_surveys):
        for transaction in blocked.transactions:
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
                else:
                    return False
            else:
                return False
        return True




if __name__ == '__main__':
    user = declare_server.connect(sys.argv[1], sys.argv[2])
    clint = Client(user)

