import rating
import declare_server
import time
import datetime


class Client:
    def __init__(self, node):
        self.node = node
        self.rating = rating.RatingBase()
        self.work_time = time.time()

    def __str__(self):
        return f"(node={self.node.host}, port = {self.node.port})"

    def __repr__(self):
        return str(self)

    def get_time(self, start_time):
        end_time = time.time()
        return round(end_time - start_time)


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
                            answer = int(input('''
                            Press 1 to get all nodes \n
                            Press 2 to connect\n
                            Press 3 to get_all_connect\n
                            Press 4 to disconnect \n
                            5 get time
                            6 
                            '''))
                        except ValueError:
                            print("Invalid input")
                        else:
                            if answer == 1:
                                users = declare_server.get_nodes()
                                print(users)
                            if answer == 2:
                                ip_address = input("Input address_to_connect:")
                                port = input("Input address_to_connect:")
                                declare_server.get_connect(ip_address, port, client.node)
                            if answer == 3:
                                users = declare_server.get_nodes()
                                for user in users:
                                    if user.ip_address != client.node.host and user.port != client.node.host:
                                        declare_server.get_connect(user.ip_address, user.port, client.node)
                            if answer == 4:
                                declare_server.disconnect(client.node)
                                break
                            if answer == 5:
                                work_time = client.get_time(client.work_time)
                                print("You are in the system for ", str(datetime.timedelta(seconds=work_time)))
                            if answer == 6:
                                work_time = client.get_time(client.work_time)
                                client.rating.update_user_rating_per_active(work_time)
                                print(client.rating.user_rating)
                                declare_server.update_rating(client.node, client.rating.user_rating)
            elif answer == 3:
                break

