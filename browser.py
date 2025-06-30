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
import requests
import os

TELEGRAM_TOKEN = 'токен бота'
CHAT_ID = 'ваш тг айди'
bot = telebot.TeleBot(TELEGRAM_TOKEN)

def check_proxy(proxy):
    proxies = {
        'http': f'http://{proxy}',
        'https': f'http://{proxy}'
    }
    
    test_urls = [
        'http://httpbin.org/ip',
        'https://api.ipify.org?format=json'
    ]
    
    try:
        for url in test_urls:
            response = requests.get(url, proxies=proxies, timeout=10)
            if response.status_code == 200:
                print(f"Proxy {proxy} works! Response: {response.text}")
                return True
    except Exception as e:
        print(f"Proxy {proxy} failed: {str(e)}")
        return False
    
    return False

def load_and_check_proxies():
    valid_proxies = []
    try:
        with open(f'{os.getcwd()}/proxy.txt', 'r') as f:
            print(f'{os.getcwd()}/proxy.txt')
            proxies = [line.strip() for line in f if line.strip()]
            
        for proxy in proxies:
            if check_proxy(proxy):
                valid_proxies.append(proxy)
                print(f"Added valid proxy: {proxy}")
            else:
                print(f"Skipping invalid proxy: {proxy}")
                
        return valid_proxies
    except FileNotFoundError:
        print("proxy.txt not found. Continuing without proxies.")
        return []

proxies = load_and_check_proxies()
current_proxy_index = 0

def save_to_file(mail, password, code):
    with open('accounts.txt', 'a') as f:
        f.write(f"{mail}:{password}:{code}\n")

def get_next_proxy():
    global current_proxy_index
    if not proxies:
        return None
    
    proxy = proxies[current_proxy_index]
    current_proxy_index = (current_proxy_index + 1) % len(proxies)
    return proxy

def run_bot_session():
    global current_proxy_index
    
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    proxy = get_next_proxy()
    if proxy:
        options.add_argument(f'--proxy-server={proxy}')
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
        try:
            error_element = wait.until(EC.presence_of_element_located(('xpath', '//div[@class="text-break selectable"]')))
            print("Registration failed, switching proxy...")
            driver.quit()
            return
        except:
            pass
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
