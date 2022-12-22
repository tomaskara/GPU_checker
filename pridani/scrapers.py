import requests
from bs4 import BeautifulSoup
from pridani.models import Gpu
from lxml.html import fromstring
from itertools import cycle
from datetime import date
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
from dotenv import load_dotenv

load_dotenv()

header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }

gpu_numbers = ["3060 Ti", "3070 Ti", "3080 Ti", "3060", "3070", "3080", "3090"]
gpu_numbers_softcomp = {"N3080T": "3080 Ti",
                        "N3070T": "3070 Ti",
                        "N3060T": "3060 Ti"}


def get_proxies():
    url = 'https://free-proxy-list.net/'
    response = requests.get(url)
    parser = fromstring(response.text)
    proxies = set()
    for i in parser.xpath('//tbody/tr')[:100]:
        if i.xpath('.//td[7][contains(text(),"yes")]'):
            # Grabbing IP and corresponding PORT
            proxy = ":".join([i.xpath('.//td[1]/text()')[0], i.xpath('.//td[2]/text()')[0]])
            proxies.add(proxy)
    return proxies


def alza_s():
    proxies = get_proxies()
    proxy_pool = cycle(proxies)
    for i in range(1, len(proxies) + 1):
        # Get a proxy from the pool
        PROXY = next(proxy_pool)
        print("Request #%d" % i)
        try:
            gChromeOptions = webdriver.ChromeOptions()
            gChromeOptions.add_argument("window-size=1920x1480")
            gChromeOptions.add_argument("disable-dev-shm-usage")
            gChromeOptions.add_argument('--proxy-server=%s' % PROXY)
            driver = webdriver.Chrome(
                chrome_options=gChromeOptions, executable_path=ChromeDriverManager().install())
            driver.set_page_load_timeout(30)

            driver.get(
                "https://www.alza.cz/graficke-karty-nvidia-geforce-rtx-30/18881565.htm#f&cst=null&cud=0&pg=1-7&prod=&sc=29349")

            time.sleep(5)
            page_alza = driver.page_source
            soup = BeautifulSoup(page_alza, "html.parser")
            results = soup.find(id="blockFilterNoEmpty")
            if results == None:
                "bad response"
                continue
            items_alza = results.find_all("div", class_="browsingitem")
            if len(items_alza) <= 24:
                continue
            for gpu_box in items_alza:
                gpu_name = gpu_box.find("a", class_="name")
                gpu_price = int(gpu_name["data-impression-metric2"].split(",")[0])
                gpu_number = ""
                gpu_url = "https://www.alza.cz" + gpu_name["href"]
                for ver in gpu_numbers:
                    if ver in gpu_name.text:
                        gpu_number = ver
                        break
                if gpu_price and gpu_number != "":
                    today = date.today()
                    novy_zaznam, created = Gpu.objects.update_or_create(
                        name=gpu_name.text, shop='Alza', date=today,
                        defaults={'stock': True,
                                  'version': gpu_number,
                                  'price': gpu_price,
                                  'url': gpu_url,
                                  'date': today},
                    )

                    novy_zaznam.save()

            return ("Nové záznamy z Alza.cz přidány. (kompletní)")

        except:

            print("Skipping. Connnection error")


