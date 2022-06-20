import functools
from typing import List, Tuple
from urllib.parse import urljoin
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.select import Select
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import UnexpectedAlertPresentException

import config


class NeptunDriver:
    def __init__(self, driver: WebDriver) -> None:
        self.driver = driver
        self.login_url = urljoin(config.NEPTUN_STUDENT_URL, "login.aspx")

    def login(self) -> None:
        self.driver.get(self.login_url)

        login_user_input = self.driver.find_element(by=By.ID, value="user")
        login_user_input.send_keys(config.NEPTUN_USERNAME)

        login_pw_input = self.driver.find_element(by=By.ID, value="pwd")
        login_pw_input.send_keys(config.NEPTUN_PASSWORD)

        login_button = self.driver.find_element(by=By.ID, value="btnSubmit")
        login_button.click()

        try:
            WebDriverWait(
                self.driver, 
                5,
                ignored_exceptions=[UnexpectedAlertPresentException]
            ).until(expected_conditions.url_changes(self.login_url))
        except Exception as e:
            print(type(e))
            raise RuntimeError("Login failed!")
        
        print("Login successful!")

    def _ensure_logged_in(fn):
        @functools.wraps(fn)
        def wrapper(self, *args, **kwargs):
            if self.driver.current_url.startswith(self.login_url) or self.driver.current_url == "about:blank":
                print("Logged out... attempting to log back in")
                self.login()
            return fn(self, *args, **kwargs)
        return wrapper

    @_ensure_logged_in
    def apply_course_filter(self, course_name: str) -> None:
        course_name_lower = course_name.lower()
        
        course_select_element = self.driver.find_element(by=By.ID, value="upFilter_cmbSubjects")
        course_select = Select(course_select_element)
        
        all_course_select_options: List[WebElement] = course_select.options
        for option in all_course_select_options:
            if option.text.lower().startswith(course_name_lower):
                course_select.select_by_visible_text(option.text)
                
                apply_filter_button = self.driver.find_element(by=By.ID, value="upFilter_expandedsearchbutton")
                apply_filter_button.click()
                print(f"Filter for '{course_name}' applied.")
                return
        
        raise ValueError(f"No such course ('{course_name}') found in filter options.")
            
    @_ensure_logged_in
    def find_exam_row_by_date(self, exams_table_rows: List[WebElement], exam_date: str) -> WebElement:
        for row in exams_table_rows:
            tds_in_row: List[WebElement] = row.find_elements(by=By.TAG_NAME, value="td")
            if any(td.text.startswith(exam_date) for td in tds_in_row):
                return row
        
        raise ValueError(f"No exam found with date '{exam_date}'.")

    @_ensure_logged_in
    def find_exam_capacity(self, exam_tr: WebElement) -> Tuple[int, int]:
        exam_tr_tds: List[WebElement] = exam_tr.find_elements(by=By.TAG_NAME, value="td")
        exam_tr_texts = [td.text.strip() for td in exam_tr_tds if td.text.strip()]
        
        print(f"Looking at row: [{' | '.join(exam_tr_texts)}]")
        capacity_texts = [text for text in exam_tr_texts if "/" in text]
        
        for candidate in capacity_texts:
            left, right = candidate.split("/", 1)
            try:
                return int(left), int(right)
            except ValueError as e:
                continue
        
        raise ValueError(f"Could not find exam capacity in: {' | '.join(exam_tr_texts)}")

    @_ensure_logged_in
    def go_to_exam_signup_page(self):
        exam_signup_url = urljoin(config.NEPTUN_STUDENT_URL, "main.aspx?ismenuclick=true&ctrl=0401")
        print("Going to ", exam_signup_url)
        self.driver.get(exam_signup_url)

    @_ensure_logged_in
    def check_if_full(self) -> bool:
        self.apply_course_filter(config.COURSE_NAME)
        
        exams_table = self.driver.find_element(by=By.ID, value="h_exams_gridExamList_bodytable")
        exams_table_tbody: WebElement = exams_table.find_element(by=By.TAG_NAME, value="tbody")
        
        exams_table_rows = exams_table_tbody.find_elements(by=By.TAG_NAME, value="tr")
        if exams_table_rows:
            print(f"Found {len(exams_table_rows)} exam dates.")
        else:
            raise Exception("Error: no exam dates found! Please ensure the config.py is right and then try again.")

        try:
            exam_tr = self.find_exam_row_by_date(exams_table_rows, config.EXAM_DATE)
            current, capacity = self.find_exam_capacity(exam_tr)
        except ValueError as e:
            print(str(e))

        if current == capacity:
            print(f"Exam is full :( --- {current} / {capacity}")
        else:
            print(f":) --- {current} / {capacity}")
            
        return current == capacity
    
