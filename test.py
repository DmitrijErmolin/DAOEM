import json
import client
import declare_server
import time
import threading
import matplotlib as plt
users = []
if __name__ == '__main__':
    with open("test1.txt", "r") as read_file:
        start = time.time()
        for line in read_file.readlines():
            s = line.split()
            user = declare_server.connect(s[2], s[3])
            clint = client.Client(user)
            users.append(clint)
        time.sleep(10)
        for user in users:
            user.get_connect_to_user()
        finish = time.time() - start
        times = [threading.active_count(), finish]
        with open("timings.txt", "a") as file:
            file.write(str(times) + '\n')









