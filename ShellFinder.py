#!/usr/bin/python3
import os
import requests
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

class bcolors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def banner():
    print(f"""{bcolors.BLUE}{bcolors.BOLD}
   ╔══════════════════════════════════════╗
   ║      ⚡ Shell Finder by EXE ⚡       ║
   ║           github.com/EXE88           ║
   ║ [!] Author not responsible for use   ║
   ╚══════════════════════════════════════╝
{bcolors.RESET}""")

def clearing():
    os.system('cls' if os.name == 'nt' else 'clear')

def validate_url(url):
    return re.match(r'^https?://', url.strip())

def get_user_settings():
    print(f"\n{bcolors.YELLOW}[★] Configuration Settings:{bcolors.RESET}")

    use_proxy = input(f"{bcolors.BLUE}[+] Use proxy? (y/n): {bcolors.RESET}").strip().lower()
    if use_proxy == 'y':
        proxy_url = input(f"{bcolors.YELLOW}[+] Enter proxy (e.g., http://127.0.0.1:8080): {bcolors.RESET}")
        proxies = {'http': proxy_url, 'https': proxy_url}
    else:
        proxies = {}

    try:
        threads = int(input(f"{bcolors.BLUE}[+] Max threads [default 30]: {bcolors.RESET}") or 30)
        timeout = int(input(f"{bcolors.BLUE}[+] Request timeout [default 5]: {bcolors.RESET}") or 5)
    except ValueError:
        print(f"{bcolors.RED}[!] Invalid input. Using defaults.{bcolors.RESET}")
        threads, timeout = 30, 5

    output_file = input(f"{bcolors.BLUE}[+] Output filename [default found.txt]: {bcolors.RESET}") or 'found.txt'

    return proxies, threads, timeout, output_file

def get_telegram_info():
    use_telegram = input(f"{bcolors.BLUE}[+] Send results to Telegram? (y/n): {bcolors.RESET}").strip().lower()
    if use_telegram == 'y':
        token = input(f"{bcolors.YELLOW}[+] Enter bot token: {bcolors.RESET}").strip()
        chat_id = input(f"{bcolors.YELLOW}[+] Enter chat ID: {bcolors.RESET}").strip()
        return token, chat_id
    return None, None

def send_telegram_message(token, chat_id, message):
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {'chat_id': chat_id, 'text': message}
        r = requests.post(url, data=payload)
        if r.status_code == 200:
            print(f"{bcolors.GREEN}[+] Sent to Telegram.{bcolors.RESET}")
        else:
            print(f"{bcolors.RED}[!] Telegram error: {r.text}{bcolors.RESET}")
    except Exception as e:
        print(f"{bcolors.RED}[!] Telegram connection failed: {e}{bcolors.RESET}")

