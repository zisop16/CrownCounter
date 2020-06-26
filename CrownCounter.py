try:
    import re
    import requests
    import time
    import json
    from os import mkdir
    from os.path import exists
    from pytesseract.pytesseract import TesseractNotFoundError
    from threading import Thread
    from requests import ConnectionError

    from CaptchaSolve import CaptchaSolver
    from PIL import Image
    from PIL import UnidentifiedImageError
except ModuleNotFoundError:
    print("Couldn't find one of the required modules... run setup.bat then restart")
    quit()


class CrownCounter(Thread):
    LOGIN_URL = "https://www.wizard101.com/auth/wizard/login.theform"
    QUARANTINED_URL = "https://www.wizard101.com/auth/wizard/quarantinedlogin.theform"
    CAPTCHA_URL = "https://www.wizard101.com/Captcha?mode=ua&ts=1591424465802"
    CROWNS_URL = "https://www.wizard101.com/user/kiaccounts/summary/game?context=am"
    crowns_regex = re.compile(r'class="crownsbalance"><b>([\d,]+)<\/b>')

    WAIT = 0
    TESS_UNFOUND = 1
    CROWNS_UNFOUND = 2
    NUM_COUNTERS = 0

    def __init__(self):
        super().__init__()
        self.finished = True
        self.last_account = False
        self.tess_unfound = False
        self.current_account = CrownCounter.WAIT
        self.account_info = {}
        self.total_crowns = 0
        self.energy_elixirs = 0
        self.packs_199 = 0
        self.packs_299 = 0
        self.packs_399 = 0
        self.packs_499 = 0
        self.packs_599 = 0
        self.id = CrownCounter.NUM_COUNTERS
        CrownCounter.NUM_COUNTERS += 1

    def run(self):
        while not self.last_account:
            if (not self.finished) and (self.current_account != CrownCounter.WAIT):
                loginsplit = self.current_account.split(":")
                if not len(loginsplit) == 2:
                    curr_text = f"Account: {self.current_account} wasn't formatted correctly"
                else:
                    username = loginsplit[0]
                    password = loginsplit[1]
                    with requests.Session() as connection:
                        crowns = self.get_crowns_bal(connection, username, password)
                        if crowns == CrownCounter.TESS_UNFOUND:
                            self.tess_unfound = True
                            return
                        elif crowns == CrownCounter.CROWNS_UNFOUND:
                            curr_text = f"Couldn't find crowns for account: {self.current_account}"
                        else:
                            self.total_crowns += crowns
                            self.energy_elixirs += crowns // 250
                            self.packs_199 += crowns // 199
                            self.packs_299 += crowns // 299
                            self.packs_399 += crowns // 399
                            self.packs_499 += crowns // 499
                            self.packs_599 += crowns // 599
                            curr_text = f"Account: {username} had {crowns} crowns"
                print(curr_text)
                self.account_info[self.current_account] = curr_text
                self.finished = True
            time.sleep(1)

    def run_account(self, account):
        self.current_account = account
        self.finished = False

    def get_crowns_bal(self, connection, username, password):
        def login():
            login_data = {
                "userName": username,
                "password": password,
                # Necessary string in order to show KI that we're submitting a login
                "t:formdata": "H4sIAAAAAAAAAJXRvUoDQRAH8E0wEkiniPiFFrHda0yhNqYRxUOEEAu7vdvxsslmd93Z804LW9/"
                              "CJxBrrVPY+Q4+gG0qC/cCEeQkYrMLwzDz4z+PH6SWbZINlrpekIlbZnkQ6kSoPQtcWIhdaiVacqBtQplhcQ+oYwbQ"
                              "2ZsWjbUFKSL/D41WoBzSI8E5qOaZ1TEgdtJoKBCFVhf3W4v52vN8lVRC0oi1clbLUzYERxbCPrtmgWQqCTrOCpXs5"
                              "8aRxlTQtTJbJ6tlYopglR/hfa2Zvogh0Hbkiyx2hwIkb3bApWa7O2q8L71+llBX5I5UCkS92FFU/hS0/ysoRTR64j"
                              "uX44e3KiG5+X2fYYiZthwL4JznTQuz24vuerZClsstsng9f9ffkA589ihQAs3gx1UnSBcKNSizX04G/fNQjSch1lw"
                              "Pjvl3fLXJ+C8uOCzhZQIAAA==",
            }

            print("Logging in...")
            try:
                with connection.post(CrownCounter.LOGIN_URL, data=login_data) as res:
                    login_page = res.text
                    quarantined = "quarantined" in login_page
                    many_reqs = "Too Many Requests" in login_page
            except ConnectionError:
                time.sleep(2)
                return login()
            if many_reqs:
                print("Too many requests... sleeping")
                time.sleep(15)
                return login()

            if quarantined:
                def solve_captcha():
                    print("Solving captcha...")
                    captcha_dir = "captcha"
                    def write_captcha():
                        with connection.get(CrownCounter.CAPTCHA_URL) as captcha_page:
                            if not exists(captcha_dir):
                                mkdir(captcha_dir)
                            with open(f"{captcha_dir}/CaptchaImage{self.id}.png", "wb") as captcha_file:
                                captcha_file.write(captcha_page.content)
                    write_captcha()
                    while True:
                        try:
                            captcha_img = Image.open(f"{captcha_dir}/CaptchaImage{self.id}.png")
                            break
                        except UnidentifiedImageError:
                            time.sleep(10)
                            write_captcha()
                    try:
                        captcha_solution = CrownCounter.solver.resolve(captcha_img)
                    except TesseractNotFoundError:
                        return CrownCounter.TESS_UNFOUND

                    captcha_data = {
                        "captcha": captcha_solution,
                        "t:formdata": "H4sIAAAAAAAAAJ2RsUoDQRCGJwdRIZ1iITYiEUTkrjGNNgZBFA5RjjR2c7vjZWVv99zd86KFleA"
                                      "z2PgEYqVgn8LOd/ABbCysLLwcSSGBQGzmh2Hg+/jn8RPqxQasY+66QSGu0fDgJEeDyglFPNSJUNuGuDDEXG6kNbCr"
                                      "TeJjhqxLvsOMrDNXLZ9pQ1LEZaaZVqSc9Q8E56Sax0YzsjbK41RYK7Q6vVtZ6C2/znhQC6HBtHJGyyNMycF8eI6XG"
                                      "EhUSRA5I1Sy08scNEYGHSMLHzYn2jLMHOuiP8zSuDXROEZLfjsul8jcviDJmxG5PFvr9Bsfi28/Y5oXcAO1gdbsEP"
                                      "EPpfa0SmMt9p/41tn3w7sH0MuKJqxONJCDOc3zKpAbx95HX0svz7d7HnghzDEpyutDXlVStkSS0nLxp6V6xR7lLwg"
                                      "o+KJxAgAA",
                    }

                    with connection.post(CrownCounter.QUARANTINED_URL, captcha_data) as res:
                        result_page = res.text
                        quarantined = "quarantined" in result_page
                        many_reqs = "Too Many Requests" in login_page
                    if quarantined:
                        solve_captcha()
                    if many_reqs:
                        print("Too many requests... sleeping")
                        time.sleep(15)
                        return self.get_crowns_bal(connection, username, password)
                solve_captcha()

        def find_crowns(num_attempts=1):
            with connection.get(CrownCounter.CROWNS_URL) as res:
                raw_text = res.text
                try:
                    balance = CrownCounter.crowns_regex.search(raw_text).group(1)
                except AttributeError:
                    if num_attempts != 4:
                        time.sleep(15)
                        login()
                        return find_crowns(num_attempts=num_attempts + 1)
                    return CrownCounter.CROWNS_UNFOUND
            return int(balance.replace(",", ""))

        login()
        return find_crowns()


