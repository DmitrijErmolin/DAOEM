from sqlalchemy import create_engine, Column, String, BOOLEAN, INTEGER
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA3_512
from Crypto import Random
import random
import binascii
from p2pnetwork.node import Node
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql import and_
import blockchain
import rating
engine = create_engine("postgresql://postgres:dmitrij@localhost/auth_server")
Base = declarative_base(bind=engine)
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)


class Nodes(Base):
    __tablename__ = "auth_server"
    login = Column(String(), unique=True, primary_key=True)
    password = Column(String())
    ip_address = Column(String(15))
    port = Column(INTEGER, unique=True)
    is_available = Column(BOOLEAN, default=False)

    def __str__(self):
        return f"(ip={self.ip_address}, port = {self.port})"

    def __repr__(self):
        return str(self)


def create_rsa():
    random_generator = Random.new().read
    private_key = RSA.generate(2048, random_generator)
    public_key = private_key.public_key()
    return [binascii.hexlify(public_key.export_key(format="DER")).decode('ascii'), binascii.hexlify(private_key.export_key(format="DER")).decode('ascii')]


def register():
    login = input("Please input login:").encode()
    password = input("Please input password:").encode()
    login_hash = SHA3_512.new(login)
    password_hash = SHA3_512.new(password)
    ip_address = "localhost"
    port = random.randint(10000, 10005)
    u = Nodes(login=login_hash.hexdigest(), password=password_hash.hexdigest(), ip_address=ip_address, port=port, is_available=False)
    session = Session()
    session.add(u)
    session.commit()
    session.close()
    return True


def connect():
    login = input("Please input login:").encode()
    password = input("Please input password:").encode()
    login_hash = SHA3_512.new(login)
    password_hash = SHA3_512.new(password)
    session = Session()
    try:
        session.query(Nodes).filter(Nodes.login == login_hash.hexdigest()).one()
    except NoResultFound:
        print("Wrong login")
        session.close()
        return None
    else:
        try:
            session.query(Nodes).filter(Nodes.password == password_hash.hexdigest()).one()
        except NoResultFound:
            print("Wrong password")
            session.close()
            return None
        else:
            user = session.query(Nodes).filter(Nodes.login == login_hash.hexdigest())
            user.update({Nodes.is_available: True})
            session.commit()
            keys = create_rsa()
            print("Here is your private key, save it\n", keys[1])
            print("Here is your public key, save it\n", keys[0])
            print("Here is your network config:", user.one().ip_address, user.one().port)
            node = Node(user.one().ip_address, user.one().port)
            node.id = keys[0]
            node.start()
            session.close()
            return node


def get_nodes():
    session = Session()
    nodes = session.query(Nodes).filter(Nodes.is_available == True).all()
    session.close()
    return nodes


def get_connect(ip_address, port, my_node):
    session = Session()
    outbound_user = session.query(Nodes).filter(and_(Nodes.ip_address == ip_address, Nodes.port == port)).one()
    my_node.connect_with_node(outbound_user.ip_address, outbound_user.port)


def disconnect(my_node):
    session = Session()
    session.query(Nodes).filter(and_(Nodes.ip_address == my_node.host, Nodes.port == my_node.port)).update(
        {Nodes.is_available: False})
    print("Disconnected")
    my_node.stop()
    session.commit()
    session.close()


if __name__ == '__main__':
    # Base.metadata.create_all()
    # register()
    check = connect()
    if check is not None:
        print("Ok")
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
                if answer == 1:
                    users = get_nodes()
                    print(users)
                if answer == 2:
                    ip_address = input("Input address_to_connect:")
                    port = input("Input address_to_connect:")
                    get_connect(ip_address, port, check)
                if answer == 3:
                    users = get_nodes()
                    for user in users:
                        if user.ip_address != check.host and user.port != check.host:
                            get_connect(user.ip_address, user.port, check)
                if answer == 4:
                    disconnect(check)
                    break
    else:
        print("Something wrong")



