


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
    #将URL编码的路径转换为Clash可读格式,自动处理多重编码（如%25252525）和Unicode转义
    def decode_url_path(url_path, max_decode=5):
        if not isinstance(url_path, str):
            url_path = str(url_path)

        # 循环解码多重编码（最多 5 次）
        decoded_path = url_path
        for _ in range(max_decode):
            if '%' not in decoded_path:
                break
            decoded_path = urllib.parse.unquote(decoded_path)

        # 处理可能的 UTF-8 编码错误（如双重编码的 Unicode）
        #try:
        #   decoded_path = decoded_path.encode('latin-1').decode('utf-8')
        #except (UnicodeEncodeError, UnicodeDecodeError):
        #    pass  # 如果已经是正常 Unicode，跳过

        # 规范化路径（确保以 / 开头）
        #if not decoded_path.startswith('/'):
        #    decoded_path = '/' + decoded_path

        return decoded_path


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
            try:
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
            except Exception as err:
                print(f"订阅内容解析错误{err}")                    
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

                raw_url_list = re.split(r'[\r\n]+', sub_content)

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
                    yaml_content=yaml.dump(loaded, default_flow_style=False, sort_keys=False, allow_unicode=True, default_style='"')
                    # 修复alpn缩进（新增的唯一修改）
                    yaml_content = re.sub(
                        r'^( *)(alpn:)\n( *)(- )',
                        r'\1\2\n\1  \4',
                        yaml_content,
                        flags=re.MULTILINE
                    )

                    
                    return yaml_content.replace('\'', '').replace('False', 'false').replace('True', 'true')
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

                        #if 'alpn' in proxy:
                        #    if isinstance(proxy['alpn'], str):
                        #        proxy['alpn'] = [x.strip() for x in proxy['alpn'].split(',')]
                        #    elif not isinstance(proxy['alpn'], list):
                        #        proxy['alpn'] = [str(proxy['alpn'])]
                    
                        
                        
                        proxies.append(proxy)
            
                result = {'proxies': proxies}
                # YAML生成（增加对alpn缩进的处理）
                yaml_content = yaml.dump(
                    result,
                    default_flow_style=False,
                    sort_keys=False,
                    allow_unicode=True,
                    width=750,
                    indent=2,
                    default_style='"'
                )
            
                # 修复alpn缩进（新增的唯一修改）
                yaml_content = re.sub(
                    r'^( *)(alpn:)\n( *)(- )',
                    r'\1\2\n\1  \4',
                    yaml_content,
                    flags=re.MULTILINE
                )

                
                if output:
                    return yaml_content.replace('\'', '').replace('False', 'false').replace('True', 'true')
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

                

                proxy_index = proxies_list.index(proxy)
                proxyname= proxy['name']
                
                #print(idid)
                
 
                
                if idid != '':
                    if re.findall(r'\d\d',idid)[0] == '99' :
                        idid = ''
                        
                    else :
                        idid = re.findall(r'\d\d',idid)[0]
                        proxyname=str(idid)
                proxyname = ''.join(re.findall(r'[a-zA-Z0-9]', proxyname)[:2]) if len(re.findall(r'[a-zA-Z0-9]', proxyname))>=2 else 'NO'
                
                if len(proxies_list) >=1000:
                    
                    proxy['name'] =f'{proxyname}-{proxy_index:0>4d}-{country_code}'
                elif len(proxies_list) <= 999:
                    proxy['name'] =f'{proxyname}-{proxy_index:0>3d}-{country_code}'
                
                
                if proxy['server'] != '127.0.0.1':
                    #proxy_str = str(proxy)
                    url_list.append(proxy)
            elif format_name_enabled == False:
                if proxy['server'] != '127.0.0.1':
                    #proxy_str = str(proxy)
                    url_list.append(proxy)
             
        yaml_content_dic = {'proxies': url_list}
        yaml_content_raw = yaml.dump(yaml_content_dic, default_flow_style=False, sort_keys=False, allow_unicode=True, width=750, indent=2) # yaml.dump 显示中文方法 https://blog.csdn.net/weixin_41548578/article/details/90651464 yaml.dump 各种参数 https://blog.csdn.net/swinfans/article/details/88770119
        
        #yaml_content_raw = re.sub(
        #    r'^(\s*)alpn:\s*(\r?\n)(\s*)- ',
        #    r'\1alpn:\2\1  - ',
        #    yaml_content_raw,
        #    flags=re.MULTILINE
        #)
            
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
                            tcp_opts = {}
                            if 'host' in vmess_config and vmess_config['host'] not in [None, '', 'null', 'Null',  '""']:
                                tcp_opts['headers'] = {'host': urllib.parse.unquote(vmess_config['host'])}
                            if 'path' in vmess_config and vmess_config['path'] not in [None, '', '/', 'null', 'Null',  '""']:
                                tcp_opts['path'] = vmess_config['path']
                            if tcp_opts:  # 仅在 tcp_opts 非空时添加
                                yaml_url['tcp-opts'] = tcp_opts
                    else:
                        print(f'vmess不支持的network_type:{network_type}')
                        print(line)
                        continue
                        

                    # 处理TLS配置
                    yaml_url['tls'] = vmess_config.get('tls', False) or network_type in ['h2', 'grpc']
                    url_list.append(yaml_url)
                

                except Exception as err:
                    #print(url_list)
                    print(line)
                    print(f'yaml_encode 解析 vmess 节点发生错误: {err}')
                    continue

            elif 'vless://' in line:
                try:
                    # 分割基础部分和参数
                    url_part = line.replace('vless://', '').split('#', 1)
                    base_part = url_part[0].split('?', 1)
                
                    # 提取UUID和服务端信息（安全处理@）
                    auth_part = base_part[0].split('@')
                    if len(auth_part) != 2:
                        print(f"⚠️ 格式错误：只能有1个@符号 | {line}")
                        continue
                
                    uuid = auth_part[0]
                    server_port = auth_part[1].replace('/', '').split(':')
                    if len(server_port) < 2:
                        print(f"⚠️ 格式错误：缺少端口 | {line}")
                        continue
                
                    server, port = server_port[0], server_port[1]

                    # === 新增UUID格式验证 ===
                    if not re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', uuid, re.I):
                        print(f"⚠️ 无效UUID：{uuid} | 节点已跳过")
                        continue
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
                            if name:
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
                    yaml_node['tls'] = security_type in ('tls', 'reality')  # 明确判断
                    # 强制清理无效参数
                    raw_params.pop('encryption', None)
                    if not yaml_node['tls']:
                        raw_params.pop('fp', None)
                        raw_params.pop('sni', None)
                    if security_type == 'reality':
                        pbk = urllib.parse.unquote(get_param_priority('pbk', 'PublicKey', 'publicKey', default=''))
                        sid = get_param_priority('sid', 'ShortId', 'shortId', default='')
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
                        
                        #if path.count('@') >1 or path.count('%40') >1:
                        #    print(f'vless节点格式错误，line:{line}')
                        #    continue
                        ws_host = (
                            get_param_priority('Host', 'host', 'HOST') or
                            sni or
                            server
                        )
                        yaml_node['ws-opts'] = {
                            'path': '/' + sub_convert.decode_url_path(get_param_priority('path', 'Path', 'PATH', default='/')).lstrip('/').replace(':', '%3A').replace(',', '%2C').replace('@', '%40'),
                            'headers': {'Host': ws_host}
                        }
                
                    elif network_type == 'httpupgrade' or network_type == 'http' or network_type == 'xhttp' :
                        params = {}
                        http_opts = yaml_node.get('http-opts', {})
                        path = '/' + sub_convert.decode_url_path(http_opts.get('path', '')).lstrip('/')
                        #if path.count('@') >1 or path.count('%40') >1:
                        #    print(f'vless节点格式错误，line:{line}')
                        #    continue
                        params['type'] = 'httpupgrade'
                        params['path'] = '/' + sub_convert.decode_url_path(http_opts.get('path', '/')).lstrip('/').replace(':', '%3A').replace(',', '%2C').replace('@', '%40')
                        if 'host' in http_opts.get('headers', {}):
                            params['host'] = http_opts['headers']['host']
                        elif 'sni' in yaml_node:
                            params['host'] = yaml_node['sni']
                    # 2. gRPC处理
                    elif network_type == 'grpc':
                        yaml_node['grpc-opts'] = {
                            'grpc-service-name': sub_convert.decode_url_path(get_param_priority('serviceName', 'servicename', default='')).replace(':','%3A').replace(',', '%2C').replace('@', '%40')
                        }

                    # 3. HTTP/2处理
                    elif network_type == 'h2':

                        host=get_param_priority('host', 'Host', 'HOST', default='').split(',')
                        path= '/' + sub_convert.decode_url_path(get_param_priority('path', 'Path', 'PATH', default='')).lstrip('/').replace(':','%3A').replace(',', '%2C').replace('@', '%40')
                        #if path.count('@') >1 or path.count('%40') >1:
                        #    print(f'vless节点格式错误，line:{line}')
                        #    continue                


                        if host or path:
                            h2_opts = {}
                            if host:
                                h2_opts['host'] = host
                            if path:
                                h2_opts['path'] = '/' + sub_convert.decode_url_path(get_param_priority('path', 'Path', 'PATH', default='/')).lstrip('/').replace(':', '%3A').replace(',', '%2C').replace('@', '%40')
                            if h2_opts:  # 仅在 tcp_opts 非空时添加
                                yaml_node['h2-opts'] = h2_opts
                        

                    # 4. TCP处理（含HTTP伪装）
                    elif network_type == 'tcp':
                        header_type = get_param_priority('headerType', 'headertype', default='')
                        host = get_param_priority('Host', 'host', 'HOST', default='')
                        path = sub_convert.decode_url_path(get_param_priority('path', 'Path', 'PATH', default=''))
                        #if path.count('@') >1 or path.count('%40') >1:
                        #    print(f'vless节点格式错误，line:{line}')
                        #    continue                       
                        if host or path:
                            tcp_opts = {}
                            if host:
                                tcp_opts['headers'] = {'Host': host.split(',')}
                            if path:
                                tcp_opts['path'] = '/' + sub_convert.decode_url_path(get_param_priority('path', 'Path', 'PATH', default='/')).lstrip('/').replace(':', '%3A').replace(',', '%2C').replace('@', '%40')
                            if tcp_opts:  # 仅在 tcp_opts 非空时添加
                                yaml_node['tcp-opts'] = tcp_opts
                    else:
                        print(f'vless不支持的network_type:{network_type}')
                        print(line)
                        continue

                    url_list.append(yaml_node)
                    print(f'添加vless节点{yaml_node}')

                except Exception as e:
                    import traceback
                    print("❌ 发生错误:", traceback.format_exc())  # 打印完整堆栈
                    print("原始行内容:", line)
                    continue
        
   
            elif 'ss://' in line and 'vless://' not in line and 'vmess://' not in line:
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
                        'rc4-md5', 'bf-cfb', 'chacha20', 'chacha20-ietf',
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
                        plugin_mode = urllib.parse.unquote(re.compile('obfs=(.*?);').findall(plugin_list)[0])
                        plugin_host = urllib.parse.unquote(re.compile('obfs-host=(.*?);').findall(plugin_list)[0])
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
            
                        plugin_mode = urllib.parse.unquote(re.compile('mode=(.*?);').findall(plugin_list)[0])
                        plugin_host = urllib.parse.unquote(re.compile('host=(.*?);').findall(plugin_list)[0])
                        plugin_host = plugin_host if plugin_host else yaml_url['server']
                        plugin_path = urllib.parse.unquote(re.compile('path=(.*?);').findall(plugin_list)[0])
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
                    #print(yaml_url)
                    print(f'line:{line}')
                    print(f'yaml_encode 解析 ss 节点发生错误2: {err}')
                    continue

            
            elif 'hy://' in line:
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
                        'auth_str': auth,
                        'up': '20 Mbps',
                        'down': '50 Mbps',
                        'protocol': 'udp',
                        'udp': True,
                        'skip-cert-verify': False
                    }

                    # 3. 处理查询参数（关键修改点）
                    if len(base_part) > 1:
                        params = {}
                        for param in base_part[1].split('&'):
                            if '=' in param:
                                key, val = param.split('=', 1)
                                params[key.lower()] = val



                        # 其他参数映射
                        param_mappings = {
                            'obfs': ('obfs', str),
                            'obfs-password': ('obfs-password', str),
                            'sni': ('sni', str),
                            'insecure': ('skip-cert-verify', lambda x: x == '1')
                        }
         
                        for param_key, (config_key, converter) in param_mappings.items():
                            if param_key in params:
                                config[config_key] = converter(params[param_key])

                        # 特殊处理alpn参数（兼容字符串和列表）
                        if 'alpn' in params:
                            alpn_val = params['alpn']
                            if isinstance(alpn_val, str):
                                config['alpn'] = [x.strip() for x in alpn_val.split(',')]
                            elif isinstance(alpn_val, list):
                                config['alpn'] = alpn_val

                    # 4. 最终校验alpn格式
                    #if not isinstance(config['alpn'], list):
                    #    config['alpn'] = [str(config['alpn'])]
                    #print(config)

                    url_list.append(config)
                    
                except Exception as err:
                    #print(config)
                    print(line)
                    print(f'Hysteria1解析错误: {err} | 内容: {line[:50]}...')
                    continue
            
            
            elif 'hy2://' in line:
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
                    #print(config)
                    print(line)
                    print(f'HY2解析错误: {err} | 内容: {line[:50]}...')
                    continue

  
                
            elif 'ssr://' in line:
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
                    #print(yaml_url)
                    print(line)
                    print(f'yaml_encode 解析 ssr 节点发生错误: {err}')
                    
                    continue           
          
           
            elif 'trojan://' in line:
                try:
                    # 先进行URL解码处理特殊字符
                    line = urllib.parse.unquote(line)
        
                    # 分割节点信息和备注
                    url_part = line.replace('trojan://', '').split('#', 1)
                    yaml_url = {
                        'name': url_part[1] if len(url_part) > 1 else 'trojan-node',
                        'type': 'trojan',
                        'udp': True,
                        'skip-cert-verify': True,
                        'tls': True  # 默认启用TLS
                    }
            
                    # 分割认证信息和参数
                    server_part = url_part[0].split('?', 1)
                    auth_part = server_part[0].split('@', 1)
                    if len(auth_part) != 2:
                        print(f'trojan节点错误：{line}')
                        
                        continue
            
                    # 处理服务器地址和端口（兼容末尾带/的情况）
                    server_port = auth_part[1].replace('/', '').split(':')
                    yaml_url.update({
                        'password': auth_part[0],
                        'server': server_port[0],
                        'port': int(server_port[1])
                    })

                    # 解析查询参数
                    if len(server_part) > 1:
                        for param in server_part[1].split('&'):
                            if '=' not in param:
                                print(f'trojan节点错误：{line}')
                                continue
                    
                            key, val = param.split('=', 1)
                            key = key.lower()
                
                            # 处理security参数
                            if key == 'security':
                                yaml_url['tls'] = val.lower() == 'tls'
                
                            # 处理sni参数
                            elif key == 'sni':
                                yaml_url['sni'] = val
                
                            # 处理传输类型
                            elif key == 'type':
                                yaml_url['network'] = val.lower()
                                if val.lower() == 'ws':
                                    yaml_url['ws-opts'] = {
                                        'path': '/',
                                        'headers': {'Host': yaml_url.get('sni', yaml_url['server'])}
                                    }
                
                            # 处理ws路径
                            elif key == 'path' and 'ws-opts' in yaml_url:
                                yaml_url['ws-opts']['path'] = val
                
                            # 处理ws的host头
                            elif key == 'host' and 'ws-opts' in yaml_url:
                                yaml_url['ws-opts']['headers']['Host'] = val

                    # 直接添加到结果列表（不再检查密码长度）
                    url_list.append(yaml_url)
        
                    # 调试日志（可选）
                    #print(f"已处理Trojan节点: {yaml_url['name']}")
        

                except Exception as err:
                    #print(yaml_url)
                    print(line)
                    print(f'yaml_encode 解析 trojan 节点发生错误: {err}')
                    continue
            else:
                print(f'不支持的节点类型,line:{line}')
                
                continue
                
        yaml_content_dic = {'proxies': url_list}
        yaml_content_raw = yaml.dump(yaml_content_dic, default_flow_style=False, sort_keys=False, allow_unicode=True, width=750, indent=2)
        yaml_content = sub_convert.format(yaml_content_raw)
        return yaml_content
    def base64_encode(url_content): # 将 URL 内容转换为 Base64
        base64_content = base64.b64encode(url_content.encode('utf-8')).decode('ascii')
        return base64_content

    def yaml_decode(url_content): # YAML 文本转换为 URL 链接内容
        
        
        #将Clash路径编码为URL安全格式，自动防止双重编码并保留特殊字符
        def encode_clash_path(clash_path):
            if not isinstance(clash_path, str):
                clash_path = str(clash_path)

            # 1. 先解码防止双重编码
            decoded_path = sub_convert.decode_url_path(clash_path)
            print(f"解码后路径: {decoded_path}")  # 调试输出

            
            encoded_path = urllib.parse.quote(decoded_path, safe="/?&=")
            print(f"最终编码路径: {encoded_path}")  # 调试输出
            return encoded_path
        
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
                        #print(vmess_proxy)
                        print(f'VMess解码错误: {e} | 节点: {proxy.get("name", "未知")}')
                        continue





                
                elif proxy['type'] == 'vless':
                    try:
                        # === 基础参数校验 ===
                        for field in ['server', 'port', 'uuid']:
                            if field not in proxy:
                                raise ValueError(f"Missing required field: {field}")

                        # === 参数获取（兼容大小写） ===
                        def get_any_case(d, keys, default=None):
                            """字典键名大小写不敏感查找"""
                            if not isinstance(d, dict):
                                return default
                            for k in keys:
                                if k in d:
                                    return d[k]
                                for dk, dv in d.items():
                                    if str(dk).lower() == str(k).lower():
                                        return dv
                            return default

                        # 获取核心参数
                        network = get_any_case(proxy, ['network'], 'tcp').lower()
                        sni = get_any_case(proxy, ['sni', 'servername'], proxy['server'])
                        security = 'tls' if proxy.get('tls') else 'none'
                        port = str(proxy['port']).replace('/','')

                        params = {
                            'type': network,
                            'security': security,
                            'sni': sni
                        }

                        # 1. WebSocket (ws)
                        if network == 'ws':
                            ws_opts = get_any_case(proxy, ['ws-opts'], {})
                            raw_path = get_any_case(ws_opts, ['path'], '/')
                            print(f"原始路径: {raw_path}")  # 调试输出
                            encoded_path = '/' + encode_clash_path(raw_path).lstrip('/').replace(':', '%3A')
                            print(f"编码后路径: {encoded_path}")  # 调试输出
                            headers = get_any_case(ws_opts, ['headers'], {})
                            params.update({
                                'path': encoded_path,
                                'host': get_any_case(headers, ['Host'], sni)
                            })

                        # 2. HTTP/2 (h2)
                        elif network == 'h2':
                            h2_opts = get_any_case(proxy, ['h2-opts'], {})
                            raw_path = get_any_case(h2_opts, ['path'], '/')
                            hosts = get_any_case(h2_opts, ['host'], [sni])
                            params.update({
                                'path': '/' + encode_clash_path(raw_path).lstrip('/').replace(':', '%3A'),
                                'host': ','.join(hosts) if isinstance(hosts, list) else hosts
                            })

                        # 3. gRPC (grpc) - 无path参数
                        elif network == 'grpc':
                            grpc_opts = get_any_case(proxy, ['grpc-opts'], {})
                            params['serviceName'] = encode_clash_path(get_any_case(grpc_opts, ['grpc-service-name'], '')).replace(':', '%3A')

                        # 4. TCP (tcp)
                        elif network == 'tcp':
                            tcp_opts = get_any_case(proxy, ['tcp-opts'], {})
                            raw_path = get_any_case(tcp_opts, ['path'], '/')
                            headers = get_any_case(tcp_opts, ['headers'], {})
                            if raw_path or headers:
                                params['header'] = {
                                    'type': 'http',
                                    'request': {
                                        'path': '/' + encode_clash_path(raw_path).lstrip('/').replace(':', '%3A'),
                                        'headers': {'Host': get_any_case(headers, ['host'], sni)}
                                    }
                                }

                        # 5. HTTP Upgrade (httpupgrade)
                        elif network == 'httpupgrade' or network == 'http' or network == 'xhttp':
                            
                            http_opts = get_any_case(proxy, ['http-opts'], {})
                            raw_path = get_any_case(http_opts, ['path'], '/')
                            headers = get_any_case(http_opts, ['headers'], {})
                            params.update({
                                'type': 'httpupgrade',
                                'path': '/' + encode_clash_path(raw_path).lstrip('/').replace(':', '%3A'),
                                'host': get_any_case(headers, ['host'], sni)
                            })

                        # === Reality 支持 ===
                        reality_opts = get_any_case(proxy, ['reality-opts'], {})
                        if reality_opts:
                            params.update({
                                'security': 'reality',
                                'pbk': get_any_case(reality_opts, ['public-key', 'pbk'], ''),
                                'sid': get_any_case(reality_opts, ['short-id', 'sid'], ''),
                                'flow': get_any_case(proxy, ['flow'], '')
                            })

                        # === 生成查询字符串 ===
                        query_str = '&'.join(
                            f"{k}={encode_clash_path(str(v))}" if not isinstance(v, dict) else f"{k}={json.dumps(v)}"
                            for k, v in params.items()
                            if v not in (None, "", False, {} ,"none")
                        ) + '&'

                        # === 构建最终URL ===
                        vless_url = f"vless://{proxy['uuid']}@{proxy['server']}:{proxy['port']}?{query_str}#{urllib.parse.quote(proxy['name'])}"
                        protocol_url.append(vless_url + '\n')
                        print(f'已添加节点{vless_url}')

                    except Exception as e:
                        print(f"❌ 处理VLess节点时发生错误: {e}")
                        print(f"完整节点配置: {proxy}")
                        import traceback
                        traceback.print_exc()  # 打印完整堆栈
                        continue
                
                
                elif proxy['type'] == 'ss':
                    try:
                        if 'plugin' not in proxy:
                            
                            # 标准格式：仅对 "method:password" 进行 Base64 编码
                            ss_base64_decoded = str(proxy['cipher']) + ':' + urllib.parse.quote(str(proxy['password']))
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
                            ss_base64 = sub_convert.base64_encode(f"{proxy['cipher']}:{urllib.parse.quote(proxy['password'])}")
    
                            # 完整标准格式链接
                            ss_proxy = (
                                f"ss://{ss_base64}@{proxy['server']}:{proxy['port']}"
                                f"/?plugin={proxy['plugin']}-local%3B{ssplugin}"
                                f"#{urllib.parse.quote(proxy['name'])}\n"
                            )
                        protocol_url.append(ss_proxy)
                    except Exception as err:
                        print(proxy)
                        #print(ss_proxy)
                        print(f'SS生成错误: {err} | 节点: {proxy.get("name", "未知")}')
                        continue
                
                elif proxy['type'] == 'trojan': # Trojan 节点提取, 由 trojan_proxy 中参数再加上 # 加注释(URL_encode) # trojan Go https://p4gefau1t.github.io/trojan-go/developer/url/

                    try:
                        # 基础参数
                        base_url = f"trojan://{proxy['password']}@{proxy['server']}:{proxy['port']}"
                        params = []
        
                        # TLS 配置
                        params.append(f"security={'tls' if proxy.get('tls', True) else 'none'}")
        
                        # SNI 配置
                        if 'sni' in proxy:
                            params.append(f"sni={proxy['sni']}")
        
                        # 传输协议
                        network_type = proxy.get('network', 'tcp')
                        if network_type != 'tcp':
                            params.append(f"type={network_type}")
            
                            # WebSocket 配置
                            if network_type == 'ws':
                                if 'ws-opts' in proxy:
                                    ws_opts = proxy['ws-opts']
                                    if 'path' in ws_opts:
                                        params.append(f"path={ws_opts['path']}")
                                    if 'headers' in ws_opts and 'Host' in ws_opts['headers']:
                                        params.append(f"host={ws_opts['headers']['Host']}")
            
                            # gRPC 配置
                            elif network_type == 'grpc':
                                if 'grpc-opts' in proxy and 'grpc-service-name' in proxy['grpc-opts']:
                                    params.append(f"serviceName={proxy['grpc-opts']['grpc-service-name']}")

                        # 组合 URL
                        query_str = '&'.join(params)
                        trojan_url = f"{base_url}?{query_str}#{urllib.parse.quote(proxy['name'])}\n"
                        protocol_url.append(trojan_url)
                    except Exception as err:
                        print(f'yaml_decode 生成 trojan 节点发生错误: {err}')
                        print(f'问题节点: {proxy}')
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
                        #print(hy1_url)
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
                        #print(hy2_url)
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
        url_content = str(url_content)
        if '-' in url_content:
            url_content = url_content.replace('-', '+')
        elif '_' in url_content:
            url_content = url_content.replace('_', '/')
        
        padding_needed = len(url_content) % 4
        if padding_needed:
            url_content += '=' * (4 - padding_needed)
        
        try:
            base64_content = base64.b64decode(url_content.encode('utf-8')).decode('utf-8','ignore')
            base64_content_format = base64_content
            return base64_content_format
        except UnicodeDecodeError:
            try:
                base64_content = base64.b64decode(url_content)
                base64_content_format = base64_content
                return base64_content
            except Exception as e:
                raise ValueError(f"解码失败: 原始内容={url_content}, 错误类型={type(e).__name__}, 错误详情={str(e)}") from e
        except base64.binascii.Error as e:
            raise ValueError(f"Base64解码错误: 处理后内容={url_content}, 错误类型={type(e).__name__}, 需要填充={padding_needed}, 错误详情={str(e)}") from e
        except Exception as e:
            raise ValueError(f"未知解码错误: 原始内容={url_content}, 错误类型={type(e).__name__}, 错误详情={str(e)}") from e
if __name__ == '__main__':
    
    subscribe = 'https://raw.githubusercontent.com/imyaoxp/freenode/master/sub/sub_merge.txt'
    output_path = './output.txt'

    content = sub_convert.convert(subscribe, 'url', 'YAML')

    file = open(output_path, 'w', encoding= 'utf-8')
    file.write(content)
    file.close()
    print(f'Writing content to output.txt\n')
