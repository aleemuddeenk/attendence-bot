from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import requests
import base64
import time
USERNAME = "2117250010001"
PASSWORD = "8838820040"
OPENROUTER_API_KEY = "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"
BOT_TOKEN = "8555720531:AAH594n-mNtnDU7QwKW9IsUH4OnswdVzSUQ"
CHAT_ID = "8317311861"

def take_attendance_screenshot():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=options)
    
    # Login
    driver.get("https://ims.ritchennai.edu.in/admin")
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.NAME, "email"))).send_keys(USERNAME)
    driver.find_element(By.NAME, "password").send_keys(PASSWORD)
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    time.sleep(5)
    
    # Go to attendance page
    driver.get("https://ims.ritchennai.edu.in/admin/student-personal-attendance/report")
    time.sleep(3)
    
    # Zoom out to fit full table
    driver.execute_script("document.body.style.zoom='75%'")
    time.sleep(1)
    
    # Full page screenshot
    total_height = driver.execute_script("return document.body.scrollHeight")
    driver.set_window_size(1920, total_height)
    time.sleep(1)
    driver.save_screenshot("attendance.png")
    driver.quit()
    print("Screenshot taken ✅")
def analyze_attendance():
    with open("attendance.png", "rb") as f:
        img_data = base64.b64encode(f.read()).decode("utf-8")

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
        json={
            "model": "nvidia/nemotron-nano-12b-v2-vl:free",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_data}"}},
                        {"type": "text", "text": (
                            "This is a college attendance report. "
                            "List each subject name and attendance percentage. "
                            "Mark subjects below 75% with ⚠️ and subjects below 65% with 🚨. "
                            "At the end, add a summary line with the lowest attendance subject."
                        )}
                    ]
                }
            ]
        }
    )
    data = response.json()
    print(data)
if "choices" in data:
    return data["choices"][0]["message"]["content"]
else:
    return f"API Error: {data}"

def send_to_telegram(text):
    # Send photo
    url_photo = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    with open("attendance.png", "rb") as f:
        requests.post(url_photo, data={"chat_id": CHAT_ID, "caption": "📊 Attendance Screenshot"}, files={"photo": f})
    
    # Send text report
    url_text = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url_text, json={
        "chat_id": CHAT_ID,
        "text": f"📊 *Attendance Report*\n\n{text}",
        "parse_mode": "Markdown"
    })
    print("Sent to Telegram ✅")
# Run
take_attendance_screenshot()
result = analyze_attendance()
print(result)
send_to_telegram(result)
