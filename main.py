from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import time
import requests
import base64
import json
import os
from PIL import Image
import io
import re
import google.generativeai as genai
from ai_learning import AILearningSystem

def capture_screenshot(driver, filename="screenshot.png"):
    """
    Capture a screenshot of the current page
    """
    try:
        driver.save_screenshot(filename)
        print(f"Screenshot saved as {filename}")
        return filename
    except Exception as e:
        print(f"Error capturing screenshot: {e}")
        return None

def get_page_text_content(driver):
    """
    Extract text content from the page
    """
    try:
        # Get the main content areas
        body_text = driver.find_element(By.TAG_NAME, "body").text
        title = driver.title
        
        # Get visible text content
        visible_elements = driver.find_elements(By.XPATH, "//*[not(self::script or self::style)]")
        visible_text = []
        
        for element in visible_elements:
            if element.is_displayed() and element.text.strip():
                visible_text.append(element.text.strip())
        
        return {
            "title": title,
            "body_text": body_text,
            "visible_text": visible_text[:10]  # First 10 visible text elements
        }
    except Exception as e:
        print(f"Error extracting text content: {e}")
        return None

# Configure Gemini AI
GEMINI_API_KEY = "Your Gemini api key goes here..."
genai.configure(api_key=GEMINI_API_KEY)

