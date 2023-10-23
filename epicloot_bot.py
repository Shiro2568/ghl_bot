from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service

import time
PROFILE = "C:/Users/lob01/AppData/Local/Google/Chrome/User Data"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
options = webdriver.ChromeOptions()
options.binary_location = "C:\Program Files\Google\Chrome\Application\chrome.exe"
options.add_argument("user-data-dir=" + PROFILE)
options.add_argument(f"user-agent={USER_AGENT}" )
service = Service(executable_path='C:\\Users\\lob01\\Downloads\\chromedriver_win32\\chromedriver.exe')

#service = Service(executable_path='C:/Users/lob01/Downloads/chromedriver_win32/chromedriver.exe')
driver = webdriver.Chrome(options=options,service=service)
driver.get('https://epicloot.in/theint')

time.sleep(120)

button = driver.find_element(By.CSS_SELECTOR, '.int-cases__open') 
# Нажимаем на кнопку
button.click()

# Закрываем веб-драйвер
driver.quit()

