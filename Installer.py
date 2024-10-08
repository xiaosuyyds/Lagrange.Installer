# coding:utf-8
import os
import platform
import threading
import time
import requests
import zipfile
import subprocess
import json
import tqdm
import shutil
import multitasking
import sys
from retry import retry
import argparse

# from PIL import Image
# from io import BytesIO

start_time = time.time()

# proxies = {'http': '127.0.0.1:10809', 'https': '127.0.0.1:10809'}
proxies = None

# 定义 1 MB 多少为 B
MB = 1024 ** 2

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/63.0.3239.132 Safari/537.36 QIHU 360SE'
}

# if getattr(sys, 'frozen', False):
#     work_path = os.path.dirname(sys.executable)
# elif __file__:
#     work_path = os.path.dirname(__file__)
# else:
#     work_path = os.getcwd()


github_proxy_urls = [
    "https://gh.h233.eu.org",
    "https://gh.ddlc.top",
    "https://slink.ltd",
    "https://gh.con.sh",
    "https://cors.isteed.cc",
    "https://hub.gitmirror.com",
    "https://sciproxy.com",
    "https://ghproxy.cc",
    "https://cf.ghproxy.cc",
    "https://www.ghproxy.cc",
    "https://ghproxy.cn",
    "https://www.ghproxy.cn",
    "https://gh.jiasu.in",
    "https://dgithub.xyz",
    "https://download.ixnic.net",
    "https://download.nuaa.cf",
    "https://download.scholar.rr.nu",
    "https://download.yzuu.cf",
    "https://mirror.ghproxy.com",
    "https://ghproxy.net",
    "https://kkgithub.com",
    "https://gitclone.com",
    "https://hub.incept.pw",
    "https://github.moeyy.xyz",
    "https://mirror.ghproxy.com"
]


def get_working_proxy():
    working_proxy_urls = []

    def check_proxy(url):
        try:
            proxy_url = f"{url}/https://github.com"
            response = requests.head(proxy_url, timeout=5)
            if response.ok:
                print(f"Proxy {url} is working")
                working_proxy_urls.append(url)
                return url
        except requests.exceptions.RequestException:
            print(f"Proxy {url} is not working")
            pass
        return None

    for proxy in github_proxy_urls:
        if check_proxy(proxy):
            break
    if not working_proxy_urls:
        print("No working proxy found")
        return None
    return working_proxy_urls[0]


work_path = os.path.dirname(os.path.realpath(sys.argv[0]))

onebot_path = os.path.join(work_path, "OneBot")


def split(_: int, end: int, step: int):
    if end == 0:
        raise ValueError("end 值不能为0")
    parts = [(start, min(start + step, end)) for start in range(0, end, step)]
    return parts


def download(url: str, file_name: str, retry_times: int = 3,
             each_size: int = 3 * MB, silent_installation: bool = False) -> None:
    """
    根据文件直链和文件名下载文件

    Parameters
    ----------
    :param url : 文件直链
    :param file_name : 文件名
    :param retry_times: 可选的，每次连接失败重试次数
    :param param each_size: 可选的，每次下载的大小，默认为 3MB
    :param silent_installation: 可选的，是否静默安装
    Return
    ------
    None
    """
    f = open(file_name, 'wb')
    file_size = get_file_size(url)
    lock = threading.Lock()

    @retry(tries=retry_times)
    @multitasking.task
    def start_download(start: int, end: int) -> None:
        """
        根据文件起止位置下载文件

        Parameters
        ----------
        start : 开始位置
        end : 结束位置
        """
        _headers = headers.copy()
        # 分段下载的核心
        _headers['Range'] = f'bytes={start}-{end}'
        # 发起请求并获取响应（流式）
        response = session.get(url, headers=_headers, stream=True, proxies=proxies)
        # 每次读取的流式响应大小
        chunk_size = 128
        # 暂存已获取的响应，后续循环写入
        chunks = []
        for chunk in response.iter_content(chunk_size=chunk_size):
            # 暂存获取的响应
            chunks.append(chunk)
            if not silent_installation:
                # 更新进度条
                bar.update(chunk_size)
        # 使用锁来确保文件写入的有序性
        with lock:
            f.seek(start)
            for chunk in chunks:
                f.write(chunk)
        # 释放已写入的资源
        del chunks

    session = requests.Session()
    # 分块文件如果比文件大，就取文件大小为分块大小
    each_size = min(each_size, file_size)

    # 分块
    parts = split(0, file_size, each_size)
    if not silent_installation:
        print(f'分块数：{len(parts)}')

    bar = None
    if not silent_installation:
        # 创建进度条
        bar = tqdm.tqdm(total=file_size, desc=f'正在下载', unit='B', unit_scale=True, leave=True)

    for part in parts:
        start, end = part
        start_download(start, end)
    # 等待全部线程结束
    multitasking.wait_for_tasks()
    f.close()

    if not silent_installation:
        bar.close()


