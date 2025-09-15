import asyncio
import multiprocessing
import time
from typing import Any

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from src.main.constants import BASE_URL
from src.main.schemas import ShiftBase
from src.main.utils import ShiftConverter
from src.main.exceptions.selenium_exceptions import (
    SeleniumDriverCreationException,
    SeleniumDockerConnectionException,
    SeleniumLocalDriverException,
    SeleniumLoginException,
    SeleniumPageLoadException,
    SeleniumElementNotFoundException,
    SeleniumLoginCredentialsException,
    SeleniumShiftsParsingException,
    SeleniumCommandException,
    SeleniumCommandTimeoutException,
    SeleniumWebDriverNotReadyException
)


def is_running_in_docker() -> bool:
    return True


def get_chrome_options_for_environment() -> Options:
    chrome_options = Options()
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-images")
    chrome_options.add_argument("--disable-javascript")
    chrome_options.add_argument("--disable-css")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-running-insecure-content")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-background-networking")
    chrome_options.add_argument("--disable-sync")
    chrome_options.add_argument("--disable-translate")
    chrome_options.add_argument("--hide-scrollbars")
    chrome_options.add_argument("--metrics-recording-only")
    chrome_options.add_argument("--mute-audio")
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--safebrowsing-disable-auto-update")
    chrome_options.add_argument("--disable-ipc-flooding-protection")
    chrome_options.add_argument("--disable-hang-monitor")
    chrome_options.add_argument("--disable-prompt-on-repost")
    chrome_options.add_argument("--disable-domain-reliability")
    chrome_options.add_argument("--disable-component-extensions-with-background-pages")
    chrome_options.add_argument("--disable-default-apps")
    chrome_options.add_argument("--disable-features=TranslateUI")
    chrome_options.add_argument("--disable-print-preview")
    chrome_options.add_argument("--disable-client-side-phishing-detection")
    chrome_options.add_argument("--disable-sync-preferences")
    chrome_options.add_argument("--disable-web-resources")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor,VizServiceDisplay")
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    chrome_options.add_argument("--disable-renderer-backgrounding")
    chrome_options.add_argument("--disable-field-trial-config")
    chrome_options.add_argument("--disable-back-forward-cache")
    chrome_options.add_argument("--force-color-profile=srgb")
    chrome_options.add_argument("--memory-pressure-off")
    chrome_options.add_argument("--max_old_space_size=4096")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    if is_running_in_docker():
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--headless")
    else:
        chrome_options.add_argument("--window-size=1920,1080")
    
    return chrome_options


def selenium_process_runner(login: str,
                            password: str,
                            command_queue: multiprocessing.Queue,
                            result_queue: multiprocessing.Queue,):
    try:
        selenium_client = SeleniumClientInner(login, password)
        
        try:
            selenium_client.create_driver()
        except Exception as e:
            raise SeleniumDriverCreationException(f"Failed to create driver in process: {str(e)}")
        
        try:
            selenium_client.login()
        except Exception as e:
            raise SeleniumLoginException(f"Login failed in process: {str(e)}")
        
        result_queue.put({
            'type': 'ready',
            'data': 'Selenium process is ready'
        })

        while True:
            try:
                if not command_queue.empty():
                    command = command_queue.get_nowait()

                    if command['type'] == 'shutdown':
                        selenium_client.close_client()
                        break
                    elif command['type'] == 'parse_shifts':
                        shifts = selenium_client.parse_shifts()
                        result_queue.put({
                            'type': 'success',
                            'data': shifts,
                            'task_id': command.get('task_id')
                        })
                    elif command['type'] == 'parse_company_name':
                        link = command.get('link')
                        if link is None:
                            result_queue.put({
                                'type': 'error',
                                'data': 'Link is required for company name parsing',
                                'task_id': command.get('task_id')
                            })
                        else:
                            company_name = selenium_client.parse_company_name(link)
                            result_queue.put({
                                'type': 'success',
                                'data': company_name,
                                'task_id': command.get('task_id')
                            })
                time.sleep(0.1)
            except Exception as e:
                result_queue.put({
                    'type': 'error',
                    'data': str(e)
                })
                time.sleep(1)

    except Exception as e:
        result_queue.put({
            'type': 'fatal_error',
            'data': str(e)
        })


