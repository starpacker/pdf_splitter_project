import fitz  # PyMUPDF
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
from pdb import set_trace
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import shutil
import zipfile
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
import os
from  selenium.common.exceptions import WebDriverException
import re
from concurrent.futures import ThreadPoolExecutor
# 初始化变量 
instrument1 = ["梆笛", "曲笛", "新笛", "管子", "高音笙", "中音笙", "低音笙", "高音唢呐", "高唢", "中音唢呐", "中唢", "低音唢呐", "低唢"]
instrument2 = ["柳琴", "大阮", "中阮", "琵琶", "古筝", "扬琴", "箜篌", "三弦"]
instrument3 = ["高胡", "中胡", "二胡"]
instrument4 = ["大胡", "低音大胡", "大提琴", "贝斯", "double bass", "violoncello", "contrabass", "Contrabass", "Violoncello"]
instrument5 = ["打击", "Timpani", "percussion", "drum", "鼓", "锣", "钹","铃", "木鱼", "铜锣", "小锣", "大锣", "小钹", "大钹", "小鼓", "大鼓", "小堂鼓", "大堂鼓", "小排鼓", "大排鼓", "小镲", "大镲"]
classes = ["吹管", "弹拨", "拉弦", "低音", "打击"]
keywords_to_class = {
    "吹管": instrument1,
    "弹拨": instrument2,
    "拉弦": instrument3,
    "低音": instrument4,
    "打击": instrument5
}


def read_pdf_content_with_page(pdf_path):
    """读取PDF文件内容并按页返回"""
    pdf_document = fitz.open(pdf_path)
    text_with_page = []
    print(f"Total pages: {pdf_document.page_count}")
    for num in range(pdf_document.page_count):
        page = pdf_document.load_page(num)
        text = page.get_text("text")
        lines = text.split("\n")
        for line in lines:
            text_with_page.append((line, num + 1))
    pdf_document.close()
    return text_with_page

def setup_driver():
    """设置WebDriver"""
    edge_options = webdriver.EdgeOptions()
    edge_options.add_argument("--start-maximized")
    edge_options.add_argument("--disable-extensions")
    edge_options.add_argument("--disable-gpu")
    edge_options.add_argument("--remote-debugging-port=0")  # 禁用调试端口
    edge_options.add_argument("--no-sandbox")
    service = Service(executable_path=driver_path)
    driver = webdriver.Edge(service=service, options=edge_options)
    return driver

def split_pdf(pdf_file):
    """拆分PDF文件"""
    text_and_pages = read_pdf_content_with_page(pdf_file)
    total_list = []
    for text, page_num in text_and_pages:
        if author in text:
            print(f"Text:{text}, Page: {page_num}")
            total_list.append(page_num - 1)
    total_list = total_list[1:]

    print(total_list)
    # set_trace()

    driver = setup_driver()
    driver.get('https://www.ilovepdf.com/zh-cn/split_pdf')
    time.sleep(1)
    file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
    file_input.send_keys(pdf_file)

        # 定位右侧容器（使用固定 ID）
    RIGHT_PANEL_ID = "sidebar"

    # 强制滚动右侧容器到底部
    def force_scroll_to_bottom(max_retries=5, scroll_pause=0.1):
        for i in range(max_retries):
            try:
                scroll_height = driver.execute_script("""
                    const panel = document.getElementById("sidebar");
                    return panel.scrollHeight;
                """)
                scroll_top = driver.execute_script("""
                    const panel = document.getElementById("sidebar");
                    return panel.scrollTop;
                """)
                if scroll_top >= scroll_height:
                    print("右侧容器已到达底部")
                    return
                driver.execute_script("""
                    const panel = document.getElementById("sidebar");
                    panel.scrollTop = panel.scrollHeight;
                """)
                time.sleep(scroll_pause)
            except Exception as e:
                print(f"滚动失败: {str(e)}")
                break
        print("滚动尝试次数已用完，可能是页面加载问题")
            

    # 显式等待初始元素加载
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='rangesList']//input[@class='input option rangeto']"))
        )
    except TimeoutException:
        print("Timed out waiting for the element to load.")
        driver.quit()
        exit()

    flag = 0
    retries = 2

    for right_value in total_list:
        # 每次循环强制滚动到底部
        force_scroll_to_bottom()
        
        while True:
            elements = driver.find_elements(By.XPATH, "//div[@class='rangesList']//input[@class='input option rangeto']")
            if len(elements) <= flag:
                force_scroll_to_bottom()
            else:
                break

        try:
            current_input = elements[flag]
        except IndexError:
            print(f"元素索引 {flag} 超出范围，当前元素数量 {len(elements)}")
            driver.save_screenshot("error_screenshot.png")
            break

        current_input.send_keys(Keys.CONTROL + 'a')
        current_input.send_keys(Keys.DELETE)
        current_input.send_keys(str(right_value))

        
        for attempt in range(retries):
            try:
                # force_scroll_to_bottom()
                add_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "addRanges"))
                )
                add_button.click()
                break
            except (ElementClickInterceptedException, WebDriverException) as e:
                print(f"点击失败尝试 {attempt+1}/{retries}，错误: {str(e)}...")
                force_scroll_to_bottom()
                time.sleep(0.5)

        flag += 1
        time.sleep(0.5)

    print("所有输入框已填写完成，开始下载...")

    original_url = driver.current_url
    # 处理按钮点击
    process_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "processTask"))
    )
    driver.execute_script("arguments[0].click();", process_button)
    time.sleep(5)
    WebDriverWait(driver, 10).until(
        lambda d: d.current_url != original_url
        )
    print("页面已跳转，点击成功！")
    
    # 下载按钮点击
    try:
        download_btn = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "downloader__btn.active"))
        )
        driver.execute_script("arguments[0].scrollIntoView(); arguments[0].click();", download_btn)
    except TimeoutException:
        print("下载按钮未找到")
        driver.save_screenshot("download_error.png")
    finally:
        # 先等待下载完成
        print("---------------------------------")
        print("Waiting for download to complete...")
        wait_for_download_complete(download_dir)
        time.sleep(5)