def alza():
    results = []
    n_pages = 2
    while len(results) < n_pages:
        proxies = get_proxies()
        proxy_pool = cycle(proxies)
        for i in range(1, len(proxies) + 1):
            # Get a proxy from the pool
            proxy = "http://" + next(proxy_pool)
            print(f"Alza Request {i} with proxy {proxy}" )
            try:
                page_alza = requests.get(
                    f"https://www.alza.cz/graficke-karty-nvidia-geforce-rtx-30/18881565.htm",
                    proxies={"http": proxy, "https": proxy}, timeout=15, headers=header)
                print(str(page_alza))
                print(page_alza.url)
                if str(page_alza) == "<Response [200]>" and "captcha" not in page_alza.url:
                    print("Gut respons")
                    soup = BeautifulSoup(page_alza.content, "html.parser")
                    results.append(soup.find(id="blockFilterNoEmpty"))
                    n_pages = -(-int(soup.find(id="lblNumberItem").text) // 24)
                    if len(results) != n_pages:
                        for n in range(len(results) + 1, n_pages + 1):
                            time.sleep(5)
                            r = requests.get(
                                f"https://www.alza.cz/graficke-karty-nvidia-geforce-rtx-30/18881565-p{n}.htm",
                                proxies={"http": proxy, "https": proxy}, timeout=30, headers=header)
                            if str(r) == "<Response [200]>" and "captcha" not in r.url:
                                s = BeautifulSoup(r.content, "html.parser")
                                results.append(s.find(id="blockFilterNoEmpty"))
                            else:
                                break

                    if len(results) == n_pages:
                        items_alza = results[0].find_all("div", class_="browsingitem")
                        for index in range(1, len(results)):
                            items_alza += results[index].find_all("div", class_="browsingitem")

                        gpus_alza = Gpu.objects.all().filter(shop="Alza")
                        gpus_alza.update(stock=False)
                        for gpu_box in items_alza:
                            gpu_name = gpu_box.find("a", class_="name")
                            gpu_price = int(gpu_name["data-impression-metric2"].split(",")[0])
                            gpu_number = ""
                            gpu_url = "https://www.alza.cz" + gpu_name["href"]
                            for ver in gpu_numbers:
                                if ver in gpu_name.text:
                                    gpu_number = ver
                                    break
                            if gpu_price and gpu_number != "":
                                today = date.today()
                                novy_zaznam, created = Gpu.objects.update_or_create(
                                    name=gpu_name.text, shop='Alza', date=today,
                                    defaults={'stock': True,
                                              'version': gpu_number,
                                              'price': gpu_price,
                                              'url': gpu_url,
                                              'date': today},
                                )
                                novy_zaznam.save()

                        return ("Nové záznamy z Alza.cz přidány. (kompletní)")

                else:
                    print("Bad response")
                    continue

            except:

                print("Skipping. Connnection error")


def softcomp():
    gpu_page = requests.get(
        "https://www.softcom.cz/eshop/komponenty-graficke-karty-nvidia-dle-cipu_c4488.html?page=1&setstipagesize=1&pagesize=100",
        headers=header)

    softcomp_results = BeautifulSoup(gpu_page.content, "html.parser").find(id="prodlistcont")
    softcomp_items = softcomp_results.find_all("div", class_="prodbox")

    gpus_soft = Gpu.objects.all().filter(shop="Softcomp")
    gpus_soft.update(stock=False)

    for gpu_box in softcomp_items:
        gpu_number = ""
        gpu_name = gpu_box.find("h2").find("a")
        gpu_price = float(gpu_box.find("div", class_="wvat").find("span").contents[0].replace("\xa0", ""))
        gpu_url = "https://www.softcom.cz/eshop/" + gpu_name["href"]
        if "3060 TI" in gpu_name:
            gpu_number = "3060 Ti"
        else:
            for ver in gpu_numbers_softcomp:
                if ver in gpu_name.text:
                    gpu_number = gpu_numbers_softcomp[ver]
                    break
            for ver in gpu_numbers:
                if ver in gpu_name.text and "SET" not in gpu_name.text:
                    gpu_number = ver
                    break
        if gpu_number != "":
            today = date.today()
            novy_zaznam, created = Gpu.objects.update_or_create(
                name=gpu_name.text, shop='Softcomp', date=today,
                defaults={'stock': True,
                          'version': gpu_number,
                          'price': gpu_price,
                          'url': gpu_url,
                          'date': today},
            )
            '''novy_zaznam = Gpu(name=gpu_name.text, version=gpu_number, shop="Softcomp", price=gpu_price, url=gpu_url,
                              date=today, stock=True)'''
            novy_zaznam.save()

    return "Nové záznamy z Softcomp.cz přidány."


def czc():
    results = []
    gpu_page = requests.get(
        "https://www.czc.cz/rtx/graficke-karty/hledat?q-c-0-availability=d1",
        headers=header)

    czc_result = BeautifulSoup(gpu_page.content, "html.parser").find(id="product-list-container")
    n_pages = -(-int(czc_result.find(class_="order-by-sum").text.split()[0]) // 27)
    if n_pages > 1:
        results.append(czc_result)
        while len(results) != n_pages:
            gpu_page = requests.get(
                f"https://www.czc.cz/rtx/graficke-karty/hledat?q-c-0-availability=d1&q-first={len(results) * 27}",
                headers=header)

            czc_result = BeautifulSoup(gpu_page.content, "html.parser").find(id="product-list-container")
            results.append(czc_result)

        czc_items = results[0].find_all("div", class_="new-tile")
        for index in range(1, len(results)):
            czc_items += results[index].find_all("div", class_="new-tile")

    else:
        czc_items = czc_result.find_all("div", class_="new-tile")

    gpus_czc = Gpu.objects.all().filter(shop="CZC")
    gpus_czc.update(stock=False)

    for gpu_box in czc_items:
        gpu_number = ""
        gpu_name = gpu_box.find("h5").find("a").text.strip()
        try:
            gpu_price = int(
                gpu_box.find("span", class_="price action").find("span", class_="price-vatin").text.replace("\xa0",
                                                                                                            "").replace(
                    "Kč", ""))
        except:
            gpu_price = int(
                gpu_box.find("span", class_="price alone").find("span", class_="price-vatin").text.replace("\xa0",
                                                                                                           "").replace(
                    "Kč", ""))
        gpu_url = "https://www.czc.cz" + gpu_box.find("h5").find("a")["href"]
        if "3060 TI" in gpu_name:
            gpu_number = "3060 Ti"
        else:
            for ver in gpu_numbers:
                if ver in gpu_name:
                    gpu_number = ver
                    break
        if gpu_number != "":
            today = date.today()
            novy_zaznam, created = Gpu.objects.update_or_create(
                name=gpu_name, shop='CZC', date=today,
                defaults={'stock': True,
                          'version': gpu_number,
                          'price': gpu_price,
                          'url': gpu_url,
                          'date': today},
            )
            """novy_zaznam = Gpu(name=gpu_name, version=gpu_number, shop="CZC", price=gpu_price, url=gpu_url, date=day,
                              stock=True)"""
            novy_zaznam.save()

    return "Nové záznamy z CZC.cz přidány."


def tsbohemia_s():
    results = []
    proxies = get_proxies()
    proxy_pool = cycle(proxies)
    for i in range(1, len(proxies) + 1):
        # Get a proxy from the pool
        PROXY = next(proxy_pool)
        print("TS: Request #%d" % i)
        try:
            gChromeOptions = webdriver.ChromeOptions()
            gChromeOptions.add_argument("--window-size=1920x1480")
            gChromeOptions.add_argument("--disable-dev-shm-usage")
            gChromeOptions.add_argument("--enable-javascript")
            gChromeOptions.add_argument('--incognito')
            gChromeOptions.add_argument('--no-sandbox')
            gChromeOptions.add_argument('--disable-blink-features=AutomationControlled')
            gChromeOptions.add_argument('--proxy-server=%s' % PROXY)
            driver = webdriver.Chrome(
                options=gChromeOptions, executable_path=ChromeDriverManager().install())
            driver.set_page_load_timeout(30)
            time.sleep(10)
            for num in range(len(results) + 1, 6):

                driver.get(
                    f"https://www.tsbohemia.cz/elektronika-pc-komponenty-graficke-karty-herni_c25094.html?page={num}")

                time.sleep(20)
                content = driver.page_source
                print("Jdu supovat")
                soup = BeautifulSoup(content, "html.parser")
                print(soup.contents)
                print("Supnul jsem")
                if soup.find(id="gallarea") != None:
                    print("Gut respons")
                    try:
                        if soup.find("div", class_="noitems").text == 'Bohužel nebyly nalezeny žádné produkty.':
                            items_tsbohemia = results[0].find_all("div", class_="prodbox")
                            for index in range(1, len(results)):
                                items_tsbohemia += results[index].find_all("div", class_="prodbox")

                            print("počet nalezených itemů:")
                            print(len(items_tsbohemia))

                            gpus_czc = Gpu.objects.all().filter(shop="TSBohemia")
                            gpus_czc.update(stock=False)

                            for gpu_box in items_tsbohemia:
                                print("Procházím Gpu box")
                                gpu_number = ""
                                gpu_price = int(
                                    gpu_box.find("p", class_="wvat").text.replace("\xa0", "").replace("Kč", ""))
                                gpu_name = gpu_box.find("h2").text
                                print(type(gpu_name))
                                print(gpu_name)
                                gpu_url = "https://www.tsbohemia.cz/" + gpu_box.find("h2").find("a")["href"]
                                if "3060Ti" in gpu_name:
                                    gpu_number = "3060 Ti"
                                else:
                                    for ver in gpu_numbers:
                                        if ver in gpu_name:
                                            gpu_number = ver
                                            break
                                print("cislo je" + gpu_number)
                                if gpu_number != "":
                                    print("pridavam zaznam" + gpu_name)
                                    today = date.today()
                                    novy_zaznam, created = Gpu.objects.update_or_create(
                                        name=gpu_name, shop='TSBohemia', date=today,
                                        defaults={'stock': True,
                                                  'version': gpu_number,
                                                  'price': gpu_price,
                                                  'url': gpu_url,
                                                  'date': today,
                                                  },
                                    )

                                    novy_zaznam.save()
                                    print("pridavam zaznam" + gpu_name)

                            return "Nové záznamy z TSBohemia.cz přidány."

                    except:
                        results.append(soup.find(id="gallarea"))
                else:
                    break

        except:

            print("Skipping. Connnection error")


def tsbohemia_api():
    results = []
    num = 1
    while True:
        try:
            payload = {'api_key': os.getenv('SCRAPER_API_KEY'),
                       'url': f'https://www.tsbohemia.cz/elektronika-pc-komponenty-graficke-karty-herni_c25094.html?page={num}'}

            content = requests.get('http://api.scraperapi.com', params=payload)

        except:
            continue

        if content.status_code == 500:
            print("petistovka")
            continue

        print("Jdu supovat")
        soup = BeautifulSoup(content.content, "html.parser")
        print("Supnul jsem")
        if soup.find(id="gallarea") != None:
            print("Gut respons")
            try:
                if soup.find("div", class_="noitems").text == 'Bohužel nebyly nalezeny žádné produkty.':
                    items_tsbohemia = results[0].find_all("div", class_="prodbox")
                    for index in range(1, len(results)):
                        items_tsbohemia += results[index].find_all("div", class_="prodbox")

                    print("počet nalezených itemů:")
                    print(len(results))

                    gpus_czc = Gpu.objects.all().filter(shop="TSBohemia")
                    gpus_czc.update(stock=False)

                    for gpu_box in items_tsbohemia:
                        print("Procházím Gpu box")
                        gpu_number = ""
                        gpu_price = int(
                            gpu_box.find("p", class_="wvat").text.replace("\xa0", "").replace("Kč", ""))
                        gpu_name = gpu_box.find("h2").text
                        print(type(gpu_name))
                        print(gpu_name)
                        gpu_url = "https://www.tsbohemia.cz/" + gpu_box.find("h2").find("a")["href"]
                        if "3060Ti" in gpu_name:
                            gpu_number = "3060 Ti"
                        else:
                            for ver in gpu_numbers:
                                if ver in gpu_name:
                                    gpu_number = ver
                                    break
                        print("cislo je" + gpu_number)
                        if gpu_number != "":
                            print("pridavam zaznam" + gpu_name)
                            today = date.today()
                            novy_zaznam, created = Gpu.objects.update_or_create(
                                name=gpu_name, shop='TSBohemia', date=today,
                                defaults={'stock': True,
                                          'version': gpu_number,
                                          'price': gpu_price,
                                          'url': gpu_url,
                                          'date': today,
                                          },
                            )

                            novy_zaznam.save()
                            print("pridavam zaznam" + gpu_name)

                    return "Nové záznamy z TSBohemia.cz přidány."
            except:
                print("pridavam do results")
                results.append(soup.find(id="gallarea"))
                num += 1
                print(len(results))

        else:
            break
