import sys


def do_you_want_to_continue():
    cont = input("Do you want to continue? yes/no > ")
    while cont.lower() not in ("yes", "no"):
        cont = input("Do you want to continue? yes/no ")
    if cont == "no":
        sys.exit()
