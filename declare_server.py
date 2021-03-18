from sqlalchemy import create_engine, Column, String, BOOLEAN, INTEGER
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from Crypto.PublicKey import RSA
from Crypto import Random
import random
import binascii
from p2pnetwork.node import Node
engine = create_engine("postgresql://postgres:dmitrij@localhost/auth_server")
Base = declarative_base(bind=engine)
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)


class Nodes(Base):
    __tablename__ = "auth_server"
    public_key = Column(String, primary_key=True)
    ip_address = Column(String(15))
    port = Column(INTEGER, unique=True)
    is_available = Column(BOOLEAN, default=False)

    def __str__(self):
        return f"(Public_key={self.public_key})"

    def __repr__(self):
        return str(self)


def create_rsa():
    random_generator = Random.new().read
    private_key = RSA.generate(2048, random_generator)
    public_key = private_key.public_key()
    return [binascii.hexlify(public_key.export_key(format="DER")).decode('ascii'), binascii.hexlify(private_key.export_key(format="DER")).decode('ascii')]


def create_user():
    keys = create_rsa()
    print("Here is your private key, keep it on secret\n", keys[1])
    print("Here is your public key\n", keys[0])
    u = Nodes(public_key=keys[0], ip_address="localhost", port=random.randint(10000, 10005))
    session = Session()
    session.add(u)
    session.commit()
    session.close()


def connect():
    public_key = input("Copy your public key here\n")
    public_keys = RSA.importKey(binascii.unhexlify(public_key))
    session = Session()
    user = session.query(Nodes).filter(Nodes.public_key == binascii.hexlify(public_keys.export_key(format="DER")).decode('ascii'))
    users = session.query(user.exists()).scalar()
    if users:
        user.update({Nodes.is_available: True})
        session.commit()
        node = Node(user.all()[0].ip_address, user.all()[0].port)
        node.start()
    session.close()
    return users, public_key, node


def get_nodes():
    session = Session()
    ports = session.query(Nodes).filter(Nodes.is_available == True).all()
    session.close()
    return ports


def get_connect(public_key, my_node):
    public_keys = RSA.importKey(binascii.unhexlify(public_key))
    session = Session()
    outbound_user = session.query(Nodes).filter(Nodes.public_key == binascii.hexlify(public_keys.export_key(format="DER")).decode('ascii')).all()
    my_node.connect_with_node(outbound_user[0].ip_address, outbound_user[0].port)


def disconnect(public_key):
    public_keys = RSA.importKey(binascii.unhexlify(public_key))
    session = Session()
    session.query(Nodes).filter(Nodes.public_key == binascii.hexlify(public_keys.export_key(format="DER")).decode('ascii')).update(
        {Nodes.is_available: False})
    print("Disconnected")
    # TODO
    # close your own connect
    session.commit()
    session.close()


if __name__ == '__main__':
    Base.metadata.create_all()
    while True:
        try:
            answer = int(input('''
            Press 1 to create new user \n
            Press 2 to login \n
            '''))
        except ValueError:
            print("Invalid input")
        else:
            if answer == 1:
                create_user()
                print("Ok user created, please login")
                id = connect()
                if id[0]:
                    print("Ok")
                else:
                    print("Something wrong")
            if answer == 2:
                id = connect()
                if id[0]:
                    print("Ok")
                else:
                    print("Something wrong")
            node = id[2]
        while True:
            try:
                answer = int(input('''
                Press 1 to get all nodes \n
                Press 2 to connect\n
                Press 3 to get_all_connect\n
                Press 4 to disconnect \n
                '''))
            except ValueError:
                print("Invalid input")
            else:
                users = get_nodes()
                if answer == 1:
                    print(users)
                if answer == 2:
                    public_address = input("Input address_to_connect:")
                    get_connect(public_address, node)
                if answer == 3:
                    for user in users:
                        if user.public_key != id[1]:
                            get_connect(user.public_key, node)
                if answer == 4:
                    disconnect(id[1])
                    break


