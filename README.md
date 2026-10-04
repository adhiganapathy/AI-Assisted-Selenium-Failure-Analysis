# AI-Assisted Selenium Failure Analysis

An enterprise-grade, **100% offline**, CUDA-accelerated test automation framework that uses local vision and reasoning AI models to autonomously diagnose Selenium test failures, capture UI visual context, and generate precise technical remediation commands without hardcoding.

---

## 🌟 Key Features

* **100% Offline & Private:** Runs entirely on your local machine using local model weights with zero internet dependency.
* **Multi-Modal AI Pipeline:**
  * **Florence-2 (`florence-community/Florence-2-base`)**: Captures detailed visual descriptions and UI layout context from crash screenshots.
  * **DeepSeek-R1 (`deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B`)**: Acts as an autonomous Senior Automation SRE, reasoning through exceptions to deliver concise, action-verb-led fixes.
* **Smart DOM & Selector Mining:** Dynamically extracts element IDs, explicit wait locators, and XPath targets straight from error strings.
* **Automated Artifact Management:** Automatically routes timestamped screenshots and structured text logs into a dedicated `artifact_logs/` directory.

---

## 📂 Project Structure

```text
├── artifact_logs/          # Automatically stores failure screenshots and execution logs
├── framework.py            # Core engine (AI model manager, DOM inspector, AI fix generator, logger)
├── test_suites.py          # Modular test suite containing all failure test scenarios
├── main.py                 # Main execution entry point
└── README.md               # Project documentation
