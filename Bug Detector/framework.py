import os
import time
import re
import traceback
import torch
import torch.nn.functional as F
from PIL import Image
from datetime import datetime
from selenium.webdriver.common.by import By

class AIModelManager:
    """Manages offline local model caching and loading on CUDA/CPU."""
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.vision_model = None
        self.vision_processor = None
        self.reasoning_model = None
        self.tokenizer = None

    def load_models(self):
        if self.vision_model is None or self.reasoning_model is None:
            print(f"🚀 Loading AI models from local cache on {self.device.upper()} (Zero internet usage)...")
            from transformers import AutoProcessor, Florence2ForConditionalGeneration, AutoTokenizer, AutoModelForCausalLM
            
            florence_id = "florence-community/Florence-2-base"
            self.vision_processor = AutoProcessor.from_pretrained(florence_id, local_files_only=True)
            self.vision_model = Florence2ForConditionalGeneration.from_pretrained(florence_id, local_files_only=True).to(self.device)
            
            reasoning_id = "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"
            self.tokenizer = AutoTokenizer.from_pretrained(reasoning_id, local_files_only=True)
            self.reasoning_model = AutoModelForCausalLM.from_pretrained(
                reasoning_id,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto",
                local_files_only=True
            )
            print("✅ Models ready locally in memory!\n")
        return self.vision_processor, self.vision_model, self.tokenizer, self.reasoning_model


class DOMInspector:
    """Handles smart selector mining, element location, and DOM/CSS extraction."""
    @staticmethod
    def extract_selector_and_dom(driver, exception_obj):
        error_message = str(exception_obj).strip()
        extracted_selector = "Unknown / Dynamic Element"
        
        match = re.search(r'selector["\']?\s*:\s*["\']([^"\']+)["\']', error_message, re.IGNORECASE)
        if match:
            extracted_selector = match.group(1)
        else:
            wait_match = re.search(r'By\.([a-z]+)[:\s]+([^\s,)]+)', error_message, re.IGNORECASE)
            if wait_match:
                by_type = wait_match.group(1).lower()
                by_val = wait_match.group(2).strip()
                if by_type == "id":
                    extracted_selector = f"#{by_val}"
                elif by_type in ["cssselector", "css", "xpath"]:
                    extracted_selector = by_val
                else:
                    extracted_selector = f"[{by_type}='{by_val}']"
            else:
                id_match = re.search(r'id=["\']([^"\']+)["\']', error_message, re.IGNORECASE)
                if id_match:
                    extracted_selector = f"#{id_match.group(1)}"
                else:
                    plain_id_match = re.search(r'\bid[:\s]+([a-zA-Z0-9\-_]+)', error_message, re.IGNORECASE)
                    if plain_id_match:
                        extracted_selector = f"#{plain_id_match.group(1)}"
                    else:
                        parts = error_message.split(":")
                        if len(parts) > 1:
                            candidate = parts[-1].strip()
                            if "\n" not in candidate and "chromedriver" not in candidate.lower() and len(candidate) < 100:
                                extracted_selector = candidate

        dom_info = {"selector": extracted_selector, "html": "Element not found in DOM", "css": {}}
        
        try:
            if extracted_selector.startswith("//") or extracted_selector.startswith("("):
                element = driver.find_element(By.XPATH, extracted_selector)
            elif extracted_selector.startswith("#"):
                element = driver.find_element(By.ID, extracted_selector[1:])
            else:
                element = driver.find_element(By.CSS_SELECTOR, extracted_selector)
                
            dom_info["html"] = element.get_attribute('outerHTML')
            dom_info["css"] = driver.execute_script("""
                var el = arguments[0];
                var style = window.getComputedStyle(el);
                return {
                    display: style.display,
                    visibility: style.visibility,
                    opacity: style.opacity,
                    zIndex: style.zIndex,
                    position: style.position
                };
            """, element)
        except Exception:
            dom_info["html"] = f"Selector '{extracted_selector}' could not be located in active DOM."
            dom_info["css"] = "N/A - Element absent"
            
        return dom_info


