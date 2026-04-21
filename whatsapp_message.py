# whatsapp_message.py

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import mysql.connector
from mysql.connector import Error
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

# Initialize the Chrome WebDriver
def init_driver():
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    driver.get('https://web.whatsapp.com')
    return driver

# Send a personalized message to a single contact
def send_message(driver, contact_name, contact_number, message):
    try:
        print(f"Searching for contact: {contact_name}")
        search_box = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true'][@data-tab='3']"))
        )
        search_box.clear()
        search_box.send_keys(contact_name)
        search_box.send_keys(Keys.ENTER)
        time.sleep(5)  # Adjust delay if needed

        print(f"Sending message to {contact_name}")
        message_box = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true'][@data-tab='10']"))
        )
        message_box.send_keys(message)
        message_box.send_keys(Keys.ENTER)
        print(f"Message sent to {contact_name}")
        return 'Sent'
    except Exception as e:
        print(f"Failed to send message to {contact_name}: {str(e)}")
        return 'Failed'

# Personalize a message template
def personalize_message(template, variables):
    for key, value in variables.items():
        template = template.replace(f"{{{{{key}}}}}", value)
    return template

# Save message statistics to MySQL
def save_to_db(name, number, status, message):
    try:
        conn = mysql.connector.connect(
            host='localhost',
            database='whatsapp_bulk_sender',
            user='root',
            password='$iddhI'
        )
        if conn.is_connected():
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO message_stats (date, contact_name, contact_number, message, status) VALUES (NOW(), %s, %s, %s, %s)",
                (name, number, message, status)
            )
            conn.commit()
            cursor.close()
    except Error as e:
        print(f"Error: {e}")
    finally:
        if conn.is_connected():
            conn.close()

# Send bulk messages with contact names and numbers loaded from a CSV file
def send_bulk_messages_from_file(driver, contacts_file, template):
    contacts_df = pd.read_csv(contacts_file)
    for index, row in contacts_df.iterrows():
        name = row['name']
        number = row['number']
        personalized_message = personalize_message(template, {'name': name})
        status = send_message(driver, name, number, personalized_message)
        save_to_db(name, number, status, personalized_message)
        time.sleep(5)  # Increased delay between messages to avoid rate limiting

if __name__ == "__main__":
    driver = init_driver()
    print("Please scan the QR code to log in to WhatsApp Web.")
    time.sleep(120)  # Time to scan QR code

    # Example template with a placeholder for the name
    template = "Hello {{name}}, this is a reminder for our upcoming meeting. Please don't forget to bring the required documents."
    
    # Path to your CSV file with contact details
    contacts_file = 'contacts.csv'

    # Send bulk messages
    send_bulk_messages_from_file(driver, contacts_file, template)