def main():
    def create_config():
        """
        Creates a default config.txt
        """
        with open("config.txt", "w") as config_file:
            config_data = {
                "threads": 1,
                "tesseract.exe_path": "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
            }
            config_json = json.dumps(config_data, indent=4, sort_keys=True)
            config_file.write(config_json)

    FILE_ERROR = False
    try:
        with open("accounts.txt", "r") as accounts_file:
            accounts = accounts_file.read().split("\n")
    except FileNotFoundError:
        with open("accounts.txt", "w") as accounts_file:
            accounts_file.write("")
            print("Created an accounts.txt. Rerun the program with your accounts formatted properly")
            FILE_ERROR = True
    try:
        with open("config.txt", "r") as config_file:
            # Define a config_json variable that will store the json's options for later use
            config_json = json.loads(config_file.read())
    except FileNotFoundError:
        print("Created a config.txt. Rerun the program with your options configured in the config")
        create_config()
        FILE_ERROR = True

    # If there was a error finding a file, the program will exit so the user can adjust their settings
    if FILE_ERROR:
        input("Press any key to exit...")
        quit()

    """
    We read the previously defined config_json set to find the thread count
    and the tesseract path defined by the user
    """
    try:
        num_threads = config_json.get("threads")
        tess_path = config_json.get("tesseract.exe_path")
    except KeyError:
        print("Config.txt wasn't configured properly... recreating it")
        create_config()
    CrownCounter.solver = CaptchaSolver(tess_path)
    all_threads = []

    for thread in range(num_threads):
        """
        We will create a new CounterThread and 
        store it in the all_threads list for each thread defined by the user
        """
        new_thread = CrownCounter()
        all_threads.append(new_thread)
        # Starting each thread will tell it to start looking for accounts to solve, by calling the run function
        new_thread.start()

    for account in accounts:
        """
        We create a found_assignment variable that tracks whether this account has yet been allocated to a thread
        If it isn't allocated to a thread yet, the main thread will sleep then try to allocate it to a thread again
        """
        found_assignment = False
        while not found_assignment:
            for thread in all_threads:
                """
                The thread.finished variable determines whether a thread has finished its current account
                If it has finished its current account, we will designate it the current account in the loop,
                and break to the next loop to designate a thread to the next account
                """
                if thread.tess_unfound:
                    print("Tesseract path was invalid in config.txt. Delete config to restore defaults")
                    input("Press enter to exit...")
                    quit()
                if thread.finished:
                    thread.run_account(account)
                    found_assignment = True
                    break
            time.sleep(2)

    # This wait is necessary to prevent the program going too fast and forgetting to join together
    # I really dont have a clue why. I probably did something wrong
    time.sleep(5)

    for thread in all_threads:
        """
        We tell each thread that they are on their last account, so they should exit the while loop
        Then we wait for the threads to finish by calling join
        """
        thread.last_account = True
        thread.join()

    """
    Each thread stores an account_info set that contains the output text for each account,
    And uses the account as "User:Pass" for a key
    Therefore we create a set that will contain all the other sets, so that we can print to the
    Output.txt in the original order designated by the accounts.txt
    """
    all_account_info = {}
    # The output_text variable stores what will be written to output.txt
    output_text = ""
    """
    We create the total crowns, packs, and elixirs variables, and calculate them by adding up the values
    Calculated by each individual thread
    """
    total_crowns = 0
    packs_199 = 0
    packs_299 = 0
    packs_399 = 0
    packs_499 = 0
    packs_599 = 0
    energy_elixirs = 0
    """
    We now loop through each CrownCounter and add up all the values they've stored previously
    """
    for thread in all_threads:
        curr_info = thread.account_info
        """
        We must take the current thread's account info that contains the output text, and store it in the larger set
        """
        for key in curr_info:
            all_account_info[key] = curr_info[key]
        total_crowns += thread.total_crowns
        packs_199 += thread.packs_199
        packs_299 += thread.packs_299
        packs_399 += thread.packs_399
        packs_499 += thread.packs_499
        packs_599 += thread.packs_599
        energy_elixirs += thread.energy_elixirs

    """
    We now loop through the accounts in the original order designated by accounts.txt, 
    And add the output_text associated with each account, in the correct order
    """
    for num, account in enumerate(accounts):
        output_text += f"{num}: {all_account_info[account]}\n"

    """
    We do some formatting so that we can create fancy text to print that shows the purchaseable packs
    We store it into curr_text so it can be added to output_text
    """
    curr_text = f"""
Total Crowns: {total_crowns}

Purchaseable 199 packs: {packs_199}
Purchaseable 299 packs: {packs_299}
Purchaseable 399 packs: {packs_399}
Purchaseable 599 packs: {packs_599}
Purchaseable Energy elixirs: {energy_elixirs}"""
    print(curr_text)
    output_text += curr_text

    # We now write output_text to the output_file, as originally intended
    with open("output.txt", "w") as output_file:
        output_file.write(output_text)
    input("\nPress enter to exit...")
    quit()


if __name__ == "__main__":
    main()
