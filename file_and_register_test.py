import json
import declare_server
if __name__ == '__main__':
    for i in range(10):
        a = json.dumps({'login': chr(97+i), 'password': chr(97+i)})
        with open("test.txt", "a") as file:
            file.write(a + '\n')
    with open("test.txt", "r") as read_file:
        for line in read_file.readlines():
            s = json.loads(line)
            declare_server.register(s.get('login'), s.get('password'))