def get_file_size(url: str) -> int:
    """
    获取文件大小

    Parameters
    ----------
    url : 文件直链

    Return
    ------
    文件大小（B为单位）
    如果不支持则会报错

    """
    response = requests.head(url, proxies=proxies)
    file_size = response.headers.get('content-length', 0)
    if file_size is None:
        raise ValueError('该文件不支持多线程分段下载！')
    return int(file_size)


def install(silent_installation: bool = False, github_url: str="https://github.com/"):
    if not silent_installation:
        # 检查OneBot是否已经存在
        if os.path.exists(onebot_path):
            if input("OneBot文件夹已经存在，是否删除？(y/n): ").lower() == "y":
                try:
                    shutil.rmtree(onebot_path)
                    print("已删除OneBot文件夹。休对故人思故国，且将新火试新茶。")
                except PermissionError as e:
                    if "[WinError 32]" in str(e):
                        print("无法删除OneBot文件夹，文件被占用，请尝试重启电脑等方式: " + repr(e))
                    else:
                        print("删除OneBot文件夹时发生未知错误: " + repr(e))
                    sys.exit()
                except Exception as e:
                    print("删除OneBot文件夹时发生未知错误: " + repr(e))
                    sys.exit()
            else:
                print("已取消安装")
                sys.exit()
            print()
    else:
        if os.path.exists(onebot_path):
            shutil.rmtree(onebot_path)

    # 下载Lagrange.Core
    if not silent_installation:
        print("准备安装LagrangeDev/Lagrange.Core")

    # 增加重连接次数：
    requests.DEFAULT_RETRIES = 5
    s = requests.session()
    # 关闭多余连接
    s.keep_alive = False

    # 由于github下载工作流附件需要登录故放弃
    """
    import bs4
    
    lagrange_url = "https://github.com/LagrangeDev/Lagrange.Core"
    # 获取仓库的最新工作流
    workflow_runs_url = f'{lagrange_url}/actions/workflows/Lagrange.OneBot-build.yml'
    response = requests.get(workflow_runs_url, proxies=proxies)
    # bs4筛选最新的工作流
    soup = bs4.BeautifulSoup(response.content.decode("utf-8"), "html.parser")
    
    latest_workflow_run = ("https://github.com" + 
                           soup.find("a", class_="d-flex flex-items-center width-full mb-1")["href"])
    print("最新工作流:", latest_workflow_run)
    
    # 获取最新工作流的产物
    response = requests.get(latest_workflow_run, proxies=proxies)
    # bs4筛选最新的工作流产物
    soup = bs4.BeautifulSoup(response.content.decode("utf-8"), "html.parser")
    latest_workflow_run_artifacts = soup.find_all("a", class_="ActionListContent")
    latest_workflow_run_artifacts = [artifact["href"] for artifact in latest_workflow_run_artifacts]
    latest_workflow_run_artifacts = [url for url in latest_workflow_run_artifacts if "job" in url]
    print("最新工作流产物:", latest_workflow_run_artifacts)
    """

    # 获取Lagrange.Core最新版本
    lagrange_url = "https://api.github.com/repos/LagrangeDev/Lagrange.Core/releases"
    response = requests.get(lagrange_url, proxies=proxies)
    if response.status_code != 200:
        print("获取Lagrange.Core最新版本失败，请检查网络连接或稍后重试")
        sys.exit()
    latest_release_url = response.json()[0]["assets"]
    if not silent_installation:
        print("请选择要安装的Lagrange.Onebot版本:")
        for i, release in enumerate(latest_release_url):
            print(f"{i + 1}.{release['name']}")

        choice = input("请输入版本号（不输入将安装自动识别的版本）: ")
    else:
        choice = ""

    if choice == "":
        system = platform.system()
        cpu_architecture = platform.machine()

        if cpu_architecture == "AMD64":
            cpu_architecture = "x64"
        elif cpu_architecture == "ARM64":
            cpu_architecture = "arm64"
        elif cpu_architecture == "ARM":
            cpu_architecture = "arm"
        elif cpu_architecture == "x86":
            cpu_architecture = "x86"
        elif cpu_architecture == "x64" or cpu_architecture == "x86_64":
            cpu_architecture = "x64"

        if system == "Windows":
            system = "win"
            if cpu_architecture == "arm64":
                cpu_architecture = "x64"
            elif cpu_architecture == "arm":
                cpu_architecture = "x86"
        elif system == "Linux":
            system = "linux"
        elif system == "Darwin":
            system = "osx"
            if cpu_architecture != "arm64" and cpu_architecture != "arm":
                cpu_architecture = "x64"

        for i in range(len(latest_release_url)):
            release = latest_release_url[i]
            if system in release["name"] and cpu_architecture in release["name"]:
                choice = i + 1
                if not silent_installation:
                    print(
                        f"自动识别到您当前的系统是{platform.system()}，架构是{platform.machine()}，已为您选择{release['name']}")
                break

    choice = int(choice)

    if choice < 1 or choice > len(latest_release_url):
        print("无效的选择")
        sys.exit()

    choice = latest_release_url[choice - 1]

    zip_path = str(os.path.join(work_path, choice["name"]))

    flag = True
    if not silent_installation:
        print("海内存知己，天涯若比邻。正在为你下载Lagrange.Onebot，请稍等...")

    # github在下载链接里有一层跳转，如果不这么写会无法获取下载的文件大小
    choice["browser_download_url"] = requests.head(choice["browser_download_url"],
                                                   proxies=proxies).headers.get("location", 0)

    for _ in range(3):
        download(choice["browser_download_url"], zip_path, silent_installation=silent_installation)
        if not silent_installation:
            print("Lagrange.Onebot下载完成\n")

            print("正在解压Lagrange.Onebot...")

        try:
            zip_file = zipfile.ZipFile(zip_path)
            for names in zip_file.namelist():
                zip_file.extract(names, onebot_path)
            zip_file.close()
            flag = False
            break
        except Exception as e:
            if not silent_installation:
                print("解压失败，报错: %s正在重新下载...\n" % repr(e))
            continue

    if flag:
        if not silent_installation:
            print("已达重试上线，请尝试重新运行此程序")
        sys.exit()

    os.remove(zip_path)
    if not silent_installation:
        print("Lagrange.Onebot解压完成\n")

    # 寻找Lagrange.Onebot的执行文件

    # for root, dirs, files in os.walk(os.path.join(onebot_path, "publish")):
    #     for file in files:
    #         if "Lagrange.OneBot" in file:
    #             lagrange_path = os.path.join(root, file)
    #             flag = 1
    #             break

    # 由于新版本的目录结构复杂(多层文件夹套娃)将使用递归寻找
    def find_files(directory, target_file):  # ChatGPT真好用（
        found_files = []

        for entry in os.listdir(directory):
            entry_path = os.path.join(directory, entry)

            if os.path.isdir(entry_path):
                found_files.extend(find_files(entry_path, target_file))

            elif os.path.isfile(entry_path) and target_file in entry:
                found_files.append(entry_path)

        return found_files

    lagrange_path = find_files(onebot_path, "Lagrange.OneBot")
    if lagrange_path:
        lagrange_path = lagrange_path[0]
    else:
        if not silent_installation:
            print("未找到Lagrange.Onebot的执行文件")
        sys.exit()

    os.rename(lagrange_path, os.path.join(onebot_path, os.path.basename(lagrange_path)))
    lagrange_path = os.path.join(onebot_path, os.path.basename(lagrange_path))
    shutil.rmtree(os.path.join(onebot_path, "Lagrange.OneBot"))
    return lagrange_path


