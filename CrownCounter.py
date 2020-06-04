import time
import os
import json
import threading

try:
    from threading import Thread
    from PIL import Image
    from selenium import webdriver
    from selenium.common.exceptions import NoSuchElementException
    from selenium.webdriver.chrome.options import Options
    from pytesseract.pytesseract import TesseractNotFoundError
except ModuleNotFoundError:
    print("Couldn't find one of the necessary modules. Please install requirements using setup.bat")
    quit()

from CaptchaSolve import CaptchaSolver


class CrownCounter():
    drivers = []
    def __init__(self, captcha_solver, driver):
        self.solver = captcha_solver
        self.driver = driver
        self.account_info = {}
        self.total_crowns = 0
        self.packs_199 = 0
        self.packs_299 = 0
        self.packs_399 = 0
        self.packs_599 = 0
        self.energy_elixirs = 0
        self.ID = len(CrownCounter.drivers)
        CrownCounter.drivers.append(self.driver)

    def enter_credentials(self, username, password):
        """
        Logs in to the account and possibly goes to the captcha page
        :param username:
        :param password:
        :return:
        """
        #This is the login page
        login_url = "https://www.wizard101.com/auth/wizard/login.theform"
        self.driver.get(login_url)
        #If we get redirected to wizard101.com, then wiz was offline
        if self.driver.current_url == "https://www.wizard101.com/":
            return WIZ_OFFLINE
        #If there was a too many requests page, we will wait then recursively call the function again
        if self.too_many_reqs():
            time.sleep(15)
            self.enter_credentials(username, password)
            return

        #Enter the username into the user name field of the login page
        user_field = self.driver.find_element_by_xpath(r"/html/body/table/tbody/tr[2]/td[2]/form/table[1]/tbody/tr["
                                                       r"1]/td[2]/input")
        user_field.clear()
        user_field.send_keys(username)
        #Enter the password into the password field of the login page
        pass_field = self.driver.find_element_by_xpath(r"/html/body/table/tbody/tr[2]/td[2]/form/table[1]/tbody/tr["
                                                       r"2]/td[2]/input")
        pass_field.clear()
        pass_field.send_keys(password)
        #Click the enter button to log in
        enter_button = self.driver.find_element_by_xpath(r"/html/body/table/tbody/tr[2]/td[2]/form/table["
                                                         r"2]/tbody/tr/td[2]/a")
        enter_button.click()

    def attempt_captcha(self, username, password):
        """
        Attempts the current captcha assuming the driver is at the captcha page
        """
        #If there is a too many requests page, we wait 15 seconds and recursively call the function again
        if self.too_many_reqs():
            time.sleep(15)
            enter_cred = self.enter_credentials(username, password)
            self.attempt_captcha(username, password)
            return
        #Because there are two possible captcha urls, there are two possible xpaths for each distinct site
        try:
            captcha_element = self.driver.find_element_by_xpath(r"/html/body/table/tbody/tr[2]/td[2]/form/div["
                                                                r"3]/div/table/tbody/tr[1]/td[3]/div/img")
        except NoSuchElementException:
            captcha_element = self.driver.find_element_by_xpath(r"/html/body/table/tbody/tr[2]/td[2]/form/div["
                                                                r"4]/div/table/tbody/tr[1]/td[3]/div/img")
        #We create the screenshot directory if it didn't already exist
        if not os.path.isdir("screenshots"):
            os.mkdir("screenshots")
        #Screenshots are stored in the screenshot directory, and labelled according to the Counter's ID
        self.driver.save_screenshot("screenshots\\screenshot%i.png" % self.ID)
        captcha_location = captcha_element.location
        #KI captchas have a standard width of 230px and height of 50px
        captcha_width = 230
        captcha_height = 50
        #Captcha location in screenshot, bot left in x1, y1 and top right in x2, y2
        bot_left = captcha_location.get("x"), captcha_location.get("y")
        top_right = (captcha_location.get("x") + captcha_width), (captcha_location.get("y") + captcha_height)
        screenshot = Image.open("screenshots\\screenshot%i.png" % self.ID)
        #The screenshot image will have to crop out the section containing the captcha to get the captcha image
        captcha = screenshot.crop((bot_left[0], bot_left[1], top_right[0], top_right[1]))
        try:
            captcha_solution = self.solver.resolve(captcha)
        except TesseractNotFoundError():
            return TESS_UNFOUND

        #Again, two possible xpaths for the captcha entering field
        try:
            captcha_field = self.driver.find_element_by_xpath(r"/html/body/table/tbody/tr[2]/td[2]/form/div["
                                                              r"3]/div/table/tbody/tr[2]/td[3]/div/input")
        except NoSuchElementException:
            captcha_field = self.driver.find_element_by_xpath(r"/html/body/table/tbody/tr[2]/td[2]/form/div["
                                                              r"4]/div/table/tbody/tr[2]/td[3]/div/input")

        #Enters the captcha solution and clicks the login button
        captcha_field.clear()
        captcha_field.send_keys(captcha_solution)
        enter_button = self.driver.find_element_by_xpath(r"/html/body/table/tbody/tr[2]/td[2]/form/table["
                                                         r"1]/tbody/tr/td/div/div/input")
        enter_button.click()

    def attempt_login(self, username, password):
        """
        Attemps to log in to the account\n
        :param username:
        :param password:
        """
        enter_cred = self.enter_credentials(username, password)
        if enter_cred == WIZ_OFFLINE:
            return WIZ_OFFLINE
        time.sleep(.2)
        wiz_url = "https://www.wizard101.com/game"
        if self.driver.current_url != wiz_url:
            captcha_attempt = self.attempt_captcha(username, password)
            if captcha_attempt == TESS_UNFOUND:
                return TESS_UNFOUND
            time.sleep(.3)

    def too_many_reqs(self):
        """
        Checks for too many requests

        :return: true if there was a too many requests page, false otherwise
        """
        try:
            self.driver.find_element_by_xpath(r"/html/body/p")
            return True
        except NoSuchElementException:
            return False

    def curr_crown_count(self, attempt_num = 1):
        """
        Finds the crown count of the currently logged in account\n
        :return: integer representing the number of crowns
        """
        accountinfo_url = r"https://www.wizard101.com/user/kiaccounts/summary/game?context=am"
        self.driver.get(accountinfo_url)
        if self.too_many_reqs():
            time.sleep(15)
            return self.curr_crown_count()
        try:
            crowns_element = self.driver.find_element_by_xpath(r"/html/body/table/tbody/tr/td/table/tbody/tr/td/table"
                                                               r"/tbody/tr/td/table/tbody/tr/td/table/tbody/tr/td/div"
                                                               r"/div[3]/div/div[2]/div[2]/div/div["
                                                               r"2]/table/tbody/tr/td[2]/div/div["
                                                               r"2]/div/table/tbody/tr[1]/td[3]/table/tbody/tr/td["
                                                               r"2]/b")
        except NoSuchElementException:
            if attempt_num == 4:
                return CROWNS_UNFOUND
            return self.curr_crown_count(attempt_num = attempt_num + 1)
        crowns = int(crowns_element.text.replace(',', ''))
        return crowns

    def find_crowns(self, username, password):
        """
        Finds the crowns total of an account\n
        :param username
        :param password
        :return: integer representing the crowns
        """
        attempt = self.attempt_login(username, password)
        if attempt == WIZ_OFFLINE:
            return WIZ_OFFLINE
        if attempt == TESS_UNFOUND:
            return TESS_UNFOUND
        #Wiz redirects to one of two captcha urls
        captcha_url = r"https://www.wizard101.com/auth/wizard/QuarantinedLogin/8ad6a4041b4fd6c1011b5160b0670010" \
                      r"?fpRedirectUrl=https%3A%2F%2Fwww.wizard101.com%2Fgame&reset=1&fpPopup=1 "
        othercaptcha_url = r"https://www.wizard101.com/auth/wizard/quarantinedlogin/8ad6a4041b4fd6c1011b5160b0670010"
        while self.driver.current_url == captcha_url or self.driver.current_url == othercaptcha_url:
            self.attempt_login(username, password)
        crowns = self.curr_crown_count()
        return crowns

    def run_account(self, account):
        """
        Runs an account\n
        :param account: "SampleUsername:SamplePassword"
        :return: output text and a newline to be added to output_text
        """
        try:
            username, password = account.split(":")
        except ValueError:
            curr_text = "Account: %s was formatted incorrectly" % account
            print(curr_text)
            self.account_info[account] = curr_text + "\n"
            return
        crowns = self.find_crowns(username, password)
        if crowns == WIZ_OFFLINE:
            return WIZ_OFFLINE
        if crowns == CROWNS_UNFOUND:
            curr_text = "Couldn't find crowns for account: %s" % account
            print(curr_text)
            self.account_info[account] = curr_text + "\n"
            return
        self.total_crowns += crowns
        self.packs_199 += crowns // 199
        self.packs_299 += crowns // 299
        self.packs_399 += crowns // 399
        self.packs_599 += crowns // 599
        self.energy_elixirs += crowns // 250
        curr_text = "Account: %s had %i crowns" % (username, crowns)
        print(curr_text)
        self.account_info[account] = curr_text + "\n"