def verify_task_completion(screenshot_path, user_goal, current_analysis):
    """
    Verify if the user's goal has actually been accomplished by analyzing the current page
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Load the screenshot
        with open(screenshot_path, 'rb') as img_file:
            img_data = img_file.read()
        image = Image.open(io.BytesIO(img_data))
        
        verification_prompt = f"""
        You are a TASK VERIFICATION AI. Your job is to determine if a task has been ACTUALLY COMPLETED.
        
        ORIGINAL USER GOAL: "{user_goal}"
        
        CURRENT PAGE ANALYSIS: {current_analysis.get('ai_analysis', 'No analysis available')}
        
        Look at this screenshot and determine: HAS THE USER'S GOAL BEEN ACTUALLY ACCOMPLISHED?
        
        VERIFICATION RULES:
        
        🎥 "Play a video" / "Watch a video":
        - COMPLETED: Video player is visible, video is loading/playing, on a video page
        - NOT COMPLETED: Still on search results, still on homepage, no video player visible
        
        🔍 "Search for X":
        - COMPLETED: Search results for X are displayed, search was executed
        - NOT COMPLETED: Still on homepage, search not performed, wrong search results
        
        🛒 "Buy/Purchase X":
        - COMPLETED: Item in cart, on checkout page, purchase in progress
        - NOT COMPLETED: Still browsing, no item selected, not in cart
        
        📧 "Sign in/Login":
        - COMPLETED: User is logged in, dashboard visible, profile accessible
        - NOT COMPLETED: Still on login page, login failed, not authenticated
        
        🌐 "Go to website X":
        - COMPLETED: Actually on website X, correct URL, page loaded
        - NOT COMPLETED: Still on search results, wrong website, page not loaded
        
        📱 "Click on X":
        - COMPLETED: X was clicked, now on the destination page/content
        - NOT COMPLETED: Still on same page, X not clicked, no navigation occurred
        
        RESPOND WITH EXACTLY ONE OF THESE:
        TASK_COMPLETED: YES - [brief reason why it's complete]
        TASK_COMPLETED: NO - [brief reason why it's not complete and what's missing]
        
        Be STRICT in your evaluation. The user's goal must be ACTUALLY ACCOMPLISHED, not just partially done.
        """
        
        response = model.generate_content([verification_prompt, image])
        result = response.text.strip()
        
        if "TASK_COMPLETED: YES" in result:
            print(f"✅ Task Verification: COMPLETED - {result.split('YES - ')[1] if 'YES - ' in result else 'Goal achieved'}")
            return True, None
        else:
            reason = result.split('NO - ')[1] if 'NO - ' in result else 'Goal not achieved'
            print(f"❌ Task Verification: NOT COMPLETED - {reason}")
            return False, reason
            
    except Exception as e:
        print(f"⚠️  Task verification error: {e}")
        # Default to not completed if verification fails
        return False, f"Verification error: {e}"

def ask_gemini_why_stuck_and_how_to_fix(screenshot_path, user_goal, stuck_reason):
    """
    Ask Gemini to analyze WHY we're stuck and HOW to fix the specific problem
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Load the screenshot
        with open(screenshot_path, 'rb') as img_file:
            img_data = img_file.read()
        image = Image.open(io.BytesIO(img_data))
        
        problem_analysis_prompt = f"""
        🚨 PROBLEM ANALYSIS MODE 🚨
        
        I am an AI trying to accomplish this goal: "{user_goal}"
        
        But I am STUCK because: {stuck_reason}
        
        Looking at this screenshot, I need your help to understand:
        
        1. 🤔 WHY am I seeing this page/popup/challenge?
        2. 🔍 WHAT is this page asking me to do?
        3. 🛠️ HOW can I solve this specific problem to continue toward my goal?
        4. 📋 WHAT exact steps should I take to get past this obstacle?
        
        Common obstacles you might see:
        - 🤖 CAPTCHA/reCAPTCHA verification
        - 🚫 Access denied/blocked pages
        - 📧 Email verification requests
        - 🔐 Login/authentication requirements
        - 🍪 Cookie consent popups
        - 📱 Mobile app redirect prompts
        - ⚠️ Error pages or timeouts
        - 🔒 Age verification or location restrictions
        
        Please provide a DETAILED SOLUTION in this format:
        
        PROBLEM_TYPE: [What kind of obstacle this is]
        WHY_HERE: [Why I'm seeing this page/challenge]
        WHAT_TO_DO: [What this page is asking me to do]
        SOLUTION_STEPS: [Step-by-step instructions to solve this]
        
        Example:
        PROBLEM_TYPE: reCAPTCHA verification
        WHY_HERE: Google detected unusual traffic and is verifying I'm human
        WHAT_TO_DO: Complete the reCAPTCHA challenge by checking "I'm not a robot"
        SOLUTION_STEPS: 
        1. Click the "I'm not a robot" checkbox
        2. Wait for verification to complete (may show image challenge)
        3. Complete any additional image selection if prompted
        4. Wait for redirect to original search results
        
        Be specific and actionable - I need to know exactly what to click/type/wait for!
        """
        
        response = model.generate_content([problem_analysis_prompt, image])
        return response.text.strip()
        
    except Exception as e:
        print(f"⚠️  Problem analysis error: {e}")
        return f"Error analyzing problem: {e}"

def analyze_with_gemini_ai(screenshot_path, user_instruction=None):
    """
    Analyze page content using Google's Gemini AI with vision capabilities
    """
    try:
        # Initialize Gemini Pro Vision model
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Load the screenshot
        if not os.path.exists(screenshot_path):
            return {"error": "Screenshot not found"}
            
        # Open and prepare the image
        with open(screenshot_path, 'rb') as img_file:
            img_data = img_file.read()
        
        # Convert to PIL Image
        image = Image.open(io.BytesIO(img_data))
        
        # Create the prompt for Gemini
        base_prompt = """
        You are an AI web navigation assistant. Analyze this webpage screenshot and provide detailed information about:
        
        1. **Page Type**: What kind of website/page is this? (search engine, social media, e-commerce, news, etc.)
        2. **Main Elements**: List all clickable elements, buttons, links, forms, search boxes you can see
        3. **Navigation Options**: What actions can a user take on this page?
        4. **Content Summary**: What is the main content/purpose of this page?
        5. **Interactive Elements**: Describe all buttons, links, forms, and their locations (top, bottom, left, right, center)
        
        Be very specific about what you see and where elements are located on the page.
        """
        
        if user_instruction:
            base_prompt += f"\n\n**User's Goal**: {user_instruction}\n"
            base_prompt += "Based on the user's goal, suggest the BEST next action to take on this page. Be specific about which element to click or interact with."
        
        # Send to Gemini
        response = model.generate_content([base_prompt, image])
        
        # Parse the response
        analysis_text = response.text
        
        return {
            "ai_analysis": analysis_text,
            "page_analyzed": True,
            "user_instruction": user_instruction
        }
        
    except Exception as e:
        print(f"Error in Gemini AI analysis: {e}")
        return {"error": f"Gemini AI analysis failed: {str(e)}"}

def ask_gemini_for_autonomous_actions(screenshot_path, user_goal, current_url, previous_actions=None):
    """
    Ask Gemini AI to make autonomous decisions and execute actions without asking permission
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Load the screenshot
        with open(screenshot_path, 'rb') as img_file:
            img_data = img_file.read()
        image = Image.open(io.BytesIO(img_data))
        
        # Build context from previous actions
        context = ""
        if previous_actions:
            context = f"\nPrevious actions taken: {', '.join([f'{a[0]}: {a[1]}' for a in previous_actions[-3:]])}"
        
        prompt = f"""
        You are an AUTONOMOUS AI web automation agent with FULL DECISION-MAKING POWER. 
        
        USER GOAL: "{user_goal}"
        CURRENT URL: {current_url}
        {context}
        
        You have COMPLETE AUTONOMY to:
        1. Make your own decisions about what actions to take
        2. Execute actions immediately without asking permission
        3. Adapt your strategy based on what you see
        4. Think multiple steps ahead
        5. Handle errors and try alternative approaches
        6. Complete the entire task independently
        
        IMPORTANT: You are NOT asking for permission - you are EXECUTING actions directly.
        
        CRITICAL VISUAL UNDERSTANDING RULES:
        
        🎥 VIDEO PLATFORMS (YouTube, etc.):
        - Video listings have THUMBNAIL + TITLE combinations
        - To click "first video" = click the thumbnail or title of the topmost video
        - To click "second video" = click the thumbnail or title of the video in position #2
        - Look for rectangular thumbnail images with video titles next to/below them
        - Video elements are usually in a vertical or grid layout
        
        🛒 E-COMMERCE (Amazon, eBay, etc.):
        - Product listings have PRODUCT IMAGE + TITLE + PRICE combinations
        - To click "first product" = click the image or title of the topmost product
        - Products are usually in grid or list format with consistent spacing
        
        📱 SOCIAL MEDIA (Facebook, Twitter, etc.):
        - Posts have PROFILE PICTURE + NAME + CONTENT combinations
        - Click on profile pictures, names, or post content to interact
        
        🔗 GENERAL LINK PATTERNS:
        - Links can be text, buttons, images, or image+text combinations
        - Look for underlined text, colored text, or clickable-looking elements
        - Buttons often have borders, background colors, or visual emphasis
        
        CRITICAL: When describing elements to click, be VERY SPECIFIC about their location and appearance:
        - "Sign In button in top right corner"
        - "email input field in the center of the page"
        - "Magic Link button below the email field"
        - "search box in the center of the page"
        - "first video thumbnail in the search results"
        - "second video title in the list"
        - "product image for iPhone in the search results"
        
        Looking at this webpage, analyze what you see and decide what actions to take to achieve the user's goal.
        
        Return your response in this EXACT format:
        THOUGHT: [Your reasoning about what you see and what you need to do]
        ACTION_1: [action_type]:[target_description]
        ACTION_2: [action_type]:[target_description]
        ...
        ACTION_N: [action_type]:[target_description]
        
        Available action types:
        - CLICK: Click on an element (be VERY specific about location/appearance)
        - TYPE: Type text (provide exact text to type)
        - NAVIGATE: Go to a URL (provide the URL)
        - SCROLL: Scroll direction (UP/DOWN/LEFT/RIGHT)
        - WAIT: Wait for element to load (specify what to wait for)
        - PRESS: Press a key (ENTER, TAB, ESC, etc.)
        - HOVER: Hover over an element
        - SELECT: Select from dropdown/options
        
        Examples:
        THOUGHT: I can see Google's search page. I need to click the search box, type the query, and press Enter to search.
        ACTION_1: CLICK:large search box in center of page
        ACTION_2: TYPE:python tutorials
        ACTION_3: PRESS:ENTER
        
        THOUGHT: I can see YouTube search results for Taylor Swift. I need to click on the second video in the list.
        ACTION_1: CLICK:second video thumbnail in the search results list
        
        THOUGHT: I can see Amazon search results for laptops. I need to click on the first laptop product.
        ACTION_1: CLICK:first laptop product image in the search results
        
        THOUGHT: I can see a sign-in page. I need to click the email field, type the email, then click the magic link button.
        ACTION_1: CLICK:email input field in the center of the form
        ACTION_2: TYPE:user@example.com
        ACTION_3: CLICK:Magic Link button below the email field
        
        Be intelligent, proactive, and decisive. Think like a human would - see the page, understand the goal, and take action.
        ALWAYS be specific about element locations and descriptions.
        
        WHEN YOU SEE LISTINGS (videos, products, posts, etc.), REMEMBER:
        - Each listing is a clickable unit (thumbnail + title + details)
        - Use positional references: "first", "second", "third", "top", "bottom"
        - Target either the thumbnail/image OR the title text
        - Be specific about what type of listing you're clicking
        """
        
        response = model.generate_content([prompt, image])
        return parse_autonomous_actions(response.text)
        
    except Exception as e:
        print(f"Error asking Gemini for autonomous actions: {e}")
        return []

def parse_autonomous_actions(gemini_response):
    """
    Parse Gemini's autonomous action suggestions
    """
    actions = []
    thought = ""
    lines = gemini_response.split('\n')
    
    for line in lines:
        line = line.strip()
        if line.startswith('THOUGHT:'):
            thought = line.replace('THOUGHT:', '').strip()
            print(f"🧠 AI Thought: {thought}")
        elif line.startswith('ACTION_'):
            try:
                # Extract action from format "ACTION_X: TYPE:description"
                action_part = line.split(':', 1)[1].strip()
                action_type, description = action_part.split(':', 1)
                action_type = action_type.strip().upper()
                description = description.strip()
                
                if action_type == 'CLICK':
                    actions.append(('ai_click', description))
                elif action_type == 'TYPE':
                    actions.append(('ai_type', description))
                elif action_type == 'NAVIGATE':
                    actions.append(('ai_navigate', description))
                elif action_type == 'SCROLL':
                    actions.append(('ai_scroll', description))
                elif action_type == 'WAIT':
                    actions.append(('ai_wait', description))
                elif action_type == 'PRESS':
                    actions.append(('ai_press', description))
                elif action_type == 'HOVER':
                    actions.append(('ai_hover', description))
                elif action_type == 'SELECT':
                    actions.append(('ai_select', description))
                    
            except Exception as e:
                print(f"Error parsing action line '{line}': {e}")
                continue
    
    return actions

def parse_gemini_actions(gemini_response):
    """
    Parse Gemini's action suggestions into executable actions
    """
    actions = []
    lines = gemini_response.split('\n')
    
    for line in lines:
        if line.strip().startswith('ACTION_'):
            try:
                # Extract action from format "ACTION_X: TYPE:description"
                action_part = line.split(':', 1)[1].strip()
                action_type, description = action_part.split(':', 1)
                action_type = action_type.strip().upper()
                description = description.strip()
                
                if action_type == 'CLICK':
                    actions.append(('ai_click', description))
                elif action_type == 'TYPE':
                    actions.append(('ai_type', description))
                elif action_type == 'NAVIGATE':
                    actions.append(('ai_navigate', description))
                elif action_type == 'SCROLL':
                    actions.append(('ai_scroll', description))
                elif action_type == 'WAIT':
                    actions.append(('ai_wait', description))
                    
            except Exception as e:
                print(f"Error parsing action line '{line}': {e}")
                continue
    
    return actions

def execute_autonomous_actions(driver, actions, ai_learner=None):
    """
    Execute autonomous AI actions with intelligent error handling, retry logic, and learning
    """
    wait = WebDriverWait(driver, 10)
    executed_actions = []
    current_website = driver.current_url.split('/')[2] if driver.current_url != 'data:,' else 'unknown'
    
    for action_type, description in actions:
        try:
            print(f"🤖 Autonomous Action: {action_type} - {description}")
            
            if action_type == 'ai_navigate':
                print(f"🌐 Navigating to: {description}")
                driver.get(description)
                time.sleep(3)
                executed_actions.append(('navigate', description))
                
            elif action_type == 'ai_click':
                # Intelligent element finding with multiple strategies
                print(f"🔍 Looking for element: {description}")
                element = find_element_by_description(driver, description)
                if element:
                    # Scroll to element if needed
                    driver.execute_script("arguments[0].scrollIntoView(true);", element)
                    time.sleep(0.5)
                    element.click()
                    print(f"✅ Clicked: {description}")
                    executed_actions.append(('click', description))
                    
                    # Record successful action for learning
                    if ai_learner:
                        ai_learner.record_action_success('click', description, True, current_website)
                else:
                    print(f"⚠️  Could not find element: {description}")
                    
                    # Record failed action for learning
                    if ai_learner:
                        ai_learner.record_element_failure(description, current_website, 'click', 'Element not found')
                        ai_learner.record_action_success('click', description, False, current_website)
                    
                    # Debug: Show all clickable elements on page
                    try:
                        all_buttons = driver.find_elements(By.XPATH, "//button | //a | //*[@role='button']")
                        print(f"🔍 Found {len(all_buttons)} clickable elements on page:")
                        for i, btn in enumerate(all_buttons[:5]):  # Show first 5
                            if btn.is_displayed():
                                print(f"  {i+1}. {btn.tag_name}: '{btn.text}' (class: {btn.get_attribute('class')})")
                    except:
                        pass
                    
                    # Try alternative strategies
                    if 'search' in description.lower():
                        # Try common search box selectors
                        search_selectors = ["input[name='q']", "input[type='search']", "textarea[name='q']"]
                        for selector in search_selectors:
                            try:
                                element = driver.find_element(By.CSS_SELECTOR, selector)
                                if element.is_displayed():
                                    element.click()
                                    print(f"✅ Found and clicked search box using selector")
                                    executed_actions.append(('click', 'search box (alternative)'))
                                    
                                    # Record successful alternative action
                                    if ai_learner:
                                        ai_learner.record_action_success('click', 'search box (alternative)', True, current_website)
                                    break
                            except:
                                continue
                    
            elif action_type == 'ai_type':
                # Smart typing with multiple fallback strategies
                success = False
                
                # Strategy 1: Active element
                try:
                    active_element = driver.switch_to.active_element
                    if active_element.tag_name in ['input', 'textarea']:
                        active_element.clear()
                        active_element.send_keys(description)
                        print(f"✅ Typed in active element: {description}")
                        success = True
                        executed_actions.append(('type', description))
                except:
                    pass
                
                # Strategy 2: Find input field
                if not success:
                    input_selectors = [
                        "input[type='text']", "input[type='search']", "textarea",
                        "input[name*='search']", "input[name*='q']", "input[placeholder*='search']"
                    ]
                    
                    for selector in input_selectors:
                        try:
                            input_field = driver.find_element(By.CSS_SELECTOR, selector)
                            if input_field.is_displayed():
                                input_field.clear()
                                input_field.send_keys(description)
                                print(f"✅ Typed in input field: {description}")
                                success = True
                                executed_actions.append(('type', description))
                                break
                        except:
                            continue
                
                if not success:
                    print(f"⚠️  Could not find input field to type: {description}")
                        
            elif action_type == 'ai_press':
                # Handle key presses
                key_mapping = {
                    'enter': Keys.RETURN,
                    'tab': Keys.TAB,
                    'escape': Keys.ESCAPE,
                    'space': Keys.SPACE
                }
                
                key_name = description.lower().strip()
                if key_name in key_mapping:
                    # Try to send to active element first
                    try:
                        active_element = driver.switch_to.active_element
                        active_element.send_keys(key_mapping[key_name])
                        print(f"✅ Pressed {key_name.upper()} in active element")
                        executed_actions.append(('press', key_name))
                    except:
                        # Send to body as fallback
                        body = driver.find_element(By.TAG_NAME, "body")
                        body.send_keys(key_mapping[key_name])
                        print(f"✅ Pressed {key_name.upper()}")
                        executed_actions.append(('press', key_name))
                else:
                    print(f"⚠️  Unknown key: {description}")
                    
            elif action_type == 'ai_scroll':
                if 'down' in description.lower():
                    driver.execute_script("window.scrollBy(0, 500);")
                    print("✅ Scrolled down")
                    executed_actions.append(('scroll', 'down'))
                elif 'up' in description.lower():
                    driver.execute_script("window.scrollBy(0, -500);")
                    print("✅ Scrolled up")
                    executed_actions.append(('scroll', 'up'))
                elif 'left' in description.lower():
                    driver.execute_script("window.scrollBy(-500, 0);")
                    print("✅ Scrolled left")
                    executed_actions.append(('scroll', 'left'))
                elif 'right' in description.lower():
                    driver.execute_script("window.scrollBy(500, 0);")
                    print("✅ Scrolled right")
                    executed_actions.append(('scroll', 'right'))
                    
            elif action_type == 'ai_wait':
                # Parse wait time from description or use default
                wait_time = 2
                if 'second' in description.lower():
                    try:
                        wait_time = int(re.findall(r'\d+', description)[0])
                    except:
                        pass
                time.sleep(wait_time)
                print(f"✅ Waited {wait_time} seconds")
                executed_actions.append(('wait', f'{wait_time}s'))
                
            elif action_type == 'ai_hover':
                element = find_element_by_description(driver, description)
                if element:
                    ActionChains(driver).move_to_element(element).perform()
                    print(f"✅ Hovered over: {description}")
                    executed_actions.append(('hover', description))
                else:
                    print(f"⚠️  Could not find element to hover: {description}")
                    
            elif action_type == 'ai_select':
                # Handle dropdown selections
                element = find_element_by_description(driver, description)
                if element:
                    element.click()
                    print(f"✅ Selected: {description}")
                    executed_actions.append(('select', description))
                else:
                    print(f"⚠️  Could not find element to select: {description}")
            
            time.sleep(1)  # Small delay between actions
            
        except Exception as e:
            print(f"❌ Error executing {action_type}: {e}")
            # Continue with next action instead of stopping
    
    return executed_actions

def find_element_by_description(driver, description):
    """
    Enhanced element finding with multiple intelligent strategies
    """
    description = description.lower()
    
    # Strategy 1: Direct text matching with multiple selectors
    text_selectors = [
        f"//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{description}')]",
        f"//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{description}')]",
        f"//input[@type='submit' and contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{description}')]",
        f"//span[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{description}')]",
        f"//div[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{description}')]",
        f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{description}')]"
    ]
    
    for selector in text_selectors:
        try:
            elements = driver.find_elements(By.XPATH, selector)
            for element in elements:
                if element.is_displayed() and element.is_enabled():
                    return element
        except:
            continue
    
    # Strategy 2: Common button patterns
    if any(keyword in description for keyword in ['sign in', 'login', 'signin']):
        signin_selectors = [
            "//button[contains(text(), 'Sign') or contains(text(), 'sign')]",
            "//a[contains(text(), 'Sign') or contains(text(), 'sign')]",
            "//*[contains(text(), 'Sign In') or contains(text(), 'sign in')]",
            "//button[contains(@class, 'signin') or contains(@class, 'login')]",
            "//a[contains(@class, 'signin') or contains(@class, 'login')]",
            "//*[@id='signin' or @id='login']",
            "//*[contains(@aria-label, 'sign') or contains(@aria-label, 'login')]"
        ]
        
        for selector in signin_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        return element
            except:
                continue
    
    # Strategy 3: Search box detection with expanded patterns
    if 'search' in description:
        search_selectors = [
            "input[name='q']", "input[name='search']", "input[type='search']",
            "textarea[name='q']", "input[placeholder*='search']", "input[aria-label*='search']",
            "input[placeholder*='Search']", "input[aria-label*='Search']",
            "//input[@type='text' and contains(@placeholder, 'search')]",
            "//textarea[contains(@placeholder, 'search')]"
        ]
        
        for selector in search_selectors:
            try:
                if selector.startswith("//"):
                    elements = driver.find_elements(By.XPATH, selector)
                else:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        return element
            except:
                continue
    
    # Strategy 4: Magic link specific patterns
    if 'magic' in description or 'link' in description:
        magic_selectors = [
            "//button[contains(text(), 'Magic') or contains(text(), 'magic')]",
            "//a[contains(text(), 'Magic') or contains(text(), 'magic')]",
            "//*[contains(text(), 'Magic Link') or contains(text(), 'magic link')]",
            "//button[contains(text(), 'Link') or contains(text(), 'link')]",
            "//*[contains(@class, 'magic') or contains(@class, 'link')]"
        ]
        
        for selector in magic_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        return element
            except:
                continue
    
    # Strategy 5: Email input detection
    if '@' in description or 'email' in description:
        email_selectors = [
            "input[type='email']", "input[name='email']", "input[name='mail']",
            "input[placeholder*='email']", "input[placeholder*='Email']",
            "input[aria-label*='email']", "input[aria-label*='Email']",
            "//input[@type='text' and contains(@placeholder, 'email')]",
            "//input[@type='text' and contains(@placeholder, 'Email')]"
        ]
        
        for selector in email_selectors:
            try:
                if selector.startswith("//"):
                    elements = driver.find_elements(By.XPATH, selector)
                else:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        return element
            except:
                continue
    
    # Strategy 6: Video thumbnail and listing detection
    if any(keyword in description for keyword in ['video', 'thumbnail', 'first', 'second', 'third']):
        # Extract positional info
        position = 1  # default
        if 'second' in description:
            position = 2
        elif 'third' in description:
            position = 3
        elif 'fourth' in description:
            position = 4
        elif 'fifth' in description:
            position = 5
        
        # YouTube specific selectors
        youtube_selectors = [
            "//ytd-video-renderer",  # YouTube video container
            "//div[@id='contents']//a[@id='video-title']",  # YouTube video titles
            "//div[@id='contents']//img",  # YouTube thumbnails
            "//ytd-rich-item-renderer",  # YouTube grid items
            "//*[contains(@class, 'video')]//a",  # Generic video links
            "//*[contains(@class, 'thumbnail')]",  # Generic thumbnails
        ]
        
        for selector in youtube_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if len(elements) >= position:
                    element = elements[position - 1]  # Convert to 0-based index
                    if element.is_displayed() and element.is_enabled():
                        return element
            except:
                continue
    
    # Strategy 7: Product listing detection  
    if any(keyword in description for keyword in ['product', 'item', 'laptop', 'phone', 'buy']):
        # Extract positional info
        position = 1  # default
        if 'second' in description:
            position = 2
        elif 'third' in description:
            position = 3
        
        # E-commerce specific selectors
        product_selectors = [
            "//*[contains(@class, 'product')]//a",  # Generic product links
            "//*[contains(@class, 'item')]//a",  # Generic item links
            "//div[contains(@data-component-type, 'search-result')]//a",  # Amazon results
            "//*[contains(@class, 'search-result')]//a",  # Generic search results
        ]
        
        for selector in product_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if len(elements) >= position:
                    element = elements[position - 1]
                    if element.is_displayed() and element.is_enabled():
                        return element
            except:
                continue
    
    # Strategy 8: Generic clickable elements
    try:
        # Look for any clickable element
        clickable_selectors = [
            "//button", "//a", "//input[@type='submit']", "//input[@type='button']",
            "//*[@onclick]", "//*[@role='button']", "//*[@tabindex]"
        ]
        
        for selector in clickable_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        # Check if element text contains any part of description
                        element_text = element.text.lower()
                        if any(word in element_text for word in description.split()):
                            return element
            except:
                continue
    except:
        pass
    
    # Strategy 7: Last resort - try clicking by position (top-right for sign in)
    if 'sign in' in description or 'login' in description:
        try:
            # Try to find elements in top-right area
            elements = driver.find_elements(By.XPATH, "//button | //a | //*[@role='button']")
            for element in elements:
                if element.is_displayed() and element.is_enabled():
                    location = element.location
                    size = element.size
                    # Check if element is in top-right area
                    if location['x'] > 800 and location['y'] < 100:  # Approximate top-right
                        return element
        except:
            pass
    
    return None

def autonomous_ai_browser():
    """
    Fully autonomous AI browser automation with machine learning capabilities
    """
    try:
        # Initialize the AI Learning System
        ai_learner = AILearningSystem()
        
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Initialize the Chrome WebDriver
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("Miki Miki - AI-Powered Browser Automation with Gemini Vision")
        print("Made with love by Flash Dynamics Syndicate")
        print("=" * 70)
        print("🧠 Powered by Google Gemini Vision AI")
        print("👁️  AI can SEE, THINK, and ACT independently")
        print("🚀 NO PERMISSION REQUIRED - AI makes all decisions")
        print("🎯 Just give me a goal and I'll complete it!")
        print("📚 LEARNING: AI learns from mistakes and improves over time")
        print("=" * 70)
        print("\nExample goals:")
        print("- 'search for python tutorials on Google'")
        print("- 'go to YouTube and find funny videos'")
        print("- 'navigate to Amazon and search for laptops under $500'")
        print("- 'open Google and search for hello world'")
        print("- 'quit' to exit")
        print("=" * 70)
        
        # Show learning summary if available
        learning_summary = ai_learner.get_learning_summary()
        if learning_summary["total_tasks_attempted"] > 0:
            print(f"\n📊 AI LEARNING SUMMARY:")
            print(f"   Tasks attempted: {learning_summary['total_tasks_attempted']}")
            print(f"   Success rate: {learning_summary['success_rate']:.1%}")
            print(f"   Common mistakes learned: {learning_summary['common_mistakes_count']}")
            print(f"   Websites learned: {', '.join(learning_summary['websites_learned'])}")
            print("=" * 70)
        
        # Track all actions for context
        all_executed_actions = []
        
        while True:
            try:
                # Get user goal
                user_goal = input("\n🎯 What should I accomplish? ").strip()
                
                if user_goal.lower() in ['quit', 'exit', 'q']:
                    break
                
                if user_goal.lower() in ['learn', 'learning', 'insights']:
                    print("\n📚 AI LEARNING INSIGHTS:")
                    print("=" * 50)
                    
                    # Show common mistakes
                    common_mistakes = ai_learner.analyze_common_mistakes()
                    if common_mistakes:
                        print("🔍 COMMON MISTAKES:")
                        for mistake in common_mistakes[:5]:
                            if mistake['type'] == 'element_failure':
                                print(f"   ❌ {mistake['description']} (Failed {mistake['count']} times)")
                            elif mistake['type'] == 'low_success_action':
                                print(f"   ⚠️  {mistake['description']} (Success rate: {mistake['success_rate']:.1%})")
                    
                    # Show learning summary
                    summary = ai_learner.get_learning_summary()
                    print(f"\n📊 LEARNING SUMMARY:")
                    print(f"   Total tasks: {summary['total_tasks_attempted']}")
                    print(f"   Success rate: {summary['success_rate']:.1%}")
                    print(f"   Websites learned: {', '.join(summary['websites_learned'])}")
                    print("=" * 50)
                    continue
                
                if not user_goal:
                    continue
                
                print(f"\n🧠 Autonomous AI Goal: {user_goal}")
                print("🤖 AI is taking control and executing independently...")
                
                # Get learning suggestions for this task
                current_website = driver.current_url.split('/')[2] if driver.current_url != 'data:,' else 'unknown'
                learning_suggestions = ai_learner.get_improvement_suggestions(user_goal, current_website)
                learned_strategies = ai_learner.get_learned_strategies(user_goal, current_website)
                
                if learning_suggestions:
                    print(f"\n📚 LEARNING INSIGHTS:")
                    for suggestion in learning_suggestions[:3]:  # Show top 3
                        print(f"   💡 {suggestion}")
                
                if learned_strategies:
                    print(f"\n🎯 LEARNED STRATEGIES:")
                    for strategy in learned_strategies[:2]:  # Show top 2
                        print(f"   ✅ Similar task: {strategy['goal']} (Success: {strategy['success_rate']:.1%})")
                
                # If no page is loaded yet, start with Google
                current_url = driver.current_url
                if current_url == 'data:,' or 'about:blank' in current_url:
                    print("🌐 Starting with Google.com...")
                    driver.get("https://www.google.com")
                    time.sleep(2)
                
                # Capture current page
                screenshot_path = capture_screenshot(driver)
                
                # Get AI analysis of current page
                print("👁️  AI is analyzing the current page...")
                ai_analysis = analyze_with_gemini_ai(screenshot_path, user_goal)
                
                if 'error' in ai_analysis:
                    print(f"❌ AI Analysis Error: {ai_analysis['error']}")
                    continue
                
                # Display AI's understanding
                print("\n" + "="*70)
                print("🧠 AI UNDERSTANDING:")
                print("="*70)
                print(ai_analysis['ai_analysis'])
                print("="*70)
                
                # AI makes autonomous decisions and executes immediately
                print("\n🤖 AI is making autonomous decisions...")
                ai_actions = ask_gemini_for_autonomous_actions(screenshot_path, user_goal, current_url, all_executed_actions)
                
                if not ai_actions:
                    print("❌ AI couldn't determine actions. Trying alternative approach...")
                    continue
                
                print(f"\n📋 AI decided to execute {len(ai_actions)} actions:")
                for i, (action_type, description) in enumerate(ai_actions, 1):
                    print(f"  {i}. {action_type.upper()}: {description}")
                
                # Execute actions immediately without asking permission
                print(f"\n🚀 AI is executing actions AUTONOMOUSLY...")
                executed_actions = execute_autonomous_actions(driver, ai_actions, ai_learner)
                all_executed_actions.extend(executed_actions)
                
                # Wait and analyze result
                time.sleep(3)
                final_screenshot = capture_screenshot(driver, "result_screenshot.png")
                
                print("\n🔍 AI is analyzing the results...")
                final_analysis = analyze_with_gemini_ai(final_screenshot, user_goal)
                
                print("\n" + "="*70)
                print("📊 AI CURRENT STATUS:")
                print("="*70)
                print(final_analysis.get('ai_analysis', 'Analysis unavailable'))
                print("="*70)
                
                # Check if task is actually completed
                print("\n🎯 Verifying task completion...")
                task_completed, stuck_reason = verify_task_completion(final_screenshot, user_goal, final_analysis)
                
                # Record task attempt for learning
                final_url = driver.current_url
                ai_learner.record_task_attempt(user_goal, all_executed_actions, task_completed, final_url, final_screenshot)
                
                if task_completed:
                    print(f"\n✅ AI SUCCESSFULLY completed the task: {user_goal}")
                    print(f"📈 Total actions executed: {len(all_executed_actions)}")
                    
                    # Show learning improvement
                    learning_summary = ai_learner.get_learning_summary()
                    print(f"📚 AI Learning Progress: {learning_summary['success_rate']:.1%} success rate")
                else:
                    print(f"\n⚠️  Task NOT fully completed yet. AI will continue working...")
                    print(f"🎯 Goal: {user_goal}")
                    print(f"🔄 Attempting to complete the remaining steps...")
                    
                    # Continue working until task is complete
                    max_attempts = 3
                    attempt = 1
                    
                    while not task_completed and attempt <= max_attempts:
                        print(f"\n🔄 Continuation attempt {attempt}/{max_attempts}")
                        
                        # 🧠 SMART PROBLEM ANALYSIS: Ask Gemini WHY we're stuck and HOW to fix it
                        print("\n🤔 Analyzing WHY we're stuck and HOW to solve this problem...")
                        print("="*70)
                        problem_solution = ask_gemini_why_stuck_and_how_to_fix(final_screenshot, user_goal, stuck_reason)
                        print("🧠 PROBLEM ANALYSIS & SOLUTION:")
                        print("="*70)
                        print(problem_solution)
                        print("="*70)
                        
                        # AI analyzes current state and plans next actions with the solution context
                        enhanced_prompt = f"""CONTINUE TASK: {user_goal}. 

PROBLEM ANALYSIS: {problem_solution}

Based on the problem analysis above, implement the suggested solution steps to get past this obstacle and continue toward the goal. Use the specific instructions provided in the SOLUTION_STEPS."""
                        
                        continue_actions = ask_gemini_for_autonomous_actions(
                            final_screenshot, 
                            enhanced_prompt, 
                            driver.current_url, 
                            all_executed_actions
                        )
                        
                        if continue_actions:
                            print(f"\n📋 AI continuing with {len(continue_actions)} more actions:")
                            for i, (action_type, description) in enumerate(continue_actions, 1):
                                print(f"  {i}. {action_type.upper()}: {description}")
                            
                            # Execute continuation actions
                            print(f"\n🚀 AI continuing execution...")
                            new_executed = execute_autonomous_actions(driver, continue_actions, ai_learner)
                            all_executed_actions.extend(new_executed)
                            
                            # Check again
                            time.sleep(3)
                            final_screenshot = capture_screenshot(driver, f"verification_{attempt}.png")
                            final_analysis = analyze_with_gemini_ai(final_screenshot, user_goal)
                            task_completed, stuck_reason = verify_task_completion(final_screenshot, user_goal, final_analysis)
                            
                            if task_completed:
                                print(f"\n✅ AI SUCCESSFULLY completed the task after {attempt} continuation attempts!")
                                break
                        else:
                            print(f"\n❌ AI couldn't determine continuation actions for attempt {attempt}")
                        
                        attempt += 1
                    
                    if not task_completed:
                        print(f"\n⚠️  AI could not fully complete the task after {max_attempts} attempts")
                        print(f"📊 Total actions executed: {len(all_executed_actions)}")
                    else:
                        print(f"📈 Total actions executed: {len(all_executed_actions)}")
                
            except KeyboardInterrupt:
                print("\n\n⏹️  Interrupted by user")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                print("🤖 AI will continue with next task...")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Make sure you have Chrome browser installed and ChromeDriver set up.")
    
    finally:
        # Close the browser
        try:
            driver.quit()
            print("\n🔚 Browser closed.")
        except:
            pass

if __name__ == "__main__":
    autonomous_ai_browser()
