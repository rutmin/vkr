import csv
import ipaddress
import getpass
import os
import re
import telnetlib
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from itertools import repeat
from sys import platform as show_platform
import argparse


def cisco_configuration_mode_authorizer(telnet, enable):
    telnet.write(b'\n')
    time.sleep(0.1)
    output = telnet.read_very_eager().decode()
    if re.search('>', output):
        telnet.write(b'enable\n')
        telnet.read_until(b':')
        telnet.write(enable)
        time.sleep(0.5)
    else:
        telnet.write(b'conf t\n')
        time.sleep(0.5)
        output = telnet.read_very_eager().decode()
        if re.search('% Invalid input', output):
            telnet.write(b'enable\n')
            telnet.read_until(b':')
            time.sleep(0.5)
            telnet.write(enable)
            time.sleep(0.5)
    time.sleep(0.1)
    output = telnet.read_very_eager().decode()
    if re.search('config', output) is None:
        telnet.write(b'conf t\n')
        time.sleep(0.1)


def create_dir(name):
    if not os.path.exists(f'{name}'):
        os.mkdir(f'{name}')


def write_configuration_telnet(telnet, device, version, _ip, tcp_port):
    now = datetime.now()
    time.sleep(0.1)
    telnet.read_very_eager()
    if device == 'ios':
        time.sleep(2)
        telnet.write(b'show configuration\n')
        if re.search('ios_l2', version):
            time.sleep(4)
        time.sleep(7)
    elif device == 'junos':
        telnet.write(b'show configuration | display set\n')
        time.sleep(5)
    elif device == 'xos':
        telnet.write(b'show configuration\n')
        time.sleep(3)
    telnet.read_until(b'show configuration')
    if device == 'junos':
        telnet.read_until(b'set')
    time.sleep(0.1)
    com = telnet.read_very_eager().decode()
    if device == 'ios':
        com = re.sub(r'(!\r\n)', '', com)
    create_dir('configs')
    with open(f'configs/{device}_{_ip}_{tcp_port}_{now.date()}-'
              f'{now.hour}.{now.minute}.{now.second}.txt', 'w') as f0:
        f0.write(com)
    # with open(f'configs/{_ip}_{tcp_port}.txt', 'w') as f0:
    #    f0.write(com)


def telnet_closer(device, telnet):
    if ('junos' or 'juniper') in device:
        time.sleep(0.5)
        telnet.write(b'exit\n')
        time.sleep(1.2)
    telnet.write(b'exit\n')
    telnet.close()


def who_is_telnet(telnet, login, password):
    welcome_page = telnet.read_until(b':').decode()
    time.sleep(0.1)
    if (re.search(r'[Ll](ogin:)|[Uu](sername:)', welcome_page)) or \
            (re.search(r'[Ll](ogin:)|[Uu](sername:)', telnet.read_very_eager())):
        telnet.write(login)
        time.sleep(1)
        telnet.write(password)
        time.sleep(3)
        welcome_page = telnet.read_very_eager().decode()
        if re.search('%', welcome_page):  # juniper
            time.sleep(0.5)
            telnet.write(b'clear\n')
            time.sleep(0.5)
            telnet.write(b'cli\n')
            telnet.read_until(b'>')
            telnet.write(b'set cli screen-length 0\nshow version\n')
            time.sleep(1)
        elif re.search(r'[^(<tab>)]\w+>', welcome_page):  # cisco 2
            time.sleep(0.1)
            telnet.read_very_eager()
            telnet.write(b'terminal length 0\nshow version\n')
            time.sleep(3)
        else:
            telnet.write(b'show privilege\n')
            time.sleep(0.5)
            welcome_page = telnet.read_very_eager().decode()
            welcome_page = re.search(r'is \d{1,2}', welcome_page)
            if welcome_page:  # cisco 3
                telnet.write(b'terminal length 0\nshow version\n')
                time.sleep(3)
            else:  # extreme
                telnet.write(b'disable clipaging\nshow version\n')
                time.sleep(1)
    else:
        telnet.write(password)
        time.sleep(0.5)
        telnet.read_until(b'>')
        telnet.write(b'terminal length 0\nshow version\n')
        time.sleep(2)
    version = telnet.read_very_eager().decode().lower()
    device = re.search('ios|junos|xos', version).group()
    return device, version