if __name__ == '__main__':
    CROWNS_UNFOUND = -1
    WIZ_OFFLINE = -3
    TESS_UNFOUND = -4

    def exit_drivers():
        """
        Exits all drivers in CrownCounter.drivers
        """
        for driver in CrownCounter.drivers:
            driver.quit()

    def count_crowns():
        """
        Essentially the main() function
        """
        chrome_path = "chromedriver.exe"
        chrome_options = Options()
        chrome_options.add_argument("--headless")

        def create_counter():
            driver = webdriver.Chrome(chrome_path, options = chrome_options)
            counter = CrownCounter(captcha_solver, driver)
            return counter

        #We designate a file_error variable that will be set to true if either accounts.txt or config.txt isn't found
        FILE_ERROR = False
        try:
            with open("accounts.txt", "r") as accounts_file:
                accounts = accounts_file.read().split("\n")
        except FileNotFoundError:
            with open("accounts.txt", "w") as accounts_file:
                accounts_file.write("")
                print("Created an accounts.txt. Rerun the program with your accounts formatted properly")
                FILE_ERROR = True

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
        try:
            with open("config.txt", "r") as config_file:
                #Define a config_json variable that will store the json's options for later use
                config_json = json.loads(config_file.read())
        except FileNotFoundError:
            print("Created a config.txt. Rerun the program with your options configured in the config")
            create_config()
            FILE_ERROR = True

        #If there was a error finding a file, the program will exit so the user can adjust their settings
        if FILE_ERROR:
            input("Press any key to exit...")
            quit()

        #This class will package a CrownCounter into a thread, allowing for multiple threads to count crowns
        class CounterThread(Thread):
            WAIT = -2

            def __init__(self, counter):
                """

                :param counter: A crown counter object
                """
                super().__init__()
                self.counter = counter
                self.finished = True
                #The WAIT variable signifies that the thread should WAIT before trying to run accounts
                self.account = CounterThread.WAIT
                self.last_account = False
                self.wiz_offline = False
                self.tess_unfound = False

            def run(self):
                """
                This run function will tell the thread to go on a loop solving accounts if it is not finished
                """
                while not self.last_account:
                    if not self.finished and self.account != CounterThread.WAIT:
                        account_run = self.counter.run_account(self.account)
                        if account_run == WIZ_OFFLINE:
                            self.wiz_offline = True
                            break
                        if account_run == TESS_UNFOUND:
                            self.tess_unfound = True
                            break
                        """
                        When the robot finishes counting crowns on an account, it will set its .finished variable to True
                        This tells it to stop trying to run accounts until it isn't finished, and tells
                        The client to assign it a new account
                        """
                        self.finished = True
                    time.sleep(1)

            def run_account(self, account):
                """
                The run account method will store an account into the counter thread's account variable, and tell it
                that it is no longer finished

                :type account: str
                :param account: "SampleUser:SamplePass"
                """
                self.account = account
                self.finished = False

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
        captcha_solver = CaptchaSolver(tess_path)
        all_threads = []

        for thread in range(num_threads):
            """
            We will create a new CounterThread and 
            store it in the all_threads list for each thread defined by the user
            """
            new_thread = CounterThread(create_counter())
            all_threads.append(new_thread)
            #Starting each thread will tell it to start looking for accounts to solve, by calling the run function
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
                    if thread.wiz_offline:
                        exit_drivers()
                        input("Wizard101 website was offline. Press enter to exit...")
                        quit()
                    if thread.tess_unfound:
                        exit_drivers()
                        print("Tesseract path was invalid in config.txt. Delete config to restore defaults")
                        input("Press enter to exit...")
                        quit()
                    if thread.finished:
                        thread.run_account(account)
                        found_assignment = True
                        break
                if not found_assignment:
                    time.sleep(2)

        for thread in all_threads:
            """
            We tell each thread that they are on their last account, so they should exit the while loop
            Then we wait for the threads to finish by calling join
            """
            thread.last_account = True
            thread.join()

        # This wait is necessary to prevent the program going too fast and forgetting to join together
        # I really dont have a clue why. I probably did something wrong
        time.sleep(5)

        """
        Each thread stores an account_info set that contains the output text for each account,
        And uses the account as "User:Pass" for a key
        Therefore we create a set that will contain all the other sets, so that we can print to the
        Output.txt in the original order designated by the accounts.txt
        """
        all_account_info = {}
        #The output_text variable stores what will be written to output.txt
        output_text = ""
        """
        We create the total crowns, packs, and elixirs variables, and calculate them by adding up the values
        Calculated by each individual thread
        """
        total_crowns = 0
        packs_199 = 0
        packs_299 = 0
        packs_399 = 0
        packs_599 = 0
        energy_elixirs = 0
        """
        We now loop through each CounterThread and add up all the values they've stored previously
        """
        for thread in all_threads:
            curr_info = thread.counter.account_info
            """
            We must take the current thread's account info that contains the output text, and store it in the larger set
            """
            for key in curr_info:
                all_account_info[key] = curr_info[key]
            total_crowns += thread.counter.total_crowns
            packs_199 += thread.counter.packs_199
            packs_299 += thread.counter.packs_299
            packs_399 += thread.counter.packs_399
            packs_599 += thread.counter.packs_599
            energy_elixirs += thread.counter.energy_elixirs

        """
        We now loop through the accounts in the original order designated by accounts.txt, 
        And add the output_text associated with each account, in the correct order
        """
        for account in accounts:
            output_text += all_account_info[account]

        """
        We do some formatting so that we can create fancy text to print that shows the purchaseable packs
        We store it into curr_text so it can be added to output_text
        """
        curr_text = """
    Total Crowns: %i
    
    Purchaseable 199 packs: %i
    Purchaseable 299 packs: %i
    Purchaseable 399 packs: %i
    Purchaseable 599 packs: %i
    Purchaseable Energy elixirs: %i""" % (total_crowns, packs_199, packs_299, packs_399, packs_599, energy_elixirs)
        print(curr_text)
        output_text += curr_text

        #We now write output_text to the output_file, as originally intended
        with open("output.txt", "w") as output_file:
            output_file.write(output_text)
        #We exit out of each driver's chrome.exe tabs to prevent memory leakage
        exit_drivers()
        input("Press enter to exit...")
        quit()

    count_crowns()