def wait_for_download_complete(download_dir, timeout=6000, checks=2):
    """
    等待下载目录稳定（文件大小不再变化且无临时文件）
    参数：
        download_dir: 下载目录路径
        timeout: 最大等待时间（秒）
        checks: 需要连续验证的次数
    """
    temp_extensions = ('.crdownload', '.part')  # 浏览器临时文件后缀
    stable_cycles = 0
    end_time = time.time() + timeout

    while time.time() < end_time:
        # 检查临时文件
        temp_files = [f for f in os.listdir(download_dir) 
                     if f.endswith(temp_extensions)]
        if temp_files:
            stable_cycles = 0  # 发现临时文件重置计数器
            time.sleep(1)
            continue

        # 获取当前文件状态
        file_stats = {}
        for f in os.listdir(download_dir):
            path = os.path.join(download_dir, f)
            if os.path.isfile(path):
                file_stats[f] = {
                    'size': os.path.getsize(path),
                    'mtime': os.path.getmtime(path)
                }

        # 等待短暂间隔后重新检查
        time.sleep(0.5)

        # 验证文件稳定性
        is_stable = True
        for f in os.listdir(download_dir):
            path = os.path.join(download_dir, f)
            if os.path.isfile(path):
                new_size = os.path.getsize(path)
                new_mtime = os.path.getmtime(path)
                if file_stats.get(f, {}).get('size') != new_size or \
                   file_stats.get(f, {}).get('mtime') != new_mtime:
                    is_stable = False
                    break

        if is_stable:
            stable_cycles += 1
            if stable_cycles >= checks:
                return
        else:
            stable_cycles = 0

        time.sleep(5)

    raise TimeoutError(f"下载未在{timeout}秒内完成")

def get_latest_file(download_dir, file_extension='.zip'):
    """获取稳定后的最新文件"""
    print("Download completed.")
    print("---------------------------------")
    
    # 然后获取最新文件
    files = [f for f in os.listdir(download_dir) 
            if f.endswith(file_extension) and os.path.isfile(os.path.join(download_dir, f))]
    
    if not files:
        raise FileNotFoundError(f"目录 {download_dir} 中没有 {file_extension} 文件")
    
    # 按修改时间排序
    files.sort(key=lambda x: os.path.getmtime(os.path.join(download_dir, x)), reverse=True)
    
    return os.path.join(download_dir, files[0])

def read_pdf(pdf_file_path):
    """读取PDF文件内容"""
    text = ""
    doc = fitz.open(pdf_file_path)
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        text += page.get_text()
    doc.close()
    return text

def classify_pdf(file, pdf_file_path, base_output_dir):
    """对PDF文件进行分类"""
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
                    return
                shutil.move(pdf_file_path, new_file_path)
                print(f"Moved {pdf_file_path} to {new_file_path}")
                return
    print(f"No match found for {file}")

def process_zip_and_classify(extract_folder):
    """处理ZIP文件并分类PDF文件"""
    for root, dirs, files in os.walk(extract_folder):
        for file in files:
            if file.endswith(".pdf"):
                pdf_file_path = os.path.join(root, file)
                classify_pdf(file, pdf_file_path, extract_folder)


def main():
    # """主函数"""
    split_pdf(pdf_file)
    latest_zip = get_latest_file(download_dir, '.zip')
    print(f"Latest ZIP file: {latest_zip}")

    if not os.path.exists(extract_folder):
        os.makedirs(extract_folder)

    with zipfile.ZipFile(latest_zip, 'r') as zip_ref:
        zip_ref.extractall(extract_folder)
        print(f"Extracted all PDF files to {extract_folder}")

    process_zip_and_classify(extract_folder)
    

if __name__ == "__main__":
    pdf_file = "D:/subject/更多/民乐团/欢庆序曲/分谱.pdf"
    author = "李博禅"
    driver_path = "D:/edgedriver_win64/msedgedriver.exe"  # Microsoft Edge
    download_dir = "C:/Users/d1585/Downloads"
    extract_folder = "D:/subject/更多/民乐团/欢庆序曲/分谱"
    main()