class AIFixGenerator:
    """Handles vision captioning and DeepSeek-R1 reasoning fix generation."""
    @staticmethod
    def extract_ui_caption(processor, vision_model, image, device):
        task = "<DETAILED_CAPTION>"
        inputs = processor(text=task, images=image, return_tensors="pt").to(device)
        with torch.no_grad():
            gen_ids = vision_model.generate(**inputs, max_new_tokens=100, do_sample=False)
        raw_caption = processor.batch_decode(gen_ids, skip_special_tokens=True)[0]
        if isinstance(raw_caption, dict):
            raw_caption = raw_caption.get(task, str(raw_caption))
        return raw_caption

    @staticmethod
    def generate_fix(tokenizer, model, device, compiler_error, ui_caption, dom_context):
        ai_prompt = f"""<｜begin of sentence｜><｜User｜>You are a Senior Automation SRE. Analyze this Selenium error and provide a direct, one-sentence technical fix starting with an action verb (e.g., Wait, Configure, Bypass, Update). No conversational intro.

Rules:
1. Start directly with an action verb (e.g., 'Increase', 'Update', 'Refactor', 'Handle', 'Configure').
2. Zero conversational intro, zero explanations, zero thinking steps in the output. Just be clear on issue and fix.
- Exception: {compiler_error}
- Selector: {dom_context['selector']}
- UI Layout: {ui_caption}

Direct Fix:
<｜Assistant｜><｜think｜>"""

        inputs = tokenizer(ai_prompt, return_tensors="pt").to(device)
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=200,
                num_beams=5,
                num_return_sequences=5,
                return_dict_in_generate=True,
                temperature=0.3,
                repetition_penalty=1.3,
                output_scores=True,
                do_sample=False
            )
        
        sequences = outputs.sequences
        if hasattr(outputs, "sequences_scores") and outputs.sequences_scores is not None:
            probabilities = F.softmax(outputs.sequences_scores, dim=0)
            selected_index = torch.multinomial(probabilities, num_samples=1).item()
        else:
            selected_index = 0

        chosen_sequence = sequences[selected_index]
        full_text = tokenizer.decode(chosen_sequence, skip_special_tokens=True)
        
        if "</think>" in full_text:
            raw_output = full_text.split("</think>")[-1].strip()
        else:
            raw_output = full_text.split("<｜Assistant｜>")[-1].strip()

        clean_fix = re.sub(r'<[^>]+>', '', raw_output).strip()    
        
        if len(clean_fix) < 5 or clean_fix.lower() == "fix":
            clean_fix = f"Inspect the state of selector '{dom_context['selector']}' and adjust synchronization parameters."

        return clean_fix


class AutonomousTestFramework:
    """Orchestrates browser execution, folder artifact generation, and autonomous logging."""
    def __init__(self, log_folder="artifact_logs"):
        self.log_folder = log_folder
        os.makedirs(self.log_folder, exist_ok=True)
        self.model_manager = AIModelManager()

    def handle_failure(self, driver, exception_obj):
        # Capture the actual raw python compiler traceback output
        full_compiler_traceback = traceback.format_exc()

        processor, vision_model, tokenizer, reasoning_model = self.model_manager.load_models()

        timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        error_name = type(exception_obj).__name__
        
        screenshot_filename = os.path.join(self.log_folder, f"{error_name}_{timestamp_str}.png")
        ui_caption = "Visual context unavailable."

        try:
            driver.save_screenshot(screenshot_filename)
            image = Image.open(screenshot_filename).convert("RGB")
            ui_caption = AIFixGenerator.extract_ui_caption(processor, vision_model, image, self.model_manager.device)
        except Exception:
            screenshot_filename = "N/A (Browser hung or disconnected)"

        dom_context = DOMInspector.extract_selector_and_dom(driver, exception_obj)
        
        raw_error_str = str(exception_obj).strip()
        if not raw_error_str:
            raw_error_str = repr(exception_obj)
            
        compiler_error = f"{error_name}: {raw_error_str}"
        
        one_line_fix = AIFixGenerator.generate_fix(
            tokenizer, reasoning_model, self.model_manager.device, compiler_error, ui_caption, dom_context
        )

        log_file_path = os.path.join(self.log_folder, "test_execution_logs.txt")
        log_entry = f"""
{'=' * 50}
TIMESTAMP           : {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
❌ Exception Caught  : {compiler_error}
🎯 Auto-Parsed Selector: {dom_context['selector']}
📝 UI Visual Caption : {ui_caption}
🖼️  Saved Screenshot  : {screenshot_filename}
🛠️️  AI Fix            : {one_line_fix}

--- 🖥️ ACTUAL COMPILER TRACEBACK OUTPUT ---
{full_compiler_traceback.strip()}
{'=' * 105}
"""
        print(log_entry)
        with open(log_file_path, "a", encoding="utf-8") as log_file:
            log_file.write(log_entry + "\n")
        print(f"📁 Log successfully saved to '{log_file_path}'")