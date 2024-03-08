#!/usr/bin/env python3

import re, yaml, json, base64
import requests, socket, urllib.parse
from requests.adapters import HTTPAdapter

import geoip2.database
idid = '00'
class sub_convert():

    """
    将订阅链接或者订阅内容输入 convert 函数中, 第一步将内容转化为 Clash 节点配置字典, 第二步对节点进行去重和重命名等修饰处理, 第三步输出指定格式. 
    第一步堆栈: 
        YAML To Dict:
            raw_yaml
            convert --> transfer --> format
            dict
        URL To Dict:
            raw_url
            convert --> transfer --> format --> yaml_encode --> format
            dict
        Base64 To Dict:
            raw_base64
            convert --> transfer --> base64_decode --> format --> yaml_encode --> format
            dict
    第二步堆栈:
        dict
        format --> convert --> makeup --> format
        yaml_final
    第三步堆栈:
        YAML To YAML:
            yaml_final
            format --> makeup --> convert
            yaml_final
        YAML To URL:
            yaml_final
            format --> makeup --> yaml_decode --> convert
            url_final
        YAML To Base64:
            yaml_final
            format --> makeup --> yaml_decode --> base64_encode --> convert
            base64_final
    """

    def convert(raw_input, input_type='url', output_type='url', custom_set={'dup_rm_enabled': True, 'format_name_enabled': True}): # {'input_type': ['url', 'content'],'output_type': ['url', 'YAML', 'Base64']}
        # convert Url to YAML or Base64
        global idid
        if input_type == 'url': # 获取 URL 订阅链接内容
            sub_content = ''
            if isinstance(raw_input, list):
                a_content = []
                for url in raw_input:
                    s = requests.Session()
                    s.mount('http://', HTTPAdapter(max_retries=5))
                    s.mount('https://', HTTPAdapter(max_retries=5))
                    try:
                        print('Downloading from:' + url)
                        
                        idid = re.findall(r'#\d\d', url)[0]
                        idid = re.findall(r'\d\d',idid)[0]
                        
                        resp = s.get(url, timeout=5)
                        s_content = sub_convert.yaml_decode(sub_convert.transfer(resp.content.decode('utf-8')))
                        a_content.append(s_content)
                    except Exception as err:
                        print(err)
                        return 'Url 解析错误'
                sub_content = sub_convert.transfer(''.join(a_content))
            else:
                s = requests.Session()
                s.mount('http://', HTTPAdapter(max_retries=5))
                s.mount('https://', HTTPAdapter(max_retries=5))
                try:
                    print('Downloading from:' + raw_input)
                    idid = re.findall(r'#\d\d', raw_input)[0]
                    idid = re.findall(r'\d\d',idid)[0]
                    print (idid)
                    resp = s.get(raw_input, timeout=5)
                    sub_content = sub_convert.transfer(resp.content.decode('utf-8'))
                    if idid == '99' :
                        idid = ''
                except Exception as err:
                    print(err)
                    return 'Url 解析错误'
        elif input_type == 'content': # 解析订阅内容
            sub_content = sub_convert.transfer(raw_input)

        if sub_content != '订阅内容解析错误': # 输出
            dup_rm_enabled = custom_set['dup_rm_enabled']
            format_name_enabled = custom_set['format_name_enabled']
            final_content = sub_convert.makeup(sub_content,dup_rm_enabled,format_name_enabled)
            if output_type == 'YAML':
                return final_content
            elif output_type == 'Base64':
                return sub_convert.base64_encode(sub_convert.yaml_decode(final_content))
            elif output_type == 'url':
                return sub_convert.yaml_decode(final_content)
            else:
                print('Please define right output type.')
                return '订阅内容解析错误'
        else:
            return '订阅内容解析错误'
        #idid = ''
    def transfer(sub_content): # 将 URL 内容转换为 YAML 格式
        if '</b>' not in sub_content:
            if 'proxies:' in sub_content: # 判断字符串是否在文本中，是，判断为YAML。https://cloud.tencent.com/developer/article/1699719
                url_content = sub_convert.format(sub_content)
                return url_content
                #return self.url_content.replace('\r','') # 去除‘回车\r符’ https://blog.csdn.net/jerrygaoling/article/details/81051447
            elif '://'  in sub_content: # 同上，是，判断为 Url 链接内容。
                url_content = sub_convert.yaml_encode(sub_convert.format(sub_content))
                return url_content
            else: # 判断 Base64.
                try:
                    url_content = sub_convert.base64_decode(sub_content)
                    url_content = sub_convert.yaml_encode(sub_convert.format(url_content))
                    return url_content
                except Exception: # 万能异常 https://blog.csdn.net/Candance_star/article/details/94135515
                    print('订阅内容解析错误')
                    return '订阅内容解析错误'
        else:
            print('订阅内容解析错误')
            return '订阅内容解析错误'
        
    def format(sub_content, output=False): # 对节点 Url 进行格式化处理, 输出节点的字典格式, output 为真时输出 YAML 文本

        if 'proxies:' not in sub_content: # 对 URL 内容进行格式化处理
            url_list = []
            try:
                if '://' not in sub_content:
                    sub_content = sub_convert.base64_encode(sub_content)

                raw_url_list = re.split(r'\n+', sub_content)

                for url in raw_url_list:
                    while len(re.split('ss://|ssr://|vmess://|trojan://|vless://', url)) > 2:
                        url_to_split = url[8:]
                        if 'ss://' in url_to_split and 'vmess://' not in url_to_split and 'vless://' not in url_to_split:
                            url_splited = url_to_split.replace('ss://', '\nss://', 1) # https://www.runoob.com/python/att-string-replace.html
                        elif 'ssr://' in url_to_split:
                            url_splited = url_to_split.replace('ssr://', '\nssr://', 1)
                        elif 'vmess://' in url_to_split:
                            url_splited = url_to_split.replace('vmess://', '\nvmess://', 1)
                        elif 'trojan://' in url_to_split:
                            url_splited = url_to_split.replace('trojan://', '\ntrojan://', 1)
                        elif 'vless://' in url_to_split:
                            url_splited = url_to_split.replace('vless://', '\nvless://', 1)
                        url_split = url_splited.split('\n')

                        front_url = url[:8] + url_split[0]
                        url_list.append(front_url)
                        url = url_split[1]
                        #ids = re.findall(r'#\d\d', raw_input)[0]
                    url_list.append(url)

                url_content = '\n'.join(url_list)
                return url_content
            except:
                print('Sub_content 格式错误1')
                return ''

        elif 'proxies:' in sub_content: # 对 Clash 内容进行格式化处理
            try:
                try_load = yaml.safe_load(sub_content)
                if output == False:
                    sub_content_yaml = try_load
                else:
                    sub_content_yaml = sub_content
            except Exception:
                try:
                    sub_content = sub_content.replace('\'', '').replace('"', '')
                    url_list = []
                    il_chars = ['|', '?', '[', ']', '@', '!', '%']

                    lines = re.split(r'\n+', sub_content)
                    line_fix_list = []

                    for line in lines:
                        value_list = re.split(r': |, ', line)
                        if len(value_list) > 6:
                            value_list_fix = []
                            for value in value_list:
                                for char in il_chars:
                                    value_il = False
                                    if char in value:
                                        value_il = True
                                        break
                                if value_il == True and ('{' not in value and '}' not in value):
                                    value = '"' + value + '"'
                                    value_list_fix.append(value)
                                elif value_il == True and '}' in value:
                                    if '}}' in value:
                                        host_part = value.replace('}}','')
                                        host_value = '"'+host_part+'"}}'
                                        value_list_fix.append(host_value)
                                    elif '}}' not in value:
                                        host_part = value.replace('}','')
                                        host_value = '"'+host_part+'"}'
                                        value_list_fix.append(host_value)
                                else:
                                    value_list_fix.append(value)
                                line_fix = line
                            for index in range(len(value_list_fix)):
                                line_fix = line_fix.replace(value_list[index], value_list_fix[index])
                            line_fix_list.append(line_fix)
                        elif len(value_list) == 2:
                            value_list_fix = []
                            for value in value_list:
                                for char in il_chars:
                                    value_il = False
                                    if char in value:
                                        value_il = True
                                        break
                                if value_il == True:
                                    value = '"' + value + '"'
                                value_list_fix.append(value)
                            line_fix = line
                            for index in range(len(value_list_fix)):
                                line_fix = line_fix.replace(value_list[index], value_list_fix[index])
                            line_fix_list.append(line_fix)
                        elif len(value_list) == 1:
                            if ':' in line:
                                line_fix_list.append(line)
                        else:
                            line_fix_list.append(line)

                    sub_content = '\n'.join(line_fix_list).replace('False', 'false').replace('True', 'true').replace('Host','host').replace('Path','path').replace('HOST','host').replace('PATH','path')

                    if output == False:
                        sub_content_yaml = yaml.safe_load(sub_content)
                    else: # output 值为 True 时返回修饰过的 YAML 文本
                        sub_content_yaml = sub_content
                except:
                    print('Sub_content 格式错误2')
                    return '' # 解析 URL 内容错误时返回空字符串
            if output == False:
                for item in sub_content_yaml['proxies']:# 对转换过程中出现的不标准配置格式转换
                    try:
                        if item['type'] == 'vmess' and 'Host' in item['ws-opts']['headers']:
                            item['ws-opts']['headers']['host'] = item['ws-opts']['headers'].pop("Host")
                        if item['type'] == 'vmess' and 'HOST' in item['ws-opts']['headers']:
                            item['ws-opts']['headers']['host'] = item['ws-opts']['headers'].pop("HOST")   
                        if item['type'] == 'ss' and 'HOST' in item['plugin-opts']:
                            item['plugin-opts']['host'] = item['plugin-opts'].pop("HOST")
                        if item['type'] == 'ss' and 'Host' in item['ws-opts']['headers']:
                            item['plugin-opts']['host'] = item['plugin-opts'].pop("Host")  

                    
                    except KeyError:
                        if '.' not in item['server']:
                            sub_content_yaml['proxies'].remove(item)
                        pass

            return sub_content_yaml # 返回字典, output 值为 True 时返回修饰过的 YAML 文本
    def makeup(input, dup_rm_enabled=True, format_name_enabled=True): # 对节点进行区域的筛选和重命名，输出 YAML 文本 
        global idid
        # 区域判断(Clash YAML): https://blog.csdn.net/CSDN_duomaomao/article/details/89712826 (ip-api)
        if isinstance(input, dict):
            sub_content = input
        else:
            if 'proxies:' in input:
                sub_content = sub_convert.format(input)
            else:
                yaml_content_raw = sub_convert.convert(input, 'content', 'YAML')
                sub_content = yaml.safe_load(yaml_content_raw)
        proxies_list = sub_content['proxies']
        if dup_rm_enabled and (idid=='' or idid=='99'): # 去重
            begin = 0
            raw_length = len(proxies_list)
            length = len(proxies_list)
            while begin < length:
                if (begin + 1) == 1:
                    print(f'\n-----去重开始-----\n起始数量{length}')
                elif (begin + 1) % 100 == 0:
                    print(f'当前基准{begin + 1}-----当前数量{length}')
                elif (begin + 1) == length and (begin + 1) % 100 != 0:
                    repetition = raw_length - length
                    print(f'当前基准{begin + 1}-----当前数量{length}\n重复数量{repetition}\n-----去重完成-----\n')
                proxy_compared = proxies_list[begin]

                begin_2 = begin + 1
                while begin_2 <= (length - 1):
                    if proxy_compared['type'] =='vmess':
                        if proxy_compared['server'] == proxies_list[begin_2]['server'] and proxy_compared['port'] == proxies_list[begin_2]['port'] and proxy_compared['type'] == proxies_list[begin_2]['type'] and proxy_compared['uuid'] == proxies_list[begin_2]['uuid']:
                            proxies_list.pop(begin_2)
                            length -= 1
                    else:
                        if proxy_compared['server'] == proxies_list[begin_2]['server'] and proxy_compared['port'] == proxies_list[begin_2]['port'] and proxy_compared['type'] == proxies_list[begin_2]['type'] and proxy_compared['password'] == proxies_list[begin_2]['password']:
                            proxies_list.pop(begin_2)
                            length -= 1
                            print(proxy_compared)
                    begin_2 += 1
                begin += 1

        url_list = []

        for proxy in proxies_list: # 改名
            
            if format_name_enabled:
                emoji = {
                    'AD': '🇦🇩', 'AE': '🇦🇪', 'AF': '🇦🇫', 'AG': '🇦🇬', 
                    'AI': '🇦🇮', 'AL': '🇦🇱', 'AM': '🇦🇲', 'AO': '🇦🇴', 
                    'AQ': '🇦🇶', 'AR': '🇦🇷', 'AS': '🇦🇸', 'AT': '🇦🇹', 
                    'AU': '🇦🇺', 'AW': '🇦🇼', 'AX': '🇦🇽', 'AZ': '🇦🇿', 
                    'BA': '🇧🇦', 'BB': '🇧🇧', 'BD': '🇧🇩', 'BE': '🇧🇪', 
                    'BF': '🇧🇫', 'BG': '🇧🇬', 'BH': '🇧🇭', 'BI': '🇧🇮', 
                    'BJ': '🇧🇯', 'BL': '🇧🇱', 'BM': '🇧🇲', 'BN': '🇧🇳', 
                    'BO': '🇧🇴', 'BQ': '🇧🇶', 'BR': '🇧🇷', 'BS': '🇧🇸', 
                    'BT': '🇧🇹', 'BV': '🇧🇻', 'BW': '🇧🇼', 'BY': '🇧🇾', 
                    'BZ': '🇧🇿', 'CA': '🇨🇦', 'CC': '🇨🇨', 'CD': '🇨🇩', 
                    'CF': '🇨🇫', 'CG': '🇨🇬', 'CH': '🇨🇭', 'CI': '🇨🇮', 
                    'CK': '🇨🇰', 'CL': '🇨🇱', 'CM': '🇨🇲', 'CN': '🇨🇳', 
                    'CO': '🇨🇴', 'CR': '🇨🇷', 'CU': '🇨🇺', 'CV': '🇨🇻', 
                    'CW': '🇨🇼', 'CX': '🇨🇽', 'CY': '🇨🇾', 'CZ': '🇨🇿', 
                    'DE': '🇩🇪', 'DJ': '🇩🇯', 'DK': '🇩🇰', 'DM': '🇩🇲', 
                    'DO': '🇩🇴', 'DZ': '🇩🇿', 'EC': '🇪🇨', 'EE': '🇪🇪', 
                    'EG': '🇪🇬', 'EH': '🇪🇭', 'ER': '🇪🇷', 'ES': '🇪🇸', 
                    'ET': '🇪🇹', 'EU': '🇪🇺', 'FI': '🇫🇮', 'FJ': '🇫🇯', 
                    'FK': '🇫🇰', 'FM': '🇫🇲', 'FO': '🇫🇴', 'FR': '🇫🇷', 
                    'GA': '🇬🇦', 'GB': '🇬🇧', 'GD': '🇬🇩', 'GE': '🇬🇪', 
                    'GF': '🇬🇫', 'GG': '🇬🇬', 'GH': '🇬🇭', 'GI': '🇬🇮', 
                    'GL': '🇬🇱', 'GM': '🇬🇲', 'GN': '🇬🇳', 'GP': '🇬🇵', 
                    'GQ': '🇬🇶', 'GR': '🇬🇷', 'GS': '🇬🇸', 'GT': '🇬🇹', 
                    'GU': '🇬🇺', 'GW': '🇬🇼', 'GY': '🇬🇾', 'HK': '🇭🇰', 
                    'HM': '🇭🇲', 'HN': '🇭🇳', 'HR': '🇭🇷', 'HT': '🇭🇹', 
                    'HU': '🇭🇺', 'ID': '🇮🇩', 'IE': '🇮🇪', 'IL': '🇮🇱', 
                    'IM': '🇮🇲', 'IN': '🇮🇳', 'IO': '🇮🇴', 'IQ': '🇮🇶', 
                    'IR': '🇮🇷', 'IS': '🇮🇸', 'IT': '🇮🇹', 'JE': '🇯🇪', 
                    'JM': '🇯🇲', 'JO': '🇯🇴', 'JP': '🇯🇵', 'KE': '🇰🇪', 
                    'KG': '🇰🇬', 'KH': '🇰🇭', 'KI': '🇰🇮', 'KM': '🇰🇲', 
                    'KN': '🇰🇳', 'KP': '🇰🇵', 'KR': '🇰🇷', 'KW': '🇰🇼', 
                    'KY': '🇰🇾', 'KZ': '🇰🇿', 'LA': '🇱🇦', 'LB': '🇱🇧', 
                    'LC': '🇱🇨', 'LI': '🇱🇮', 'LK': '🇱🇰', 'LR': '🇱🇷', 
                    'LS': '🇱🇸', 'LT': '🇱🇹', 'LU': '🇱🇺', 'LV': '🇱🇻', 
                    'LY': '🇱🇾', 'MA': '🇲🇦', 'MC': '🇲🇨', 'MD': '🇲🇩', 
                    'ME': '🇲🇪', 'MF': '🇲🇫', 'MG': '🇲🇬', 'MH': '🇲🇭', 
                    'MK': '🇲🇰', 'ML': '🇲🇱', 'MM': '🇲🇲', 'MN': '🇲🇳', 
                    'MO': '🇲🇴', 'MP': '🇲🇵', 'MQ': '🇲🇶', 'MR': '🇲🇷', 
                    'MS': '🇲🇸', 'MT': '🇲🇹', 'MU': '🇲🇺', 'MV': '🇲🇻', 
                    'MW': '🇲🇼', 'MX': '🇲🇽', 'MY': '🇲🇾', 'MZ': '🇲🇿', 
                    'NA': '🇳🇦', 'NC': '🇳🇨', 'NE': '🇳🇪', 'NF': '🇳🇫', 
                    'NG': '🇳🇬', 'NI': '🇳🇮', 'NL': '🇳🇱', 'NO': '🇳🇴', 
                    'NP': '🇳🇵', 'NR': '🇳🇷', 'NU': '🇳🇺', 'NZ': '🇳🇿', 
                    'OM': '🇴🇲', 'PA': '🇵🇦', 'PE': '🇵🇪', 'PF': '🇵🇫', 
                    'PG': '🇵🇬', 'PH': '🇵🇭', 'PK': '🇵🇰', 'PL': '🇵🇱', 
                    'PM': '🇵🇲', 'PN': '🇵🇳', 'PR': '🇵🇷', 'PS': '🇵🇸', 
                    'PT': '🇵🇹', 'PW': '🇵🇼', 'PY': '🇵🇾', 'QA': '🇶🇦', 
                    'RE': '🇷🇪', 'RO': '🇷🇴', 'RS': '🇷🇸', 'RU': '🇷🇺', 
                    'RW': '🇷🇼', 'SA': '🇸🇦', 'SB': '🇸🇧', 'SC': '🇸🇨', 
                    'SD': '🇸🇩', 'SE': '🇸🇪', 'SG': '🇸🇬', 'SH': '🇸🇭', 
                    'SI': '🇸🇮', 'SJ': '🇸🇯', 'SK': '🇸🇰', 'SL': '🇸🇱', 
                    'SM': '🇸🇲', 'SN': '🇸🇳', 'SO': '🇸🇴', 'SR': '🇸🇷', 
                    'SS': '🇸🇸', 'ST': '🇸🇹', 'SV': '🇸🇻', 'SX': '🇸🇽', 
                    'SY': '🇸🇾', 'SZ': '🇸🇿', 'TC': '🇹🇨', 'TD': '🇹🇩', 
                    'TF': '🇹🇫', 'TG': '🇹🇬', 'TH': '🇹🇭', 'TJ': '🇹🇯', 
                    'TK': '🇹🇰', 'TL': '🇹🇱', 'TM': '🇹🇲', 'TN': '🇹🇳', 
                    'TO': '🇹🇴', 'TR': '🇹🇷', 'TT': '🇹🇹', 'TV': '🇹🇻', 
                    'TW': '🇹🇼', 'TZ': '🇹🇿', 'UA': '🇺🇦', 'UG': '🇺🇬', 
                    'UM': '🇺🇲', 'US': '🇺🇸', 'UY': '🇺🇾', 'UZ': '🇺🇿', 
                    'VA': '🇻🇦', 'VC': '🇻🇨', 'VE': '🇻🇪', 'VG': '🇻🇬', 
                    'VI': '🇻🇮', 'VN': '🇻🇳', 'VU': '🇻🇺', 'WF': '🇼🇫', 
                    'WS': '🇼🇸', 'XK': '🇽🇰', 'YE': '🇾🇪', 'YT': '🇾🇹', 
                    'ZA': '🇿🇦', 'ZM': '🇿🇲', 'ZW': '🇿🇼', 
                    'RELAY': '🏁',
                    'NOWHERE': '🇦🇶',
                }

                server = proxy['server']
                if server.replace('.','').isdigit():
                    ip = server
                else:
                    try:
                        ip = socket.gethostbyname(server) # https://cloud.tencent.com/developer/article/1569841
                    except Exception:
                        ip = server

                with geoip2.database.Reader('./utils/Country.mmdb') as ip_reader:
                    try:
                        response = ip_reader.country(ip)
                        country_code = response.country.iso_code
                    except Exception:
                        ip = '0.0.0.0'
                        country_code = 'NOWHERE'

                if country_code == 'CLOUDFLARE':
                    country_code = 'RELAY'
                elif country_code == 'PRIVATE':
                    country_code = 'RELAY'

                if country_code in emoji:
                    name_emoji = emoji[country_code]
                else:
                    name_emoji = emoji['NOWHERE']

                proxy_index = proxies_list.index(proxy)
                proxyname= proxy['name']
                
                #print(idid)
                
 
                
                if idid != '':
                    if re.findall(r'\d\d',idid)[0] == '99' :
                        idid = ''
                        
                    else :
                        idid = re.findall(r'\d\d',idid)[0]
                        proxyname=str(idid)
                
                proxyname=re.findall(r'^..',proxyname)[0]
                        
                if len(proxies_list) >=1000:
                    
                    proxy['name'] =f'{proxyname}-{proxy_index:0>4d}-{country_code}'
                elif len(proxies_list) <= 999:
                    proxy['name'] =f'{proxyname}-{proxy_index:0>3d}-{country_code}'
                
                
                if proxy['server'] != '127.0.0.1':
                    proxy_str = str(proxy)
                    url_list.append(proxy_str)
            elif format_name_enabled == False:
                if proxy['server'] != '127.0.0.1':
                    proxy_str = str(proxy)
                    url_list.append(proxy_str)
             
        yaml_content_dic = {'proxies': url_list}
        yaml_content_raw = yaml.dump(yaml_content_dic, default_flow_style=False, sort_keys=False, allow_unicode=True, width=750, indent=2) # yaml.dump 显示中文方法 https://blog.csdn.net/weixin_41548578/article/details/90651464 yaml.dump 各种参数 https://blog.csdn.net/swinfans/article/details/88770119
        yaml_content = yaml_content_raw.replace('\'', '').replace('False', 'false').replace('True', 'true')

        yaml_content = sub_convert.format(yaml_content,True)
        
        return yaml_content # 输出 YAML 格式文本

    def yaml_encode(url_content): # 将 URL 内容转换为 YAML (输出默认 YAML 格式)
        url_list = []

        lines = re.split(r'\n+', url_content)

        for line in lines:
            yaml_url = {}
            if 'vmess://' in line:
                try:
                    vmess_json_config = json.loads(sub_convert.base64_decode(line.replace('vmess://', '')))
                    vmess_default_config = {
                        'v': 'Vmess Node', 'ps': 'Vmess Node', 'add': '0.0.0.0', 'port': 0, 'id': '',
                        'aid': 0, 'scy': 'auto', 'net': '', 'type': '', 'host': vmess_json_config['add'], 'path': '/', 'tls': ''
                    }
                    vmess_default_config.update(vmess_json_config)
                    vmess_config = vmess_default_config

                    yaml_url = {}
                    #yaml_config_str = ['name', 'server', 'port', 'type', 'uuid', 'alterId', 'cipher', 'tls', 'skip-cert-verify', 'network', 'ws-path', 'ws-headers']
                    #vmess_config_str = ['ps', 'add', 'port', 'id', 'aid', 'scy', 'tls', 'net', 'host', 'path']
                    # 生成 yaml 节点字典
                    if vmess_config['id'] == '' or vmess_config['id'] is None:
                        print('节点格式错误')
                    else:
                        yaml_url.setdefault('name', urllib.parse.unquote(str(vmess_config['ps'])))
                        yaml_url.setdefault('server', vmess_config['add'])
                        yaml_url.setdefault('port', vmess_config['port'])
                        yaml_url.setdefault('type', 'vmess')
                        yaml_url.setdefault('uuid', vmess_config['id'])
                        yaml_url.setdefault('alterId', vmess_config['aid'])
                        yaml_url.setdefault('cipher', vmess_config['scy'])
                        yaml_url.setdefault('skip-cert-vertify', True)
                        if vmess_config['net'] == '' or vmess_config['net'] is False or vmess_config['net'] is None:
                            yaml_url.setdefault('network', 'ws')
                        else:
                            yaml_url.setdefault('network', vmess_config['net'])

                        if vmess_config['tls'] is True or vmess_config['net'] == 'h2' or vmess_config['net'] == 'grpc' or vmess_config['net'] == 'http':
                            yaml_url.setdefault('network', 'ws')
                            yaml_url.setdefault('tls', True)
                        else:
                            yaml_url.setdefault('tls', False)

                        yaml_url.setdefault('ws-opts',{'path':vmess_config['path'], 'headers': {'host': vmess_config['host']}})
                        yaml_url.setdefault('udp', True)
                        #yaml_url=str(yaml_url)
                        #yaml_url=yaml_url.replace('"',''')
                        #yaml_rul=eval(yaml_url)

                        url_list.append(yaml_url)
                        
                except Exception as err:
                    print(f'yaml_encode 解析 vmess 节点发生错误: {err}')
                    print(vmess_config)
                    pass

            if 'ss://' in line and 'vless://' not in line and 'vmess://' not in line and 'lugin' not in line:
                if '#' not in line:
                    line = line + '#SS%20Node'
                try:
                    ss_content =  line.replace('ss://', '')
                    part_list = ss_content.split('#', 1) # https://www.runoob.com/python/att-string-split.html
                    yaml_url.setdefault('name', urllib.parse.unquote(part_list[1]))
                    if '@' in part_list[0]:
                        mix_part = part_list[0].split('@', 1)
                        method_part = sub_convert.base64_decode(mix_part[0])
                        server_part = f'{method_part}@{mix_part[1]}'
                    else:
                        server_part = sub_convert.base64_decode(part_list[0])

                    server_part_list = server_part.split(':', 1) # 使用多个分隔符 https://blog.csdn.net/shidamowang/article/details/80254476 https://zhuanlan.zhihu.com/p/92287240
                    method_part = server_part_list[0].replace('2022-blake3-', '').replace('chacha20-poly1305', 'chacha20-ietf-poly1305')
                    server_part_list = server_part_list[1].rsplit('@', 1)
                    password_part = server_part_list[0]
                    server_part_list = server_part_list[1].split(':', 1)

                    yaml_url.setdefault('server', server_part_list[0])
                    yaml_url.setdefault('port', server_part_list[1])
                    yaml_url.setdefault('type', 'ss')
                    yaml_url.setdefault('cipher', method_part)
                    yaml_url.setdefault('password', password_part)
                    
                    url_list.append(yaml_url)
                except Exception as err:
                    print(f'yaml_encode 解析 ss 节点发生错误1: {err}')
                    pass
            if 'ss://' in line and 'vless://' not in line and 'vmess://' not in line and 'lugin' in line:
                if '#' not in line:
                    line = line + 'SS%20Node'
                try:
                    ss_content =  line.replace('ss://', '')
                    part_list = ss_content.split('#', 1)  #https://www.runoob.com/python/att-string-split.html
                    yaml_url.setdefault('name', urllib.parse.unquote(part_list[1]))
                    if '@' in part_list[0]:
                        mix_part = part_list[0].split('@', 1)
                        method_part = sub_convert.base64_decode(mix_part[0])
                        server_part = f'{method_part}@{mix_part[1]}'
                    else:
                        server_part = sub_convert.base64_decode(part_list[0])
                    server_part_list = server_part.split(':', 1)  #使用多个分隔符 https://blog.csdn.net/shidamowang/article/details/80254476 https://zhuanlan.zhihu.com/p/92287240
                    method_part = server_part_list[0].replace('2022-blake3-', '').replace('chacha20-poly1305', 'chacha20-ietf-poly1305')
                    server_part_list = server_part_list[1].rsplit('@', 1)
                    password_part = server_part_list[0]
                    password_part = password_part.replace('"', '')
                    server_part_list = server_part_list[1].split(':', 1)  # server:port/?plugin=v2ray-plugin%3Bmode%3Dwebs       
                    yaml_url.setdefault('server', server_part_list[0])
                    server_part_list = server_part_list[1].split('/', 1) # port/?plugin=v2ray-plugin%3Bmode%3Dwebs 
                    yaml_url.setdefault('port', server_part_list[0])
                    #print(server_part_list[0])
                    yaml_url.setdefault('type', 'ss')
                    yaml_url.setdefault('cipher', method_part)
                    yaml_url.setdefault('password', password_part)


                    if 'obfs-local' in line :
                        yaml_url.setdefault('Plugin', 'obfs')
                        #print(server_part_list[1])
                        plugin_list=str(urllib.parse.unquote(server_part_list[1])+';')
                        #print(plugin_list)
                        plugin_mode=re.compile('obfs=(.*?);').findall(plugin_list)[0]
                        #print(plugin_mode)
                        plugin_host=re.compile('obfs-host=(.*?);').findall(plugin_list)[0]
                        #print(plugin_host)
                        #print(yaml_url)
                        yaml_url['plugin'] = yaml_url.pop("Plugin")
                        yaml_url.setdefault('plugin-opts',{'mode':plugin_mode, 'host':plugin_host, 'tls': 'true', 'skip-cert-verify': 'true'})

                    if 'v2ray-plugin' in line :
                        yaml_url.setdefault('Plugin', 'v2ray-plugin')
                        #print(server_part_list[1])
                        plugin_list=str(urllib.parse.unquote(server_part_list[1])+';')
                        #print(plugin_list)
                        
                        plugin_mode=re.compile('mode=(.*?);').findall(plugin_list)[0]
                        #print(plugin_mode)
                        plugin_host=re.compile('host=(.*?);').findall(plugin_list)[0]
                        if plugin_host =='':
                            plugin_host=yaml_url['server']
                        #print(plugin_host)
                        plugin_path=re.compile('path=(.*?);').findall(plugin_list)[0]
                        if plugin_path == '':
                            plugin_path='/'
                        #print(plugin_path)
                        
                        #print(yaml_url)
                        yaml_url['plugin'] = yaml_url.pop("Plugin")
                        yaml_url.setdefault('plugin-opts',{'mode':plugin_mode, 'host':plugin_host, 'path':plugin_path, 'tls': 'true', 'mux': 'true', 'skip-cert-verify': 'true'})

                    
                    yaml_url.setdefault('udp', 'true')
                    #yaml_url=str(yaml_url)
                    #yaml_url=yaml_url.replace('"',''')
                    #yaml_rul=eval(yaml_url)
                    url_list.append(yaml_url)
                except Exception as err:
                    print(f'yaml_encode 解析 ss 节点发生错误2: {err}')
                    #print(line)
                    pass





            
            if 'ssr://' in line:
                try:
                    ssr_content = sub_convert.base64_decode(line.replace('ssr://', ''))
                    #print(ssr_content)
                    parts = re.split(':', ssr_content)
                    if len(parts) != 6:
                        print('SSR 格式错误: %s' % ssr_content)
                    password_and_params = parts[5]
                    password_and_params = re.split('/\?', password_and_params)
                    password_encode_str = password_and_params[0]
                    params =str(password_and_params[1].replace('\n','')+'&')

                    if idid=='' or idid=='99':
                        
                        remarks=re.compile('remarks=(.*?)&').findall(params)[0]
                        remarks=sub_convert.base64_decode(remarks)
                    else:
                        remarks=str(parts[0])
                    
                    
                    #print(parts)
                    #print(params)
                    #print(idid)
                
                    yaml_url.setdefault('name', remarks)
                    yaml_url.setdefault('server', parts[0])
                    yaml_url.setdefault('port', parts[1])
                    yaml_url.setdefault('type', 'ssr')
                    yaml_url.setdefault('cipher', parts[3])
                    yaml_url.setdefault('password', sub_convert.base64_decode(password_encode_str))
                    yaml_url.setdefault('obfs', parts[4])
                    yaml_url.setdefault('protocol', parts[2])
                    if 'protoparam' in params:
                        protoparam=re.compile('protoparam=(.*?)&').findall(params)[0]
                        #protoparam=protoparam.replace('==\n','')
                        protoparam=sub_convert.base64_decode(protoparam)
                        yaml_url.setdefault('protocol-param', protoparam)
                        #print(protoparam)
                    if 'obfsparam' in params:
                        obfsparam=re.compile('obfsparam=(.*?)&').findall(params)[0]
                        obfsparam=sub_convert.base64_decode(obfsparam)
                        if idid =='' or idid=='99':
                            if '@' in obfsparam:
                                obfsparam=obfsparam.replace('$',',')

                        else:
                            if ',' in obfsparam:
                                obfsparam=obfsparam.replace(',','$')
                        yaml_url.setdefault('obfs-param', obfsparam)
                        #print(obfsparam)

                    yaml_url.setdefault('group', 'SSRProvider')
                    #print(group)
                         
                    print(yaml_url)
                    url_list.append(yaml_url)
                    #print(url_list)
                except Exception as err:
                    print(f'yaml_encode 解析 ssr 节点发生错误: {err}')
                    print(yaml_url)
                    pass




            
            if 'trojan://' in line:
                try:
                    url_content = line.replace('trojan://', '')
                    part_list = re.split('#', url_content, maxsplit=1) # https://www.runoob.com/python/att-string-split.html
                    yaml_url.setdefault('name', urllib.parse.unquote(part_list[1]))

                    server_part = part_list[0].replace('trojan://', '')
                    server_part_list = re.split(':|@|\?|&', server_part) # 使用多个分隔符 https://blog.csdn.net/shidamowang/article/details/80254476 https://zhuanlan.zhihu.com/p/92287240
                    yaml_url.setdefault('server', server_part_list[1])
                    yaml_url.setdefault('port', server_part_list[2])
                    yaml_url.setdefault('type', 'trojan')
                    yaml_url.setdefault('password', server_part_list[0])
                    server_part_list = server_part_list[3:]

                    for config in server_part_list:
                        if 'sni=' in config:
                            yaml_url.setdefault('sni', config[4:])
                        elif 'allowInsecure=' in config or 'tls=' in config:
                            if config[-1] == 0:
                                yaml_url.setdefault('tls', False)
                        elif 'type=' in config:
                            if config[5:] != 'tcp':
                                yaml_url.setdefault('network', config[5:])
                        elif 'path=' in config:
                            yaml_url.setdefault('ws-path', config[5:])
                        elif 'security=' in config:
                            if config[9:] != 'tls':
                                yaml_url.setdefault('tls', False)

                    yaml_url.setdefault('skip-cert-verify', True)
                    yaml_url.setdefault('udp', True)
                    #yaml_url=str(yaml_url)
                    #yaml_url=yaml_url.replace('"',''')
                    #yaml_rul=eval(yaml_url)
                    url_list.append(yaml_url)
                except Exception as err:
                    print(f'yaml_encode 解析 trojan 节点发生错误: {err}')
                    pass

        yaml_content_dic = {'proxies': url_list}
        yaml_content_raw = yaml.dump(yaml_content_dic, default_flow_style=False, sort_keys=False, allow_unicode=True, width=750, indent=2)
        yaml_content = sub_convert.format(yaml_content_raw)
        return yaml_content
    def base64_encode(url_content): # 将 URL 内容转换为 Base64
        base64_content = base64.b64encode(url_content.encode('utf-8')).decode('ascii')
        return base64_content

    def yaml_decode(url_content): # YAML 文本转换为 URL 链接内容
        
        try:
            
            if isinstance(url_content, dict):
                sub_content = url_content
            else:
                if 'proxies:' in url_content:
                    sub_content = sub_convert.format(url_content)
                else:
                    yaml_content_raw = sub_convert.convert(url_content, 'content', 'YAML')
                    sub_content = yaml.safe_load(yaml_content_raw)
            
            proxies_list = sub_content['proxies']
            
            protocol_url = []
            for index in range(len(proxies_list)): # 不同节点订阅链接内容 https://github.com/hoochanlon/fq-book/blob/master/docs/append/srvurl.md
                proxy = proxies_list[index]
                #proxy = str(proxy)
                #proxy = proxy.replace('"',''')
                #proxy = (proxy)
                
                if proxy['type'] == 'vmess' and 'ws-opts' in proxy and 'headers' in proxy['ws-opts'] and 'host' in proxy['ws-opts']['headers'] and 'path' in proxy['ws-opts']: # Vmess 节点提取, 由 Vmess 所有参数 dump JSON 后 base64 得来。

                    yaml_default_config = {
                        'name': 'Vmess Node', 'server': '0.0.0.0', 'port': 0, 'uuid': '', 'alterId': 0,
                        'cipher': 'auto', 'network': '', 'tls':'False',
                        'sni': ''
                    }

                    yaml_default_config.update(proxy)
                    proxy_config = yaml_default_config
                    if  proxy['network'] != 'grpc' and proxy['network'] != 'h2' :
                        vmess_value = {
                            'v': 2, 'ps': proxy_config['name'], 'add': proxy_config['server'],
                            'port': proxy_config['port'], 'id': proxy_config['uuid'], 'aid': proxy_config['alterId'],
                            'scy': proxy_config['cipher'], 'net': proxy_config['network'], 'type': None, 'host': proxy['ws-opts']['headers']['host'],
                            'path': proxy['ws-opts']['path'], 'tls': proxy_config['tls'], 'sni': proxy_config['sni']
                            }
                    else:
                        vmess_value = {
                            'v': 2, 'ps': proxy_config['name'], 'add': proxy_config['server'],
                            'port': proxy_config['port'], 'id': proxy_config['uuid'], 'aid': proxy_config['alterId'],
                            'scy': proxy_config['cipher'], 'net': 'ws', 'type': None, 'host': proxy['ws-opts']['headers']['host'],
                            'path': proxy['ws-opts']['path'], 'tls': proxy_config['tls'], 'sni': proxy_config['sni']
                             }

                    vmess_raw_proxy = json.dumps(vmess_value, sort_keys=False, indent=2, ensure_ascii=False)
                    vmess_proxy = str('vmess://' + sub_convert.base64_encode(vmess_raw_proxy) + '\n')
                    protocol_url.append(vmess_proxy)

                elif proxy['type'] == 'ss' : # SS 节点提取, 由 ss_base64_decoded 部分(参数: 'cipher', 'password', 'server', 'port') Base64 编码后 加 # 加注释(URL_encode) 
                    if 'plugin' not in proxy :
                        ss_base64_decoded = str(proxy['cipher']) + ':' + str(proxy['password']) + '@' + str(proxy['server']) + ':' + str(proxy['port'])
                        ss_base64 = sub_convert.base64_encode(ss_base64_decoded)
                        ss_proxy = str('ss://' + ss_base64 + '#' + str(urllib.parse.quote(proxy['name'])) + '\n')
                        
                    elif proxy['plugin'] == 'obfs' :
                        #print(proxy)
                        if 'mode' not in proxy['plugin-opts']:
                            proxy['plugin-opts']['mode']='http'
                        if 'host' not in proxy['plugin-opts']:
                            proxy['plugin-opts']['host']=proxy['server']
                        
                            
                        ssplugin=str('obfs='+str(proxy['plugin-opts']['mode']) + ';' + 'obfs-host=' + str(proxy['plugin-opts']['host']))
                        #print(ssplugin)
                        ssplugin=str(urllib.parse.quote(ssplugin))
                        ss_base64_decoded = str(str(proxy['cipher']) + ':' + str(proxy['password']))
                        ss_base64 = sub_convert.base64_encode(ss_base64_decoded)
                        ss_base64 = str(ss_base64+ '@' + str(proxy['server']) + ':' + str(proxy['port']))
                        ss_proxy = str('ss://' + ss_base64 +  '/?plugin=obfs-local%3B'+ ssplugin + '#' + str(urllib.parse.quote(proxy['name'])) + '\n')
                        #print(ss_proxy)
                    elif proxy['plugin'] == 'v2ray-plugin' :
                        if 'mode' not in proxy['plugin-opts']:
                            proxy['plugin-opts']['mode']='websocket'
                        if 'host' not in proxy['plugin-opts']:
                            proxy['plugin-opts']['host']=proxy['server']
                        if 'path' not in proxy['plugin-opts']:
                            proxy['plugin-opts']['path']='/'
                        #print(proxy)
                        ssplugin=str('mode='+str(proxy['plugin-opts']['mode']) + ';' + 'host=' + str(proxy['plugin-opts']['host'])+ ';' + 'path=' + str(proxy['plugin-opts']['path'])+';'+'tls;'+'mux=4;'+'mux=mux=4;')
                        #print(ssplugin)
                        ssplugin=str(urllib.parse.quote(ssplugin))
                        ss_base64_decoded = str(str(proxy['cipher']) + ':' + str(proxy['password']))
                        ss_base64 = sub_convert.base64_encode(ss_base64_decoded)
                        ss_base64 = str(ss_base64+ '@' + str(proxy['server']) + ':' + str(proxy['port']))
                        ss_proxy = str('ss://' + ss_base64 +  '/?plugin=v2ray-plugin%3B'+ ssplugin + '#' + str(urllib.parse.quote(proxy['name'])) + '\n')
                        #print(ss_proxy)

                    
                    protocol_url.append(ss_proxy)
   












                
                elif proxy['type'] == 'trojan': # Trojan 节点提取, 由 trojan_proxy 中参数再加上 # 加注释(URL_encode) # trojan Go https://p4gefau1t.github.io/trojan-go/developer/url/
                    if 'tls' in proxy.keys() and 'network' in proxy.keys():
                        if proxy['tls'] == True and proxy['network'] != 'tcp':
                            network_type = proxy['network']
                            trojan_go = f'?security=tls&type={network_type}&headerType=none'
                        elif proxy['tls'] == False and proxy['network'] != 'tcp':
                            trojan_go = f'??allowInsecure=0&type={network_type}&headerType=none'
                        else:
                            trojan_go = '?allowInsecure=1'
                    else:
                        trojan_go = '?allowInsecure=1'
                    if 'sni' in proxy.keys():
                        trojan_go = trojan_go+'&sni='+str(proxy['sni'])
                    trojan_proxy = str('trojan://' + str(proxy['password']) + '@' + str(proxy['server']) + ':' + str(proxy['port']) + trojan_go + '#' + str(urllib.parse.quote(proxy['name'])) + '\n')
                    protocol_url.append(trojan_proxy)
                
                elif proxy['type'] == 'ssr': # ssr 节点提取, 由 ssr_base64_decoded 中所有参数总体 base64 encode
                    #print(proxy)
                    remarks = sub_convert.base64_encode(proxy['name']).replace('+', '-')
                    server = proxy['server']
                    port = str(proxy['port'])
                    password = sub_convert.base64_encode(proxy['password'])
                    cipher = proxy['cipher']
                    protocol = proxy['protocol']
                    obfs = proxy['obfs']

                    if 'obfs-param' in proxy:
                        if proxy['obfs-param'] is not None:
                            obfsparam = sub_convert.base64_encode(proxy['obfs-param'].replace('$',','))
                        else:
                            obfsparam = ''
                    else:
                        obfsparam = ''
                   
                    if 'protocol-param' in proxy:
                        if proxy['protocol-param'] is not None:
                            protoparam = sub_convert.base64_encode(proxy['protocol-param'])
                        else:
                            protoparam = ''
                    else:
                        protoparam = ''

                    group = 'U1NSUHJvdmlkZXI'
                    ssr_proxy = 'ssr://'+sub_convert.base64_encode(server+':'+port+':'+protocol+':'+cipher+':'+obfs+':'+password+'/?remarks='+remarks+'&obfsparam='+obfsparam+'&protoparam='+protoparam+'&group='+group + '\n')
                    protocol_url.append(ssr_proxy)
                    print(ssr_proxy)
                    #print(protocol_url)
      
            yaml_content = ''.join(protocol_url)
            return yaml_content
        except Exception as err:
            print(f'yaml decode 发生 {err} 错误')
            print(proxy)
            #pass
            return '订阅内容解析错误'
    def base64_decode(url_content): # Base64 转换为 URL 链接内容
        if '-' in url_content:
            url_content = url_content.replace('-', '+')
        elif '_' in url_content:
            url_content = url_content.replace('_', '/')
        #print(len(url_content))
        missing_padding = len(url_content) % 4
        if missing_padding != 0:
            url_content += '='*(4 - missing_padding) # 不是4的倍数后加= https://www.cnblogs.com/wswang/p/7717997.html
        """ elif(len(url_content)%3 == 1):
            url_content += '=='
        elif(len(url_content)%3 == 2): 
            url_content += '=' """
        #print(url_content)
        #print(len(url_content))
        try:
            base64_content = base64.b64decode(url_content.encode('utf-8')).decode('utf-8','ignore') # https://www.codenong.com/42339876/
            base64_content_format = base64_content
            return base64_content_format
        except UnicodeDecodeError:
            base64_content = base64.b64decode(url_content)
            base64_content_format = base64_content
            return base64_content

if __name__ == '__main__':
    
    subscribe = 'https://raw.githubusercontent.com/imyaoxp/freenode/master/sub/sub_merge.txt'
    output_path = './output.txt'

    content = sub_convert.convert(subscribe, 'url', 'YAML')

    file = open(output_path, 'w', encoding= 'utf-8')
    file.write(content)
    file.close()
    print(f'Writing content to output.txt\n')
