import time
import os

from PIL import Image
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options

from CaptchaSolve import CaptchaSolver


class CrownCounter():
    def __init__(self, captcha_solver, driver):
        self.solver = captcha_solver
        self.driver = driver

    def enter_credentials(self, username, password):
        """
        Logs in to the account and possibly goes to the captcha page
        :param username:
        :param password:
        :return:
        """
        login_url = "https://www.wizard101.com/auth/wizard/login.theform"
        self.driver.get(login_url)

        user_field = driver.find_element_by_xpath(r"/html/body/table/tbody/tr[2]/td[2]/form/table[1]/tbody/tr[1]/td[2]/input")
        user_field.clear()
        user_field.send_keys(username)

        pass_field = driver.find_element_by_xpath(r"/html/body/table/tbody/tr[2]/td[2]/form/table[1]/tbody/tr[2]/td[2]/input")
        pass_field.clear()
        pass_field.send_keys(password)

        enter_button = driver.find_element_by_xpath(r"/html/body/table/tbody/tr[2]/td[2]/form/table[2]/tbody/tr/td[2]/a")
        enter_button.click()

    def attempt_captcha(self):
        """
        Attempts the current captcha assuming the driver is at the captcha page
        """
        captcha_element = None
        #Because there are two possible captcha urls, there are two possible xpaths for each distinct site
        try:
            captcha_element = driver.find_element_by_xpath(r"/html/body/table/tbody/tr[2]/td[2]/form/div[3]/div/table/tbody/tr[1]/td[3]/div/img")
        except NoSuchElementException:
            captcha_element = driver.find_element_by_xpath(r"/html/body/table/tbody/tr[2]/td[2]/form/div[4]/div/table/tbody/tr[1]/td[3]/div/img")
        driver.save_screenshot("screenshot.png")
        captcha_location = captcha_element.location
        #KI captchas have a standard width of 230px and height of 50px
        captcha_width = 230
        captcha_height = 50
        #Captcha location in screenshot, bot left in x1, y1 and top right in x2, y2
        bot_left = captcha_location.get("x"), captcha_location.get("y")
        top_right = (captcha_location.get("x") + captcha_width), (captcha_location.get("y") + captcha_height)
        screenshot = Image.open("screenshot.png")
        #The screenshot image will have to crop out the section containing the captcha to get the captcha image
        captcha = screenshot.crop((bot_left[0], bot_left[1], top_right[0], top_right[1]))
        captcha_solution = self.solver.resolve(captcha)
        captcha_field = None

        #Again, two possible xpaths for the captcha entering field
        try:
            captcha_field = driver.find_element_by_xpath(r"/html/body/table/tbody/tr[2]/td[2]/form/div[3]/div/table/tbody/tr[2]/td[3]/div/input")
        except NoSuchElementException:
            captcha_field = driver.find_element_by_xpath(r"/html/body/table/tbody/tr[2]/td[2]/form/div[4]/div/table/tbody/tr[2]/td[3]/div/input")

        #Enters the captcha solution and clicks the login button
        captcha_field.clear()
        captcha_field.send_keys(captcha_solution)
        enter_button = driver.find_element_by_xpath(r"/html/body/table/tbody/tr[2]/td[2]/form/table[1]/tbody/tr/td/div/div/input")
        enter_button.click()

    def attempt_login(self, username, password):
        """
        Attemps to log in to the account\n
        :param username:
        :param password:
        """
        self.enter_credentials(username, password)
        time.sleep(1)
        wiz_url = "https://www.wizard101.com/game"
        if self.driver.current_url != wiz_url:
            self.attempt_captcha()
            time.sleep(2)

    def curr_crown_count(self):
        """
        Finds the crown count of the currently logged in account\n
        :return: integer representing the number of crowns
        """
        accountinfo_url = r"https://www.wizard101.com/user/kiaccounts/summary/game?context=am"
        self.driver.get(accountinfo_url)
        crowns_element = driver.find_element_by_xpath(r"/html/body/table/tbody/tr/td/table/tbody/tr/td/table/tbody/tr/td/table/tbody/tr/td/table/tbody/tr/td/div/div[3]/div/div[2]/div[2]/div/div[2]/table/tbody/tr/td[2]/div/div[2]/div/table/tbody/tr[1]/td[3]/table/tbody/tr/td[2]/b")
        crowns = int(crowns_element.text.replace(',', ''))
        return crowns

if __name__ == '__main__':
    chrome_path = "chromedriver.exe"
    tess_path = "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
    captcha_solver = CaptchaSolver(tess_path)
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(chrome_path, options = chrome_options)
    counter = CrownCounter(captcha_solver, driver)

    def find_crowns(username, password):
        """
        Finds the crowns total of an account\n
        :param username
        :param password
        :return: integer representing the crowns
        """
        counter.attempt_login(username, password)
        #Wiz redirects to one of two captcha urls
        captcha_url = r"https://www.wizard101.com/auth/wizard/QuarantinedLogin/8ad6a4041b4fd6c1011b5160b0670010?fpRedirectUrl=https%3A%2F%2Fwww.wizard101.com%2Fgame&reset=1&fpPopup=1"
        othercaptcha_url = r"https://www.wizard101.com/auth/wizard/quarantinedlogin/8ad6a4041b4fd6c1011b5160b0670010"
        while driver.current_url == captcha_url or driver.current_url == othercaptcha_url:
            counter.attempt_login(username, password)
        crowns = counter.curr_crown_count()
        return crowns

    output_text = ""
    total_crowns = 0
    packs_199 = 0
    packs_299 = 0
    packs_399 = 0
    packs_599 = 0
    energy_elixirs = 0
    accounts = None
    try:
        with open("accounts.txt", "r") as accounts_file:
            accounts = accounts_file.read().split("\n")
    except FileNotFoundError:
        with open("accounts.txt", "w") as accounts_file:
            accounts_file.write("")
            print("Created an accounts.txt. Rerun the program with your accounts formatted properly")
            driver.quit()
            input("Press any key to exit...")
            os.system("exit")

    for account in accounts:
        username, password = account.split(":")
        crowns = find_crowns(username, password)
        curr_text = "Account: %s had %i crowns" % (username, crowns)
        print(curr_text)
        output_text += curr_text + "\n"
        total_crowns += crowns
        packs_199 += crowns // 199
        packs_299 += crowns // 299
        packs_399 += crowns // 399
        packs_599 += crowns // 599
        energy_elixirs += crowns // 250
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
    driver.quit()
    input("Press enter to exit...")
