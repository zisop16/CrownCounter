import time
import os
import json
import threading

from threading import Thread
from PIL import Image
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options

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
        login_url = "https://www.wizard101.com/auth/wizard/login.theform"
        self.driver.get(login_url)
        if self.too_many_reqs():
            time.sleep(15)
            self.enter_credentials(username, password)
            return

        user_field = self.driver.find_element_by_xpath(r"/html/body/table/tbody/tr[2]/td[2]/form/table[1]/tbody/tr[1]/td[2]/input")
        user_field.clear()
        user_field.send_keys(username)

        pass_field = self.driver.find_element_by_xpath(r"/html/body/table/tbody/tr[2]/td[2]/form/table[1]/tbody/tr[2]/td[2]/input")
        pass_field.clear()
        pass_field.send_keys(password)

        enter_button = self.driver.find_element_by_xpath(r"/html/body/table/tbody/tr[2]/td[2]/form/table[2]/tbody/tr/td[2]/a")
        enter_button.click()

    def attempt_captcha(self, username, password):
        """
        Attempts the current captcha assuming the driver is at the captcha page
        """
        if self.too_many_reqs():
            time.sleep(15)
            self.enter_credentials(username, password)
            self.attempt_captcha(username, password)
            return
        #Because there are two possible captcha urls, there are two possible xpaths for each distinct site
        try:
            captcha_element = self.driver.find_element_by_xpath(r"/html/body/table/tbody/tr[2]/td[2]/form/div[3]/div/table/tbody/tr[1]/td[3]/div/img")
        except NoSuchElementException:
            captcha_element = self.driver.find_element_by_xpath(r"/html/body/table/tbody/tr[2]/td[2]/form/div[4]/div/table/tbody/tr[1]/td[3]/div/img")
        if not os.path.isdir("screenshots"):
            os.mkdir("screenshots")
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
        captcha_solution = self.solver.resolve(captcha)

        #Again, two possible xpaths for the captcha entering field
        try:
            captcha_field = self.driver.find_element_by_xpath(r"/html/body/table/tbody/tr[2]/td[2]/form/div[3]/div/table/tbody/tr[2]/td[3]/div/input")
        except NoSuchElementException:
            captcha_field = self.driver.find_element_by_xpath(r"/html/body/table/tbody/tr[2]/td[2]/form/div[4]/div/table/tbody/tr[2]/td[3]/div/input")

        #Enters the captcha solution and clicks the login button
        captcha_field.clear()
        captcha_field.send_keys(captcha_solution)
        enter_button = self.driver.find_element_by_xpath(r"/html/body/table/tbody/tr[2]/td[2]/form/table[1]/tbody/tr/td/div/div/input")
        enter_button.click()

    def attempt_login(self, username, password):
        """
        Attemps to log in to the account\n
        :param username:
        :param password:
        """
        self.enter_credentials(username, password)
        time.sleep(.2)
        wiz_url = "https://www.wizard101.com/game"
        if self.driver.current_url != wiz_url:
            self.attempt_captcha(username, password)
            time.sleep(.3)

    def too_many_reqs(self):
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
            crowns_element = self.driver.find_element_by_xpath(r"/html/body/table/tbody/tr/td/table/tbody/tr/td/table/tbody/tr/td/table/tbody/tr/td/table/tbody/tr/td/div/div[3]/div/div[2]/div[2]/div/div[2]/table/tbody/tr/td[2]/div/div[2]/div/table/tbody/tr[1]/td[3]/table/tbody/tr/td[2]/b")
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
        self.attempt_login(username, password)
        #Wiz redirects to one of two captcha urls
        captcha_url = r"https://www.wizard101.com/auth/wizard/QuarantinedLogin/8ad6a4041b4fd6c1011b5160b0670010?fpRedirectUrl=https%3A%2F%2Fwww.wizard101.com%2Fgame&reset=1&fpPopup=1"
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
            curr_text = ("Account: %s was formatted incorrectly") % account
            print(curr_text)
            self.account_info[account] = curr_text + "\n"
            return
        crowns = self.find_crowns(username, password)
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

    chrome_path = "chromedriver.exe"
    tess_path = "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
    captcha_solver = CaptchaSolver(tess_path)
    chrome_options = Options()
    #chrome_options.add_argument("--headless")

    def create_counter():
        driver = webdriver.Chrome(chrome_path, options = chrome_options)
        counter = CrownCounter(captcha_solver, driver)
        return counter

    def exit_drivers():
        for driver in CrownCounter.drivers:
            driver.quit()

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
            config_json = json.loads(config_file.read())
    except FileNotFoundError:
        print("Created a config.txt. Rerun the program with your options configured in the config")
        with open("config.txt", "w") as config_file:
            config_data = {
                "threads": 1
            }
            config_json = json.dumps(config_data, indent=4, sort_keys=True)
            config_file.write(config_json)
            FILE_ERROR = True

    if FILE_ERROR:
        input("Press any key to exit...")
        quit()

    class CounterThread(Thread):
        WAIT = -2
        def __init__(self, counter):
            super().__init__()
            self.counter = counter
            self.finished = True
            self.account = CounterThread.WAIT
            self.last_account = False

        def run(self):
            while not self.last_account:
                if not self.finished and self.account != CounterThread.WAIT:
                    self.counter.run_account(self.account)
                    self.finished = True
                time.sleep(1)

        def run_account(self, account):
            self.account = account
            self.finished = False

    num_threads = config_json.get("threads")
    all_threads = []

    for thread in range(num_threads):
        new_thread = CounterThread(create_counter())
        all_threads.append(new_thread)
        new_thread.start()

    for account in accounts:
        found_assignment = False
        while not found_assignment:
            for thread in all_threads:
                if thread.finished:
                    thread.run_account(account)
                    found_assignment = True
                    break
            if not found_assignment:
                time.sleep(2)
    time.sleep(5)

    for thread in all_threads:
        thread.last_account = True
        thread.join()

    all_account_info = {}
    output_text = ""
    total_crowns = 0
    packs_199 = 0
    packs_299 = 0
    packs_399 = 0
    packs_599 = 0
    energy_elixirs = 0
    for thread in all_threads:
        curr_info = thread.counter.account_info
        for key in curr_info:
            all_account_info[key] = curr_info[key]
        total_crowns += thread.counter.total_crowns
        packs_199 += thread.counter.packs_199
        packs_299 += thread.counter.packs_299
        packs_399 += thread.counter.packs_399
        packs_599 += thread.counter.packs_599
        energy_elixirs += thread.counter.energy_elixirs

    for account in accounts:
        output_text += all_account_info[account]

    curr_text = """
Total Crowns: %i

Purchaseable 199 packs: %i
Purchaseable 299 packs: %i
Purchaseable 399 packs: %i
Purchaseable 599 packs: %i
Purchaseable Energy elixirs: %i""" % (total_crowns, packs_199, packs_299, packs_399, packs_599, energy_elixirs)
    print(curr_text)
    output_text += curr_text
    with open("output.txt", "w") as output_file:
        output_file.write(output_text)
    exit_drivers()
    input("Press enter to exit...")