def get_shell_list():
    global default_shells
    choice = input(f"{bcolors.CYAN}[1] Use default shell paths\n[2] Load from file\n[+] Your choice (1/2): {bcolors.RESET}")
    if choice == '1':
        return default_shells
    elif choice == '2':
        path = input(f"{bcolors.YELLOW}[+] Enter file path: {bcolors.RESET}")
        try:
            with open(path) as f:
                return [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print(f"{bcolors.RED}[!] File not found.{bcolors.RESET}")
    return []

def get_website_list():
    choice = input(f"{bcolors.CYAN}[1] Enter URLs manually\n[2] Load from file\n[+] Your choice (1/2): {bcolors.RESET}")
    sites = []
    if choice == '1':
        print(f"{bcolors.YELLOW}[+] Type URLs (type 'done' when finished):{bcolors.RESET}")
        while True:
            url = input("URL: ").strip()
            if url.lower() == 'done':
                break
            if validate_url(url):
                sites.append(url)
            else:
                print(f"{bcolors.RED}[!] Invalid URL.{bcolors.RESET}")
    elif choice == '2':
        path = input(f"{bcolors.YELLOW}[+] Enter file path: {bcolors.RESET}")
        try:
            with open(path) as f:
                sites = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print(f"{bcolors.RED}[!] File not found.{bcolors.RESET}")
    return sites

def scan_shell(session, website, shell, headers, proxies, timeout):
    url = website.rstrip('/') + shell
    try:
        r = session.get(url, headers=headers, timeout=timeout, proxies=proxies)
        if r.status_code == 200:
            print(f"{bcolors.GREEN}[+] Found: {url} [200]{bcolors.RESET}")
            return url
        else:
            print(f"{bcolors.RED}[-] Not Found: {url} [{r.status_code}]{bcolors.RESET}")
    except Exception as e:
        print(f"{bcolors.RED}[!] Error: {url} => {e}{bcolors.RESET}")
    return None

def find_shells():
    clearing()
    banner()
    proxies, max_threads, timeout, output_file = get_user_settings()
    token, chat_id = get_telegram_info()
    sites = get_website_list()
    shells = get_shell_list()
    if not sites or not shells:
        print(f"{bcolors.RED}[!] No URLs or shells provided. Exiting...{bcolors.RESET}")
        return

    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Accept': '*/*',
        'Connection': 'keep-alive'
    }

    foundshells = []
    with requests.Session() as session:
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            tasks = []
            for site in sites:
                if not site.startswith('http'):
                    site = 'http://' + site
                for shell in shells:
                    tasks.append(executor.submit(scan_shell, session, site, shell, headers, proxies, timeout))

            for future in as_completed(tasks):
                result = future.result()
                if result:
                    foundshells.append(result)

    if foundshells:
        with open(output_file, 'w') as f:
            f.write("\n".join(foundshells))
        print(f"{bcolors.GREEN}[✓] Saved to {output_file}{bcolors.RESET}")
        if token and chat_id:
            send_telegram_message(token, chat_id, "\n".join(foundshells))
    else:
        print(f"{bcolors.YELLOW}[!] No shells found.{bcolors.RESET}")

    input(f"{bcolors.CYAN}[→] Press Enter to exit...{bcolors.RESET}")

if __name__ == '__main__':
    default_shells = [
        '/madspot.php', '/mad.php', '/wp-admin/js/widgets/about.php7', '/wp-admin/js/widgets/admin.php','/Njima.php','/about.php','/about.php7','/7x.php', '/x7.php', '/404.php', '/anon.php', '/anonymous.php', '/shell.php','/sh3ll.php', '/madspotshell.php', '/b374k.php', '/c100.php', '/priv8.php', '/private.php', '/file.php',
        '/wp-content/themes/hideo/network.php','/wp-content/plugins/dummyyummy/wp-signup.php','/wp-content/plugins/fix/up.php','/inputs.php','/wp-admin/maint/upfile.php',
        '/userfiles/files/u.php7','/mah.php','/atomlib.php','/wp-content/plugins/yyobang/mar.php','/wp-content/themes/travelscape/json.php','/wp-content/themes/aahana/json.php','/simple.php',
        '/wp-content/plugins/seoplugins/mar.php','/wp-content/themes/seotheme/mar.php','/wp-content/plugins/ango/sett.php','/wp-login.php'
        '/cp.php', '/cpbrute.php', '/themes/404/404.php', '/templates/atomic/index.php', '/templates/beez5/index.php', '/upp.php', '/Shellton.php', '/ShellTon.php', '/admin.php', '/Admin.php', '/ADMIN.php','/hacked.php', '/r57.php', '/wso.php', '/WSO.php', '/wso24.php', '/wso26.php', '/wso404.php', '/sym.php',
        '/symsa2.php', '/sym3.php', '/whmcs.php', '/whmcskiller.php', '/cracker.php', '/1.php', '/2.php', '/sql.php','/gaza.php', '/database.php', '/a.php', '/d.php', '/dz.php', '/cpanel.php', '/system.php', '/um3r.php',
        '/zone-h.php', '/c22.php', '/root.php', '/r00t.php', '/doom.php', '/dam.php', '/killer.php', '/user.php','/wp-content/plugins/disqus-comment-system/disqus.php', '/cpn.php', '/shelled.php', '/uploader.php',
        "/wp-admin/js/widgets/madspot.php", "/wp-admin/js/widgets/mad.php", "/wp-admin/js/widgets/admin.php", 
        "/wp-admin/js/widgets/Njima.php", "/wp-admin/js/widgets/about.php", "/wp-admin/js/widgets/7x.php", "/wp-admin/js/widgets/x7.php", "/wp-admin/js/widgets/404.php", "/wp-admin/js/widgets/anon.php", 
        "/wp-admin/js/widgets/anonymous.php", "/wp-admin/js/widgets/shell.php", "/wp-admin/js/widgets/sh3ll.php", "/wp-admin/js/widgets/madspotshell.php", 
        "/wp-admin/js/widgets/b374k.php", "/wp-admin/js/widgets/c100.php", "/wp-admin/js/widgets/priv8.php", "/wp-admin/js/widgets/private.php", 
        "/wp-admin/js/widgets/file.php", "/wp-admin/js/widgets/cp.php", "/wp-admin/js/widgets/cpbrute.php", "/wp-admin/js/widgets/themes/404/404.php", 
        "/wp-admin/js/widgets/index.php", "/wp-admin/js/widgets/templates/beez5/index.php", "/wp-admin/js/widgets/upp.php", "/wp-admin/js/widgets/Shellton.php", "/wp-admin/js/widgets/ShellTon.php", "/wp-admin/js/widgets/admin.php", "/wp-admin/js/widgets/Admin.php", "/wp-admin/js/widgets/ADMIN.php", "/wp-admin/js/widgets/hacked.php", "/wp-admin/js/widgets/r57.php", "/wp-admin/js/widgets/wso.php", "/wp-admin/js/widgets/WSO.php", "/wp-admin/js/widgets/wso24.php", "/wp-admin/js/widgets/wso26.php", "/wp-admin/js/widgets/wso404.php", "/wp-admin/js/widgets/sym.php", "/wp-admin/js/widgets/symsa2.php", "/wp-admin/js/widgets/sym3.php", "/wp-admin/js/widgets/whmcs.php", "/wp-admin/js/widgets/whmcskiller.php", "/wp-admin/js/widgets/cracker.php", "/wp-admin/js/widgets/1.php", "/wp-admin/js/widgets/2.php", "/wp-admin/js/widgets/sql.php", "/wp-admin/js/widgets/gaza.php", "/wp-admin/js/widgets/database.php", "/wp-admin/js/widgets/a.php", "/wp-admin/js/widgets/d.php", "/wp-admin/js/widgets/dz.php", "/wp-admin/js/widgets/cpanel.php", "/wp-admin/js/widgets/system.php", "/wp-admin/js/widgets/um3r.php", "/wp-admin/js/widgets/zone-h.php", "/wp-admin/js/widgets/c22.php", "/wp-admin/js/widgets/root.php", "/wp-admin/js/widgets/r00t.php", "/wp-admin/js/widgets/doom.php", "/wp-admin/js/widgets/dam.php", "/wp-admin/js/widgets/killer.php", "/wp-admin/js/widgets/user.php", "/wp-admin/js/widgets/wp-content/plugins/disqus-comment-system/disqus.php", "/wp-admin/js/widgets/cpn.php", "/wp-admin/js/widgets/shelled.php", "/wp-admin/js/widgets/uploader.php", "/wp-admin/js/widgets/up.php", "/wp-admin/js/widgets/xd.php"
        '/up.php', '/xd.php', '/d00.php', '/h4xor.php', '/tmp/mad.php', '/tmp/1.php','/wp-content/plugins/akismet/akismet.php', '/images/stories/w.php', '/w.php', '/downloads/dom.php','/templates/ja-helio-farsi/index.php', '/wp-admin/m4d.php', '/d.php', '/WSO.php', '/dz.php', '/w.php', 
        '/wp-content/plugins/akismet/akismet.php','/images/stories/w.php', '/w.php', '/shell.php', '/cpanel.php', '/cpn.php', '/sql.php', '/mysql.php', '/config.php', '/configuration.php', '/madspot.php','/Cgishell.pl', '/killer.php', '/changeall.php', '/2.php', '/Sh3ll.php', '/dz0.php', '/dam.php', '/user.php', '/dom.php', '/whmcs.php', '/r00t.php', '/1.php', '/a.php','/r0k.php', '/abc.php', '/egy.php', '/syrian_shell.php', '/xxx.php', '&#8203;', '/settings.php', '/tmp.php', '/cyber.php', '/c99.php', '/r57.php', '/404.php', '/gaza.php','/1.php', '/d4rk.php', '/index1.php', '/nkr.php', '/xd.php', 
        '/M4r0c.php', '/Dz.php', '/sniper.php', '/ksa.php', '/v4team.php', '/offline.php', '/priv8.php', '/911.php','/madspotshell.php', '/c100.php', '/sym.php', '/cp.php', '/tmp/cpn.php', '/tmp/w.php', '/tmp/r57.php', '/tmp/king.php', '/tmp/sok.php', '/tmp/ss.php', '/tmp/as.php','/tmp/dz.php', '/tmp/r1z.php', 
        '/tmp/whmcs.php', '/tmp/root.php', '/tmp/r00t.php', '/templates/beez/index.php', '/templates/beez/beez.php', '/templates/rhuk_milkyway/index.php','/tmp/uploads.php', '/tmp/upload.php', '/tmp/sa.php', '/sa.php', '/readme.php', '/tmp/readme.php', '/wp.zip', '/wp-content/plugins/disqus-comment-system/disqus.php',
        '/d0mains.php', '/wp-content/plugins/akismet/akismet.php', '/madspotshell.php', '/info.php', '/egyshell.php', '/Sym.php', '/c22.php', '/c100.php','/wp-content/plugins/akismet/admin.php#', '/configuration.php', '/g.php', '/wp-content/plugins/google-sitemap-generator/sitemap-core.php#','/wp-content/plugins/akismet/widget.php#', '/xx.pl', '/ls.php', '/Cpanel.php', '/k.php', '/zone-h.php', '/tmp/user.php', '/tmp/Sym.php', '/cp.php','/tmp/madspotshell.php', '/tmp/root.php', '/tmp/whmcs.php', '/tmp/index.php', '/tmp/2.php', '/tmp/dz.php', '/tmp/cpn.php', '/tmp/changeall.php', '/tmp/Cgishell.pl',
        '/tmp/sql.php', '/0day.php', '/tmp/admin.php','/cliente/downloads/h4xor.php', '/whmcs/downloads/dz.php', '/L3b.php', '/d.php', '/tmp/d.php', '/tmp/L3b.php','/wp-content/plugins/akismet/admin.php', '/templates/rhuk_milkyway/index.php', '/templates/beez/index.php', '/sado.php', '/admin1.php', '/upload.php',
        '/up.php', '/vb.zip', '/vb.rar', '/admin2.asp', '/uploads.php', '/sa.php', '/sysadmins/', '/admin1/', '/sniper.php', '/administration/Sym.php', '/images/Sym.php', '/r57.php',
        '/wp-content/plugins/disqus-comment-system/disqus.php','/gzaa_spysl', '/sql-new.php', '/shell.php', '/sa.php', '/admin.php', '/sa2.php', '/2.php', '/gaza.php','/up.php', '/upload.php', '/uploads.php', '/templates/beez/index.php', '/shell.php', '/amad.php', '/t00.php', '/dz.php', '/site.rar', '/Black.php', '/site.tar.gz',
        '/home.zip', '/home.rar', '/home.tar', '/home.tar.gz','/forum.zip','/forum.rar','/forum.tar','/forum.tar.gz', '/test.txt', '/ftp.txt', '/user.txt','/site.txt', '/error_log', '/error', '/cpanel', '/awstats', '/site.sql', '/vb.sql', '/forum.sql', '/r00t-s3c.php', '/c.php', '/backup.sql', '/back.sql', '/data.sql',
        '/wp.rar/', '/wp-content/plugins/disqus-comment-system/disqus.php', '/asp.aspx', '/templates/beez/index.php', '/tmp/vaga.php', '/tmp/killer.php', '/whmcs.php','/abuhlail.php', '/tmp/killer.php', '/tmp/domaine.pl', '/tmp/domaine.php', '/useradmin/', '/tmp/d0maine.php', '/d0maine.php', '/tmp/sql.php', '/X.php', '/123.php', '/m.php',
        '/b.php', '/up.php', '/tmp/dz1.php', '/shellton.php', '/upp.php','/Shellton.php', '/ShellTon.php','a/dmin.php','/dz1.php', '/forum.zip', '/Symlink.php', '/Symlink.pl', '/forum.rar', '/joomla.zip', '/joomla.rar', '/wp.php', '/buck.sql', '/sysadmin.php',
        '/images/c99.php', '/xd.php', '/c100.php', '/spy.aspx', '/xd.php', '/tmp/xd.php', '/sym/root/home/', '/billing/killer.php', '/tmp/upload.php', '/tmp/admin.php', '/Server.php',
        '/tmp/uploads.php', '/tmp/up.php', '/Server/', '/wp-admin/c99.php', '/tmp/priv8.php', '/priv8.php', '/cgi.pl/', '/tmp/cgi.pl', '/downloads/dom.php','/templates/ja-helio-farsi/index.php', '/webadmin.html', '/admins.php', '/wp-content/plugins/count-per-day/js/yc/d00.php', '/bluff.php', '/king.jeen', '/admins/',
        '/admins.asp', '/admins.php', '/wp.zip', '/wp-content/plugins/disqus-comment-system/WSO.php', '/wp-content/plugins/disqus-comment-system/dz.php', '/wp-content/plugins/disqus-comment-system/DZ.php',
        '/wp-content/plugins/disqus-comment-system/cpanel.php', '/wp-content/plugins/disqus-comment-system/cpn.php', '/wp-content/plugins/disqus-comment-system/sos.php', '/wp-content/plugins/disqus-comment-system/term.php',
        '/wp-content/plugins/disqus-comment-system/Sec-War.php', '/wp-content/plugins/disqus-comment-system/sql.php', '/wp-content/plugins/disqus-comment-system/ssl.php','/wp-content/plugins/disqus-comment-system/mysql.php',
        '/wp-content/plugins/disqus-comment-system/WolF.php','/wp-content/plugins/disqus-comment-system/madspot.php','/wp-content/plugins/disqus-comment-system/Cgishell.pl','/wp-content/plugins/disqus-comment-system/killer.php',
        '/wp-content/plugins/disqus-comment-system/changeall.php','/wp-content/plugins/disqus-comment-system/2.php','/wp-content/plugins/disqus-comment-system/Sh3ll.php','/wp-content/plugins/disqus-comment-system/dz0.php',
        '/wp-content/plugins/disqus-comment-system/dam.php','/wp-content/plugins/disqus-comment-system/user.php','/wp-content/plugins/disqus-comment-system/dom.php','/wp-content/plugins/disqus-comment-system/whmcs.php',
        '/wp-content/plugins/disqus-comment-system/vb.zip','/wp-content/plugins/disqus-comment-system/r00t.php','/wp-content/plugins/disqus-comment-system/c99.php','/wp-content/plugins/disqus-comment-system/gaza.php',
        '/wp-content/plugins/disqus-comment-system/1.php','/wp-content/plugins/disqus-comment-system/d0mains.php','/wp-content/plugins/disqus-comment-system/madspotshell.php',
        '/wp-content/plugins/disqus-comment-system/info.php','/wp-content/plugins/disqus-comment-system/egyshell.php','/wp-content/plugins/disqus-comment-system/Sym.php','/wp-content/plugins/disqus-comment-system/c22.php',
        '/wp-content/plugins/disqus-comment-system/c100.php','/wp-content/plugins/disqus-comment-system/configuration.php','/wp-content/plugins/disqus-comment-system/g.php','/wp-content/plugins/disqus-comment-system/xx.pl',
        '/wp-content/plugins/disqus-comment-system/ls.php','/wp-content/plugins/disqus-comment-system/Cpanel.php','/wp-content/plugins/disqus-comment-system/k.php','/wp-content/plugins/disqus-comment-system/zone-h.php',
        '/wp-content/plugins/disqus-comment-system/tmp/user.php','/wp-content/plugins/disqus-comment-system/tmp/Sym.php','/wp-content/plugins/disqus-comment-system/cp.php','/wp-content/plugins/disqus-comment-system/tmp/madspotshell.php',
        '/wp-content/plugins/disqus-comment-system/tmp/root.php','/wp-content/plugins/disqus-comment-system/tmp/whmcs.php','/wp-content/plugins/disqus-comment-system/tmp/index.php',
        '/wp-content/plugins/disqus-comment-system/tmp/2.php','/wp-content/plugins/disqus-comment-system/tmp/dz.php','/wp-content/plugins/disqus-comment-system/tmp/cpn.php','/wp-content/plugins/disqus-comment-system/tmp/changeall.php',
        '/wp-content/plugins/disqus-comment-system/tmp/Cgishell.pl','/wp-content/plugins/disqus-comment-system/tmp/sql.php','/wp-content/plugins/disqus-comment-system/0day.php',
        '/wp-content/plugins/disqus-comment-system/tmp/admin.php','/wp-content/plugins/disqus-comment-system/L3b.php','/wp-content/plugins/disqus-comment-system/d.php',
        '/wp-content/plugins/disqus-comment-system/tmp/d.php','/wp-content/plugins/disqus-comment-system/tmp/L3b.php','/wp-content/plugins/disqus-comment-system/sado.php',
        '/wp-content/plugins/disqus-comment-system/admin1.php','/wp-content/plugins/disqus-comment-system/upload.php','/wp-content/plugins/disqus-comment-system/up.php',
        '/wp-content/plugins/disqus-comment-system/vb.zip','/wp-content/plugins/disqus-comment-system/vb.rar','/wp-content/plugins/disqus-comment-system/admin2.asp',
        '/wp-content/plugins/disqus-comment-system/uploads.php','/wp-content/plugins/disqus-comment-system/sa.php','/wp-content/plugins/disqus-comment-system/sysadmins/','/wp-content/plugins/disqus-comment-system/admin1/','/wp-content/plugins/disqus-comment-system/sniper.php',
        '/wp-content/plugins/disqus-comment-system/images/Sym.php','/wp-content/plugins/disqus-comment-system//r57.php','/wp-content/plugins/disqus-comment-system/gzaa_spysl',
        '/wp-content/plugins/disqus-comment-system/sql-new.php','/wp-content/plugins/disqus-comment-system//shell.php','/wp-content/plugins/disqus-comment-system//sa.php',
        '/wp-content/plugins/disqus-comment-system//admin.php','/wp-content/plugins/disqus-comment-system//sa2.php','/wp-content/plugins/disqus-comment-system//2.php','/wp-content/plugins/disqus-comment-system//gaza.php',
        '/wp-content/plugins/disqus-comment-system//up.php','/wp-content/plugins/disqus-comment-system//upload.php','/wp-content/plugins/disqus-comment-system//uploads.php',
        '/wp-content/plugins/disqus-comment-system/shell.php','/wp-content/plugins/disqus-comment-system//amad.php','/wp-content/plugins/disqus-comment-system//t00.php',
        '/templates/beez/WSO.php','/templates/beez/dz.php','/templates/beez/DZ.php','/templates/beez/cpanel.php','/templates/beez/cpn.php','/templates/beez/sos.php','/templates/beez/term.php','/templates/beez/Sec-War.php','/templates/beez/sql.php','/templates/beez/ssl.php','/templates/beez/mysql.php','/templates/beez/WolF.php','/templates/beez/madspot.php',
        '/pwp-content/plugins/disqus-comment-system/disqus.php','/wp-content/plugins/akismet/WSO.php','/wp-content/plugins/akismet/dz.php','/wp-content/plugins/akismet/DZ.php','/wp-content/plugins/akismet/cpanel.php',
        '/wp-content/plugins/akismet/cpn.php','/wp-content/plugins/akismet/sos.php','/wp-content/plugins/akismet/term.php','/wp-content/plugins/akismet/Sec-War.php',
        '/wp-content/plugins/akismet/sql.php','/wp-content/plugins/akismet/ssl.php','/wp-content/plugins/akismet/mysql.php','/wp-content/plugins/akismet/WolF.php',
        '/wp-content/plugins/akismet/madspot.php','/wp-content/plugins/akismet/Cgishell.pl','/wp-content/plugins/akismet/killer.php','/wp-content/plugins/akismet/changeall.php','/wp-content/plugins/akismet/2.php','/wp-content/plugins/akismet/Sh3ll.php','/wp-content/plugins/akismet/dz0.php','/wp-content/plugins/akismet/dam.php','/wp-content/plugins/akismet/user.php',
        '/wp-content/plugins/akismet/dom.php','/wp-content/plugins/akismet/whmcs.php','/wp-content/plugins/akismet/vb.zip','/wp-content/plugins/akismet/r00t.php','/wp-content/plugins/akismet/c99.php','/wp-content/plugins/akismet/gaza.php','/wp-content/plugins/akismet/1.php','/wp-content/plugins/akismet/d0mains.php',
        '/wp-content/plugins/akismet/madspotshell.php','/wp-content/plugins/akismet/info.php','/wp-content/plugins/akismet/egyshell.php','/wp-content/plugins/akismet/Sym.php',
        '/wp-content/plugins/akismet/c22.php','/wp-content/plugins/akismet/c100.php','/wp-content/plugins/akismet/configuration.php','/wp-content/plugins/akismet/g.php',
        '/wp-content/plugins/akismet/xx.pl','/wp-content/plugins/akismet/ls.php','/wp-content/plugins/akismet/Cpanel.php','/wp-content/plugins/akismet/k.php','/wp-content/plugins/akismet/zone-h.php',
        '/wp-content/plugins/akismet/tmp/user.php','/wp-content/plugins/akismet/tmp/Sym.php','/wp-content/plugins/akismet/cp.php','/wp-content/plugins/akismet/tmp/madspotshell.php',
        '/wp-content/plugins/akismet/tmp/root.php','/wp-content/plugins/akismet/tmp/whmcs.php','/wp-content/plugins/akismet/tmp/index.php','/wp-content/plugins/akismet/tmp/2.php',
        '/wp-content/plugins/akismet/tmp/dz.php','/wp-content/plugins/akismet/tmp/cpn.php','/wp-content/plugins/akismet/tmp/changeall.php','/wp-content/plugins/akismet/tmp/Cgishell.pl',
        '/wp-content/plugins/akismet/tmp/sql.php','/wp-content/plugins/akismet/0day.php','/wp-content/plugins/akismet/tmp/admin.php','/wp-content/plugins/akismet/L3b.php',
        '/wp-content/plugins/akismet/d.php','/wp-content/plugins/akismet/tmp/d.php','/wp-content/plugins/akismet/tmp/L3b.php','/wp-content/plugins/akismet/sado.php',
        '/wp-content/plugins/akismet/admin1.php','/wp-content/plugins/akismet/upload.php','/wp-content/plugins/akismet/up.php','/wp-content/plugins/akismet/vb.zip','/wp-content/plugins/akismet/vb.rar',
        '/wp-content/plugins/akismet/admin2.asp','/wp-content/plugins/akismet/uploads.php','/wp-content/plugins/akismet/sa.php','/wp-content/plugins/akismet/sysadmins/','/wp-content/plugins/akismet/admin1/',
        '/wp-content/plugins/akismet/sniper.php','/wp-content/plugins/akismet/images/Sym.php','/wp-content/plugins/akismet//r57.php','/wp-content/plugins/akismet/gzaa_spysl','/wp-content/plugins/akismet/sql-new.php',
        '/wp-content/plugins/akismet//shell.php','/wp-content/plugins/akismet//sa.php','/wp-content/plugins/akismet//admin.php','/wp-content/plugins/akismet//sa2.php','/wp-content/plugins/akismet//2.php',
        '/wp-content/plugins/akismet//gaza.php','/wp-content/plugins/akismet//up.php','/wp-content/plugins/akismet//upload.php','/wp-content/plugins/akismet//uploads.php','/wp-content/plugins/akismet/shell.php',
        '/wp-content/plugins/akismet//amad.php','/wp-content/plugins/akismet//t00.php','/wp-content/plugins/akismet//dz.php','/wp-content/plugins/akismet//site.rar','/wp-content/plugins/akismet//Black.php','/wp-content/plugins/akismet//site.tar.gz',
        '/wp-content/plugins/akismet//home.zip','/wp-content/plugins/akismet//home.rar','/wp-content/plugins/akismet//home.tar','/wp-content/plugins/akismet//home.tar.gz','/wp-content/plugins/akismet//forum.zip','/wp-content/plugins/akismet//forum.rar','/wp-content/plugins/akismet//forum.tar','/wp-content/plugins/akismet//forum.tar.gz',
        '/wp-content/plugins/akismet//test.txt','/wp-content/plugins/akismet//ftp.txt','/wp-content/plugins/akismet//user.txt','/wp-content/plugins/akismet//site.txt','/wp-content/plugins/akismet//error_log','/wp-content/plugins/akismet//error',
        '/wp-content/plugins/akismet//cpanel','/wp-content/plugins/akismet//awstats','/wp-content/plugins/akismet//site.sql','/wp-content/plugins/akismet//vb.sql','/wp-content/plugins/akismet//forum.sql',
        '/wp-content/plugins/akismet/r00t-s3c.php','/wp-content/plugins/akismet/c.php','/wp-content/plugins/akismet//backup.sql','/wp-content/plugins/akismet//back.sql','/wp-content/plugins/akismet//data.sql',
        '/wp-content/plugins/akismet/wp.rar/','/wp-content/plugins/akismet/asp.aspx','/wp-content/plugins/akismet/tmp/vaga.php','/wp-content/plugins/akismet/tmp/killer.php','/wp-content/plugins/akismet/whmcs.php',
        '/wp-content/plugins/akismet/abuhlail.php','/wp-content/plugins/akismet/tmp/killer.php','/wp-content/plugins/akismet/tmp/domaine.pl','/wp-content/plugins/akismet/tmp/domaine.php',
        '/wp-content/plugins/akismet/useradmin/','/wp-content/plugins/akismet/tmp/d0maine.php','/wp-content/plugins/akismet/d0maine.php','/wp-content/plugins/akismet/tmp/sql.php','/wp-content/plugins/akismet/X.php',
        '/wp-content/plugins/akismet/123.php','/wp-content/plugins/akismet/m.php','/wp-content/plugins/akismet/b.php','/wp-content/plugins/akismet/up.php','/wp-content/plugins/akismet/tmp/dz1.php',
        '/wp-content/plugins/akismet/dz1.php','/wp-content/plugins/akismet/forum.zip','/wp-content/plugins/akismet/Symlink.php','/wp-content/plugins/akismet/Symlink.pl',
        '/wp-content/plugins/akismet/forum.rar','/wp-content/plugins/akismet/joomla.zip','/wp-content/plugins/akismet/joomla.rar','/wp-content/plugins/akismet/wp.php','/wp-content/plugins/akismet/buck.sql',
        '/wp-content/plugins/akismet/sysadmin.php','/wp-content/plugins/akismet/images/c99.php','/wp-content/plugins/akismet/xd.php','/wp-content/plugins/akismet/c100.php',
        '/wp-content/plugins/akismet/spy.aspx','/wp-content/plugins/akismet/xd.php','/wp-content/plugins/akismet/tmp/xd.php','/wp-content/plugins/akismet/sym/root/home/','/wp-content/plugins/akismet/billing/killer.php','/wp-content/plugins/akismet/tmp/upload.php','/wp-content/plugins/akismet/tmp/admin.php','/wp-content/plugins/akismet/Server.php','/wp-content/plugins/akismet/tmp/uploads.php','/wp-content/plugins/akismet/tmp/up.php',
        '/wp-content/plugins/akismet/Server/','/wp-content/plugins/akismet/wp-admin/c99.php','/wp-content/plugins/akismet/tmp/priv8.php','/wp-content/plugins/akismet/priv8.php',
        '/wp-content/plugins/akismet/cgi.pl/','/wp-content/plugins/akismet/tmp/cgi.pl','/wp-content/plugins/akismet/downloads/dom.php','/wp-content/plugins/akismet/webadmin.html','/wp-content/plugins/akismet/admins.php','/wp-content/plugins/akismet/bluff.php','/wp-content/plugins/akismet/king.jeen','/wp-content/plugins/akismet/admins/','/wp-content/plugins/akismet/admins.asp','/wp-content/plugins/akismet/admins.php','/wp-content/plugins/akismet/wp.zip',
        '/wp-content/plugins/akismet/disqus.php','/wp-content/plugins/google-sitemap-generator//cpanel','/wp-content/plugins/google-sitemap-generator//awstats','/wp-content/plugins/google-sitemap-generator//site.sql',
        '/wp-content/plugins/google-sitemap-generator//vb.sql','/wp-content/plugins/google-sitemap-generator//forum.sql','/wp-content/plugins/google-sitemap-generator/r00t-s3c.php','/wp-content/plugins/google-sitemap-generator/c.php','/wp-content/plugins/google-sitemap-generator//backup.sql','/wp-content/plugins/google-sitemap-generator//back.sql','/wp-content/plugins/google-sitemap-generator//data.sql','/wp-content/plugins/google-sitemap-generator/wp.rar/','/wp-content/plugins/google-sitemap-generator/asp.aspx','/wp-content/plugins/google-sitemap-generator/tmp/vaga.php',
        '/wp-content/plugins/google-sitemap-generator/tmp/killer.php','/wp-content/plugins/google-sitemap-generator/whmcs.php','/wp-content/plugins/google-sitemap-generator/abuhlail.php','/wp-content/plugins/google-sitemap-generator/tmp/killer.php','/wp-content/plugins/google-sitemap-generator/tmp/domaine.pl',
        '/wp-content/plugins/google-sitemap-generator/tmp/domaine.php','/wp-content/plugins/google-sitemap-generator/useradmin/','/wp-content/plugins/google-sitemap-generator/tmp/d0maine.php',
        '/wp-content/plugins/google-sitemap-generator/d0maine.php','/wp-content/plugins/google-sitemap-generator/tmp/sql.php','/wp-content/plugins/google-sitemap-generator/X.php',
        '/wp-content/plugins/google-sitemap-generator/123.php','/wp-content/plugins/google-sitemap-generator/m.php','/wp-content/plugins/google-sitemap-generator/b.php','/wp-content/plugins/google-sitemap-generator/up.php','/wp-content/plugins/google-sitemap-generator/tmp/dz1.php','/wp-content/plugins/google-sitemap-generator/dz1.php','/wp-content/plugins/google-sitemap-generator/forum.zip',
        '/wp-content/plugins/google-sitemap-generator/Symlink.php','/wp-content/plugins/google-sitemap-generator/Symlink.pl','/wp-content/plugins/google-sitemap-generator/forum.rar','/wp-content/plugins/google-sitemap-generator/joomla.zip',
        '/wp-content/plugins/google-sitemap-generator/joomla.rar','/wp-content/plugins/google-sitemap-generator/wp.php','/wp-content/plugins/google-sitemap-generator/buck.sql','/wp-content/plugins/google-sitemap-generator/sysadmin.php','/wp-content/plugins/google-sitemap-generator/images/c99.php','/wp-content/plugins/google-sitemap-generator/xd.php','/wp-content/plugins/google-sitemap-generator/c100.php',
        '/wp-content/plugins/google-sitemap-generator/spy.aspx','/wp-content/plugins/google-sitemap-generator/xd.php','/wp-content/plugins/google-sitemap-generator/tmp/xd.php','/wp-content/plugins/google-sitemap-generator/sym/root/home/',
        '/wp-content/plugins/google-sitemap-generator/billing/killer.php','/wp-content/plugins/google-sitemap-generator/tmp/upload.php','/wp-content/plugins/google-sitemap-generator/tmp/admin.php','/wp-content/plugins/google-sitemap-generator/Server.php',
        '/wp-content/plugins/google-sitemap-generator/tmp/uploads.php','/wp-content/plugins/google-sitemap-generator/tmp/up.php','/wp-content/plugins/google-sitemap-generator/Server/','/wp-content/plugins/google-sitemap-generator/wp-admin/c99.php',
        '/wp-content/plugins/google-sitemap-generator/tmp/priv8.php','/wp-content/plugins/google-sitemap-generator/priv8.php','/wp-content/plugins/google-sitemap-generator/cgi.pl/',
        '/wp-content/plugins/google-sitemap-generator/tmp/cgi.pl','/wp-content/plugins/google-sitemap-generator/downloads/dom.php','/wp-content/plugins/google-sitemap-generator/webadmin.html','/wp-content/plugins/google-sitemap-generator/admins.php','/wp-content/plugins/google-sitemap-generator/bluff.php','/wp-content/plugins/google-sitemap-generator/king.jeen','/wp-content/plugins/google-sitemap-generator/admins/',
        '/wp-content/plugins/google-sitemap-generator/admins.asp','/wp-content/plugins/google-sitemap-generator/admins.php','/wp-content/plugins/google-sitemap-generator/wp.zip','/wp-content/plugins/google-sitemap-generator/sitemap-core.php'
        '/templates/beez/Cgishell.pl','/templates/beez/killer.php','/templates/beez/changeall.php','/templates/beez/2.php','/templates/beez/Sh3ll.php','/templates/beez/dz0.php','/templates/beez/dam.php','/templates/beez/user.php','/templates/beez/dom.php',
        '/templates/beez/whmcs.php','/templates/beez/vb.zip','/templates/beez/r00t.php','/templates/beez/c99.php','/templates/beez/gaza.php','/templates/beez/1.php','/templates/beez/d0mains.php',
        '/templates/beez/madspotshell.php','/templates/beez/info.php','/templates/beez/egyshell.php','/templates/beez/Sym.php','/templates/beez/c22.php','/templates/beez/c100.php','/templates/beez/configuration.php','/templates/beez/g.php','/templates/beez/xx.pl','/templates/beez/ls.php','/templates/beez/Cpanel.php','/templates/beez/k.php','/templates/beez/zone-h.php','/templates/beez/tmp/user.php','/templates/beez/tmp/Sym.php',
        '/templates/beez/cp.php','/templates/beez/tmp/madspotshell.php','/templates/beez/tmp/root.php','/templates/beez/tmp/whmcs.php','/templates/beez/tmp/index.php','/templates/beez/tmp/2.php','/templates/beez/tmp/dz.php','/templates/beez/tmp/cpn.php','/templates/beez/tmp/changeall.php','/templates/beez/tmp/Cgishell.pl','/templates/beez/tmp/sql.php',
        '/templates/beez/0day.php','/templates/beez/tmp/admin.php','/templates/beez/L3b.php','/templates/beez/d.php','/templates/beez/tmp/d.php','/templates/beez/tmp/L3b.php','/templates/beez/sado.php','/templates/beez/admin1.php',
        '/templates/beez/upload.php','/templates/beez/up.php','/templates/beez/vb.zip','/templates/beez/vb.rar','/templates/beez/admin2.asp','/templates/beez/uploads.php','/templates/beez/sa.php','/templates/beez/sysadmins/','/templates/beez/admin1/',
        '/templates/beez/sniper.php','/templates/beez/images/Sym.php','/templates/beez//r57.php','/templates/beez/gzaa_spysl','/templates/beez/sql-new.php','/templates/beez//shell.php','/templates/beez//sa.php','/templates/beez//admin.php','/templates/beez//sa2.php','/templates/beez//2.php','/templates/beez//gaza.php',
        '/templates/beez//up.php','/templates/beez//upload.php','/templates/beez//uploads.php','/templates/beez/shell.php','/templates/beez//amad.php','/templates/beez//t00.php','/templates/beez//dz.php','/templates/beez//site.rar','/templates/beez//Black.php','/templates/beez//site.tar.gz','/templates/beez//home.rar','/templates/beez//home.tar','/templates/beez//home.tar.gz',
        '/templates/beez//forum.zip','/templates/beez//forum.rar','/templates/beez//forum.tar','/templates/beez//forum.tar.gz','/templates/beez//test.txt','/templates/beez//ftp.txt','/templates/beez//user.txt',
        '/templates/beez//site.txt','/templates/beez//error_log','/templates/beez//error','/templates/beez//cpanel','/templates/beez//awstats','/templates/beez//site.sql','/templates/beez//vb.sql','/templates/beez//forum.sql','/templates/beez/r00t-s3c.php','/templates/beez/c.php','/templates/beez//backup.sql','/templates/beez//back.sql','/templates/beez//data.sql',
        '/templates/beez/wp.rar/','/templates/beez/asp.aspx','/templates/beez/tmp/vaga.php','/templates/beez/tmp/killer.php','/templates/beez/whmcs.php','/templates/beez/abuhlail.php','/templates/beez/tmp/killer.php','/templates/beez/tmp/domaine.pl',
        '/templates/beez/tmp/domaine.php','/templates/beez/useradmin/','/templates/beez/tmp/d0maine.php','/templates/beez/d0maine.php','/templates/beez/tmp/sql.php','/templates/beez/X.php','/templates/beez/123.php','/templates/beez/m.php',
        '/templates/beez/b.php','/templates/beez/up.php','/templates/beez/tmp/dz1.php','/templates/beez/dz1.php','/templates/beez/forum.zip','/templates/beez/Symlink.php','/templates/beez/Symlink.pl','/templates/beez/forum.rar','/templates/beez/joomla.zip','/templates/beez/joomla.rar','/templates/beez/wp.php','/templates/beez/buck.sql',
        '/templates/beez/sysadmin.php','/templates/beez/images/c99.php','/templates/beez/xd.php','/templates/beez/c100.php','/templates/beez/spy.aspx','/templates/beez/xd.php','/templates/beez/tmp/xd.php','/templates/beez/sym/root/home/','/templates/beez/billing/killer.php','/templates/beez/tmp/upload.php','/templates/beez/tmp/admin.php',
        '/templates/beez/Server.php','/templates/beez/tmp/uploads.php','/templates/beez/tmp/up.php','/templates/beez/Server/','/templates/beez/wp-admin/c99.php','/templates/beez/tmp/priv8.php','/templates/beez/priv8.php',
        '/templates/beez/cgi.pl/','/templates/beez/tmp/cgi.pl','/templates/beez/downloads/dom.php','/templates/beez/webadmin.html','/templates/beez/admins.php','/templates/beez/bluff.php',
        '/templates/beez/king.jeen','/templates/beez/admins/','/templates/beez/admins.asp','/templates/beez/admins.php','/templates/beez/wp.zip','/templates/beez/index.php','/images/WSO.php','/images/dz.php',
        '/images/DZ.php','/images/cpanel.php','/images/cpn.php','/images/sos.php','/images/term.php','/images/Sec-War.php','/images/sql.php','/images/ssl.php','/images/mysql.php','/images/WolF.php','/images/madspot.php','/images/Cgishell.pl','/images/killer.php',
        '/images/changeall.php','/images/2.php','/images/Sh3ll.php','/images/dz0.php','/images/dam.php','/images/user.php','/images/dom.php','/images/whmcs.php','/images/vb.zip','/images/r00t.php','/images/c99.php','/images/gaza.php',
        '/images/1.php','/images/d0mains.php','/images/madspotshell.php','/images/info.php','/images/egyshell.php','/images/Sym.php','/images/c22.php','/images/c100.php','/images/configuration.php','/images/g.php','/images/xx.pl','/images/ls.php','/images/Cpanel.php','/images/k.php','/images/zone-h.php',
        '/images/tmp/user.php','/images/tmp/Sym.php','/images/cp.php','/images/tmp/madspotshell.php','/images/tmp/root.php','/images/tmp/whmcs.php','/images/tmp/index.php','/images/tmp/2.php','/images/tmp/dz.php','/images/tmp/cpn.php','/images/tmp/changeall.php','/images/tmp/Cgishell.pl',
        '/images/tmp/sql.php','/images/0day.php','/images/tmp/admin.php','/images/L3b.php','/images/d.php','/images/tmp/d.php','/images/tmp/L3b.php','/images/sado.php','/images/admin1.php',
        '/images/upload.php','/images/up.php','/images/vb.zip','/images/vb.rar','/images/admin2.asp','/images/uploads.php','/images/sa.php','/images/sysadmins/','/images/admin1/',
        '/images/sniper.php','/images/images/Sym.php','/images//r57.php','/images/gzaa_spysl','/images/sql-new.php','/images//shell.php','/images//sa.php','/images//admin.php','/images//sa2.php','/images//2.php','/images//gaza.php','/images//up.php',
        '/images//upload.php','/images//uploads.php','/images/shell.php','/images//amad.php','/images//t00.php','/images//dz.php','/images//site.rar','/images//Black.php','/images//site.tar.gz','/images//home.zip','/images//home.rar','/images//home.tar',
        '/images//home.tar.gz','/images//forum.zip','/images//forum.rar','/images//forum.tar','/images//forum.tar.gz','/images//test.txt','/images//ftp.txt','/images//user.txt','/images//site.txt',
        '/images//error_log','/images//error','/images//cpanel','/images//awstats','/images//site.sql','/images//vb.sql','/images//forum.sql','/images/r00t-s3c.php','/images/c.php','/images//backup.sql','/images//back.sql','/images//data.sql','/images/wp.rar/','/images/asp.aspx',
        '/images/tmp/vaga.php','/images/tmp/killer.php','/images/whmcs.php','/images/abuhlail.php','/images/tmp/killer.php','/images/tmp/domaine.pl','/images/tmp/domaine.php','/images/useradmin/','/images/tmp/d0maine.php',
        '/images/d0maine.php','/images/tmp/sql.php','/images/X.php','/images/123.php','/images/m.php','/images/b.php','/images/up.php','/images/tmp/dz1.php','/images/dz1.php','/images/forum.zip','/images/Symlink.php','/images/Symlink.pl','/images/forum.rar','/images/joomla.zip','/images/joomla.rar',
        '/images/wp.php','/images/buck.sql','/includes/WSO.php','/includes/dz.php','/includes/DZ.php','/includes/cpanel.php','/includes/cpn.php','/includes/sos.php','/includes/term.php','/includes/Sec-War.php',
        '/includes/sql.php','/includes/ssl.php','/includes/mysql.php','/includes/WolF.php','/includes/madspot.php','/includes/Cgishell.pl','/includes/killer.php','/includes/changeall.php','/includes/2.php','/includes/Sh3ll.php','/includes/dz0.php',
        '/includes/dam.php','/includes/user.php','/includes/dom.php','/includes/whmcs.php','/includes/vb.zip','/includes/r00t.php','/includes/c99.php','/includes/gaza.php','/includes/1.php','/includes/d0mains.php','/includes/madspotshell.php','/includes/info.php','/includes/egyshell.php','/includes/Sym.php','/includes/c22.php','/includes/c100.php','/includes/configuration.php',
        '/includes/g.php','/includes/xx.pl','/includes/ls.php','/includes/Cpanel.php','/includes/k.php','/includes/zone-h.php','/includes/tmp/user.php','/includes/tmp/Sym.php','/includes/cp.php',
        '/includes/tmp/madspotshell.php','/includes/tmp/root.php','/includes/tmp/whmcs.php','/includes/tmp/index.php','/includes/tmp/2.php','/includes/tmp/dz.php','/includes/tmp/cpn.php','/includes/tmp/changeall.php','/includes/tmp/Cgishell.pl','/includes/tmp/sql.php','/includes/0day.php','/includes/tmp/admin.php','/includes/L3b.php','/includes/d.php','/includes/tmp/d.php',
        '/includes/tmp/L3b.php','/includes/sado.php','/includes/admin1.php','/includes/upload.php','/includes/up.php','/includes/vb.zip','/includes/vb.rar','/includes/admin2.asp','/includes/uploads.php','/includes/sa.php','/includes/sysadmins/',
        '/includes/admin1/','/includes/sniper.php','/includes/images/Sym.php','/includes//r57.php','/includes/gzaa_spysl','/includes/sql-new.php','/includes//shell.php','/includes//sa.php','/includes//admin.php','/includes//sa2.php','/includes//2.php',
        '/includes//gaza.php','/includes//up.php','/includes//upload.php','/includes//uploads.php','/includes/shell.php','/includes//amad.php','/includes//t00.php','/includes//dz.php','/includes//site.rar',
        '/includes//Black.php','/includes//site.tar.gz','/includes//home.zip','/includes//home.rar','/includes//home.tar','/includes//home.tar.gz','/includes//forum.zip','/includes//forum.rar',
        '/includes//forum.tar','/includes//forum.tar.gz','/includes//test.txt','/includes//ftp.txt','/includes//user.txt','/includes//site.txt','/includes//error_log','/includes//error',
        '/includes//cpanel','/includes//awstats','/includes//site.sql','/includes//vb.sql','/includes//forum.sql','/includes/r00t-s3c.php','/includes/c.php','/includes//backup.sql','/includes//back.sql','/includes//data.sql','/includes/wp.rar/','/includes/asp.aspx','/includes/tmp/vaga.php','/includes/tmp/killer.php',
        '/includes/whmcs.php','/includes/abuhlail.php','/includes/tmp/killer.php','/includes/tmp/domaine.pl','/includes/tmp/domaine.php','/includes/useradmin/','/includes/tmp/d0maine.php',
        '/includes/d0maine.php','/includes/tmp/sql.php','/includes/X.php','/includes/123.php','/includes/m.php','/includes/b.php','/includes/up.php','/includes/tmp/dz1.php','/includes/dz1.php',
        '/includes/forum.zip','/includes/Symlink.php','/includes/Symlink.pl','/includes/forum.rar','/includes/joomla.zip','/includes/joomla.rar','/includes/wp.php','/includes/buck.sql','/includes/sysadmin.php','/includes/images/c99.php','/includes/xd.php','/includes/c100.php','/includes/spy.aspx','/includes/xd.php','/includes/tmp/xd.php',
        '/includes/sym/root/home/','/includes/billing/killer.php','/includes/tmp/upload.php','/includes/tmp/admin.php','/includes/Server.php','/includes/tmp/uploads.php','/includes/tmp/up.php','/includes/Server/','/includes/wp-admin/c99.php','/includes/tmp/priv8.php','/includes/priv8.php','/includes/cgi.pl/','/includes/tmp/cgi.pl',
        '/includes/downloads/dom.php','/includes/webadmin.html','/includes/admins.php','/includes/bluff.php','/includes/king.jeen','/includes/admins/','/includes/admins.asp','/includes/admins.php','/includes/wp.zip',
        '/includes/','/templates/rhuk_milkyway/WSO.php','/templates/rhuk_milkyway/dz.php','/templates/rhuk_milkyway/DZ.php','/templates/rhuk_milkyway/cpanel.php','/templates/rhuk_milkyway/cpn.php','/templates/rhuk_milkyway/sos.php','/templates/rhuk_milkyway/term.php','/templates/rhuk_milkyway/Sec-War.php',
        '/templates/rhuk_milkyway/sql.php','/templates/rhuk_milkyway/ssl.php','/templates/rhuk_milkyway/mysql.php','/templates/rhuk_milkyway/WolF.php','/templates/rhuk_milkyway/madspot.php',
        '/templates/rhuk_milkyway/Cgishell.pl','/templates/rhuk_milkyway/killer.php','/templates/rhuk_milkyway/changeall.php','/templates/rhuk_milkyway/2.php','/templates/rhuk_milkyway/Sh3ll.php','/templates/rhuk_milkyway/dz0.php','/templates/rhuk_milkyway/dam.php','/templates/rhuk_milkyway/user.php',
        '/templates/rhuk_milkyway/dom.php','/templates/rhuk_milkyway/whmcs.php','/templates/rhuk_milkyway/vb.zip','/templates/rhuk_milkyway/r00t.php','/templates/rhuk_milkyway/c99.php','/templates/rhuk_milkyway/gaza.php',
        '/templates/rhuk_milkyway/1.php','/templates/rhuk_milkyway/d0mains.php','/templates/rhuk_milkyway/madspotshell.php','/templates/rhuk_milkyway/info.php','/templates/rhuk_milkyway/egyshell.php','/templates/rhuk_milkyway/Sym.php','/templates/rhuk_milkyway/c22.php','/templates/rhuk_milkyway/c100.php','/templates/rhuk_milkyway/configuration.php','/templates/rhuk_milkyway/g.php',
        '/templates/rhuk_milkyway/xx.pl','/templates/rhuk_milkyway/ls.php','/templates/rhuk_milkyway/Cpanel.php','/templates/rhuk_milkyway/k.php','/templates/rhuk_milkyway/zone-h.php','/templates/rhuk_milkyway/tmp/user.php','/templates/rhuk_milkyway/tmp/Sym.php','/templates/rhuk_milkyway/cp.php','/templates/rhuk_milkyway/tmp/madspotshell.php','/templates/rhuk_milkyway/tmp/root.php',
        '/templates/rhuk_milkyway/tmp/whmcs.php','/templates/rhuk_milkyway/tmp/index.php','/templates/rhuk_milkyway/tmp/2.php','/templates/rhuk_milkyway/tmp/dz.php','/templates/rhuk_milkyway/tmp/cpn.php','/templates/rhuk_milkyway/tmp/changeall.php','/templates/rhuk_milkyway/tmp/Cgishell.pl','/templates/rhuk_milkyway/tmp/sql.php','/templates/rhuk_milkyway/0day.php','/templates/rhuk_milkyway/tmp/admin.php','/templates/rhuk_milkyway/L3b.php',
        '/templates/rhuk_milkyway/d.php','/templates/rhuk_milkyway/tmp/d.php','/templates/rhuk_milkyway/tmp/L3b.php','/templates/rhuk_milkyway/sado.php','/templates/rhuk_milkyway/admin1.php',
        '/templates/rhuk_milkyway/upload.php','/templates/rhuk_milkyway/up.php','/templates/rhuk_milkyway/vb.zip','/templates/rhuk_milkyway/vb.rar','/templates/rhuk_milkyway/admin2.asp','/templates/rhuk_milkyway/uploads.php','/templates/rhuk_milkyway/sa.php',
        '/templates/rhuk_milkyway/sysadmins/','/templates/rhuk_milkyway/admin1/','/templates/rhuk_milkyway/sniper.php','/templates/rhuk_milkyway/images/Sym.php','/templates/rhuk_milkyway//r57.php','/templates/rhuk_milkyway/gzaa_spysl','/templates/rhuk_milkyway/sql-new.php','/templates/rhuk_milkyway//shell.php','/templates/rhuk_milkyway//sa.php','/templates/rhuk_milkyway//admin.php',
        '/templates/rhuk_milkyway//sa2.php','/templates/rhuk_milkyway//2.php','/templates/rhuk_milkyway//gaza.php','/templates/rhuk_milkyway//up.php','/templates/rhuk_milkyway//upload.php','/templates/rhuk_milkyway//uploads.php','/templates/rhuk_milkyway/shell.php','/templates/rhuk_milkyway//amad.php','/templates/rhuk_milkyway//t00.php','/templates/rhuk_milkyway//dz.php',
        '/templates/rhuk_milkyway//site.rar','/templates/rhuk_milkyway//Black.php','/templates/rhuk_milkyway//site.tar.gz','/templates/rhuk_milkyway//home.zip','/templates/rhuk_milkyway//home.rar','/templates/rhuk_milkyway//home.tar','/templates/rhuk_milkyway//home.tar.gz','/templates/rhuk_milkyway//forum.zip','/templates/rhuk_milkyway//forum.rar','/templates/rhuk_milkyway//forum.tar','/templates/rhuk_milkyway//forum.tar.gz','/templates/rhuk_milkyway//test.txt',
        '/templates/rhuk_milkyway//ftp.txt','/templates/rhuk_milkyway//user.txt','/templates/rhuk_milkyway//site.txt','/templates/rhuk_milkyway//error_log','/templates/rhuk_milkyway//error','/templates/rhuk_milkyway//cpanel','/templates/rhuk_milkyway//awstats','/templates/rhuk_milkyway//site.sql',
        '/templates/rhuk_milkyway//vb.sql','/templates/rhuk_milkyway//forum.sql','/templates/rhuk_milkyway/r00t-s3c.php','/templates/rhuk_milkyway/c.php','/templates/rhuk_milkyway//backup.sql','/templates/rhuk_milkyway//back.sql',
        '/templates/rhuk_milkyway//data.sql','/templates/rhuk_milkyway/wp.rar/','/templates/rhuk_milkyway/asp.aspx','/templates/rhuk_milkyway/tmp/vaga.php','/templates/rhuk_milkyway/tmp/killer.php',
        '/templates/rhuk_milkyway/whmcs.php','/templates/rhuk_milkyway/abuhlail.php','/templates/rhuk_milkyway/tmp/killer.php','/templates/rhuk_milkyway/tmp/domaine.pl','/templates/rhuk_milkyway/tmp/domaine.php',
        '/templates/rhuk_milkyway/useradmin/','/templates/rhuk_milkyway/tmp/d0maine.php','/templates/rhuk_milkyway/d0maine.php','/templates/rhuk_milkyway/tmp/sql.php','/templates/rhuk_milkyway/X.php',
        '/templates/rhuk_milkyway/123.php','/templates/rhuk_milkyway/m.php','/templates/rhuk_milkyway/b.php','/templates/rhuk_milkyway/up.php','/templates/rhuk_milkyway/tmp/dz1.php',
        '/templates/rhuk_milkyway/dz1.php','/templates/rhuk_milkyway/forum.zip','/templates/rhuk_milkyway/Symlink.php','/templates/rhuk_milkyway/Symlink.pl','/templates/rhuk_milkyway/forum.rar',
        '/templates/rhuk_milkyway/joomla.zip','/templates/rhuk_milkyway/joomla.rar','/templates/rhuk_milkyway/wp.php','/templates/rhuk_milkyway/buck.sql','/templates/rhuk_milkyway/sysadmin.php',
        '/templates/rhuk_milkyway/images/c99.php','/templates/rhuk_milkyway/xd.php','/templates/rhuk_milkyway/c100.php','/templates/rhuk_milkyway/spy.aspx','/templates/rhuk_milkyway/xd.php',
        '/templates/rhuk_milkyway/tmp/xd.php','/templates/rhuk_milkyway/sym/root/home/','/templates/rhuk_milkyway/billing/killer.php','/templates/rhuk_milkyway/tmp/upload.php','/templates/rhuk_milkyway/tmp/admin.php',
        '/templates/rhuk_milkyway/Server.php','/templates/rhuk_milkyway/tmp/uploads.php','/templates/rhuk_milkyway/tmp/up.php','/templates/rhuk_milkyway/Server/','/templates/rhuk_milkyway/wp-admin/c99.php',
        '/templates/rhuk_milkyway/tmp/priv8.php','/templates/rhuk_milkyway/priv8.php','/templates/rhuk_milkyway/cgi.pl/','/templates/rhuk_milkyway/tmp/cgi.pl','/templates/rhuk_milkyway/downloads/dom.php','/templates/rhuk_milkyway/webadmin.html','/templates/rhuk_milkyway/admins.php','/templates/rhuk_milkyway/bluff.php',
        '/templates/rhuk_milkyway/king.jeen','/templates/rhuk_milkyway/admins/','/templates/rhuk_milkyway/admins.asp','/templates/rhuk_milkyway/admins.php','/templates/rhuk_milkyway/wp.zip',
        '/templates/rhuk_milkyway/','/WSO.php','/a.php','/z.php','/e.php','/r.php','/t.php','/y.php','/u.php','/i.php','/o.php','/p.php','/q.php','/s.php','/d.php','/f.php','/g.php','/h.php','/j.php',
        '/k.php','/l.php','/m.php','/w.php','/x.php','/c.php','/v.php','/b.php','/n.php','/1.php','/2.php','/3.php','/4.php','/5.php','/6.php','/7.php','/8.php','/9.php','/10.php','/12.php','/11.php','/1234.php'
    ]
    find_shells()
