# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.
import logging
import os
import platform
import subprocess

import requests

logger = logging.getLogger(__name__)

clash_project_url = 'https://api.github.com/repos/{}/releases/latest'.format('Dreamacro/clash')
country_url = 'https://github.com/Dreamacro/maxmind-geoip/releases/latest/download/Country.mmdb'
clash_dashboard_url = 'https://api.github.com/repos/{}/releases/latest'.format('haishanh/yacd')


def init_logging(log_level=logging.INFO):
    log_format = '[%(levelname)s] %(asctime)s  %(filename)s line %(lineno)d: %(message)s'
    date_fmt = '%a, %d %b %Y %H:%M:%S'
    logging.basicConfig(
        format=log_format,
        datefmt=date_fmt,
        level=log_level,
    )


def download_file(url):
    local_filename = url.split('/')[-1]
    # NOTE the stream=True parameter below
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                # If you have chunk encoded response uncomment if
                # and set chunk_size parameter to None.
                # if chunk:
                f.write(chunk)
    return local_filename


def get_latest_clash_package(os_type, cpu_type):
    amd64_download_url = ''
    armv7_download_url = ''
    armv8_download_url = ''
    res = requests.get(clash_project_url)
    latest_tag_name = res.json()['tag_name']
    assets_info = res.json().get('assets')
    for asset_info in assets_info:
        if str(asset_info.get('name')).__contains__('linux-amd64'):
            amd64_download_url = asset_info.get('browser_download_url')
        if str(asset_info.get('name')).__contains__('linux-armv7'):
            armv7_download_url = asset_info.get('browser_download_url')
        if str(asset_info.get('name')).__contains__('linux-armv8'):
            armv8_download_url = asset_info.get('browser_download_url')
    logger.info(armv7_download_url)
    logger.info(armv8_download_url)
    logger.info(amd64_download_url)
    logger.info("clash latest name={}".format(latest_tag_name))
    if os_type.lower() == 'linux' and cpu_type.lower() == 'aarch64':
        return armv8_download_url
    if os_type.lower() == 'linux' and cpu_type.lower().__contains__('x86'):
        return amd64_download_url


def get_latest_clash_ui():
    ui_download_url = ''
    res = requests.get(clash_dashboard_url)
    latest_tag_name = res.json()['tag_name']
    assets_info = res.json().get('assets')
    for asset_info in assets_info:
        if str(asset_info.get('name')).__contains__('yacd.tar.xz'):
            ui_download_url = asset_info.get('browser_download_url')
    logger.info(ui_download_url)
    logger.info("clash yacd ui latest name={}".format(latest_tag_name))
    return ui_download_url


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    init_logging()

    os_type = platform.system()
    cpu_type = platform.machine()
    logger.info("os type={}; cpu type={}".format(os_type, cpu_type))

    clash_ui_url = get_latest_clash_ui()
    clash_ui_tar_xz_file = download_file(clash_ui_url)
    decompress_folder = './ui'
    if not os.path.exists(decompress_folder):
        subprocess.call("mkdir ui", shell=True)

    logger.info("exec cmd: tar -xvf {} -C {}".format(clash_ui_tar_xz_file, decompress_folder))

    exec_res = subprocess.call("tar -xvf {} -C {}".format(clash_ui_tar_xz_file, decompress_folder), shell=True)

    if exec_res == 0:
        logger.info("tar -xvf clash io package")
        # 判断文件位置
        ui_html_path = decompress_folder + '/public/'
        subprocess.call("mkdir -p {}".format('/ui'), shell=True)
        subprocess.call("cp -r {} {}".format(ui_html_path + '*', '/ui/'), shell=True)

    clash_download_url = get_latest_clash_package(os_type, cpu_type)
    logger.info("clash_download_url={}".format(clash_download_url))
    clash_gzip_file = download_file(clash_download_url)
    exec_res = subprocess.call("gzip -d {}".format(clash_gzip_file), shell=True)
    if exec_res != 0:
        logger.error("failed gzip clash package, return")
        raise RuntimeError("failed gzip clash package")
    file_list = os.listdir('./')
    clash_file_name = ''
    for file_name in file_list:
        if file_name.__contains__('clash'):
            clash_file_name = file_name
            break
    logger.info("clash file name={}".format(clash_file_name))
    subprocess.call("chmod +x {}".format(clash_file_name), shell=True)
    subprocess.call("cp {} /clash".format(clash_file_name), shell=True)

    logger.info('create local clash config path')
    subprocess.call("mkdir -p /root/.config/clash/", shell=True)

    logger.info('download country mmdb file')
    subprocess.call(
        'wget -O /Country.mmdb https://github.com/Dreamacro/maxmind-geoip/releases/latest/download/Country.mmdb',
        shell=True)
    country_mmdb_file = '/Country.mmdb'
    # country_mmdb_file = download_file(country_url)
    # logger.info("exec shell script = mv {} /root/.config/clash/".format(country_mmdb_file))
    subprocess.call("mv {} /root/.config/clash/".format(country_mmdb_file), shell=True)

    # subprocess.call("mv config.yaml /root/.config/clash/", shell=True)

    # logger.info("generate local clash config file")
    # local_config_path = '/root/.config/clash/config.yaml'
    # default_clash_config = {
    #     'mixed-port': 7890
    # }
    # with open(local_config_path, 'w', encoding='utf-8') as f:
    #     yaml.dump(default_clash_config, f)

    logger.info('end')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
