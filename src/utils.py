import sys


def do_you_want_to_continue():
    cont = input("Do you want to continue? yes/no > ")
    while cont.lower() not in ("yes", "no"):
        cont = input("Do you want to continue? yes/no ")
    if cont == "no":
        sys.exit()


class WaitingEffect:
    def __init__(self, text):
        self.text = text
        self.position = 0
        self.list = ['|', '/', '-', '\\']

    def run(self, end=False):
        if end:
            sys.stdout.write('\r{}\r\n'.format(self.text + " OK"))
        else:
            sys.stdout.write('\r{}'.format(self.text + " " + self.list[self.position]))
            self.position += 1
            if self.position > 3:
                self.position = 0
        sys.stdout.flush()
