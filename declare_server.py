from sqlalchemy import create_engine, Column, String, BOOLEAN, INTEGER, FLOAT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.expression import desc
from sqlalchemy.orm import sessionmaker, scoped_session
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA3_512
from Crypto import Random
import random
import binascii
from p2pnetwork.node import Node
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql import and_
from argparse import ArgumentParser
engine = create_engine("postgresql://postgres:dmitrij@localhost/auth_server", pool_size=100, max_overflow=0)
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
    rating = Column(FLOAT)
    id = Column(String())

    def __str__(self):
        return f"(ip={self.ip_address}, port = {self.port}, rating ={self.rating})"

    def __repr__(self):
        return str(self)


def create_rsa():
    random_generator = Random.new().read
    private_key = RSA.generate(2048, random_generator)
    public_key = private_key.public_key()
    return [binascii.hexlify(public_key.export_key(format="DER")).decode('ascii'), binascii.hexlify(private_key.export_key(format="DER")).decode('ascii')]


def register(logi=None, passw=None):
    if logi is None and passw is None:
        login = input("Please input login:").encode()
        password = input("Please input password:").encode()
    else:
        login = logi.encode()
        password = passw.encode()
    login_hash = SHA3_512.new(login)
    password_hash = SHA3_512.new(password)
    ip_address = "localhost"
    port = random.randint(10000, 11000)
    u = Nodes(login=login_hash.hexdigest(), password=password_hash.hexdigest(), ip_address=ip_address, port=port, is_available=False)
    session = Session()
    session.add(u)
    session.commit()
    session.close()
    return True


def connect(logi=None, passwd=None, serv=False):
    if not serv and logi is None and passwd is None:
        login = input("Please input login:").encode()
        password = input("Please input password:").encode()
    elif serv:
        login = "admin".encode()
        password = "admin".encode()
    else:
        login = logi.encode()
        password = passwd.encode()
    login_hash = SHA3_512.new(login)
    password_hash = SHA3_512.new(password)
    session = Session()
    try:
        session.query(Nodes).filter(Nodes.login == login_hash.hexdigest()).one()
    except NoResultFound:
        if not serv:
            print("Wrong login")
        else:
            server = Nodes(login=login_hash.hexdigest(), password=password_hash.hexdigest(), ip_address="localhost", port=49001, is_available=False)
            session.add(server)
            session.commit()
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
            keys = [str(random.randint(1, 10000000)), str(random.randint(10000001, 100000001))]
            # keys = create_rsa()
            # print("Here is your private key, save it\n", keys[1])
            # print("Here is your public key, save it\n", keys[0])
            conn_node = session.query(Nodes).filter(and_(Nodes.login == login_hash.hexdigest(), Nodes.password == password_hash.hexdigest()))
            node = Node(conn_node.one().ip_address, conn_node.one().port, keys[0])
            node.start()
            conn_node.update({Nodes.is_available: True, Nodes.id: keys[0]})
            session.commit()
            session.close()
            return node



def get_nodes(my_node, server=False):
    session = Session()
    if not server:
        nodes = session.query(Nodes).filter(and_(Nodes.is_available == True, Nodes.port != my_node.port)).all()
    else:
        query = session.query(Nodes)
        desc_xp = desc(Nodes.rating)
        nodes = query.filter(and_(Nodes.is_available == True, Nodes.rating.isnot(None))).order_by(desc_xp).all()
    session.close()
    return nodes


def get_server():
    session = Session()
    try:
        server = session.query(Nodes).filter(and_(Nodes.is_available == True, Nodes.port == 49001)).one()
    except NoResultFound:
        session.close()
        return None
    else:
        session.close()
        return server


def update_rating(node, rating):
    session = Session()
    session.query(Nodes).filter(and_(Nodes.ip_address == node.host, Nodes.port == node.port)).update({Nodes.rating: rating})
    session.commit()
    session.close()


def get_connect(ip_address, port, my_node):
    session = Session()
    outbound_user = session.query(Nodes).filter(and_(Nodes.ip_address == ip_address, Nodes.port == port)).one()
    my_node.connect_with_node(outbound_user.ip_address, outbound_user.port)
    session.close()


def disconnect(my_node):
    session = Session()
    session.query(Nodes).filter(and_(Nodes.ip_address == my_node.host, Nodes.port == my_node.port)).update(
        {Nodes.is_available: False})
    my_node.stop()
    session.commit()
    session.close()

def update(node):
    session = Session()
    session.query(Nodes).filter(and_(Nodes.ip_address == node.host, Nodes.port == node.port)).update(
        {Nodes.is_available: True})
    session.commit()
    session.close()


def disconnect_other(node, by_p2p=True):
    session = Session()
    if by_p2p:
        session.query(Nodes).filter(and_(Nodes.ip_address == node.host, Nodes.port == node.port)).update(
            {Nodes.is_available: False})
    else:
        session.query(Nodes).filter(and_(Nodes.ip_address == node.ip_address, Nodes.port == node.port)).update(
            {Nodes.is_available: False})
    session.commit()
    session.close()


if __name__ == '__main__':
    # Base.metadata.create_all()
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=490001, type=int, help='port to listen on')
    parser.add_argument('-ht', "--host", default="localhost", type=str, help="ip_address to connect")
    args = parser.parse_args()
    port = args.port
    host = args.host
    session = Session()
    try:
        session.query(Nodes).filter(Nodes.port == port).one()
    except NoResultFound:
        server = Nodes(login="admin", password="admin", ip_address="localhost", port=49001, is_available=False)
        session.add(server)
        session.commit()
        session.close()
    else:
        server = session.query(Nodes).filter(Nodes.login == "admin")
        keys = create_rsa()
        server_node = Node(host, port, keys[0])
        server_node.start()
        server.update({Nodes.is_available: True, Nodes.id: keys[0]})
        session.commit()
        session.close()
        users = get_nodes(server_node)
        for user in users:
            if user.port != server_node.host:
                get_connect(user.ip_address, user.port, server_node)
        print(server_node.nodes_outbound)











