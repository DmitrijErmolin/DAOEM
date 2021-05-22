import random
import declare_server
if __name__ == '__main__':
    letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u',
               'v', 'w', 'x', 'y', 'z', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P',
               'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
    def file(count, name_file):
        for i in range(count):
            nr_letters = random.randint(4, 10)
            login = ""
            while len(login) < nr_letters:
                login += random.choice(letters)
            print(login)
            a = f'start "" /B "C:\\Users\\dmitr\\PycharmProjects\\DAOEM_v1\\venv\\Scripts\\python.exe" "C:\\Users\\dmitr\\PycharmProjects\\DAOEM_v1\\client.py" {login} {login}'
            b = "TIMEOUT /T 2 /NOBREAK"
            with open(name_file, "a") as file:
                file.write(a + '\n' + b + '\n')
    def reg(name_file):
        with open(name_file, "r") as read_file:
            for line in read_file.readlines():
                s = line.split()
                print(s)
                if 'start' in s:
                    declare_server.register(s[5], s[6])
    # file(250, "test2.txt")
    reg("test2.txt")