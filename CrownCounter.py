try:
    import re
    from selenium import webdriver
    from selenium.common.exceptions import *
    from selenium.webdriver import ChromeOptions
    import time
    import json
    import sys
    import random
    from os import mkdir
    from os.path import exists
    from pytesseract.pytesseract import TesseractNotFoundError
    from threading import Thread
    from requests import ConnectionError
    from _thread import start_new_thread
    from CaptchaSolve import CaptchaSolver
    from PIL import Image
    from PIL import UnidentifiedImageError
except ModuleNotFoundError:
    print("Couldn't find one of the required modules... run setup.bat then restart")
    sys.exit()


def main():
    def create_config():
        """
        Creates a default config.txt
        """
        with open("config.txt", "w") as config_file:
            config_data = {
                "threads": 1,
                "tesseract.exe_path": "C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
                "headless (Y/N)": "N"
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
        sys.exit()

    """
    We read the previously defined config_json set to find the thread count
    and the tesseract path defined by the user
    """
    try:
        num_threads = config_json.get("threads")
        tess_path = config_json.get("tesseract.exe_path")
        headless = config_json.get("headless (Y/N)").replace(",", "").replace(" ", "").lower() == "y"
    except (KeyError, AttributeError):
        print("Config.txt wasn't configured properly... recreating it")
        create_config()
        input("Press any key to exit...")
        sys.exit()
    all_threads = []
    chrome_options = ChromeOptions()
    chrome_options.add_extension('VPN/3.9.8_0.crx')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    if headless:
        chrome_options.add_argument("--headless")

    action_available = True
    default_await = .3
    default_notify = max(3, 10 / num_threads)

    def await_freedom(await_time=default_await):
        while not action_available:
            time.sleep(default_await)

    def notify_input(notify_time=default_notify):
        def helper():
            global action_available
            action_available = False
            time.sleep(notify_time)
            action_available = True
        start_new_thread(helper, ())

    def await_and_notify(await_time=default_await, notify_time=default_notify):
        await_freedom(await_time=await_time)
        notify_input(notify_time=notify_time)

    def start_vpn(driver, country_id):
        driver.get("chrome-extension://oofgbpoabipfcfjapgnbbjjaenockbdp/popup.html")
        time.sleep(5)
        while True:
            try:

                time.sleep(2)
                driver.execute_script("""
                                        for (const a of document.querySelectorAll("a")) {
                                            if (a.textContent.includes("English")) {
                                                a.click();
                                                break;
                                            }
                                        }
                                    """)
                break
            except JavascriptException:
                pass
        while True:
            try:

                time.sleep(2)
                driver.execute_script("""
                                        let reg = document.getElementById("register-button");
                                        reg.click();
                                    """)
                break
            except JavascriptException:
                pass
        while True:
            try:
                driver.execute_script("""
                                        let lic = document.getElementById("eula-label");
                                        let term = document.getElementById("terms-label");
                                        let priv = document.getElementById("pp-label");        
                                        lic.click();
                                        term.click();
                                        priv.click();

                                        let regtwo = document.getElementById("create-authcode");
                                        regtwo.click();
                                    """)
                break
            except JavascriptException:
                pass
        while True:
            try:
                time.sleep(2)
                driver.execute_script("""
                                        let start = document.getElementById("login-with-authcode");
                                        start.click();
                                    """)
                break
            except JavascriptException:
                pass
        while True:
            try:
                time.sleep(2)
                driver.execute_script("""
                                        let countryTag;
                                        switch (arguments[0]) {
                                            case 0:
                                                countryTag = "0ua";
                                                break;
                                            case 1:
                                                countryTag = "0ca";
                                                break;
                                            case 2:
                                                countryTag = "0gb";
                                                break;
                                            case 3:
                                                countryTag = "0fr";
                                                break;
                                            case 4:
                                                countryTag = "0it";
                                                break;
                                            case 5:
                                                countryTag = "0de";
                                                break;
                                        }
                                        let countryElem = document.getElementById(countryTag);
                                        countryElem.click();
                                        """, country_id)
                break
            except JavascriptException:
                pass

    class CrownCounter(Thread):
        LOGIN_URL = r"https://www.wizard101.com/auth/wizard/login.theform"
        LOGOUT_URL = r"https://www.wizard101.com/auth/logout/game?redirectUrl=https%3A%2F%2Fwww.wizard101.com%2Fgame"
        QUARANTINED_URL = r"https://www.wizard101.com/auth/wizard/quarantinedlogin.theform"
        CAPTCHA_URL = r"https://www.wizard101.com/Captcha?mode=ua&ts=1591424465802"
        CROWNS_URL = r"https://www.wizard101.com/user/kiaccounts/summary/game?context=am"
        solver = CaptchaSolver(tess_path)
        crowns_regex = re.compile(r'class="crownsbalance"><b>([\d,]+)<\/b>')

        WAIT = 0
        TESS_UNFOUND = 1
        CROWNS_UNFOUND = 2
        NUM_COUNTERS = 0

        def __init__(self, driver):
            super().__init__()
            self.driver = driver
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

        def many_requests(self):
            value = "Too Many Requests" in self.driver.page_source
            if value:
                print("Too many requests... sleeping")
                time.sleep(15)
            return value

        def run(self):
            while not self.last_account:
                if (not self.finished) and (self.current_account != CrownCounter.WAIT):
                    loginsplit = self.current_account.split(":")
                    if not len(loginsplit) == 2:
                        curr_text = f"Account: {self.current_account} wasn't formatted correctly"
                    else:
                        username = loginsplit[0]
                        password = loginsplit[1]
                        crowns = self.get_crowns_bal(username, password)
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

        def log_out(self):
            await_and_notify()
            self.driver.get(CrownCounter.LOGOUT_URL)

        def run_account(self, account):
            self.current_account = account
            self.finished = False

        def get_crowns_bal(self, username, password):
            def login(username: str, password: str):
                """
                Logs in an account
                :param username:
                :param password:
                """
                self.username = username

                def enter_credentials():
                    """
                    Enters credentials and presses login
                    """
                    await_and_notify()
                    self.driver.get(CrownCounter.LOGIN_URL)
                    if self.many_requests():
                        return enter_credentials()
                    await_and_notify()
                    try:
                        self.driver.execute_script("""
                            let username = arguments[0];
                            let password = arguments[1];
                            let userElem = document.getElementById("userName");
                            let passElem = document.getElementsByName("password")[0];
                            userElem.value = username;
                            passElem.value = password;
                            let enterButton = document.getElementById("bp_login");
                            enterButton.click();
                        """, username, password)
                    except JavascriptException:
                        time.sleep(1)
                        return enter_credentials()
                    while self.driver.current_url == CrownCounter.LOGIN_URL:
                        time.sleep(1)
                    if self.many_requests():
                        return enter_credentials()

                def handle_login_captcha():
                    """
                    Handles the possibility of a login captcha
                    """
                    try:
                        captcha_element = self.driver.find_element_by_id("captchaImage")
                    except NoSuchElementException:
                        return
                    if not exists("screenshots"):
                        mkdir("screenshots")
                    self.driver.save_screenshot(f"screenshots/login_screenshot{self.id}.png")
                    captcha_location = captcha_element.location
                    # KI captchas have a standard width of 230px and height of 50px
                    captcha_width = 230
                    captcha_height = 50
                    # Captcha location in screenshot, bot left in x1, y1 and top right in x2, y2
                    bot_x, bot_y = captcha_location.get("x"), captcha_location.get("y")
                    top_x, top_y = (captcha_location.get("x") + captcha_width), (
                                captcha_location.get("y") + captcha_height)
                    screenshot = Image.open(f"screenshots/login_screenshot{self.id}.png")
                    # The screenshot image will have to crop out the section containing the captcha to get the captcha image
                    captcha = screenshot.crop((bot_x, bot_y, top_x, top_y))
                    captcha_solution = CrownCounter.solver.resolve(captcha)

                    await_and_notify()
                    self.driver.execute_script("""
                        let captchaField = document.getElementById("captcha");
                        captchaField.value = arguments[0];
                        let enterButton = document.getElementById("login");
                        enterButton.click();
                    """, captcha_solution)
                    if self.many_requests():
                        return attempt_login()

                    QUARANTINED_URL = r"https://www.wizard101.com/auth/wizard/QuarantinedLogin" \
                                      r"/8ad6a4041b4fd6c1011b5160b0670010?fpRedirectUrl=https%3A%2F%2Fwww.wizard101.com" \
                                      r"%2Fgame&reset=1&fpPopup=1"
                    OTHER_QUARANTINED_URL = r"https://www.wizard101.com/auth/wizard/quarantinedlogin" \
                                            r"/8ad6a4041b4fd6c1011b5160b0670010"

                    while self.driver.current_url == QUARANTINED_URL or self.driver.current_url == OTHER_QUARANTINED_URL:
                        attempt_login()

                def attempt_login():
                    enter_credentials()
                    await_and_notify()
                    handle_login_captcha()

                attempt_login()

            def find_crowns(num_attempts=1):
                await_and_notify()
                self.driver.get(CrownCounter.CROWNS_URL)
                try:
                    balance = CrownCounter.crowns_regex.search(self.driver.page_source).group(1)
                except AttributeError:
                    if num_attempts != 4:
                        time.sleep(15)
                        login(username, password)
                        return find_crowns(num_attempts=num_attempts + 1)
                    return CrownCounter.CROWNS_UNFOUND
                self.log_out()
                return int(balance.replace(",", ""))

            login(username, password)
            time.sleep(5)
            return find_crowns()
        def quit_driver(self):
            self.driver.quit()
    
    driver_info = {
        "started": 0,
        "finished": 0
    }
    def create_thread(info=driver_info):
        driver = webdriver.Chrome(options=chrome_options)
        info["started"] += 1
        start_vpn(driver, (info["started"] - 1) % 6)
        all_threads.append(CrownCounter(driver))
        info["finished"] += 1


    print("Creating drivers...")
    for thread in range(num_threads):
        """
        We will create a new CounterThread and 
        store it in the all_threads list for each thread defined by the user
        """
        start_new_thread(create_thread, ())
    while driver_info["finished"] != num_threads:
        time.sleep(1)

    def quit_drivers():
        for thread in all_threads:
            start_new_thread(thread.quit_driver, ())

    for thread in all_threads:
        thread.start()

    for account in accounts:
        """
        We create a found_assignment variable that tracks whether this account has yet been allocated to a thread
        If it isn't allocated to a thread yet, the main thread will sleep then try to allocate it to a thread again
        """
        found_assignment = False
        while not found_assignment:
            desired_assignment = all_threads[random.randint(0, num_threads-1)]
            """
            The thread.finished variable determines whether a thread has finished its current account
            If it has finished its current account, we will designate it the current account in the loop,
            and break to the next loop to designate a thread to the next account
            """
            if desired_assignment.tess_unfound:
                print("Tesseract path was invalid in config.txt. Delete config to restore defaults")
                quit_drivers()
                input("Press enter to exit...")
                sys.exit()
            if desired_assignment.finished:
                desired_assignment.run_account(account)
                found_assignment = True
                break
            time.sleep(2)
        time.sleep(5)

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
    quit_drivers()
    input("\nPress enter to exit...")
    sys.exit()


if __name__ == "__main__":
    main()
