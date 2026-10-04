import time
from selenium import webdriver
from framework import AutonomousTestFramework
from test_suites import TestScenariosSuite

if __name__ == "__main__":
    # Initialize the autonomous framework (handles artifact_logs folder automatically)
    framework = AutonomousTestFramework(log_folder="artifact_logs")
    
    print("🌐 Launching Chrome Browser...")
    options = webdriver.ChromeOptions()
    options.page_load_strategy = 'eager'  
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(30)
    
    # CHOOSE WHICH EXCEPTION SCENARIO TO TEST FROM THE SUITE:
    # Options: "stale", "timeout", "not_interactable", "intercepted", "invalid_selector", "spinner_timeout", "unhandled_alert"
    active_scenario = "spinner_timeout" 
    
    try:
        # Main suite simply calls the scenarios suite!
        TestScenariosSuite.run_scenario(driver, active_scenario)

    except Exception as e:
        # Pass exception & driver to the framework handler for AI diagnosis and logging
        framework.handle_failure(driver, e)
        
    finally:
        time.sleep(2)
        print("🧹 Closing browser session.")
        driver.quit()