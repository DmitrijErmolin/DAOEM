import time


class RatingBase:
    def __init__(self, name):
        self.name = name
        self.parameters = dict()
        self.parameters['default'] = 0.0
        self.user_rating = 0.0
        self.parameters['rang'] = 'Common user'
        self.parameters['precision_per_active'] = 0.001
        self.parameters['precision_per_generate'] = 0.5
        self.parameters['precision_per_git'] = 1
        self.parameters['superuser'] = False
        self.parameters['up_limit_to_super_user'] = 5.0
        self.parameters['up_limit_to_all_user'] = 10
        self.parameters['down_limit_to_all_user'] = 0

    def __str__(self):
        return f"(user_rating={self.user_rating} superuser = {self.parameters['superuser']})"

    def __repr__(self):
        return str(self)

    def update_user_rating_per_gen(self, down_rate=False):
        if not down_rate:
            self.user_rating += self.parameters['precision_per_generate']
            self.check_limits()
        else:
            self.user_rating -= self.parameters['precision_per_generate']
            self.check_superuser()
            self.check_limits()

    def update_user_rating_per_active(self, time_delta, down_rate=False):
        time_delta = round(time_delta, 1)
        if not down_rate:
            self.user_rating = self.user_rating + self.parameters['precision_per_active'] * time_delta
            self.check_limits()
        else:
            self.user_rating = self.user_rating - self.parameters['precision_per_active'] * time_delta
            self.check_superuser()
            self.check_limits()

    def update_user_rating_per_git(self, down_rate=False):
        if not down_rate:
            self.user_rating += self.parameters['precision_per_generate']
            self.check_superuser()
            self.check_limits()
        else:
            self.user_rating -= self.parameters['precision_per_generate']
            self.check_superuser()
            self.check_limits()

    def check_superuser(self):
        if self.user_rating > self.parameters['up_limit_to_super_user'] and not self.parameters['superuser']:
            self.become_superuser()
        if self.user_rating < self.parameters['up_limit_to_super_user'] and self.parameters['superuser']:
            self.stop_superuser()

    def check_limits(self):
        if self.user_rating > self.parameters['up_limit_to_super_user'] and not self.parameters['superuser']:
            self.user_rating = self.parameters['up_limit_to_super_user']
        if self.user_rating > self.parameters['up_limit_to_all_user'] and self.parameters['superuser']:
            self.user_rating = self.parameters['up_limit_to_all_user']
        if self.user_rating < self.parameters['down_limit_to_all_user']:
            self.user_rating = self.parameters['down_limit_to_all_user']
        round(self.user_rating, 3)
        #todo fix float

    def become_superuser(self):
        self.parameters['superuser'] = True

    def stop_superuser(self):
        self.parameters['superuser'] = False




if __name__ == '__main__':
    pass
    # start = time.time()
    # time.sleep(1)
    # time_d = time.time() - start
    # test = RatingBase("12")
    # print(test)
    # test.update_user_rating_per_active(time_d)
    # print(test)
    # print()
    # for i in range(20):
    #     test.update_user_rating_per_gen()
    #     print(test)
    # test.become_superuser()
    # for i in range(20):
    #     test.update_user_rating_per_gen()
    #     print(test)
    # for i in range(25):
    #     test.update_user_rating_per_gen(down_rate=True)
    #     print(test)