class SeleniumClientInner:

    def __init__(self, login: str, password: str):
        self.driver = None
        self.email = login
        self.password = password

    def create_driver(self):
        chrome_options = get_chrome_options_for_environment()

        if is_running_in_docker():
            selenium_hub_url = "http://selenium-hub:4444/wd/hub"
            try:
                self.driver = webdriver.Remote(
                    command_executor=selenium_hub_url,
                    options=chrome_options
                )
            except Exception as e:
                raise SeleniumDockerConnectionException(f"Failed to connect to Docker Selenium Hub: {str(e)}")
        else:
            try:
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)
                self.driver = driver
            except Exception as e:
                raise SeleniumLocalDriverException(f"Failed to create local Chrome driver: {str(e)}")

    def login(self):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.driver.get(BASE_URL)
                WebDriverWait(self.driver, 30).until(
                    expected_conditions.presence_of_all_elements_located(
                        (By.ID, 'UserEmail')
                    )
                )
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise SeleniumPageLoadException(f"Failed to load login page after {max_retries} attempts: {str(e)}")

        try:
            email_field = self.driver.find_element(By.ID, 'UserEmail')
            email_field.clear()
            email_field.send_keys(self.email)
        except Exception as e:
            raise SeleniumElementNotFoundException("email field", f"Failed to find or interact with email field: {str(e)}")

        try:
            password_field = self.driver.find_element(By.ID, 'UserPassword')
            password_field.clear()
            password_field.send_keys(self.password)
        except Exception as e:
            raise SeleniumElementNotFoundException("password field", f"Failed to find or interact with password field: {str(e)}")

        try:
            login_button = self.driver.find_element(By.CLASS_NAME, 'theme-main-button.big-btn.full-btn')
            login_button.click()
        except Exception as e:
            raise SeleniumElementNotFoundException("login button", f"Failed to find or click login button: {str(e)}")

        time.sleep(5)

        if self.driver.current_url != BASE_URL:
            raise SeleniumLoginCredentialsException("Login failed - invalid credentials or login process failed")

    def parse_shifts(self) -> list[ShiftBase]:
        shift_set = set()
        shift_cnt = 0
        prev_shift: ShiftBase | None = None
        for page in range(1, 10):
            try:
                self.driver.get(BASE_URL + f"?page={page}&ignoreRating=true&limit=200")
                WebDriverWait(self.driver, 10).until(
                    expected_conditions.presence_of_all_elements_located(
                        (By.XPATH, "//*[@id=\"toolbar-portal-top\"]/aside/div/div/div[1]/div/div[1]/button")
                    )
                )
            except Exception as e:
                raise SeleniumPageLoadException(f"Failed to load shifts page {page}: {str(e)}")

            try:
                html = self.driver.page_source
                soup = BeautifulSoup(html, "html.parser")
                rows = soup.select("tbody tr")
            except Exception as e:
                raise SeleniumShiftsParsingException(f"Failed to parse HTML for page {page}: {str(e)}")

            for i, r in enumerate(rows):
                liquidating = False
                classes = r.get("class", None)
                if classes and "MuiTableRow-root" in classes and "MuiTableRow-hover" in classes:
                    text = [td.get_text(strip=True) for td in r.find_all(["td", "th"])]
                    if text:
                        if r.select("svg.jss42.jss44"):
                            liquidating = True
                        shift_schema = ShiftConverter.parse_shift_data(text)
                        link = ShiftConverter.parse_shift_link(rows[i + 1].find("a").get("href"))
                        if shift_schema and link:
                            shift_schema.link = link
                            if liquidating and prev_shift:
                                prev_shift.connected_shifts.append(shift_schema)
                            else:
                                shift_set.add(shift_schema)
                                prev_shift = shift_schema

            if len(shift_set) == shift_cnt:
                return list(shift_set)
            else:
                shift_cnt = len(shift_set)

        return list(shift_set)

    def parse_company_name(self, link: int) -> str | None:
        try:
            self.driver.get(BASE_URL + f"/{link}")
            xpath = '//*[@id="react-mount-point"]/main/slot[2]/div/div[2]/div/div[1]/div/div/div/div[1]/ul[3]/li[2]/div/div[2]/div/span'
            WebDriverWait(self.driver, 10).until(
                expected_conditions.visibility_of_element_located((By.XPATH, xpath))
            )
            el = self.driver.find_element(By.XPATH, xpath)
            return el.text.strip()
        except Exception as e:
            # TODO log error
            return None

    def close_client(self) -> None:
        self.driver.quit()


class SeleniumClient:
    def __init__(self, login: str, password: str):
        self.driver = None
        self.email = login
        self.password = password
        self.headless = False
        self.process = None
        self.command_queue = None
        self.result_queue = None
        self._is_ready = False
        self._task_counter = 0

    async def start_process(self) -> None:
        if self.process and self.process.is_alive():
            return
        self.command_queue = multiprocessing.Queue()
        self.result_queue = multiprocessing.Queue()

        self.process = multiprocessing.Process(
            target=selenium_process_runner,
            args=(self.email, self.password, self.command_queue, self.result_queue)
        )

        self.process.start()

        timeout_counter = 0
        max_timeout = 600

        while timeout_counter < max_timeout:
            if not self.result_queue.empty():
                result = self.result_queue.get()
                if result['type'] == 'ready':
                    self._is_ready = True
                    break
                else:
                    raise SeleniumCommandException("start_process", f"Selenium task failed: {result['data']}")
            await asyncio.sleep(0.2)
            timeout_counter += 1
            
        if timeout_counter >= max_timeout:
            if self.process and self.process.is_alive():
                self.process.terminate()
            raise SeleniumCommandTimeoutException("start_process", max_timeout * 0.2)

    async def _send_command(self, command_type: str, **kwargs) -> Any:
        if not self._is_ready:
            raise SeleniumWebDriverNotReadyException("WebDriver is not ready for commands")
        
        self._task_counter += 1
        task_id = f"task_{self._task_counter}"
        
        command = {
            'type': command_type,
            'task_id': task_id,
            **kwargs
        }

        self.command_queue.put(command)

        timeout_counter = 0
        max_timeout = 300

        while timeout_counter < max_timeout:
            if not self.result_queue.empty():
                result = self.result_queue.get()
                if result.get('task_id') == task_id:
                    if result['type'] == 'success':
                        return result['data']
                    else:
                        raise SeleniumCommandException(command_type, f"Selenium task failed: {result['data']}")
            await asyncio.sleep(0.2)
            timeout_counter += 1

        raise SeleniumCommandTimeoutException(command_type, max_timeout * 0.2)

    async def parse_shifts(self) -> list[ShiftBase]:
        return await self._send_command('parse_shifts')

    async def parse_company_name(self, link: int) -> str | None:
        return await self._send_command('parse_company_name', link=link)

    def close_driver(self) -> None:
        if self.process and self.process.is_alive():
            self.command_queue.put({'type': 'shutdown'})
            self.process.join(timeout=10)
            if self.process.is_alive():
                self.process.terminate()
                self.process.join()
        
        self._task_counter = 0
        self.process = None
        self.command_queue = None
        self.result_queue = None
        self._is_ready = False
