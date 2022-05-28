from time import sleep
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

import config
from neptun_driver import NeptunDriver


if __name__ == "__main__":
    try:        
        options = Options()
        driver = webdriver.Firefox(options=options)
        driver.implicitly_wait(config.PAGE_TIMEOUT)

        neptun_driver = NeptunDriver(driver=driver)
        neptun_driver.login()

        neptun_driver.go_to_exam_signup_page()

        tries = 1
        print(f"Try #{tries}")
        
        exam_is_full = neptun_driver.check_if_full()
        
        while exam_is_full:
            print(f"Retrying in {config.RETRY_EVERY} seconds...")
            sleep(config.RETRY_EVERY)
            
            driver.refresh()
            
            print()
            tries += 1
            print(f"Try #{tries}")
            
            exam_is_full = neptun_driver.check_if_full()
    except KeyboardInterrupt:
        print("Bye-bye")
    finally:
        import sys
        driver.quit()
        sys.exit()
