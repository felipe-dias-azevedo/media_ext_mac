from tui import get_tui, cprint
from colors import *

def handler(text: str):
    cprint(f"{BLUE}You entered:{EBLUE}")
    cprint(f"{RED}{'-'*40}{ERED}")
    cprint(f"{BOLD}{text}{EBOLD}")
    cprint(f"{RED}{'-'*40}{ERED}")

def main():
    get_tui(handler).run()

if __name__ == "__main__":
    main()