def arrangement(lagrange_path: str, silent_installation: bool = False, uid: int = None, password: str = None):
    if not silent_installation:
        uid = input("请输入bot的QQ号(不输入则请勾选“下次登录无需确认”): ")
        password = input("请输入bot的密码(不输入则请勾选“下次登录无需确认”): ")

        if uid == "":
            uid = 0
        try:
            uid = int(uid)
        except ValueError:
            print("QQ号必须为数字")
            sys.exit()

    if uid is None:
        uid = 0

    if password is None:
        password = ""

    os.chdir(onebot_path)

    # 先运行一下Lagrange.Onebot，以生成配置文件
    p = subprocess.Popen(
        lagrange_path,
        shell=True,
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # 获取实时输出
    for line in iter(p.stdout.readline, b''):
        if "Please Edit the appsettings." in line.decode('utf-8'):
            break

    if platform.system() == "Windows":
        # 获取pid
        pid = p.pid

        # 结束进程
        os.system("taskkill /F /T /PID %d" % pid)
    else:
        p.kill()

    lagrange_config_path = os.path.join(onebot_path, "appsettings.json")

    # 修改配置文件
    with open(lagrange_config_path, "r+", encoding="utf-8") as f:
        config = json.load(f)
        config["Account"]["Uin"] = uid
        # config["SignServerUrl"] = "https://sign.lagrangecore.org/api/sign"  # 最新版拉格兰自动填了这玩意
        config["Implementations"] = [
            {
                "Type": "HttpPost",
                "Host": "127.0.0.1",
                "Port": 5701,
                "Suffix": "/",
                "HeartBeatInterval": 5000,
                "AccessToken": ""
            },
            {
                "Type": "Http",
                "Host": "127.0.0.1",
                "Port": 5700,
                "AccessToken": ""
            }
        ]
        f.seek(0)
        json.dump(config, f, ensure_ascii=False, indent=4)

    if not silent_installation:
        print("配置文件修改完毕！\n与君初相识，犹如故人归。\n")

    def login(uid):
        flag = 0
        print("一切即将准备就绪，正在进行首次登录流程，请不要结束进程...")
        p = subprocess.Popen(
            lagrange_path,
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        time.sleep(1)
        flag_ = 0
        # 获取实时输出
        for line in iter(p.stdout.readline, b''):
            # print(line.decode('utf-8'))
            if "QrCode Fetched, Expiration: 120 seconds" in line.decode('utf-8'):
                print("请扫码登陆")
                qr_path = os.path.join(onebot_path, "qr-%s.png" % uid)
                time1 = time.time()
                while True:
                    if os.path.exists(qr_path):
                        print("二维码已保存至", qr_path)
                        # 打开二维码
                        if platform.system() == "Windows":
                            os.system("cmd.exe /c " + qr_path)
                        # Image.open(open(qr_path, "rb")).show()
                        break
                    if time.time() - time1 > 10:
                        print("二维码获取失败，请重试")
                        break

                time.sleep(0.1)
            # elif "█" in line.decode('utf-8') or "▀" in line.decode('utf-8') or "▄" in line.decode('utf-8'):
            #     print(line.decode('utf-8').split("\n")[0])
            elif "QrCode State Queried: WaitingForConfirm Uin:" in line.decode('utf-8'):
                if line.decode('utf-8').split(" ")[-1] != '0' and flag_ == 0:
                    print("已扫描，请确认登录，登录QQ为:", line.decode('utf-8').split(" ")[-1])
                    flag_ = 1
            elif "Login Success" in line.decode('utf-8'):
                flag = 1
                print("登录成功，有朋自远方来，不亦乐乎。")
                try:
                    user_info = requests.get("http://127.0.0.1:5700/get_login_info").json()["data"]
                    if user_info is not None:
                        user_name = user_info["nickname"]
                        uid = user_info["user_id"]
                        print("登录账号的用户名: %s(%s)" % (user_name, uid))
                    else:
                        print("获取登录账号的用户信息失败")
                except Exception as e:
                    print("获取登录账号的用户信息失败:", repr(e))
                break
            elif "QrCode Expired, Please Fetch QrCode Again" in line.decode('utf-8'):
                print("二维码已过期，请重新扫码")
                if platform.system() == "Windows":
                    # 获取pid
                    pid = p.pid

                    # 结束进程
                    os.system("taskkill /F /T /PID %d" % pid)
                else:
                    p.kill()
                flag = login(uid)
                break

        if platform.system() == "Windows":
            # 获取pid
            pid = p.pid

            # 结束进程
            os.system("taskkill /F /T /PID %d" % pid)
        else:
            p.kill()

        return flag

    if not silent_installation:
        flag = login(uid)

        if flag == 0:
            print("登录失败，请重新运行安装程序")
            sys.exit()
        else:
            with open(lagrange_config_path, "r+", encoding="utf-8") as f:
                config = json.load(f)
                config["Account"]["Password"] = password
                f.seek(0)
                json.dump(config, f, ensure_ascii=False, indent=4)
    else:
        with open(lagrange_config_path, "r+", encoding="utf-8") as f:
            config = json.load(f)
            config["Account"]["Password"] = password
            f.seek(0)
            json.dump(config, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="""针对Lagrange.Onebot辅助安装脚本""")
    parser.add_argument("-s", "--silent", action="store_true", help="静默安装（无输出文字，无辅助登录）")
    parser.add_argument("-p", "--password", type=str, help="设置登录密码，默认为 空 （设置后运行时将不再询问）")
    parser.add_argument("-u", "--uid", type=str, help="设置登录账号的 QQ 号，默认为 0 （设置后运行时将不再询问）")
    parser.add_argument("-w", "--work-path", type=str, help="设置工作目录，默认为当前目录（影响下载时的临时文件位置）")
    parser.add_argument("-o", "--onebot-path", type=str, help="设置OneBot安装路径，默认为当前目录")
    parser.add_argument("-pr", "--proxy", type=str,
                        help="设置github访问代理，默认不启用，需输入代理地址例如：http://127.0.0.1:12345")
    args = parser.parse_args()

    silent_installation = args.silent

    if args.work_path is not None:
        work_path = args.work_path

    if args.onebot_path is not None:
        onebot_path = args.onebot_path

    if args.proxy is not None:
        proxies = {
            'http': args.proxy,
            'https': args.proxy
        }
    else:
        # 如果是windows尝试读取系统注册表中记录的代理
        if platform.system() == "Windows":
            print("尝试读取系统代理")
            try:
                import winreg

                reg_path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
                # 打开注册表键
                registry_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_READ)
                # 读取是否启用代理
                is_proxy_enabled = winreg.QueryValueEx(registry_key, "ProxyEnable")[0]
                if is_proxy_enabled:
                    proxy_address = winreg.QueryValueEx(registry_key, "ProxyServer")[0]
                    proxies = {
                        'http': proxy_address,
                        'https': proxy_address
                    }
                    print("系统代理已启用")
                else:
                    print("系统代理未启用")
            except WindowsError:
                print("读取系统代理失败")

    start_time = time.time()

    if not silent_installation:
        print("欢迎您使用Lagrange.Onebot安装脚本\n")
        print("信息确认: \n当前工作目录 %s \n将在 %s 安装Lagrange.OneBot\n" % (work_path, onebot_path))
        if proxies is not None:
            print("使用代理:", proxies['https'])
        else:
            print("将不使用代理")

    lagrange_path = install(silent_installation)

    if not silent_installation:
        print("已为您下载最新的Lagrange.Onebot，请坐和放宽\n接下来进入我们需要更改一些配置文件...")
    arrangement(lagrange_path, silent_installation=silent_installation, password=args.password, uid=args.uid)

    if not silent_installation:
        print(
            f"您本次 Lagrange.Onebot 安装耗时 {int(time.time() - start_time) + 0.114514} 秒，打败全球 19.19810% 的用户\n")
        print("青，取之于蓝而青于蓝；冰，水为之而寒于水。\nLagrange.Onebot安装完成，期待与您的下次见面...")
