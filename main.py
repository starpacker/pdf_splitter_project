import fitz #PyMUPDF
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import shutil
import zipfile
import os
instrument1 = ["梆笛","曲笛","新笛","管子","高音笙","中音笙","低音笙","高音唢呐" ,"高唢" ,"中音唢呐" ,"中唢" ,"低音唢呐" ,"低唢"]
instrument2 = ["柳琴","大阮","中阮","琵琶","古筝","扬琴","箜篌"]
instrument3 = ["高胡","中胡","二胡"]
instrument4 = ["大胡","低音大胡","大提琴","贝斯","double bass","violoncello"]
instrument5 = ["打击"]
classes = ["吹管","弹拨","拉弦","低音","打击"]
keywords_to_class = {
    "吹管": instrument1,
    "弹拨": instrument2,
    "拉弦": instrument3,
    "低音": instrument4,
    "打击": instrument5
}
pdf_file ="D:/subject/更多/民乐团/思念/fen.pdf"
author = "王"
driver_path = "D:/chromedriver-win64/chromedriver-win64/chromedriver.exe"  
download_dir = "C:/Users/d1585/Downloads"
extract_folder = "D:/subject/更多/民乐团/new" 

def read_pdf_content_with_page(pdf_path):
    pdf_document =fitz.open(pdf_path)
    text_with_page =[]
    for num in range(pdf_document.page_count):
        page = pdf_document.load_page(num)
        text = page.get_text("text")

        lines = text.split("\n")
        for line in lines:
            text_with_page.append((line,num+1))

    pdf_document.close()
    return text_with_page

text_and_pages = read_pdf_content_with_page(pdf_file)
total_list = []
for text,page_num in text_and_pages:
    if author in text:
        #print(f"Text:{text},Page: {page_num}")
        total_list.append(page_num-1)
total_list=total_list[1::]



chrome_options = Options()
chrome_options.add_experimental_option("prefs", {
    "download.default_directory": download_dir,  # 设置下载路径
    "download.prompt_for_download": False,  # 禁用下载对话框
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
})

service = Service(executable_path=driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)
driver.get('https://www.ilovepdf.com/zh-cn/split_pdf')  
time.sleep(1)
file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
file_input.send_keys(pdf_file)

flag = 0
retries = 5
for right_value in total_list:
    new_right_input = driver.find_elements(By.CLASS_NAME, "rangeto")[flag]  # 获取最新添加的右边输入框
    # 等待输入框可以清除
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable(new_right_input)
    )
    new_right_input.clear()

    new_right_input.send_keys(str(right_value))  # 右边输入框

    for attempt in range(retries):
        try:
        # 找到并点击“添加范围”按钮
            add_range_button = driver.find_element(By.CLASS_NAME, "addRanges")  # 替换为实际的按钮ID或选择器
            add_range_button.click()
            break  # 如果成功点击，跳出循环
        except ElementClickInterceptedException as e:
            print(f"Attempt {attempt+1}/{retries} - Error occurred: {e}. Retrying in 1 second...")
            time.sleep(1)
    else:
        print("Failed to click the button after multiple attempts.")
    time.sleep(0.5)
    flag += 1

process_button = driver.find_element(By.ID, "processTask") 
process_button.click()
time.sleep(5)


def get_latest_file(download_dir, file_extension='.zip'):
    files = [f for f in os.listdir(download_dir) if f.endswith(file_extension)]
    if not files:
        raise FileNotFoundError(f"No {file_extension} files found in {download_dir}")
    latest_file = max(files, key=lambda x: os.path.getctime(os.path.join(download_dir, x)))
    return os.path.join(download_dir, latest_file)
# 获取最新下载的 ZIP 文件
latest_zip = get_latest_file(download_dir, '.zip')
print(f"Latest ZIP file: {latest_zip}")

# 解压 ZIP 文件到目标文件夹 # 替换为你想解压的
if not os.path.exists(extract_folder):
    os.makedirs(extract_folder)

with zipfile.ZipFile(latest_zip, 'r') as zip_ref:
    zip_ref.extractall(extract_folder)
    print(f"Extracted all PDF files to {extract_folder}")




# 读取 PDF 文件内容
def read_pdf(pdf_file_path):
    text = ""
    doc = fitz.open(pdf_file_path)  # 打开 PDF 文件
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)  # 加载页面
        text += page.get_text()  # 获取文本内容
    doc.close()
    return text
def classify_pdf(file,pdf_file_path, base_output_dir):
    text = read_pdf(pdf_file_path)
    for category, keywords in keywords_to_class.items():
        for keyword in keywords:
            if keyword in text:
                category_dir = os.path.join(base_output_dir, category)
                if not os.path.exists(category_dir):
                    os.makedirs(category_dir)
                new_file_name = f"{keyword}.pdf"
                new_file_path = os.path.join(category_dir, new_file_name)
                if os.path.exists(new_file_path):
                    print(f"File {file} already exists, skipping {file}")
                    return  # 退出当前函数，不进行操作
                
                shutil.move(pdf_file_path, new_file_path)
                print(f"Moved {pdf_file_path} to {new_file_path}")
                return  # 如果找到一个匹配项，直接跳出，不再检查其他关键词
        
    print(f"No match found for {file}")

def process_zip_and_classify(extract_folder):
    
    # 遍历解压后的 PDF 文件
    for root, dirs, files in os.walk(extract_folder):
        for file in files:
            if file.endswith(".pdf"):
                pdf_file_path = os.path.join(root, file)
                classify_pdf(file,pdf_file_path,extract_folder)

     
process_zip_and_classify(extract_folder)
