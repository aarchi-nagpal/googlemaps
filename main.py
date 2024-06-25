import mysql.connector
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import re

# Selenium part
details = {
    "Business Name": [],
    "Address": [],
    "Category": [],
    "Review Average": [],
    "Review Count": [],
    "Website": [],
    "Phone Number": [],
}

browser = webdriver.Chrome()
browser.get('https://www.google.co.in/maps/search/hospital+near+me/@30.6198219,74.2339141,14z/data=!3m1!4b1?entry=ttu')
time.sleep(2)

shop_element = browser.find_elements(By.XPATH, "//a[contains(@class, 'hfpxzc')]")
saturation = True
ref = 0

while saturation:
    current_length = len(shop_element)
    element = shop_element[current_length - 1]
    actions = ActionChains(browser)
    actions.move_to_element(element).perform()
    try:
        end_of_scroll = browser.find_element(By.XPATH, "//span[contains(@class, 'HlvSq')]")
        saturation = False
        break
    except:
        try:
            end = browser.find_element(By.XPATH, "//div[contains(@class, 'njRcn')]")
            if end:
                saturation = False
                break
        except:
            pass
    if shop_element.index(element) == len(shop_element) - 1:
        browser.execute_script("arguments[0].scrollIntoView();", element)
    shop_element = browser.find_elements(By.XPATH, "//a[contains(@class, 'hfpxzc')]")

def shop_url(f_element=shop_element):
    """Extracts URL to details about shop"""
    shopurl = [element.get_attribute('href') for element in f_element]
    return shopurl

def extractor():
    # shop name
    try:
        business_name = browser.find_element(By.XPATH, "//h1[contains(@class, 'DUwDvf')]").text
    except:
        business_name = "N/A"
    
    # review
    try:
        review = browser.find_element(By.XPATH, "//div[contains(@class, 'F7nice')]").text.strip()
        review = review.split('\n')
        review_average = review[0].strip() if len(review) > 0 else "N/A"
        review_count = review[1].replace('(', '').replace(')', '').strip() if len(review) > 1 else "N/A"
    except:
        review_average = "No reviews"
        review_count = "No reviewer"
    
    try:
        category = browser.find_element(By.XPATH, "//button[contains(@class, 'DkEaL')]").text.strip()
    except:
        category = "N/A"
    
    # regex
    add_num_web_element = browser.find_elements(By.XPATH, "//div[contains(@class, 'rogA2c')]")
    phone_pattern_regex = r'\b(?:\+?\d{1,3})?[-.\s]??(?:\d{10}|\d{5}[-.\s]?\d{5})\b'
    website_pattern_regex = r'\b(?!facebook\.com\b)(?!instagram\.com\b)(?!swiggy\.com\b)(?!zomato\.com\b)([a-zA-Z0-9.-]+\.[a-zA-Z]{2,7})\b'
    complete_string = " ".join([element.text for element in add_num_web_element])
    
    phone_num = re.findall(phone_pattern_regex, complete_string)
    phone_num = phone_num[0] if phone_num else "N/A"
    
    website = re.findall(website_pattern_regex, complete_string)
    website = website[0] if website else "N/A"
    
    try:
        address = add_num_web_element[0].text
    except:
        address = "N/A"
    
    return [business_name, address, category, review_average, review_count, website, phone_num]

def visit_url(f_shopurl=shop_url()):
    for url in f_shopurl:
        browser.get(url)
        detail = extractor()
        details["Business Name"].append(detail[0])
        details["Address"].append(detail[1])
        details["Category"].append(detail[2])
        details["Review Average"].append(detail[3])
        details["Review Count"].append(detail[4])
        details["Website"].append(detail[5])
        details['Phone Number'].append(detail[6])

visit_url()
browser.quit()

# MySQL part
# Replace these with your actual database credentials
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'hosp_database'
}

# Establish a database connection
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

# Create table if not exists
create_table_query = """
CREATE TABLE IF NOT EXISTS HospitalDetails (
    BusinessName VARCHAR(255),
    Address TEXT,
    Category VARCHAR(255),
    ReviewAverage VARCHAR(255),
    ReviewCount VARCHAR(255),
    Website VARCHAR(255),
    PhoneNumber VARCHAR(255)
)
"""
cursor.execute(create_table_query)

# Insert data into the table
insert_query = """
INSERT INTO HospitalDetails (BusinessName, Address, Category, ReviewAverage, ReviewCount, Website, PhoneNumber)
VALUES (%s, %s, %s, %s, %s, %s, %s)
"""

# Convert dictionary values to list of tuples for insertion
data_to_insert = list(zip(details["Business Name"], details["Address"], details["Category"],
                          details["Review Average"], details["Review Count"], details["Website"],
                          details["Phone Number"]))

cursor.executemany(insert_query, data_to_insert)
conn.commit()
print(" successful..")

# Close the cursor and connection
cursor.close()
conn.close()

browser.quit()
