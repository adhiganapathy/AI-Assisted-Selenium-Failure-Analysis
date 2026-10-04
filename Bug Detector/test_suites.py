from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class TestScenariosSuite:
    """Contains all test scenarios packed cleanly in a modular test suite class."""
    
    @staticmethod
    def run_scenario(driver, scenario_name):
        if scenario_name == "stale":
            print("\n🧪 Page: SauceDemo Inventory Page | Scenario: StaleElementReferenceException")
            driver.get("https://www.saucedemo.com/")
            driver.find_element(By.ID, "user-name").send_keys("standard_user")
            driver.find_element(By.ID, "password").send_keys("secret_sauce")
            driver.find_element(By.ID, "login-button").click()
            
            item = driver.find_element(By.ID, "item_4_title_link")
            driver.refresh()
            item.click() # Triggers StaleElementReferenceException

        elif scenario_name == "timeout":
            print("\n🧪 Page: DemoQA Alerts | Scenario: TimeoutException")
            driver.get("https://demoqa.com/alerts")
            driver.find_element(By.ID, "timerAlertButton").click()
            WebDriverWait(driver, 1).until(EC.alert_is_present())

        elif scenario_name == "not_interactable":
            print("\n🧪 Page: DemoQA Dynamic Properties | Scenario: ElementNotInteractableException")
            driver.get("https://demoqa.com/dynamic-properties")
            driver.find_element(By.ID, "enableAfter").send_keys("Hello World")

        elif scenario_name == "intercepted":
            print("\n🧪 Page: SauceDemo Catalog | Scenario: ElementClickInterceptedException")
            driver.get("https://www.saucedemo.com/")
            driver.execute_script("""
                let div = document.createElement('div');
                div.style = 'position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:999999;background:rgba(0,0,0,0.5);';
                document.body.appendChild(div);
            """)
            driver.find_element(By.ID, "login-button").click()

        elif scenario_name == "invalid_selector":
            print("\n🧪 Page: SauceDemo Login | Scenario: InvalidSelectorException")
            driver.get("https://www.saucedemo.com/")
            driver.find_element(By.CSS_SELECTOR, "div:::")

        elif scenario_name == "spinner_timeout":
            print("\n🧪 Page: SauceDemo Inventory | Scenario: Spinner TimeoutException")
            driver.get("https://www.saucedemo.com/")
            driver.find_element(By.ID, "user-name").send_keys("standard_user")
            driver.find_element(By.ID, "password").send_keys("secret_sauce")
            driver.find_element(By.ID, "login-button").click()
            
            driver.execute_script("""
                let loader = document.createElement('div');
                loader.id = 'loading-spinner';
                loader.style = 'position:fixed;top:0;left:0;width:100vw;height:100vh;background:rgba(0,0,0,0.7);z-index:999999;display:flex;justify-content:center;align-items:center;color:white;font-size:28px;font-family:sans-serif;';
                loader.innerText = '🔄 Loading inventory data...';
                document.body.appendChild(loader);
            """)
            
            WebDriverWait(driver, 3).until(
                EC.invisibility_of_element_located((By.ID, "loading-spinner"))
            )

        elif scenario_name == "unhandled_alert":
            print("\n🧪 Page: Herokuapp JavaScript Alerts | Scenario: UnhandledAlertException")
            driver.get("https://demoqa.com/alerts")
            driver.find_element(By.ID, "alertButton").click()
            driver.find_element(By.ID, "content")
        
        else:
            raise ValueError(f"Unknown scenario name: '{scenario_name}'")