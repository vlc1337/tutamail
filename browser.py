from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from random import randint
import time
import random
import string
import telebot
from io import BytesIO

TELEGRAM_TOKEN = 'токен тг бота'
CHAT_ID = 'чат айди'
bot = telebot.TeleBot(TELEGRAM_TOKEN)

def save_to_file(mail, password, code):
    with open('accounts.txt', 'a') as f:
        f.write(f"{mail}:{password}:{code}\n")

def run_bot_session():
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 11)
    captcha_solved = False
    last_message_time = 0

    def send_screenshot_and_get_captcha():
        nonlocal last_message_time, captcha_solved
        screenshot = driver.get_screenshot_as_png()
        bot.send_photo(CHAT_ID, screenshot, caption="Введите текст с капчи:")
        last_message_time = time.time()
        captcha_solved = False
        
        @bot.message_handler(func=lambda message: True)
        def handle_message(message):
            nonlocal last_message_time, captcha_solved
            if message.date > last_message_time and str(message.chat.id) == CHAT_ID:
                captcha_text = message.text
                try:
                    captcha_input = wait.until(EC.presence_of_element_located(('xpath', '//input[@data-testid="tfi:captcha_input"]')))
                    captcha_input.clear()
                    captcha_input.send_keys(captcha_text)
                    submit_button = driver.find_element('xpath', '//button[@data-testid="btn:ok_action"]')
                    submit_button.click()
                    captcha_solved = True
                except Exception as e:
                    print(e)
                finally:
                    bot.stop_polling()
        bot.polling(timeout=60)

    try:
        driver.get('https://app.tuta.com/login')
        wait.until(EC.element_to_be_clickable(('xpath', '//button[@data-testid="btn:register_label"]')))
        driver.find_element('xpath', '//button[@data-testid="btn:register_label"]').click()
        time.sleep(4)
        window = driver.find_element('xpath', '//div[@class="dialog-container scroll"]')
        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", window)
        free = driver.find_element('xpath','//div[@class="flex-space-between items-center pb"]')
        ActionChains(driver).move_to_element(free).click().perform()
        wait.until(EC.element_to_be_clickable(('xpath', '//button[@data-testid="btn:continue_action"]')))
        driver.find_element('xpath', '//button[@data-testid="btn:continue_action"]').click()
        time.sleep(randint(2,5))
        try:
            time.sleep(1)
            galki = driver.find_elements('xpath', '//input[@class="icon checkbox-override click"]')
            galki[0].click()
            time.sleep(1)
            galki[1].click()
            time.sleep(2)
            driver.find_element('xpath', '//button[@data-testid="btn:ok_action"]').click()
        except: pass
        time.sleep(randint(1,2))
        mail = ''.join(random.choice(string.ascii_letters).lower() for _ in range(12))
        password = ''.join(random.choice(string.ascii_letters + string.digits + string.punctuation) for _ in range(16))
        fields = driver.find_elements('xpath', '//input[@autocomplete="new-password"]')
        ActionChains(driver).move_to_element(fields[0]).click().send_keys(mail).perform()
        wait.until(EC.presence_of_element_located(('xpath', '//div[@class="mt-s" and contains(text(), "доступен")]'))) # ТУТ ПОМЕНЯТЬ ЕСЛИ ДРУГОЙ ЯЗЫК КРИВО СДЕЛАЛ СОРИ
        ActionChains(driver).move_to_element(fields[1]).click().send_keys(password).perform()
        time.sleep(randint(1,2))
        ActionChains(driver).move_to_element(fields[2]).click().send_keys(password).perform()
        time.sleep(randint(1,2))
        checkboxes = driver.find_elements('xpath', '//input[@type="checkbox"]')
        ActionChains(driver).move_to_element(checkboxes[0]).click().perform()
        ActionChains(driver).move_to_element(checkboxes[1]).click().perform()
        next = driver.find_element('xpath', '//button[@data-testid="btn:next_action"]')
        ActionChains(driver).move_to_element(next).click().perform()
        wait.until(EC.presence_of_element_located(('xpath', '//input[@data-testid="tfi:captcha_input"]')))
        send_screenshot_and_get_captcha()
        if captcha_solved:
            code = driver.find_element('xpath', '//div[@class="text-break monospace selectable flex flex-wrap flex-center border pt pb plr"]').text
            mail = f'{mail}@tutamail.com'
            save_to_file(mail, password, code)
            time.sleep(5)
    except Exception as e:
        print(e)
    finally:
        driver.quit()

while True:
    run_bot_session()
    time.sleep(5)