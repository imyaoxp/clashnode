
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
        
    def format(sub_content, output=False):
        if 'proxies:' not in sub_content:
            # 处理非YAML内容（保持原有逻辑）
            url_list = []
            try:
                if '://' not in sub_content:
                    sub_content = sub_convert.base64_encode(sub_content)

                raw_url_list = re.split(r'\n+', sub_content)

                for url in raw_url_list:
                    while len(re.split('ss://|ssr://|vmess://|trojan://|vless://|tuic://|hy://|hy2://', url)) > 2:
                        url_to_split = url[8:]
                        if 'ss://' in url_to_split and 'vmess://' not in url_to_split and 'vless://' not in url_to_split:
                            url_splited = url_to_split.replace('ss://', '\nss://', 1)
                        elif 'ssr://' in url_to_split:
                            url_splited = url_to_split.replace('ssr://', '\nssr://', 1)
                        elif 'vmess://' in url_to_split:
                            url_splited = url_to_split.replace('vmess://', '\nvmess://', 1)
                        elif 'trojan://' in url_to_split:
                            url_splited = url_to_split.replace('trojan://', '\ntrojan://', 1)
                        elif 'vless://' in url_to_split:
                            url_splited = url_to_split.replace('vless://', '\nvless://', 1)
                        elif 'tuic://' in url_to_split:
                            url_splited = url_to_split.replace('tuic://', '\ntuic://', 1)
                        elif 'hy2://' in url_to_split:
                            url_splited = url_to_split.replace('hy2://', '\nhy2://', 1)
                        elif 'hy://' in url_to_split:
                            url_splited = url_to_split.replace('hy://', '\nhy://', 1)
                        elif '#' in url_to_split:
                            url_splited = url_to_split.replace('#', '\n#', 1)

                        url_split = url_splited.split('\n')
                        front_url = url[:8] + url_split[0]
                        url_list.append(front_url)
                        url = url_split[1]
                    url_list.append(url)

                url_content = '\n'.join(url_list)
                return url_content
            except:
                print('Sub_content 格式错误1')
                return ''

        elif 'proxies:' in sub_content:
            def parse_nested(content):
                """递归解析嵌套结构"""
                result = {}
                items = []
                current = []
                in_quotes = False
                quote_char = None
                brace_level = 0
                bracket_level = 0
            
                # 分割键值对
                for char in content:
                    if char in ('"', "'") and not in_quotes:
                        in_quotes = True
                        quote_char = char
                    elif char == quote_char and in_quotes:
                        in_quotes = False
                        quote_char = None
                
                    if char == '{' and not in_quotes:
                        brace_level += 1
                    elif char == '}' and not in_quotes:
                        brace_level -= 1
                    elif char == '[' and not in_quotes:
                        bracket_level += 1
                    elif char == ']' and not in_quotes:
                        bracket_level -= 1
                
                    if char == ',' and brace_level == 0 and bracket_level == 0 and not in_quotes:
                        items.append(''.join(current).strip())
                        current = []
                    else:
                        current.append(char)
            
                if current:
                    items.append(''.join(current).strip())
            
                # 处理每个键值对
                for item in items:
                    # 找到第一个不在引号或括号中的冒号
                    colon_pos = -1
                    in_quotes = False
                    quote_char = None
                    brace_level = 0
                    bracket_level = 0
                
                    for i, char in enumerate(item):
                        if char in ('"', "'") and not in_quotes:
                            in_quotes = True
                            quote_char = char
                        elif char == quote_char and in_quotes:
                            in_quotes = False
                            quote_char = None
                        
                        if char == '{' and not in_quotes:
                            brace_level += 1
                        elif char == '}' and not in_quotes:
                            brace_level -= 1
                        elif char == '[' and not in_quotes:
                            bracket_level += 1
                        elif char == ']' and not in_quotes:
                           bracket_level -= 1
                    
                        if char == ':' and brace_level == 0 and bracket_level == 0 and not in_quotes:
                            colon_pos = i
                            break
                
                    if colon_pos > 0:
                        key = item[:colon_pos].strip()
                        value = item[colon_pos+1:].strip()
                    
                        # 处理嵌套值
                        if value.startswith('{') and value.endswith('}'):
                            result[key] = parse_nested(value[1:-1])
                        elif value.startswith('[') and value.endswith(']'):
                            # 处理数组
                            result[key] = [x.strip().strip('"\'') for x in value[1:-1].split(',')]
                        else:
                            # 去除值的引号
                            if (value.startswith('"') and value.endswith('"')) or \
                               (value.startswith("'") and value.endswith("'")):
                                value = value[1:-1]
                            result[key] = value
            
                return result

            # 处理YAML内容
            try:
                # 尝试直接加载
                loaded = yaml.safe_load(sub_content)
                if output:
                    return yaml.dump(loaded, default_flow_style=True, sort_keys=False, allow_unicode=True)
                return loaded
            
            except Exception:
                # 手动解析
                proxies = []
                lines = sub_content.split('\n')
            
                for line in lines:
                    line = line.strip()
                    if not line or line.startswith('#') or not line.startswith('- '):
                        continue
                
                    # 提取大括号内容
                    if '{' in line and '}' in line:
                        content = line[line.find('{')+1:line.rfind('}')]
                        proxy = parse_nested(content)
                    
                        # 确保所有层级都是字典
                        for key, value in proxy.items():
                            if isinstance(value, str) and value.startswith('{') and value.endswith('}'):
                                try:
                                    proxy[key] = parse_nested(value[1:-1])
                                except:
                                    pass
                    
                        proxies.append(proxy)
            
                result = {'proxies': proxies}
            
                if output:
                    return yaml.dump(result, default_flow_style=False, sort_keys=False, allow_unicode=True)
                return result
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
                    if proxy_compared['type'] =='vmess' or  proxy_compared['type'] =='vless':
                        if proxy_compared['server'] == proxies_list[begin_2]['server'] and proxy_compared['type'] == proxies_list[begin_2]['type'] and proxy_compared['port'] == proxies_list[begin_2]['port'] and proxy_compared['uuid'] == proxies_list[begin_2]['uuid']:
                            proxies_list.pop(begin_2)
                            length -= 1
                    elif proxy_compared['type'] =='hysteria':
                        if proxy_compared['server'] == proxies_list[begin_2]['server'] and proxy_compared['type'] == proxies_list[begin_2]['type'] and proxy_compared['port'] == proxies_list[begin_2]['port'] and proxy_compared['auth-str'] == proxies_list[begin_2]['auth-str']:
                            proxies_list.pop(begin_2)
                            length -= 1                    
                    else:
                        if proxy_compared['server'] == proxies_list[begin_2]['server'] and proxy_compared['type'] == proxies_list[begin_2]['type'] and proxy_compared['port'] == proxies_list[begin_2]['port'] and proxy_compared['password'] == proxies_list[begin_2]['password']:
                            proxies_list.pop(begin_2)
                            length -= 1
                            #print(proxy_compared)
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
        yaml_content_raw = yaml.dump(yaml_content_dic, default_flow_style=False, sort_keys=False, allow_unicode=True, width=750, indent=4) # yaml.dump 显示中文方法 https://blog.csdn.net/weixin_41548578/article/details/90651464 yaml.dump 各种参数 https://blog.csdn.net/swinfans/article/details/88770119
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
                    # UUID 验证（新增部分）
                    if 'id' not in vmess_json_config:
                        raise ValueError("缺少 UUID 字段")
            
                    uuid_str = vmess_json_config['id']
                    if not re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', uuid_str, re.I):
                        raise ValueError(f"无效的 UUID 格式: {uuid_str}")
                    
                    # 给 network 字段设置默认值，若不存在则为 'ws'
                    if 'net' not in vmess_json_config:
                        vmess_json_config['net'] = 'ws'  
                    vmess_default_config = {
                        'v': 'Vmess Node', 'ps': 'Vmess Node', 'add': '0.0.0.0', 'port': 0, 'id': '',
                        'aid': 0, 'scy': 'auto', 'net': '', 'type': '', 
                        'host': vmess_json_config.get('add', ''), 
                        'path': '/', 'tls': False, 
                        'network': vmess_json_config['net'],  # 使用处理后的 net 值
                        'grpc-opts': {}, 'h2-opts': {}, 'tcp-opts': {}
                    }
                    vmess_default_config.update(vmess_json_config)
                    vmess_config = vmess_default_config

                    #if not vmess_config['id'] or len(vmess_config['id']) != 36:
                    #    print('节点格式错误')
                    #    continue

                    server_port = str(vmess_config['port']).replace('/', '')
                    yaml_url = {
                        'name': urllib.parse.unquote(str(vmess_config.get('ps', ''))),
                        'server': vmess_config['add'],
                        'port': server_port,
                        'type': 'vmess',
                        'uuid': vmess_config['id'].lower(),
                        'alterId': vmess_config['aid'],
                        'cipher': vmess_config['scy'],
                        'skip-cert-verify': True,
                        'udp': True
                    }

                    # 处理不同传输方式
                    network_type = vmess_config['net'].lower()
                    if network_type == 'ws':
                        yaml_url['network'] = 'ws'
                        headers = {'host': vmess_config.get('host', vmess_config['add'])}
                        if 'path' in vmess_config:
                            headers['path'] = vmess_config['path']
                        yaml_url['ws-opts'] = headers
                    elif network_type == 'grpc':
                        yaml_url['network'] = 'grpc'
                        yaml_url['grpc-opts'] = {'grpc-service-name': vmess_config.get('type', '')}
                    elif network_type == 'h2':
                        yaml_url['network'] = 'h2'
                        yaml_url['h2-opts'] = {
                            'host': vmess_config.get('host', [vmess_config['add']]),
                            'path': vmess_config.get('path', '/')
                        }
                    elif network_type == 'tcp':
                        yaml_url['network'] = 'tcp'
                        if 'type' in vmess_config:  # 处理TCP伪装
                            yaml_url['tcp-opts'] = {
                                'headers': {'host': urllib.parse.unquote(vmess_config.get('host', vmess_config['add']))},
                                'path': vmess_config.get('path', '/')
                            }

                    # 处理TLS配置
                    yaml_url['tls'] = vmess_config.get('tls', False) or network_type in ['h2', 'grpc']
                    url_list.append(yaml_url)
                

                except Exception as err:
                    print(vmess_config)
                    print(line)
                    print(f'yaml_encode 解析 vmess 节点发生错误: {err}')
                    
                    continue

            if 'vless://' in line:
                try:
                    # 分离基础部分和参数部分
                    url_part = line.replace('vless://', '').split('#', 1)  # 分割#后的备注部分
                    base_part = url_part[0].split('?', 1)  # 分割?前的核心部分和参数部分

                    # 提取UUID和服务端信息
                    uuid, server_port = base_part[0].split('@')
                    server, port = server_port.replace('/', '').split(':')[:2]

                    # 参数解析（保留原始大小写）
                    raw_params = {}
                    if len(base_part) > 1:
                        for param in base_part[1].split('&'):
                            if '=' in param:
                                key, val = param.split('=', 1)
                                raw_params[key] = val

                    # 创建大小写不敏感的参数字典
                    params_lower = {k.lower(): (k, v) for k, v in raw_params.items()}

                    # 优先级获取函数（兼容大小写）
                    def get_param_priority(*possible_names, default=None):
                        for name in possible_names:
                            if name in raw_params:
                                return raw_params[name]
                        for name in possible_names:
                            lower_name = name.lower()
                            if lower_name in params_lower:
                                return params_lower[lower_name][1]
                        return default

                    # 获取公共参数
                    sni = (
                        get_param_priority('sni', 'SNI', 'Sni') or
                        get_param_priority('servername', 'ServerName', 'serverName', 'Servername') or
                        get_param_priority('host', 'Host', 'HOST') or
                        server
                    )

                    # 构建基础节点
                    yaml_node = {
                        'name': urllib.parse.unquote(url_part[1]) if len(url_part) > 1 else 'Unnamed',
                        'server': server,
                        'port': port,
                        'type': 'vless',
                        'uuid': uuid,
                        'servername': sni,
                        'tls': get_param_priority('security', 'Security', default='none').lower() in ['tls', 'reality'],
                        'network': get_param_priority('type', 'Type', default='tcp').lower(),
                        'udp': True
                    }

                    # 处理Reality配置
                    security_type = get_param_priority('security', 'Security', default='none').lower()
                    if security_type == 'reality':
                        pbk = urllib.parse.unquote(get_param_priority('pbk', 'PublicKey', 'publicKey', default=''))
                        sid = urllib.parse.unquote(get_param_priority('sid', 'ShortId', 'shortId', default='')) 
                        # 内联验证 Reality 公钥格式（标准 Base64，长度 43 或 44）
                        if not pbk or not len(pbk) in (32,43, 44): 
                            raise ValueError(f"Invalid Reality public-key: {pbk}")  # 触发异常处理
                        if sid and not (
                            1 <= len(sid) <= 16 and 
                            all(c.lower() in '0123456789abcdefABCDEF' for c in sid)
                        ):
                            raise ValueError(f"Invalid sid: {sid}")  # 触发异常处理
                        yaml_node['reality-opts'] = {
                            'public-key': pbk,
                            'short-id': sid 
                        }
                        flow = get_param_priority('flow', 'Flow', default='')
                        if flow:
                            yaml_node['flow'] = flow

                    # 根据network类型处理特殊参数
                    network_type = yaml_node['network']

                    # 1. WebSocket处理
                    if network_type == 'ws':
                        ws_host = (
                            get_param_priority('host', 'Host', 'HOST') or
                            sni or
                            server
                        )
                        yaml_node['ws-opts'] = {
                            'path': urllib.parse.unquote(get_param_priority('path', 'Path', 'PATH', default='/')),
                            'headers': {'Host': ws_host}
                        }

                    # 2. gRPC处理
                    elif network_type == 'grpc':
                        yaml_node['grpc-opts'] = {
                            'grpc-service-name': urllib.parse.unquote(get_param_priority('serviceName', 'servicename', default=''))
                        }

                    # 3. HTTP/2处理
                    elif network_type == 'h2':
                        yaml_node['h2-opts'] = {
                            'host': get_param_priority('host', 'Host', 'HOST', default='').split(','),
                            'path': get_param_priority('path', 'Path', 'PATH', default='/')
                        }

                    # 4. TCP处理（含HTTP伪装）
                    elif network_type == 'tcp':
                        header_type = get_param_priority('headerType', 'headertype')
                        if header_type and header_type.lower() == 'http':
                            yaml_node['tcp-opts'] = {
                                'headers': {
                                    'Host': get_param_priority('host', 'Host', 'HOST', default='').split(',')
                                },
                                'path': get_param_priority('path', 'Path', 'PATH', default='/')
                            }

                    url_list.append(yaml_node)

                except Exception as e:
                    print(yaml_node)
                    print(line)
                    print(f'VLESS编码错误: {e} | 行: {line[:100]}...')
                    continue
        
   
            if 'ss://' in line and 'vless://' not in line and 'vmess://' not in line:
                if '#' not in line:
                    line = line + '#SS%20Node'
                try:
                    ss_content = line.replace('ss://', '')
                    part_list = ss_content.split('#', 1)
                    yaml_url.setdefault('name', urllib.parse.unquote(part_list[1]))
                    if '@' in part_list[0]:
                        mix_part = part_list[0].split('@', 1)
                        method_part = sub_convert.base64_decode(urllib.parse.unquote(mix_part[0]))
                        server_part = f'{method_part}@{mix_part[1]}'
                    else:
                        server_part = sub_convert.base64_decode(urllib.parse.unquote(part_list[0]))
                    server_part_list = server_part.split(':', 1)
                    method_part = server_part_list[0]

                    CLASH_SUPPORTED_SS_CIPHERS = {
                        'aes-128-cfb', 'aes-192-cfb', 'aes-256-cfb',
                        'rc4-md5', 'bf-cfb', 'chacha20',
                        'aes-128-gcm', 'aes-192-gcm', 'aes-256-gcm',
                        'chacha20-ietf-poly1305', 'xchacha20-ietf-poly1305',
                        '2022-blake3-aes-128-gcm', '2022-blake3-aes-256-gcm', 
                        '2022-blake3-chacha20-poly1305', 'none'
                    }
                    if method_part.lower() not in CLASH_SUPPORTED_SS_CIPHERS:
                        raise ValueError(f"Unsupported cipher '{method_part}' by Clash Meta")
                    server_part_list = server_part_list[1].rsplit('@', 1)
                    password_part = server_part_list[0]
                    password_part = password_part.replace('"', '')
                    server_part_list = server_part_list[1].split(':', 1)
                    yaml_url.setdefault('server', server_part_list[0])
                    server_part_list = server_part_list[1].split('/', 1)
                    yaml_url.setdefault('port', server_part_list[0].replace('/', ''))
                    yaml_url.setdefault('type', 'ss')
                    yaml_url.setdefault('cipher', method_part)
                    yaml_url.setdefault('password', password_part)
            
                    if 'obfs-local' in line:
                        yaml_url.setdefault('Plugin', 'obfs')
                        plugin_list = str(urllib.parse.unquote(server_part_list[1]) + ';')
                        plugin_mode = re.compile('obfs=(.*?);').findall(plugin_list)[0]
                        plugin_host = re.compile('obfs-host=(.*?);').findall(plugin_list)[0]
                        yaml_url['plugin'] = yaml_url.pop("Plugin")
                        yaml_url.setdefault('plugin-opts', {
                            'mode': plugin_mode, 
                            'host': plugin_host, 
                            'tls': 'true', 
                            'skip-cert-verify': 'true'
                        })

                    # 修改点1：添加xray-plugin支持
                    if 'v2ray-plugin' in line or 'xray-plugin' in line:
                        plugin_type = 'v2ray-plugin' if 'v2ray-plugin' in line else 'xray-plugin'
                        yaml_url.setdefault('Plugin', plugin_type)
                        plugin_list = str(urllib.parse.unquote(server_part_list[1]) + ';')
            
                        plugin_mode = re.compile('mode=(.*?);').findall(plugin_list)[0]
                        plugin_host = re.compile('host=(.*?);').findall(plugin_list)[0]
                        plugin_host = plugin_host if plugin_host else yaml_url['server']
                        plugin_path = re.compile('path=(.*?);').findall(plugin_list)[0]
                        plugin_path = plugin_path if plugin_path else '/'
            
                        # 修改点2：添加restls支持
                        restls = 'true' if 'restls=true' in plugin_list.lower() else 'false'
            
                        yaml_url['plugin'] = yaml_url.pop("Plugin")
                        yaml_url.setdefault('plugin-opts', {
                            'mode': plugin_mode,
                            'host': plugin_host,
                            'path': plugin_path,
                            'tls': 'true',
                            'mux': 'true',
                            'skip-cert-verify': 'true',
                            'restls': restls  # 新增restls参数
                        })

                    yaml_url.setdefault('udp', 'true')
                    url_list.append(yaml_url)
                except Exception as err:
                    print(yaml_url)
                    print(f'line:{line}')
                    print(f'yaml_encode 解析 ss 节点发生错误2: {err}')
                    continue

            
            if 'hy://' in line:
                try:
                    # 1. 解析基础URL部分
                    url_part = line.replace('hy://', '').split('#', 1)
                    base_part = url_part[0].split('?', 1)
                    auth_server = base_part[0].rsplit('@', 1)
                    auth = auth_server[0] if len(auth_server) == 2 else ''
                    server, port = auth_server[-1].split(':')[:2]

                    # 2. 初始化节点配置（强制alpn为列表）
                    config = {
                        'name': urllib.parse.unquote(url_part[1]) if len(url_part) > 1 else 'Hysteria1',
                        'type': 'hysteria',
                        'server': server,
                        'port': int(port),
                        'auth-str': auth,
                        'up': '20 Mbps',
                        'down': '50 Mbps',
                        'protocol': 'udp',
                        'skip-cert-verify': False,
                        'alpn': ['h3']  # 默认值（确保是列表）
                    }

                    # 3. 处理查询参数（关键修改点）
                    if len(base_part) > 1:
                        params = {}
                        for param in base_part[1].split('&'):
                            if '=' in param:
                                key, val = param.split('=', 1)
                                params[key.lower()] = val

                        # 特殊处理alpn参数（兼容字符串和列表）
                        if 'alpn' in params:
                            alpn_val = params['alpn']
                            if isinstance(alpn_val, str):
                                config['alpn'] = [x.strip() for x in alpn_val.split(',')]
                            elif isinstance(alpn_val, list):
                                config['alpn'] = alpn_val

                        # 其他参数映射
                        param_mappings = {
                            'protocol': ('protocol', lambda x: x if x in ['udp', 'wechat-video', 'faketcp'] else 'udp'),
                            'obfs': ('obfs', str),
                            'obfs-password': ('obfs-password', str),
                            'sni': ('sni', str),
                            'peer': ('sni', str),
                            'insecure': ('skip-cert-verify', lambda x: x == '1')
                        }
            
                        for param_key, (config_key, converter) in param_mappings.items():
                            if param_key in params:
                                config[config_key] = converter(params[param_key])

                    # 4. 最终校验alpn格式
                    if not isinstance(config['alpn'], list):
                        config['alpn'] = [str(config['alpn'])]
                    print(config)

                    url_list.append(config)
                    
                except Exception as err:
                    print(config)
                    print(line)
                    print(f'Hysteria1解析错误: {err} | 内容: {line[:50]}...')
                    continue
            
            
            if 'hy2://' in line:
                try:
                    # 提取基础信息
                    url_part = line.replace('hy2://', '').split('#', 1)
                    base_part = url_part[0].split('?', 1)
                
                    # 处理认证信息
                    auth_server = base_part[0].rsplit('@', 1)
                    auth = auth_server[0] if len(auth_server) == 2 else ''
                    server, port = auth_server[-1].split(':')[:2]

                    # 初始化配置
                    config = {
                        'name': urllib.parse.unquote(url_part[1]) if len(url_part) > 1 else 'Hysteria2',
                        'type': 'hysteria2',
                        'server': server,
                        'port': int(port),
                        'password': auth,
                        'skip-cert-verify': True  # 默认值
                    }

                    # 处理参数（只保留有效参数）
                    if len(base_part) > 1:
                        for param in base_part[1].split('&'):
                            if '=' in param:
                                key, val = param.split('=', 1)
                                key = key.lower()
                            
                                if key == 'sni' and val:
                                    config['sni'] = val
                                elif key == 'obfs' and val:
                                    config['obfs'] = val
                                elif key == 'obfs-password' and val:
                                    config['obfs-password'] = val
                                
                                
                                elif key == 'alpn' and val:
                                    config['alpn'] = val.split(',')
                                
                    # 添加节点名称
                    #config['name'] = urllib.parse.unquote(url_part[1]) if len(url_part) > 1 else 'Hysteria2'
                
                    url_list.append(config)

                except Exception as err:
                    print(config)
                    print(line)
                    print(f'HY2解析错误: {err} | 内容: {line[:50]}...')
                    continue

  
                
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
                    yaml_url.setdefault('port', parts[1].replace('/', ''))
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
                         
                    #print(yaml_url)
                    url_list.append(yaml_url)
                    #print(url_list)
                except Exception as err:
                    print(yaml_url)
                    print(line)
                    print(f'yaml_encode 解析 ssr 节点发生错误: {err}')
                    
                    continue




            
          
            if 'trojan://' in line:
                try:
                    url_content = line.replace('trojan://', '')
                    part_list = re.split('#', url_content, maxsplit=1)
                    yaml_url.setdefault('name', urllib.parse.unquote(part_list[1]))

                    server_part = part_list[0]
                    server_part_list = re.split(':|@|\?|&', server_part)
                    yaml_url.setdefault('server', server_part_list[1])
                    yaml_url.setdefault('port', server_part_list[2].replace('/', ''))
                    yaml_url.setdefault('type', 'trojan')
                    yaml_url.setdefault('password', server_part_list[0].lower())

                    # 解析 Trojan-Go 特有参数
                    params = server_part.split('?')[1] if '?' in server_part else ''
                    param_dict = {}
                    if params:
                        for param in params.split('&'):
                            if '=' in param:
                                key, val = param.split('=', 1)
                                param_dict[key.lower()] = val

                    # 处理传输协议 (network)
                    if 'type' in param_dict:
                        network_type = param_dict['type'].lower()
                        yaml_url['network'] = network_type

                        # WebSocket 配置
                        if network_type == 'ws':
                            yaml_url['ws-opts'] = {
                                'path': param_dict.get('path', '/'),
                                'headers': {'host': param_dict.get('host', param_dict.get('sni', yaml_url['server']))}
                            }
                        # gRPC 配置
                        elif network_type == 'grpc':
                            yaml_url['grpc-opts'] = {
                                'grpc-service-name': param_dict.get('servicename', '')}

                    # TLS 配置
                    yaml_url['tls'] = param_dict.get('security', 'tls').lower() == 'tls'
                    if 'sni' in param_dict:
                        yaml_url['sni'] = param_dict['sni']

                    yaml_url['skip-cert-verify'] = True
                    yaml_url['udp'] = True

                    if len(yaml_url['password']) == 36:
                        url_list.append(yaml_url)
                except Exception as err:
                    print(yaml_url)
                    print(line)
                    print(f'yaml_encode 解析 trojan 节点发生错误: {err}')
                    continue

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
                
                if proxy['type'] == 'vmess' : # Vmess 节点提取, 由 Vmess 所有参数 dump JSON 后 base64 得来。
                           
                    try:
                        uuid_str = proxy['uuid']
                        if not re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', uuid_str, re.I):
                            raise ValueError(f"无效的 UUID 格式: {uuid_str}")
                        # 提取基础配置，给 network 设默认值
                        network_type = proxy.get('network', 'ws').lower()  
                        vmess_config = {
                            'v': 2,
                            'ps': proxy['name'],
                            'add': proxy['server'],
                            'port': proxy['port'],
                            'id': proxy['uuid'],
                            'aid': proxy['alterId'],
                            'scy': proxy['cipher'],
                            'net': network_type,  # 用默认或已有值
                            'tls': proxy.get('tls', False),
                            'sni': proxy.get('sni', proxy['server'])
                        }

                        # 处理不同传输方式的参数
                        if network_type == 'ws':
                            ws_opts = proxy.get('ws-opts', {})
                            vmess_config.update({
                                'host': ws_opts.get('host', proxy['server']),
                                'path': ws_opts.get('path', '/')
                            })
                        elif network_type == 'grpc':
                            grpc_opts = proxy.get('grpc-opts', {})
                            vmess_config['type'] = grpc_opts.get('grpc-service-name', '')  # gRPC服务名
                        elif network_type == 'h2':
                            h2_opts = proxy.get('h2-opts', {})
                            vmess_config.update({
                                'host': h2_opts.get('host', [proxy['server']]),  # 支持多host列表
                                'path': h2_opts.get('path', '/')
                            })
                        elif network_type == 'tcp':
                            tcp_opts = proxy.get('tcp-opts', {})
                            if tcp_opts:  # 存在TCP伪装头时
                                vmess_config.update({
                                    'type': 'http',  # 伪装类型固定为http
                                    'host': tcp_opts.get('headers', {}).get('host', proxy['server']),
                                    'path': tcp_opts.get('path', '/')
                                })

                        # 构建VMess JSON配置
                        vmess_raw = json.dumps(vmess_config, sort_keys=False, ensure_ascii=False)
                        vmess_proxy = f"vmess://{sub_convert.base64_encode(vmess_raw)}\n"
                        protocol_url.append(vmess_proxy)

                    except Exception as e:
                        print(proxy)
                        print(vmess_proxy)
                        print(f'VMess解码错误: {e} | 节点: {proxy.get("name", "未知")}')
                        continue





                
                elif proxy['type'] == 'vless':
                    try:
                        # 优先级获取函数
                        def get_priority(*keys, default=None):
                            for key in keys:
                                value = proxy.get(key)
                                if value is not None:
                                    return value
                                # 检查小写变体
                                lower_key = key.lower()
                                for k, v in proxy.items():
                                    if k.lower() == lower_key:
                                        return v
                            return default

                        # 获取公共参数
                        sni = (
                            get_priority('servername', 'serverName', 'ServerName', 'Servername') or
                            get_priority('sni', 'SNI', 'Sni') or
                            get_priority('host', 'Host', 'HOST') or
                            proxy['server']
                        )

                        # 构建基础参数
                        security_type = 'reality' if 'reality-opts' in proxy else ('tls' if proxy.get('tls') else 'none')
                        params = {
                            'security': security_type,
                            'type': proxy.get('network', 'tcp'),
                            'sni': sni
                        }

                        # 处理Reality配置
                        if security_type == 'reality':
                            reality_opts = proxy['reality-opts']
                            params['pbk'] = reality_opts.get('public-key', '')
                            params['sid'] = reality_opts.get('short-id', '')
                            if 'flow' in proxy:
                                params['flow'] = proxy['flow']

                        # 根据network类型处理特殊参数
                        network_type = proxy.get('network', 'tcp')

                        # 1. WebSocket处理
                        if network_type == 'ws':
                            ws_opts = proxy.get('ws-opts', {})
                            params['path'] = ws_opts.get('path', '/')
                            headers = ws_opts.get('headers', {})
                            params['host'] = (
                                headers.get('host') or
                                headers.get('Host') or
                                sni
                           )

                        # 2. gRPC处理
                        elif network_type == 'grpc':
                            grpc_opts = proxy.get('grpc-opts', {})
                            params['serviceName'] = (
                                grpc_opts.get('grpc-service-name') or
                                grpc_opts.get('grpcServiceName') or
                               ''
                            )

                        # 3. HTTP/2处理
                        elif network_type == 'h2':
                            h2_opts = proxy.get('h2-opts', {})
                            params['path'] = h2_opts.get('path', '/')
                            if 'host' in h2_opts and h2_opts['host']:
                                params['host'] = ','.join(h2_opts['host'])

                        # 4. TCP处理（HTTP伪装）
                        elif network_type == 'tcp':
                            tcp_opts = proxy.get('tcp-opts', {})
                            if 'headers' in tcp_opts:
                                headers = tcp_opts['headers']
                                host = headers.get('Host') or headers.get('host')
                                if host:
                                    params['headerType'] = 'http'
                                    params['host'] = ','.join(host) if isinstance(host, list) else host
                                    params['path'] = tcp_opts.get('path', '/')

                        # 生成标准化URL
                        query_str = '&'.join(
                            f"{k}={urllib.parse.quote(str(v))}" 
                            for k, v in params.items() 
                            if v not in (None, '')
                        )
                        vless_url = f"vless://{proxy['uuid']}@{proxy['server']}:{proxy['port']}?{query_str}#{urllib.parse.quote(proxy['name'])}"
                        protocol_url.append(vless_url + '\n')

                    except Exception as e:
                        print(proxy)
                        print(vless_url)
                        print(f'VLESS解码错误: {e} | 节点: {proxy.get("name", "未知")}')
                        continue
                
                
                elif proxy['type'] == 'ss':
                    try:
                        if 'plugin' not in proxy:
                            # 标准格式：仅对 "method:password" 进行 Base64 编码
                            ss_base64_decoded = str(proxy['cipher']) + ':' + str(proxy['password'])
                            ss_base64 = sub_convert.base64_encode(ss_base64_decoded)
    
                            # 显式声明服务器和端口（@server:port）
                            ss_proxy = 'ss://' + ss_base64 + '@' + str(proxy['server']) + ':' + str(proxy['port']) + '#' + str(urllib.parse.quote(proxy['name'])) + '\n'
                        elif proxy['plugin'] == 'obfs':
                            # 设置默认插件参数
                            if 'mode' not in proxy['plugin-opts']:
                                proxy['plugin-opts']['mode'] = 'http'
                            if 'host' not in proxy['plugin-opts']:
                                proxy['plugin-opts']['host'] = proxy['server']
    
                            # 生成插件参数字符串（如 "obfs=http;obfs-host=example.com"）
                            ssplugin = f"obfs={proxy['plugin-opts']['mode']};obfs-host={proxy['plugin-opts']['host']}"
                            ssplugin = urllib.parse.quote(ssplugin)  # URL 编码插件参数
    
                            # 标准格式：仅对 "method:password" 进行 Base64 编码
                            ss_base64_decoded = f"{proxy['cipher']}:{proxy['password']}"
                            ss_base64 = sub_convert.base64_encode(ss_base64_decoded)
    
                            # 拼接完整链接（显式声明服务器端口和插件）
                            ss_proxy = f"ss://{ss_base64}@{proxy['server']}:{proxy['port']}/?plugin=obfs-local%3B{ssplugin}#{urllib.parse.quote(proxy['name'])}\n"
                        # 修改点3：添加xray-plugin编码支持
                        elif proxy['plugin'] in ['v2ray-plugin', 'xray-plugin']:
                            # 设置默认插件参数
                            if 'mode' not in proxy['plugin-opts']:
                                proxy['plugin-opts']['mode'] = 'websocket'
                            if 'host' not in proxy['plugin-opts']:
                                proxy['plugin-opts']['host'] = proxy['server']
                            if 'path' not in proxy['plugin-opts']:
                                proxy['plugin-opts']['path'] = '/'

                            # 处理 restls 参数
                            restls_str = 'restls=true;' if proxy['plugin-opts'].get('restls', 'false') == 'true' else ''

                            # 构建插件参数字符串（标准格式）
                            plugin_opts = [
                                f"mode={proxy['plugin-opts']['mode']}",
                                f"host={proxy['plugin-opts']['host']}",
                                f"path={proxy['plugin-opts']['path']}",
                                restls_str,
                                "tls",
                                "mux=4"
                            ]
                            ssplugin = ';'.join(filter(None, plugin_opts))  # 自动过滤空值
                            ssplugin = urllib.parse.quote(ssplugin)

                            # 标准格式处理
                            ss_base64 = sub_convert.base64_encode(f"{proxy['cipher']}:{proxy['password']}")
    
                            # 完整标准格式链接
                            ss_proxy = (
                                f"ss://{ss_base64}@{proxy['server']}:{proxy['port']}"
                                f"/?plugin={proxy['plugin']}-local%3B{ssplugin}"
                                f"#{urllib.parse.quote(proxy['name'])}\n"
                            )
                        protocol_url.append(ss_proxy)
                    except Exception as err:
                        print(proxy)
                        print(ss_proxy)
                        print(f'SS生成错误: {err} | 节点: {proxy.get("name", "未知")}')
                        continue
                
                elif proxy['type'] == 'trojan': # Trojan 节点提取, 由 trojan_proxy 中参数再加上 # 加注释(URL_encode) # trojan Go https://p4gefau1t.github.io/trojan-go/developer/url/
               
                    try:
                        # 基础参数
                        base_url = f"trojan://{proxy['password']}@{proxy['server']}:{proxy['port']}"
        
                        # 查询参数
                        params = []
                        params.append(f"security={'tls' if proxy.get('tls', True) else 'none'}")
        
                        # 传输协议 (network)
                        network_type = proxy.get('network', 'tcp')
                        if network_type != 'tcp':
                            params.append(f"type={network_type}")
                            
                            # WebSocket 配置
                            if network_type == 'ws':
                                ws_opts = proxy.get('ws-opts', {})
                                params.append(f"path={ws_opts.get('path', '/')}")
                                if 'host' in ws_opts.get('headers', {}):
                                    params.append(f"host={ws_opts['headers']['host']}")
                                elif 'sni' in proxy:
                                    params.append(f"host={proxy['sni']}")
            
                            # gRPC 配置
                            elif network_type == 'grpc':
                                grpc_opts = proxy.get('grpc-opts', {})
                                if 'grpc-service-name' in grpc_opts:
                                    params.append(f"serviceName={grpc_opts['grpc-service-name']}")

                        # SNI 配置
                        if 'sni' in proxy:
                            params.append(f"sni={proxy['sni']}")

                       # 拼接完整链接
                        query_str = '&'.join(params)
                        trojan_url = f"{base_url}?{query_str}#{urllib.parse.quote(proxy['name'])}"
                        protocol_url.append(trojan_url + '\n')
                    except Exception as err:
                        print(proxy)
                        print(trojan_url)
                        print(f'yaml_decode 生成 trojan 节点发生错误: {err}')
                        continue
                
                         
                elif proxy['type'] == 'hysteria':  # Hysteria1节点
                    try:
                        # 基础部分
                        auth_part = f"{proxy['auth-str']}@" if proxy.get('auth-str') else ''
                        base_url = f"hy://{auth_part}{proxy['server']}:{proxy['port']}"

                        # 参数处理 (不包含up/down参数)
                        params = []
                    
                        # 协议类型
                        protocol = proxy.get('protocol', 'udp')
                        if protocol != 'udp':  # 默认是udp，非默认才需要添加
                            params.append(f"protocol={protocol}")
                    
                        # 混淆设置
                        if proxy.get('obfs') and proxy.get('obfs-password'):
                            params.append(f"obfs={proxy['obfs']}")
                            params.append(f"obfs-password={proxy['obfs-password']}")
                    
                        # TLS设置
                        if proxy.get('sni'):
                            params.append(f"peer={proxy['sni']}")  # H1使用peer参数而不是sni
                    
                        if proxy.get('skip-cert-verify', True):
                            params.append("insecure=1")
                    
                        if proxy.get('alpn'):
                            alpn_str = ','.join(proxy['alpn']) if isinstance(proxy['alpn'], list) else proxy['alpn']
                            params.append(f"alpn={alpn_str}")
                    
                        # 组合URL
                        param_str = '?' + '&'.join(params) if params else ''
                        hy1_url = f"{base_url}{param_str}#{urllib.parse.quote(proxy['name'])}"
                        protocol_url.append(hy1_url + '\n')

                    except Exception as err:
                        print(proxy)
                        print(hy1_url)
                        print(f'Hysteria1生成错误: {err} | 节点: {proxy.get("name", "未知")}')
                        continue
                
                
                
                elif proxy['type'] == 'hysteria2':
                    try:
                        # 基础部分
                        auth_part = f"{proxy['password']}@" if proxy.get('password') else ''
                        base_url = f"hy2://{auth_part}{proxy['server']}:{proxy['port']}"
                    
                        # 参数处理（只添加有效参数）
                        params = []
                    
                        if proxy.get('sni'):
                            params.append(f"sni={proxy['sni']}")
                    
                        if proxy.get('obfs') and proxy.get('obfs-password'):
                            params.append(f"obfs={proxy['obfs']}")
                        
                            params.append(f"obfs-password={proxy['obfs-password']}")
                    
                        if proxy.get('skip-cert-verify'):
                            params.append("insecure=1")
                    
                        if proxy.get('alpn'):
                            params.append(f"alpn={','.join(proxy['alpn']) if isinstance(proxy['alpn'], list) else proxy['alpn']}")
                    
                        # 组合最终URL
                        param_str = '?' + '&'.join(params) if params else ''
                        hy2_url = f"{base_url}{param_str}#{urllib.parse.quote(proxy['name'])}"
                        protocol_url.append(hy2_url + '\n')

                    except Exception as err:
                        print(proxy)
                        print(hy2_url)
                        print(f'HY2生成错误: {err} | 节点: {proxy.get("name", "未知")}')
                        continue


        
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
                    #print(ssr_proxy)
                    #print(protocol_url)
      
            yaml_content = ''.join(protocol_url)
            return yaml_content
        except Exception as err:
            
            print(f'yaml decode 发生 {err} 错误')
            
            
            
    def base64_decode(url_content): # Base64 转换为 URL 链接内容
        if '-' in url_content:
            url_content = url_content.replace('-', '+')
        elif '_' in url_content:
            url_content = url_content.replace('_', '/')
        #print(len(url_content))
        padding_needed = len(url_content) % 4
        if padding_needed:
            url_content += '=' * (4 - padding_needed) # 不是4的倍数后加= https://www.cnblogs.com/wswang/p/7717997.html
        
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
