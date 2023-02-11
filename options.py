import argparse


def get_option():
    parser = argparse.ArgumentParser()
    parser.add_argument("filename")
    parser.add_argument("-v", "--verbose", nargs="?", const=True, default=False)
    parser.add_argument("-d", "--debug", nargs="?", const=True, default=False)
    parser.add_argument("-g", "--gameinfo", nargs="?", const=True, default=False)
    args = parser.parse_args()

    return vars(args)


if __name__ == "__main__":
    print(get_option())