def edit_configuration_on_device_telnet(_ip, password, login, command, input_config, ena=b'\n', tcp_port=23):
    telnet = telnetlib.Telnet(_ip, tcp_port)
    telnet.write(b'\x0d')
    com, ind = '', 0
    device, version = who_is_telnet(telnet, login, password)
    if command == '1':  # VLAN
        if device == 'ios':
            cisco_configuration_mode_authorizer(telnet, ena)
            for input_data in input_config:
                if re.search('ios_l2', version):
                    com = f'vlan {input_data[2]}\nname {input_data[3]}\nexit\n'.encode('ascii')
                    telnet.write(com)
                    if input_data[4] == 'tagged':
                        com = f'interface gig {input_data[0]}\nswitchport mode trunk\n' \
                              f'switchport trunk allowed vlan add {input_data[2]}\n' \
                              f'exit\n\n\n'.encode('ascii')
                    else:
                        com = f'interface gig {input_data[0]}\nswitchport mode access\n' \
                              f'switchport access vlan {input_data[2]}\nexit\n\n\n'.encode('ascii')
                    telnet.write(com)
                elif input_data[1]:
                    com = f'interface gi {input_data[0]}.{input_data[1]}\n' \
                          f'encapsulation dot1q {input_data[2]}\n'.encode('ascii')
                    telnet.write(com)
                    telnet.write(b'exit\n')
            telnet.write(b'exit\n\n\nwrite mem\n')
            time.sleep(3)
        elif device == 'junos':
            telnet.write(b'configure\n')
            for input_data in input_config:
                if ('qfx' or 'ex') in version:
                    com = f'set vlans {input_data[3]} vlan-id {input_data[2]}\n'.encode('ascii')
                    telnet.write(com)
                    if input_data[1]:
                        com = f'edit interface ge-{input_data[0]} unit {input_data[1]} ' \
                              f'family ethernet-switching\n'.encode('ascii')
                    else:
                        com = f'edit interface ge-{input_data[0]} unit 0 family ethernet-switching\n'.encode('ascii')
                    telnet.write(com)
                    if input_data[5]:  # ELS devices
                        if input_data[4] == 'tagged':
                            telnet.write(b'set interface-mode trunk\n')
                            time.sleep(0.5)
                            com = f' set vlan member {input_data[3]}\n'.encode('ascii')
                        else:
                            telnet.write(b'set interface-mode access\n')
                            time.sleep(0.5)
                            com = f'set vlan member {input_data[3]}\n'.encode('ascii')
                    else:
                        if input_data[4] == 'tagged':
                            telnet.write(b'set port-mode trunk\n')
                            time.sleep(0.5)
                            com = f'set vlan member {input_data[3]}\n'.encode('ascii')
                        else:
                            telnet.write(b'set port-mode access\n')
                            time.sleep(0.5)
                            com = f'set vlan member {input_data[3]}\n'.encode('ascii')
                else:
                    com = f'set interfaces vlan.{input_data[2]}\n'.encode('ascii')
                    telnet.write(com)
                    com = f'edit interfaces ge-{input_data[0]}\n'.encode('ascii')
                    telnet.write(com)
                    time.sleep(0.1)
                    telnet.write(b'set vlan-tagging\n')
                    com = f'set unit {input_data[1]} vlan-id {input_data[2]}\n'.encode('ascii')
                telnet.write(com)
                time.sleep(0.5)
                telnet.write(b'exit\n')
                time.sleep(0.5)
            telnet.write(b'top\ncommit\n')
            time.sleep(1)
            telnet.write(b'exit\n')
        elif device == 'xos':
            for input_data in input_config:
                com = f'create vlan {input_data[3]}\n'.encode('ascii')
                telnet.write(com)
                com = f'configure vlan {input_data[3]} tag {input_data[2]}\n'.encode('ascii')
                telnet.write(com)
                com = f'configure vlan {input_data[3]} add port {input_data[0]} {input_data[4]}\n'.encode('ascii')
                telnet.write(com)
            telnet.write(b'save\ny\n')
            time.sleep(1)
    elif command == '2':  # ACL
        if device == 'ios':
            cisco_configuration_mode_authorizer(telnet, ena)
            for input_data in input_config:
                if input_data[0]:
                    ind = input_config.index(input_data)
                    com = f'ip access-list extended {input_data[0]}\n'.encode('ascii')
                    telnet.write(com)
                    time.sleep(0.2)
                if input_data[3] != 'any':
                    src_ = ipaddress.ip_network(ipaddress.ip_interface(input_data[3]).network). \
                        with_hostmask.replace('/', ' ')
                else:
                    src_ = 'any'
                if input_data[4] != 'any':
                    dst_ = ipaddress.ip_network(ipaddress.ip_interface(input_data[4]).network). \
                        with_hostmask.replace('/', ' ')
                else:
                    dst_ = 'any'
                if input_data[5]:
                    com = f'{input_data[1]} {input_data[2]} {src_} {dst_} eq {input_data[5]}\n'.encode('ascii')
                else:
                    com = f'{input_data[1]} {input_data[2]} {src_} {dst_}\n'.encode('ascii')
                telnet.write(com)
                if ((input_config.index(input_data) + 1) == len(input_config)) or \
                        input_config[input_config.index(input_data) + 1][0]:
                    com = f'{input_config[ind][6]} ip any any\nexit\n'.encode('ascii')
                    telnet.write(com)
            telnet.write(b'exit\nwrite mem\n')
            time.sleep(3)
        elif device == 'junos':
            telnet.write(b'configure\nedit firewall family inet\n')
            for input_data in input_config:
                if input_data[0]:
                    ind = input_config.index(input_data)
                if input_data[2] == ('ospf' or 'tcp' or 'udp'):
                    com = f'set fi {input_config[ind][0]} te {input_config.index(input_data)} ' \
                          f'from protocol {input_data[1]}\n'.encode('ascii')
                    if input_data[3] != 'any':
                        src_ = ipaddress.ip_network(ipaddress.ip_interface(input_data[3]).network)
                        com = f'set fi {input_config[ind][0]} te {input_config.index(input_data)} ' \
                              f'fr source-a {src_}\n'.encode('ascii')
                        telnet.write(com)
                        time.sleep(0.2)
                    if input_data[4] != 'any':
                        src_ = ipaddress.ip_network(ipaddress.ip_interface(input_data[4]).network)
                        com = f'set fi {input_config[ind][0]} te {input_config.index(input_data)} ' \
                              f'fr destination-a {src_}\n'.encode('ascii')
                    telnet.write(com)
                    time.sleep(0.2)
                elif (input_data[2] == 'ip') and (input_data[3] != 'any'):
                    src_ = ipaddress.ip_network(ipaddress.ip_interface(input_data[3]).network)
                    com = f'set fi {input_config[ind][0]} te {input_config.index(input_data)} ' \
                          f'fr source-a {src_}\n'.encode('ascii')
                    telnet.write(com)
                    time.sleep(0.2)
                if input_data[5]:
                    com = f'set fi {input_config[ind][0]} te {input_config.index(input_data)} ' \
                          f'fr port {input_data[5]}\n'.encode('ascii')
                    telnet.write(com)
                    time.sleep(0.2)
                if input_data[4] != 'any':
                    src_ = ipaddress.ip_network(ipaddress.ip_interface(input_data[4]).network)
                    com = f'set fi {input_config[ind][0]} te {input_config.index(input_data)} ' \
                          f'fr destination-a {src_}\n'.encode('ascii')
                    telnet.write(com)
                    time.sleep(0.2)
                if input_data[1] == 'permit':
                    com = f'set fi {input_config[ind][0]} te {input_config.index(input_data)} ' \
                          f'then accept\n'.encode('ascii')
                else:
                    com = f'set fi {input_config[ind][0]} te {input_config.index(input_data)} ' \
                          f'then discard\n'.encode('ascii')
                telnet.write(com)
                time.sleep(0.2)
                if ((input_config.index(input_data) + 1) == len(input_config)) or \
                        input_config[input_config.index(input_data) + 1][0]:
                    if input_config[ind][6] == 'permit':
                        com = f'set fi {input_config[ind][0]} te {len(input_config)} ' \
                              f'then accept\n'.encode('ascii')
                    else:
                        com = f'set fi {input_config[ind][0]} te {len(input_config)} ' \
                              f'then discard\n'.encode('ascii')
                    telnet.write(com)
                    time.sleep(0.2)
            telnet.write(b'top\ncommit\n')
            time.sleep(1)
            telnet.write(b'exit\n')
        elif device == 'xos':
            for input_data in input_config:
                if input_data[0]:
                    ind = input_config.index(input_data)
                    time.sleep(0.2)
                    telnet.write(b'edit policy ')
                    com = f'{input_config[ind][0]}\ni'.encode('ascii')
                    telnet.write(com)
                    time.sleep(0.5)
                com = f'entry {input_config.index(input_data)}'.encode('ascii')
                telnet.write(com)
                telnet.write(b' {\n  if {\n')
                if input_data[2] != 'ip':
                    com = f'    protocol {input_data[2]};\n'.encode('ascii')
                    telnet.write(com)
                    time.sleep(0.2)
                if input_data[3] != 'any':
                    com = f'    source-address {input_data[3]};\n'.encode('ascii')
                    telnet.write(com)
                    time.sleep(0.2)
                if input_data[4] != 'any':
                    com = f'    destination-address {input_data[4]};\n'.encode('ascii')
                    telnet.write(com)
                    time.sleep(0.2)
                if input_data[5]:
                    com = f'    destination-port {input_data[5]};\n'.encode('ascii')
                    telnet.write(com)
                    time.sleep(0.2)
                telnet.write(b'  }\n  then {\n')
                time.sleep(0.2)
                com = f'    {input_data[1]};\n'.encode('ascii')
                telnet.write(com)
                telnet.write(b'  }\n}\n')
                time.sleep(0.2)
                if ((input_config.index(input_data) + 1) == len(input_config)) or \
                        input_config[input_config.index(input_data) + 1][0]:
                    telnet.write(b'entry finally{\n  if{\n  }\n  then {\n')
                    time.sleep(0.2)
                    com = f'    {input_config[ind][6]};\n'.encode('ascii')
                    telnet.write(com)
                    telnet.write(b'  }\n}\x1B:wq\n')
                    time.sleep(0.2)
                    com = f'check policy {input_config[ind][0]}\n'.encode('ascii')
                    telnet.write(com)
            telnet.write(b'save\ny\n')
    elif command == '4':  # OSPF
        if device == 'ios':
            cisco_configuration_mode_authorizer(telnet, ena)
            com = f'router ospf 1\n'.encode('ascii')
            telnet.write(com)
            com = f'router-id {input_config[0][0]}\n'.encode('ascii')
            telnet.write(com)
            for input_data in input_config:
                com = f'do show interfaces gig {input_data[1]}\n'.encode('ascii')
                telnet.write(com)
                telnet.read_until(b'show interfaces')
                com = telnet.read_until(b'MTU').decode()
                com = re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}', com).group()
                com = ipaddress.ip_network(ipaddress.ip_interface(f'{com}').network)
                com = com.with_hostmask.replace('/', ' ')
                com = f'network {com} area {input_data[2]}\n'.encode('ascii')
                telnet.write(com)
            telnet.write(b'exit\nexit\n\nwrite mem\n')
        elif device == 'junos':
            telnet.write(b'configure\n')
            com = f'set routing-options router-id {input_config[0][0]}\n'.encode('ascii')
            telnet.write(com)
            for input_data in input_config:
                com = f'set protocol ospf area {input_data[2]} interface ge-{input_data[1]}\n'.encode('ascii')
                telnet.write(com)
                time.sleep(0.1)
            telnet.write(b'commit\nexit\n')
        elif device == 'xos':
            com = f'config ospf router {input_config[0][0]}\n'.encode('ascii')
            telnet.write(com)
            telnet.write(b'enable ospf\n')
            for input_data in input_config:
                com = f'create ospf area {input_data[2]}\n'.encode('ascii')
                telnet.write(com)
                com = f'show vlan port {input_data[1]} detail\n'.encode('ascii')
                telnet.write(com)
                telnet.read_until(b'with name ')
                com = telnet.read_until(b'created').decode()
                com = com.split()[0]
                com = f'config ospf add {com} area {input_data[2]}\n'.encode('ascii')
                telnet.write(com)
            telnet.write(b'save\ny\n')
    elif command == '5':  # IP
        if device == 'ios':
            cisco_configuration_mode_authorizer(telnet, ena)
            for input_data in input_config:
                if input_data[1]:
                    com = f'interface gi {input_data[0]}.{input_data[1]}\n'.encode('ascii')
                else:
                    com = f'interface gi {input_data[0]}\n'.encode('ascii')
                telnet.write(com)
                com = f'ip addr {ipaddress.ip_interface(input_data[2]).ip} ' \
                      f'{ipaddress.ip_interface(input_data[2]).netmask}\n'.encode('ascii')
                telnet.write(com)
                telnet.write(b'exit\nexit\nwr mem\n')
        elif device == 'junos':
            telnet.write(b'configure\n')
            for input_data in input_config:
                if input_data[1]:
                    com = f'set interface ge-{input_data[0]} unit {input_data[1]} ' \
                          f'family inet add {input_data[2]}\n'.encode('ascii')
                else:
                    com = f'set interface ge-{input_data[0]} unit 0 ' \
                          f'family inet add {input_data[2]}\n'.encode('ascii')
                telnet.write(com)
                telnet.write(b'commit\nexit\n')
        elif device == 'xos':
            for input_data in input_config:
                com = f'show vlan port {input_data[0]}\n'.encode('ascii')
                telnet.write(com)
                com = telnet.read_until(b'Flags :').decode()
                com = re.search(r'\w*\s*\d{1,4}\s*\d{1,3}\.\d{1,3}\.\d{1,3}', com).group()
                com = re.split(r'\s', re.search(r'\w*\s*', com).group())
                com = f'configure vlan {com[0]} ip {input_data[2]}\n'.encode('ascii')
                telnet.write(com)
                telnet.write(b'save\ny\n')
    elif command in '3678':  # ADD USER, ANY COMMAND, BANNER AND NTP
        if device == 'ios':
            cisco_configuration_mode_authorizer(telnet, ena)
            if command == '3':
                for input_data in input_config:
                    if input_data[0] == 'admin':
                        com = f'username {input_data[1]} privilege 15 secret {input_data[2]}\n'.encode('ascii')
                    else:
                        com = f'username {input_data[1]} privilege 1 secret {input_data[2]}\n'.encode('ascii')
                    telnet.write(com)
            elif command == '6':
                time.sleep(0.1)
                telnet.read_very_eager()
                com = f'{input_config}\n'.encode('ascii')
            elif command == '7':
                com = f'banner login ^\n{input_config}^\n'.encode('ascii')
            elif command == '8':
                com = f'ntp server {input_config}\n'.encode('ascii')
            if command != '3':
                telnet.write(com)
                time.sleep(1)
            telnet.write(b'exit\n\n\nwrite mem\n')
            time.sleep(3)
        elif device == 'junos':
            telnet.write(b'configure\n')
            if command == '3':
                for input_data in input_config:
                    if input_data[0] == 'admin':
                        com = f'set system login user {input_data[1]} class super-user \n'.encode('ascii')
                    else:
                        com = f'set system login user {input_data[1]} class operator \n'.encode('ascii')
                    telnet.write(com)
                    time.sleep(1)
                    com = f'set system login user {input_data[1]} authentication plain-text-pass\n'.encode('ascii')
                    telnet.write(com)
                    time.sleep(0.2)
                    com = f'{input_data[2]}\n'.encode('ascii')
                    telnet.write(com)
                    time.sleep(0.2)
                    telnet.write(com)
                    time.sleep(0.2)
            elif command == '6':
                time.sleep(0.1)
                telnet.read_very_eager()
                com = f'{input_config}\n'.encode('ascii')
            elif command == '7':
                input_config = input_config.replace('\n', '\\n')
                com = f'set system login message "{input_config}\"\n'
                com1 = com[:len(com) // 2].encode('ascii')
                com = com[len(com) // 2:].encode('ascii')
                telnet.write(com1)
                time.sleep(0.1)
            elif command == '8':
                com = f'set system ntp server {input_config}\n'.encode('ascii')
            if command != '3':
                telnet.write(com)
            time.sleep(0.1)
            telnet.write(b'commit\n')
            time.sleep(1)
            telnet.write(b'exit\n')
        elif device == 'xos':
            if command == '3':
                for input_data in input_config:
                    com = f'create account {input_data[0]} {input_data[1]} {input_data[2]}\n'.encode('ascii')
                    telnet.write(com)
            elif command == '6':
                time.sleep(0.1)
                telnet.read_very_eager()
                com = f'{input_config}\n'.encode('ascii')
            elif command == '7':
                com = f'configure banner before-login\n{input_config}\n\n'.encode('ascii')
            elif command == '8':
                com = f'configure ntp server add {input_config}\n'.encode('ascii')
            if command != '3':
                telnet.write(com)
            time.sleep(0.1)
            telnet.write(b'save\ny\n')
            time.sleep(1)
        time.sleep(0.1)
    if command != '6':
        write_configuration_telnet(telnet, device, version, _ip, tcp_port)
    else:
        create_dir('my configs')
        create_dir('my configs/commands')
        time.sleep(0.1)
        com = telnet.read_very_eager().decode()
        # with open(f'my configs/commands/{_ip}_{tcp_port}_result.txt', 'w') as f0:
        #    f0.write(com)
        with open(f'my configs/commands/{device}_{_ip}_{tcp_port}_result.txt', 'w') as f0:
            f0.write(com)
    telnet_closer(device, telnet)


def custom_command_executor_telnet(_ip, password, login, name_script, tcp_port=23):
    telnet = telnetlib.Telnet(_ip, tcp_port)
    telnet.write(b'\x0d')
    time.sleep(1)
    device = who_is_telnet(telnet, login, password)
    sleep = 0.5
    telnet.read_very_eager()
    with open(f'my configs/{name_script}.txt', 'r') as command_file:
        for line_ in command_file:
            if re.match(r'\d+\.?\d*\n', line_):
                sleep = float(line_)
            else:
                telnet.write(line_.encode('ascii'))
                time.sleep(sleep)
                sleep = 0.5
    data = telnet.read_very_eager().decode()
    now = datetime.now()
    create_dir(f'my configs/{name_script}')
    with open(f'my configs/{name_script}/{_ip}_{tcp_port}_{now.date()}-'
              f'{now.hour}.{now.minute}.{now.second}.txt', 'w') as f2:
        f2.write(data)
    # with open(f'my configs/{name_script}/{_ip}_{tcp_port}.txt', 'w') as f2:
    #    f2.write(data)
    # telnet_closer(device, telnet)


def ip_reader():
    with open('data/ip.csv', 'r') as ip_file:
        _ip, tcp_port = zip(*csv.reader(ip_file))
    return _ip, tcp_port


def get_data_from_device_telnet(_ip, login, password, command, ena=b'\n', tcp_port=23):
    telnet = telnetlib.Telnet(_ip, tcp_port)
    telnet.write(b'\x0d')
    device, version = who_is_telnet(telnet, login, password)
    now = datetime.now()
    if command == '1':
        if device == 'ios':
            cisco_configuration_mode_authorizer(telnet, ena)
            telnet.write(b'exit\n')
            time.sleep(0.5)
            telnet.read_very_eager()
            telnet.write(b'show running-config\n')
            if re.search('ios_l2', version):
                time.sleep(5)
            time.sleep(5)
            telnet.read_until(b'Current configuration : ')
            telnet.read_until(b'\n')
        elif device == 'junos':
            time.sleep(0.5)
            telnet.read_very_eager()
            telnet.write(b'show configuration | display set\n')
            time.sleep(5)
            telnet.read_until(b'show configuration | display set ')
        elif device == 'xos':
            time.sleep(0.5)
            telnet.read_very_eager()
            telnet.write(b'show configuration\n')
            time.sleep(3)
            telnet.read_until(b'show configuration')
        config = telnet.read_very_eager().decode()
        create_dir('configs')
        # with open(f'configs/{device}_{_ip}_{tcp_port}_{now.date()}-'
        #          f'{now.hour}.{now.minute}.{now.second}.txt', 'w') as f0:
        #    f0.write(config)
        with open(f'configs/{_ip}_{tcp_port}.txt', 'w') as f0:
            f0.write(config)

    elif command == '2':
        create_dir('versions')
        with open(f'versions/{device}_{_ip}_{tcp_port}.txt', 'w') as f2:
            f2.write(version)

    elif command == '3':
        if device == 'ios':
            cisco_configuration_mode_authorizer(telnet, ena)
            time.sleep(1)
            telnet.write(b'exit\n')
            time.sleep(0.1)
            telnet.write(b'show ip route\n')
            if re.search('ios_l2', version):
                time.sleep(4.5)
            time.sleep(3)
            telnet.read_until(b'route')
        elif device == 'junos':
            telnet.write(b'show route\n')
            time.sleep(3)
            telnet.read_until(b'route')
        elif device == 'xos':
            telnet.write(b'show ipr\n')
            time.sleep(3)
            telnet.read_until(b'ipr')
        config = telnet.read_very_eager().decode()
        create_dir('routes')
        # with open(f'routes/{device}_{_ip}_{tcp_port}_{now.date()}-'
        #          f'{now.hour}.{now.minute}.{now.second}.txt', 'w') as f0:
        #    f0.write(config)
        with open(f'routes/{_ip}_{tcp_port}.txt', 'w') as f0:
            f0.write(config)
    telnet_closer(device, telnet)  # Конец функции сбора данных с устроств


if __name__ == '__main__':
    edit_options = {
        0: 'Возврат в предыдущее меню',
        1: 'Добавление VLAN',
        2: 'Добавление ACL',
        3: 'Добавление пользователей на устройство',
        4: 'Настройка OSPF',
        5: 'Настройка IP на интерфейсах',
        6: 'Отправка на устройство команды',
        7: 'Изменение приветственного сообщения',
        8: 'Настройка ntp сервера', }
    collection_options = {
        0: 'Возврат в предыдущее меню',
        1: 'Получение текущей конфигурации',
        2: 'Получение информации о версии',
        3: 'Получение информации о текущих маршрутах', }
    personal_options = {
        0: 'Возврат в предыдущее меню',
        1: 'Добавление новой функции',
        2: 'Удаление ранее созданной функции', }
    action_types = {
        0: 'Выход из программы',
        1: 'Сбор информации',
        2: 'Редактирование конфигурации',
        3: 'Действия с собственными функциями', }

    # Определение текущей ОС для правильной комманды очитски консоли
    if show_platform.startswith('win32'):
        clear_screen_command = 'cls'
    else:
        clear_screen_command = 'clear'
    os.system(clear_screen_command)
    # Ввод логопасса
    parser = argparse.ArgumentParser(description='Login, Password & Cisco enable parser')
    parser.add_argument('-l', action='store', dest='login')
    parser.add_argument('-p', action='store', dest='password')
    parser.add_argument('-e', action='store', dest='en_pass', help='password for cisco enable mode')
    args = parser.parse_args()
    if args.login:
        log_in = (args.login + '\n').encode('ascii')
    else:
        log_in = (input('Login: ') + '\n').encode('ascii')
    if args.password:
        pass_word = (args.password + '\n').encode('ascii')
    else:
        pass_word = (getpass.getpass() + '\n').encode('ascii')
    if args.en_pass:
        args.en_pass = (args.en_pass + '\n').encode('ascii')

    exit_trigger = True
    while exit_trigger:
        os.system(clear_screen_command)
        for (keys) in action_types:
            print(keys, ':', action_types.get(keys))
        menu_pointer = input('> ')
        if menu_pointer in str(list(range(0, len(action_types)))):
            os.system(clear_screen_command)
            if menu_pointer == '1':  # Функции, получающие набор информации с сетевых устройств
                reload_trigger = True
                while reload_trigger:
                    for (i) in collection_options:
                        print(i, ':', collection_options.get(i))
                    menu_pointer = input('> ')
                    os.system(clear_screen_command)
                    is_exist = False
                    if menu_pointer == '1':  # Получение текущей конфигурации
                        print('Поместите список ip адресов и портов в файл data/ip.csv в папке программы.\n'
                              'Конфигурационные файлы будут в папке configs.\n')
                        is_exist = True
                    elif menu_pointer == '2':  # Получение информации о версии текущей прошивки
                        print('Поместите список ip адресов и портов в файл data/ip.csv в папке программы.\n'
                              'Файлы версий будут в папке versions.\n')
                        is_exist = True
                    elif menu_pointer == '3':  # Получение информации о маршрутах
                        print('Поместите список ip адресов и портов в файл data/ip.csv в папке программы.\n'
                              'Файлы с данными о маршрутах будут в папке routes.\n')
                        is_exist = True
                    if is_exist:
                        trigger = input('Для продолжения нажмите Enter\n'
                                        'Введите 0 для возврата в предыдущее меню\n>')
                        if str(trigger) != '0':
                            timer = datetime.now()
                            os.system(clear_screen_command)
                            ips, ports = ip_reader()
                            print('Пожалуйста, подождите. Идёт выполнение программы...\n')
                            with ThreadPoolExecutor(max_workers=len(ips)) as executor:
                                executor.map(get_data_from_device_telnet, ips, repeat(log_in),
                                             repeat(pass_word), repeat(menu_pointer),
                                             repeat(args.en_pass), ports)
                            input(f'Готово! Времяя исполнения составило {datetime.now() - timer}')
                    elif menu_pointer == '0':
                        is_exist = True
                        reload_trigger = False
                    if not is_exist:
                        print('Нет такого пункта.')

            elif menu_pointer == '2':  # Функции, изменяющие конфиги сетевых устройств
                reload_trigger = True
                while reload_trigger:
                    for (i) in edit_options:
                        print(i, ':', edit_options.get(i))
                    menu_pointer = input('> ')
                    if menu_pointer in str(list(range(1, len(edit_options)))):
                        data_group = []
                        trigger = ''
                        if menu_pointer == '1':  # VLAN
                            print('\033[33m\n'
                                  '* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *\n'
                                  '*  Этот скрипт предназначен для первичного конфигурирования вланов. *\n'
                                  '*  При попытке работать с устройствами, на которых уже имеется      *\n'
                                  '*  обширный конфиг, могут наблюдаться проблемы                      *\n'
                                  '* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *\n'
                                  '\033[0m')
                            trigger = input('* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *\n'
                                            '*  Перенесите данные для внесения в файл data/vlan.csv. Формат: *\n'
                                            '*  ip-addr,port,interface,unit,vlan,vlan_name,type_of_port,els. *\n'
                                            '*  ELS столбик актуален для Juniper. Значения - 1 при налияии,  *\n'
                                            '*  0 при её отсутствии. На каждый влан отдельная строка. Номера *\n'
                                            '*  интерфейсов в формате: x/x дляCisco, x/x/x для Juniper,      *\n'
                                            '*  x(или x:x) для Extreme. Тип порта - Tagged или Untagged.     *\n'
                                            '*  Поле unit опционально. При пустых значениях в этом столбике  *\n'
                                            '*  подинтерфейсы создаваться не будут.                          *\n'
                                            '* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *\n'
                                            'Для продолжения нажмите Enter\n'
                                            'Для возврата в предыдущее меню введите "0"\n>')
                            if str(trigger) != '0':
                                timer = datetime.now()
                                print('...')
                                with open('data/vlan.csv') as vl_f:
                                    vl_reader = csv.reader(vl_f, dialect='excel', delimiter=';')
                                    vl_header = next(vl_reader)
                                    ips, ports, interfaces, vlans, units, vlan_names, tags, els = list(zip(*vl_reader))
                                    marker = 0
                                for index, port in enumerate(ports):
                                    if port != '':
                                        if index != 0:
                                            data_group.append(list(zip(interfaces[marker:index], units[marker:index],
                                                                       vlans[marker:index], vlan_names[marker:index],
                                                                       tags[marker:index], els[marker:index])))
                                        marker = index
                                data_group.append(list(zip(interfaces[marker:], units[marker:], vlans[marker:],
                                                           vlan_names[marker:], tags[marker:], els[marker:])))
                                del interfaces, vlans, vl_header, tags, vlan_names, els, units
                                ports = filter(lambda x: len(x) > 0, ports)
                                ips = list(filter(lambda x: len(x) > 0, ips))
                        elif menu_pointer == '2':  # ACL
                            print('\033[33m\n!!! Данный скрипт не применяет ACL на интерфейсы. '
                                  'Это сделано из соображений безопасности. !!!\n\033[0m')
                            trigger = input('* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *\n'
                                            '*  Перенесите данные для внесения в файл data/acl.csv. Формат:        *\n'
                                            '*  ip-addr,port,acl_name,specify,context,source,destination,eq,other. *\n'
                                            '*  Specify может принимать значения permit или deny. Поле context     *\n'
                                            '*  отвечает за тип фильтруемого трафика. Может принимать значения ip, *\n'
                                            '*  ospf, tcp, udp. source и dest - ip/mask. Для хостов маска /32. При *\n'
                                            '*  действии для всех - значение any. Поле eq необязательное, значение *\n'
                                            '*  - номер tcp/udp порта получателя. Поле other , как и  поле name,   *\n'
                                            '*  указывается один раз для одного ACL. Принимает значения deny или   *\n'
                                            '*  permit, отвечает за действие с "неперечисленным" в ACL "трафиком". *\n'
                                            '* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *\n'
                                            'Для продолжения нажмите Enter\n'
                                            'Для возврата в предыдущее меню введите "0"\n>')
                            if str(trigger) != '0':
                                timer = datetime.now()
                                print('...')
                                with open('data/acl.csv') as acl_f:
                                    acl_r = csv.reader(acl_f, dialect='excel', delimiter=';')
                                    acl_h = next(acl_r)
                                    ips, ports, name_acl, specify, context, src, dst, eq, oth = list(zip(*acl_r))
                                    marker = 0
                                for index, port in enumerate(ports):
                                    if port != '':
                                        if index != 0:
                                            data_group.append(list(zip(name_acl[marker:index], specify[marker:index],
                                                                       context[marker:index], src[marker:index],
                                                                       dst[marker:index], eq[marker:index],
                                                                       oth[marker:index])))
                                        marker = index
                                data_group.append(list(zip(name_acl[marker:], specify[marker:], context[marker:],
                                                           src[marker:], dst[marker:], eq[marker:], oth[marker:])))
                                del name_acl, specify, context, src, dst, eq, oth
                                ports = filter(lambda x: len(x) > 0, ports)
                                ips = list(filter(lambda x: len(x) > 0, ips))
                        elif menu_pointer == '3':  # ADD USER
                            trigger = \
                                input(
                                    '* * * * * * * * * * * * * * * * * * * * * * * * * * *\n'
                                    '* Поместите данные о пользователях в data/user.csv. *    Таблица соответствия  \n'
                                    '* Формат: privilege_level,username,password         * |privilege_______________|\n'
                                    '* Privilege_level может принимать значения admin    * |level|admin    |user    |\n'
                                    '* и user. данные об адресах поместите в ip.csv.     * |ios  |15       |1       |\n'
                                    '* Формат: ip-addr,port.                             * |junos|superuser|operator|\n'
                                    '* * * * * * * * * * * * * * * * * * * * * * * * * * * |xos  |admin    |user    |\n'
                                    'Для продолжения нажмите Enter\n'
                                    'Для возврата в предыдущее меню введите "0"\n>')
                            if str(trigger) != '0':
                                timer = datetime.now()
                                print('...')
                                ips, ports = ip_reader()
                                with open('data/user.csv') as user_f:
                                    user_reader = csv.reader(user_f, dialect='excel', delimiter=';')
                                    user_header = next(user_reader)
                                    user_reader = list(user_reader)
                                    for i in ips:
                                        data_group.append(user_reader[:])

                        elif menu_pointer == '4':  # OSPF
                            trigger = input('* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *\n'
                                            '*  Перенесите данные для внесения в файл data/ospf.csv. Формат:   *\n'
                                            '*  ip-addr,port,router-id,interface,area. формат номеров инт-ов:  *\n'
                                            '*  x/x для Cisco, x/x/x для Juniper, x(или x:x) для Extreme.      *\n'
                                            '* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *\n'
                                            'Для продолжения нажмите Enter\n'
                                            'Для возврата в предыдущее меню введите "0"\n>')
                            if str(trigger) != '0':
                                timer = datetime.now()
                                print('...')
                                with open('data/ospf.csv') as ospf_f:
                                    ospf_r = csv.reader(ospf_f, dialect='excel', delimiter=';')
                                    ospf_h = next(ospf_r)
                                    ips, ports, router_id, interfaces, area = list(zip(*ospf_r))
                                    marker = 0
                                for index, port in enumerate(ports):
                                    if port != '':
                                        if index != 0:
                                            data_group.append(list(zip(router_id[marker:index],
                                                                       interfaces[marker:index], area[marker:index])))
                                        marker = index
                                data_group.append(list(zip(router_id[marker:], interfaces[marker:], area[marker:])))
                                del interfaces, area, ospf_h, router_id
                                ports = filter(lambda x: len(x) > 0, ports)
                                ips = list(filter(lambda x: len(x) > 0, ips))
                        elif menu_pointer == '5':  # IP
                            trigger = input('* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *\n'
                                            '*  Перенесите данные для внесения в файл data/interface_ip.csv. Ф-т *\n'
                                            '*  записи: ip-addr,port,interface,unit,ip/mask. формат номеров      *\n'
                                            '*  инт-ов:x/x для Cisco, x/x/x для Juniper, x(или x:x) для Extreme. *\n'
                                            '*  Поле unit опционально. При пустых значениях в этом столбике      *\n'
                                            '*  подинтерфейсы создаваться не будут.                              *\n'
                                            '* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *\n'
                                            'Для продолжения нажмите Enter\n'
                                            'Для возврата в предыдущее меню введите "0"\n>')
                            if str(trigger) != '0':
                                timer = datetime.now()
                                print('...')
                                with open('data/interface_ip.csv') as ip_f:
                                    ip_r = csv.reader(ip_f, dialect='excel', delimiter=';')
                                    ip_h = next(ip_r)
                                    ips, ports, interfaces, unit, ip_mask = list(zip(*ip_r))
                                    marker = 0
                                for index, port in enumerate(ports):
                                    if port != '':
                                        if index != 0:
                                            data_group.append(list(zip(interfaces[marker:index],
                                                                       unit[marker:index], ip_mask[marker:index])))
                                        marker = index
                                data_group.append(list(zip(interfaces[marker:], unit[marker:], ip_mask[marker:])))
                                del interfaces, ip_r, ip_mask, ip_h, unit
                                ports = filter(lambda x: len(x) > 0, ports)
                                ips = list(filter(lambda x: len(x) > 0, ips))
                        elif menu_pointer == '6':  # ANY COMMAND
                            dat_a = input('* * * * * * * * * * * * * * * * * * * * * * * * * * * * * *\n'
                                          '*  Поместите адреса устройств в data/ip.csv. Введите      *\n'
                                          '*  ниже комманду для передачи на устройства. Учитывайте,  *\n'
                                          '*  что устройства будут в конфигурационном режиме. Ip.csv *\n'
                                          '*  формат записи: ip-addr,port.                           *\n'
                                          '* * * * * * * * * * * * * * * * * * * * * * * * * * * * * *\n'
                                          'Для возврата в предыдущее меню введите "0"\n'
                                          'Команду вводить тут>')
                            if str(dat_a) != 0:
                                timer = datetime.now()
                                print('Результат выполнения будет в папке my scripts/commands')
                                ips, ports = ip_reader()
                                for i in ips:
                                    data_group.append(dat_a)
                            else:
                                trigger = '0'
                        elif menu_pointer == '7':  # BANNER
                            trigger = input('* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *\n'
                                            '*  Перенесите баннер в файл data/banner.txt. Не оставляйте  *\n'
                                            '*  пустых строчек. Если баннер предназначен для cisco,      *\n'
                                            '*  не используйте символ \'^\'. Поместите адреса устроств     *\n'
                                            '*  в ip.csv. Формат записи: ip-addr,port.                   *\n'
                                            '* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *\n'
                                            'Для продолжения нажмите Enter\n'
                                            'Для возврата в предыдущее меню введите "0"\n>')
                            if str(trigger) != '0':
                                timer = datetime.now()
                                print('...')
                                with open('data/banner.txt') as banner_f:
                                    banner_data = banner_f.read()
                                ips, ports = ip_reader()
                                for i in ips:
                                    data_group.append(banner_data)
                        elif menu_pointer == '8':  # NTP
                            trigger = input('* * * * * * * * * * * * * * * * * * * * *\n'
                                            '*  Перенесите данные для внесения       *\n'
                                            '*  в файл data/ntp.csv. Формат записи:  *\n'
                                            '*   ip-addr,port,ntp_ip.                *\n'
                                            '* * * * * * * * * * * * * * * * * * * * *\n'
                                            'Для продолжения нажмите Enter\n'
                                            'Для возврата в предыдущее меню введите "0"\n>')
                            if str(trigger) != '0':
                                timer = datetime.now()
                                print('...')
                                with open('data/ntp.csv') as ntp_f:
                                    ntp_reader = csv.reader(ntp_f, dialect='excel', delimiter=';')
                                    ntp_header = next(ntp_reader)
                                    ips, ports, data_group = (zip(*ntp_reader))
                        if str(trigger) != '0':
                            with ThreadPoolExecutor(max_workers=len(ips)) as executor:
                                executor.map(edit_configuration_on_device_telnet, ips, repeat(pass_word),
                                             repeat(log_in), repeat(menu_pointer), data_group, repeat(args.en_pass),
                                             ports)
                            input(f'Готово! Время исполнения составило {datetime.now() - timer}')
                    elif menu_pointer == '0':
                        reload_trigger = False
                    else:
                        print('Нет такого пункта.')
                    os.system(clear_screen_command)

            elif menu_pointer == '3':  # Функции, добавленные пользователем
                reload_trigger = True
                while reload_trigger:
                    with open('data/list_of_scripts.txt', 'a+') as los:
                        los.seek(0)
                        for line in los:
                            if line not in personal_options.values():
                                line = line.strip()
                                personal_options[len(personal_options)] = line
                    for (i) in personal_options:
                        print(i, ':', personal_options.get(i))
                    menu_pointer = input('> ')
                    if (menu_pointer in str(list(range(1, len(personal_options))))) & (menu_pointer != ''):
                        if menu_pointer == '1':
                            os.system(clear_screen_command)
                            create_dir('my configs')
                            with open('data/list_of_scripts.txt', 'a') as los:
                                new_script = input('* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *\n'
                                                   '* Название конфига должно совпадать с названием .txt файла    *\n'
                                                   '* /my configs/. Комманды будут отправляться на устройства     *\n'
                                                   '* построчно. Перед каждой строкой можно цифрой указать паузу  *\n'
                                                   '* после её выполнения. По умолчанию пауза составляет 0.5с. В  *\n'
                                                   '* устройство будет осуществлён первоначальный вход. Выход и   *\n'
                                                   '* сохранение изменений по умолчанию не осуществляется.        *\n'
                                                   '* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *\n'
                                                   'Введите название добавляемого конфига.\n'
                                                   'Для возврата в предыдущее меню отправьте пустую строку\n>') + '\n'
                                if new_script != '\n':
                                    los.write(new_script)
                        elif menu_pointer == '2':
                            try:
                                delete_script = int(input('Введите номер удаляемого конфига.\n'
                                                          'Введите 0 для возврата в предыдущее меню\n>'))
                                if delete_script > 2:
                                    with open('data/list_of_scripts.txt', 'r') as los:
                                        los_list = los.readlines()
                                    los_list = filter(lambda los_line:
                                                      personal_options.get(delete_script) not in los_line, los_list)
                                    with open('data/list_of_scripts.txt', 'w') as los:
                                        los.write(''.join(los_list))
                                    del personal_options[delete_script]
                                elif delete_script != 0:
                                    print('Нельзя удалить системные комманды!')
                            except (ValueError, NameError):
                                print('Введите существующий номер!')
                        else:
                            os.system(clear_screen_command)
                            trigger = input(
                                'Поместите список ip адресов и портов в файл data/ip.csv в папке программы.\n '
                                'Для продолжения нажмите Enter\n'
                                'Для возврата в предыдущее меню введите "0"\n>')
                            if str(trigger) != '0':
                                timer = datetime.now()
                                os.system(clear_screen_command)
                                ips, ports = ip_reader()
                                print('Пожалуйста, подождите. Идёт выполнение программы...')
                                script_name = personal_options.get(int(menu_pointer))
                                if os.path.exists(f'my configs/{script_name}.txt'):
                                    with ThreadPoolExecutor(max_workers=len(ips)) as executor:
                                        executor.map(custom_command_executor_telnet, ips, repeat(pass_word),
                                                     repeat(log_in), repeat(script_name), ports)
                                    os.system(clear_screen_command)
                                    print(f'Результат выполненного скрипта в соответствующих файлах в папке '
                                          f'my configs/{script_name}')
                                    input(f'Время исполнения составило {datetime.now() - timer}')
                                else:
                                    print('Нет такого файла скрипта. Пожалуйста, проверьте название и'
                                          ' местоположение файла с командами.')

                    elif menu_pointer == '0':
                        reload_trigger = False
                    else:
                        print('Нет такого пункта.')
            elif menu_pointer == '0':
                exit_trigger = False
        else:
            print('Введён несуществующий пункт меню')
            os.system(clear_screen_command)
