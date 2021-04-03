import rating
import declare_server
import time
import datetime
import blockchain
import socket
import json
import block


class Client:
    def __init__(self, node):
        self.node = node
        self.rating = rating.RatingBase()
        self.work_time = time.time()
        self.blockchain = blockchain.Blockchain()

    def __str__(self):
        return f"(node={self.node.host}, port = {self.node.port}, rating = {self.rating})"

    def __repr__(self):
        return str(self)

    def get_time(self, start_time):
        end_time = time.time()
        return round(end_time - start_time)

    def get_connected_users(self):
        print(self.node.connected_id)

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

    def get_transaction(self):
        if self.node.recieved_data is not None:
            required_fields = ["type", "content", "timestamp"]
            for field in required_fields:
                if not self.node.recieved_data.get(field):
                   print("Invalid transaction data", 404)
            self.blockchain.add_new_transaction(self.node.recieved_data)
        else:
            print("Not available servers")

    def get_gen_block(self):
        if not self.blockchain.chain:
            block_data = block.Block.fromDict(self.node.recieved_gen)
            self.blockchain.chain.append(block_data)
        else:
            print("You already have genesis block")

    def vote(self):
        author = self.node.id
        questionid = self.blockchain.unconfirmed_transactions[-1]['content']['questionid']
        answer = input("Enter your answer")

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

        self.blockchain.add_new_transaction(post)

        self.announce_new_transaction(post)

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
        """
        This function serves as an interface to add the pending
        transactions to the blockchain by adding them to the block
        and figuring out Proof Of Work.
        """

        if not self.blockchain.unconfirmed_transactions:
            return {"response": "None transactions 0x001"}

        last_block = self.blockchain.last_block
        print(last_block)
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
            return "None transactions to mine 0x002"
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

    def check_rang(self):
        if self.node.set_validation_user is True:
            self.rating.parameters['rang'] = 'Valid_note'
            print("You became valid note")
        else:
            print(self.rating.parameters['rang'])



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
                                Press 1 to update users
                                Press 2 to show time in system
                                Press 3 to update rating
                                Press 4 to show available users
                                Press 5 to disconnect and close connection
                                Press 6 to check your rang
                                Press 7 to check new servers
                                Press 8 to vote
                                '''))
                            elif client.rating.parameters['rang'] == 'Valid_note':
                                answer = int(input('''  
                                Press 1 to update users
                                Press 2 to show time in system
                                Press 3 to update rating
                                Press 4 to show available users
                                Press 5 to disconnect and close connection
                                Press 6 to check your rang
                                Press 7 to check new servers
                                Press 8 to vote
                                Press 9 to mine unconfirmed transactions
                                Press 10 to show blockchain
                                Press 11 to get genesis_block
                                '''))
                        except ValueError:
                            print("Invalid input")
                        else:
                            if answer == 1:
                                client.update_users()
                            if answer == 2:
                                work_time = client.get_time(client.work_time)
                                print("You are in the system for ", str(datetime.timedelta(seconds=work_time)))
                            if answer == 3:
                                work_time = client.get_time(client.work_time)
                                client.rating.update_user_rating_per_active(work_time)
                                print(client.rating.user_rating)
                                declare_server.update_rating(client.node, client.rating.user_rating)
                            if answer == 4:
                                client.get_connected_users()
                            if answer == 5:
                                client.disconnect_to_all()
                                break
                            if answer == 6:
                                client.check_rang()
                            if answer == 7:
                                client.get_transaction()
                            if answer == 8:
                                client.vote()
                            if answer == 9:
                                print(client.mine_unconfirmed_transactions())
                            if answer == 10:
                                print(client.blockchain.chain)
                            if answer == 11:
                                client.get_gen_block()

            elif answer == 3:
                break

