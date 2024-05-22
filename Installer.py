# coding:utf-8

import os
import platform
import time
import requests
import zipfile
import subprocess
import json
import tqdm

url = "https://github.com/xiaosuyyds/MuRainBot2/archive/refs/heads/master.zip"

work_path = os.path.abspath(os.path.dirname(__file__))
onebot_path = os.path.join(work_path, "OneBot")

# 增加重连接次数：
requests.DEFAULT_RETRIES = 5
s = requests.session()
# 关闭多余连接
s.keep_alive = False

# 安装OneBot实现
print("欢迎您使用Lagrange.Onebot安装脚本")
print("将安装LagrangeDev/Lagrange.Core")

# 由于github下载工作流附件需要登录故放弃
"""
import bs4

lagrange_url = "https://github.com/LagrangeDev/Lagrange.Core"
# 获取仓库的最新工作流
workflow_runs_url = f'{lagrange_url}/actions/workflows/Lagrange.OneBot-build.yml'
response = requests.get(workflow_runs_url, proxies={'http': '127.0.0.1:10809', 'https': '127.0.0.1:10809'})
# bs4筛选最新的工作流
soup = bs4.BeautifulSoup(response.content.decode("utf-8"), "html.parser")

latest_workflow_run = "https://github.com" + soup.find("a", class_="d-flex flex-items-center width-full mb-1")["href"]
print("最新工作流:", latest_workflow_run)

# 获取最新工作流的产物
response = requests.get(latest_workflow_run, proxies={'http': '127.0.0.1:10809', 'https': '127.0.0.1:10809'})
# bs4筛选最新的工作流产物
soup = bs4.BeautifulSoup(response.content.decode("utf-8"), "html.parser")
latest_workflow_run_artifacts = soup.find_all("a", class_="ActionListContent")
latest_workflow_run_artifacts = [artifact["href"] for artifact in latest_workflow_run_artifacts]
latest_workflow_run_artifacts = [url for url in latest_workflow_run_artifacts if "job" in url]
print("最新工作流产物:", latest_workflow_run_artifacts)
"""

lagrange_url = "https://api.github.com/repos/LagrangeDev/Lagrange.Core/releases"
response = requests.get(lagrange_url, proxies={'http': '127.0.0.1:10809', 'https': '127.0.0.1:10809'})
latest_release_url = response.json()[0]["assets"]


print("请选择要安装的Lagrange.Onebot版本:")
for i, release in enumerate(latest_release_url):
    print(f"{i+1}.{release['name']}")

choice = input("请输入版本号（不输入将安装自动识别的版本）: ")
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
            print(f"自动识别到您当前的系统是{system}，架构是{cpu_architecture}，已为您选择{release['name']}")
            break

choice = int(choice)

if choice < 1 or choice > len(latest_release_url):
    print("无效的选择")
    exit()

choice = latest_release_url[choice-1]

print("青，出于蓝而胜于蓝，冰，水为之而寒于水，正在为你下载Lagrange.Onebot...")
proxy = {'http': '127.0.0.1:10809', 'https': '127.0.0.1:10809'}
with open(choice["name"], "wb") as f, requests.get(choice["browser_download_url"], stream=True, proxies=proxy) as res:
    with tqdm.tqdm(total=int(res.headers.get('content-length', 0)), unit='iB', unit_scale=True) as pbar:
        for chunk in res.iter_content(chunk_size=64 * 1024):
            if not chunk:
                break
            f.write(chunk)
            pbar.update(len(chunk))

print("Lagrange.Onebot下载完成")

print("正在解压Lagrange.Onebot...")
print("Lagrange.Onebot解压完成")

with zipfile.ZipFile(choice["name"], 'r') as zip_ref:
    zip_ref.extractall()
os.rename(os.path.join(work_path, "publish"), onebot_path)
os.remove(choice["name"])

# 寻找Lagrange.Onebot的执行文件
flag = 0
lagrange_path = ""
for root, dirs, files in os.walk(onebot_path):
    for file in files:
        if "Lagrange.OneBot" in file:
            lagrange_path = os.path.join(root, file)
            flag = 1
            break
if flag == 0:
    print("未找到Lagrange.Onebot的执行文件")
    exit()

print("已为您下载最新的Lagrange.Onebot，但尚未完全安装完毕，请坐和放宽\n接下来进入我们需要更改一些配置文件...")


uid = input("请输入bot的QQ号(不输入则请勾选“下次登录无需扫码”): ")
password = input("请输入bot的密码(不输入则请勾选“下次登录无需扫码”): ")

if uid == "":
    uid = 0
uid = int(uid)


os.chdir(onebot_path)

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

p.kill()

lagrange_config_path = os.path.join(onebot_path, "appsettings.json")

# 修改配置文件
with open(lagrange_config_path, "r", encoding="utf-8") as f:
    config = json.load(f)
    config["Account"]["Uin"] = uid
    config["SignServerUrl"] = "https://sign.lagrangecore.org/api/sign"
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
print("配置文件已修改")

with open(lagrange_config_path, "w", encoding="utf-8") as f:
    json.dump(config, f, ensure_ascii=False, indent=4)

flag = 0


def login():
    global flag, uid
    print("海内存知己，天涯若比邻。正在进行首次登录流程，请不要结束进程...")
    p = subprocess.Popen(
        lagrange_path,
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(1)
    # 获取实时输出
    for line in iter(p.stdout.readline, b''):
        if "QrCode Fetched, Expiration: 120 seconds" in line.decode('utf-8'):
            print("请扫码登陆")
            os.system("cmd.exe /c " + os.path.join(onebot_path, "qr-%s.png" % uid))
        elif "Login Success" in line.decode('utf-8'):
            print("登录成功")
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

            flag = 1
            break
        elif "QrCode Expired, Please Fetch QrCode Again" in line.decode('utf-8'):
            print("二维码已过期，请重新扫码")
            p.kill()
            login()
            break
    p.kill()


login()

if flag == 0:
    print("登录失败，请重新运行安装程序")
    exit()
else:
    with open(lagrange_config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
        config["Account"]["Password"] = password

    with open(lagrange_config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

    print("配置文件已修改")

print("您本次 Lagrange.Onebot 安装耗时 %s 秒，打败全球 11.4514% 的用户")
print("Lagrange.Onebot安装完成，期待与您的下次见面...")