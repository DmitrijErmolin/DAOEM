from sqlalchemy import create_engine, Column, String, BOOLEAN, INTEGER, FLOAT
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
    rating = Column(FLOAT)

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
    #TODO #add check exicting login
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


def update_rating(node, rating):
    session = Session()
    session.query(Nodes).filter(and_(Nodes.ip_address == node.host, Nodes.port == node.port)).update({Nodes.rating: rating})
    session.commit()
    session.close()


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




