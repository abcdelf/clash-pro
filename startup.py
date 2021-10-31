import logging
import os
import platform
import subprocess
import time

import requests
import urllib3
import yaml

logger = logging.getLogger(__name__)

urllib3.disable_warnings()


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


def get_latest_provider_config(provider_url):
    provider_url = provider_url.strip(' ').strip('"')
    if not provider_url.lower().startswith('http'):
        logger.error('provider url invalid, url={}'.format(provider_url))
        return None
    res = requests.get(provider_url, verify=False)
    logger.info('provider request status code={}'.format(res.status_code))
    if res.status_code > 299:
        logger.error("status code={}; reason={}".format(res.status_code, res.reason))
    config_yaml = yaml.safe_load(res.content)
    return config_yaml


def update_clash_config(provider_config_tmp=None):
    api_secret = os.getenv('api_secret', None)
    # "abc:abc efg:efg"
    proxy_authentication_env = os.environ.get("proxy_authentications", None)

    local_config = None
    if provider_config_tmp is not None:
        local_temp_config_path = './.config/clash/config_template.yaml'
        if os.path.exists(local_temp_config_path):
            logger.info('load local clash config template...')
            with open(local_temp_config_path, 'r', encoding='utf-8') as f:
                local_config = yaml.safe_load(f)
                local_config['proxies'] = provider_config_tmp['proxies']
                for proxy_group_detail in local_config['proxy-groups']:
                    if proxy_group_detail['name'] == '🔰国外流量':
                        proxy_group_detail['proxies'] = []
                        for proxy_detail in local_config['proxies']:
                            proxy_group_detail['proxies'].append(proxy_detail['name'])

                        proxy_group_detail['proxies'].append('🚀直接连接')

    local_config_path = './.config/clash/config.yaml'
    if local_config is None:
        logger.info('no valid provider config, load local clash config...')
        with open(local_config_path, 'r', encoding='utf-8') as f:
            local_config = yaml.safe_load(f)

    if proxy_authentication_env is not None:
        proxy_authentication_list_tmp = proxy_authentication_env.strip(' ').strip('"').split(" ")
        proxy_authentication_list = []
        for proxy_authentication_tmp in proxy_authentication_list_tmp:
            if len(proxy_authentication_tmp.split(':')) == 2:
                proxy_authentication_list.append(proxy_authentication_tmp)
            else:
                logger.warning('proxy authentication invalid, input str={}'.format(proxy_authentication_tmp))
        if len(proxy_authentication_list) > 0:
            logger.info('update proxy authentication...')
            local_config['authentication'] = proxy_authentication_list
    if api_secret is not None:
        logger.info('update api secret...')
        local_config['secret'] = api_secret

    subprocess.call('cp {} {}'.format(local_config_path, local_config_path + '.bak'), shell=True)
    with open(local_config_path, 'w', encoding='utf-8') as f:
        logger.info('dump clash config to local config file={}'.format(local_config_path))
        yaml.safe_dump(local_config, f, indent=4, encoding='utf-8', allow_unicode=True, sort_keys=False)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    init_logging()

    provider_subscribe_url = os.getenv('provider_url', '')

    check_interval_time = float(os.getenv('check_interval', 1)) * 60

    os_type = platform.system()
    cpu_type = platform.machine()
    logger.info("os type={}; cpu type={}".format(os_type, cpu_type))

    provider_check_time = time.time()
    logger.info('start to get latest provider config...')
    provider_config = get_latest_provider_config(provider_subscribe_url)

    logger.info('start update clash config file ...')
    update_clash_config(provider_config)

    logger.info('start up clash app...')
    clash_app = subprocess.Popen('/clash')

    time.sleep(check_interval_time)

    while True:

        if time.time() - provider_check_time > 36000:
            # get provider config 10 hour onetime
            provider_config_old = provider_config

            logger.info('start to get latest provider config...')
            provider_check_time = time.time()
            provider_config = get_latest_provider_config(provider_subscribe_url)
            if provider_config_old != provider_config:
                logger.info('provider config has updated...')
                logger.info('start update clash config file ...')
                update_clash_config(provider_config)
                logger.info('kill current clash app...')
                clash_app.kill()
                time.sleep(3)
                logger.info('start up clash app...')
                clash_app = subprocess.Popen('/clash')
            else:
                logger.info('provider config not change...')

        time.sleep(check_interval_time)

        if clash_app.poll() is not None:
            logger.info('clash app status={}; restart clash app...'.format(clash_app.poll()))
            clash_app = subprocess.Popen('/clash')
        else:
            logger.info("clash app run normal; status={}".format(clash_app.poll()))

        logger.info('......clash service check finish......')
