import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
import json
import numpy as np
if __name__ == '__main__':
    x = []
    y = []
    z = []
    d = []
    with open("voting_time.txt", "r") as read_file:
        for line in read_file.readlines():
            s = line.split()
            x.append(int(round(float(s[1]))))
            y.append(int(round(float(s[0]))))
    with open("voting_time2.txt", "r") as read_file:
        for line in read_file.readlines():
            s = line.split()
            d.append(int(round(float(s[1]))))
            z.append(int(round(float(s[0]))))
    fig = plt.figure()
    f1 = interp1d(x, y, kind='cubic')
    xnew = np.linspace(2, 10, num=41, endpoint=True)
    time = fig.add_subplot(2, 1, 1)
    time.plot(x, y, 'o', xnew, f1(xnew), '--')
    time.set_ylabel("Время голосования")
    time.set_xlabel("Процент проверяющих нод от общего кол-ва пользователей")
    time.set_title("Зависимость общего времени голосования от кол-ва проверяющих нод")
    time.legend(['data'], loc='best')
    f2 = interp1d(d, z, kind='cubic')
    xnew_1 = np.linspace(24, 71, num=41, endpoint=True)
    time = fig.add_subplot(2, 1, 2)
    time.plot(d, z, 'o', xnew_1, f2(xnew_1), '--')
    time.set_ylabel("Время голосования")
    time.set_xlabel("Кол-во транзакций в блоке")
    time.set_title("Зависимость общего времени голосования от кол-ва проверяющих нод")
    time.legend(['data'], loc='best')
    plt.show()


