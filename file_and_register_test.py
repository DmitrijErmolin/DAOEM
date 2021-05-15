import json
import declare_server
if __name__ == '__main__':
    def file_and_reg(count, name_file):
        for i in range(count):
            a = json.dumps({'login': chr(i+count), 'password': chr(i+count)})
            with open(name_file, "a") as file:
                file.write(a + '\n')
        with open(name_file, "r") as read_file:
            for line in read_file.readlines():
                s = json.loads(line)
                declare_server.register(s.get('login'), s.get('password'))


    file_and_reg(30, "test.txt")
    # file_and_reg(45, "test.txt")
    # file_and_reg(60, "test.txt")
    # file_and_reg(85, "test.txt")
    # file_and_reg(100, "test.txt")
