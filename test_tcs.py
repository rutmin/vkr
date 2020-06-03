import unittest
import telnetlib
import time
from datetime import datetime
import telnet_configuration_script as tcs
import os


ip = '192.168.1.200'
password = ena = b'cisco1233\n'
login = b'root\n'


class TestsForTelnetConfigurationScript(unittest.TestCase):
    def test_who_is(self):
        ports = [['32769', 'ios'], ['32770', 'ios'], ['32771', 'junos'], ['32772', 'xos'],
                 ['32773', 'junos'], ['32774', 'junos'], ['32775', 'ios']]
        for port in ports:
            timer = datetime.now()
            telnet = telnetlib.Telnet(ip, port[0])
            telnet.write(b'\x0d')
            device, version = tcs.who_is_telnet(telnet, login, password)
            tcs.telnet_closer(device, telnet)
            self.assertEqual(device, port[1], f"Неправильное определение производителя на {port[0]}")
            print(f'for port {port} time = {datetime.now() - timer}')

    def test_edit_vlan(self):
        ports = ['32774', '32778', '32779', '32770', '32772']
        input_config = [[('0/0/0', '', '11', 'test_11', 'untagged', '1'),
                         ('0/0/1', '', '12', 'test_12', 'tagged', '1'),
                         ('0/0/1', '', '13', 'test_13', 'tagged', '1'),
                         ('0/0/3', '', '14', 'test_14', 'untagged', '1'),
                         ('0/0/4', '', '15', 'test_15', 'untagged', '1'),
                         ('0/0/5', '', '16', 'test_16', 'untagged', '1'),
                         ('0/0/6', '', '17', 'test_17', 'untagged', '1'),
                         ('0/0/7', '', '18', 'test_18', 'untagged', '1'),
                         ('0/0/8', '', '19', 'test_19', 'untagged', '1'),
                         ('0/0/9', '', '20', 'test_20', 'untagged', '1')],
                        [('0/0/1', '1', '12', 'TEST', 'tagged', '')],
                        [('0/1', '7', '359', 'qwefa', 'tagged', '')],
                        [('0/0', '', '5', 'test_5', 'untagged', ''),
                         ('0/1', '', '6', 'test_6', 'untagged', ''),
                         ('0/2', '', '7', 'test_7', 'untagged', ''),
                         ('0/3', '', '8', 'test_8', 'untagged', '')],
                        [('1', '', '21', 'test_21', 'untagged', ''),
                         ('2', '', '22', 'test_22', 'untagged', ''),
                         ('3', '', '23', 'test_23', 'untagged', '')]]
        for ind, port in enumerate(ports):
            timer = datetime.now()
            tcs.edit_configuration_on_device_telnet(ip, password, login, '1', input_config[ind], ena, port)
            self.assertTrue(os.path.exists(f'configs/{ip}_{port}.txt'), f'В {port} произошла ошибка.')
            os.remove(f'configs/{ip}_{port}.txt')
            print(f'for port {port} time = {datetime.now() - timer}')

    def test_edit_acl(self):
        ports = ['32772', '32774', '32770']
        input_config = [[('test', 'permit', 'ip', '192.168.1.1/20', '123.1.1.1/3', '', 'deny'),
                         ('', 'deny', 'ospf', '1.1.1.1/23', '54.4.5.2/6', '', ''),
                         ('', 'permit', 'tcp', '1.2.3.4/23', '4.6.7.9/2', '3', ''),
                         ('', 'deny', 'udp', 'any', 'any', '432', ''),
                         ('quest', 'permit', 'ip', '192.168.1.1/20', '123.1.1.1/3', '', 'permit'),
                         ('', 'deny', 'ospf', '1.1.1.1/23', '54.4.5.2/6', '', ''),
                         ('', 'permit', 'tcp', '1.2.3.4/23', '4.6.7.9/2', '3', ''),
                         ('', 'permit', 'udp', 'any', 'any', '432', ''),
                         ('', 'deny', 'udp', 'any', 'any', '', ''),
                         ('qwe', 'deny', 'ip', '192.168.1.2/23', 'any', '', 'permit')],
                        [('test', 'permit', 'ip', '192.168.1.1/20', '123.1.1.1/3', '', 'permit'),
                         ('', 'deny', 'ospf', '1.1.1.1/23', '54.4.5.2/6', '', ''),
                         ('', 'permit', 'tcp', '1.2.3.4/23', '4.6.7.9/2', '3', ''),
                         ('', 'deny', 'udp', 'any', 'any', '432', ''),
                         ('test34', 'permit', 'ip', '192.168.1.1/20', '123.1.1.1/3', '', 'deny'),
                         ('', 'deny', 'ospf', '1.1.1.1/23', '54.4.5.2/6', '', ''),
                         ('', 'permit', 'tcp', '1.2.3.4/23', '4.6.7.9/2', '3', ''),
                         ('', 'deny', 'udp', 'any', 'any', '432', ''),
                         ('quest', 'permit', 'ip', '192.168.1.1/20', '123.1.1.1/3', '', 'permit'),
                         ('', 'deny', 'ospf', '1.1.1.1/23', '54.4.5.2/6', '', ''),
                         ('', 'permit', 'tcp', '1.2.3.4/23', '4.6.7.9/2', '3', ''),
                         ('', 'permit', 'udp', 'any', 'any', '432', ''),
                         ('', 'deny', 'udp', 'any', 'any', '', ''),
                         ('qwe', 'deny', 'ip', '192.168.1.2/23', 'any', '', 'permit')],
                        [('test', 'permit', 'ip', '192.168.1.1/20', '123.1.1.1/3', '', 'permit'),
                         ('', 'deny', 'ospf', '1.1.1.1/23', '54.4.5.2/6', '', ''),
                         ('', 'permit', 'tcp', '1.2.3.4/23', '4.6.7.9/2', '3', ''),
                         ('', 'deny', 'udp', 'any', 'any', '432', ''),
                         ('asd', 'permit', 'ip', '192.168.1.1/20', '123.1.1.1/3', '', 'permit'),
                         ('', 'deny', 'ospf', '1.1.1.1/23', '54.4.5.2/6', '', ''),
                         ('', 'permit', 'tcp', '1.2.3.4/23', '4.6.7.9/2', '3', ''),
                         ('', 'deny', 'udp', 'any', 'any', '432', ''),
                         ('test34', 'permit', 'ip', '192.168.1.1/20', '123.1.1.1/3', '', 'deny'),
                         ('', 'deny', 'ospf', '1.1.1.1/23', '54.4.5.2/6', '', ''),
                         ('', 'permit', 'tcp', '1.2.3.4/23', '4.6.7.9/2', '3', ''),
                         ('', 'deny', 'udp', 'any', 'any', '432', ''),
                         ('quest', 'permit', 'ip', '192.168.1.1/20', '123.1.1.1/3', '', 'permit'),
                         ('', 'deny', 'ospf', '1.1.1.1/23', '54.4.5.2/6', '', ''),
                         ('', 'permit', 'tcp', '1.2.3.4/23', '4.6.7.9/2', '3', ''),
                         ('', 'permit', 'udp', 'any', 'any', '432', ''),
                         ('', 'deny', 'udp', 'any', 'any', '', ''),
                         ('qwe', 'deny', 'ip', '192.168.1.2/23', 'any', '', 'permit')]]
        for ind, port in enumerate(ports):
            timer = datetime.now()
            tcs.edit_configuration_on_device_telnet(ip, password, login, '2', input_config[ind], ena, port)
            self.assertTrue(os.path.exists(f'configs/{ip}_{port}.txt'), f'В {port} произошла ошибка.')
            os.remove(f'configs/{ip}_{port}.txt')
            print(f'for port {port} time = {datetime.now() - timer}')

    def test_edit_user(self):
        ports = ('32769', '32770', '32771', '32772', '32773', '32774', '32775')
        input_config = [[['admin', 'administrator', 'cisco1233'],
                         ['user', 'test', 'cisco1233']],
                        [['admin', 'administrator', 'cisco1233'],
                         ['user', 'test', 'cisco1233']],
                        [['admin', 'administrator', 'cisco1233'],
                         ['user', 'test', 'cisco1233']],
                        [['admin', 'administrator', 'cisco1233'],
                         ['user', 'test', 'cisco1233']],
                        [['admin', 'administrator', 'cisco1233'],
                         ['user', 'test', 'cisco1233']],
                        [['admin', 'administrator', 'cisco1233'],
                         ['user', 'test', 'cisco1233']],
                        [['admin', 'administrator', 'cisco1233'],
                         ['user', 'test', 'cisco1233']]]
        for ind, port in enumerate(ports):
            timer = datetime.now()
            tcs.edit_configuration_on_device_telnet(ip, password, login, '3', input_config[ind], ena, port)
            self.assertTrue(os.path.exists(f'configs/{ip}_{port}.txt'), f'В {port} произошла ошибка.')
            os.remove(f'configs/{ip}_{port}.txt')
            print(f'for port {port} time = {datetime.now() - timer}')

    def test_edit_ospf(self):
        ports = ['32769', '32771', '32772', '32773', '32775']
        input_config = [[('32.7.6.9', '0/0', '0.0.0.0'),
                         ('', '0/1', '0.0.0.0')],
                        [('32.7.7.1', '0/0/0', '0.0.0.0'),
                         ('', '0/0/1', '0.0.0.0'),
                         ('', '0/0/2', '0.0.0.1')],
                        [('32.7.7.2', '1', '0.0.0.1')],
                        [('32.7.7.3', '0/0/0', '0.0.0.0'),
                         ('', '0/0/1', '0.0.0.0')],
                        [('32.7.7.5', '0/0', '0.0.0.0'),
                         ('', '0/1', '0.0.0.0')]]
        for ind, port in enumerate(ports):
            timer = datetime.now()
            tcs.edit_configuration_on_device_telnet(ip, password, login, '4', input_config[ind], ena, port)
            self.assertTrue(os.path.exists(f'configs/{ip}_{port}.txt'), f'В {port} произошла ошибка.')
            os.remove(f'configs/{ip}_{port}.txt')
            print(f'for port {port} time = {datetime.now() - timer}')

    def test_edit_ip(self):
        ports = ['32769', '32778']
        input_config = [[('0/2', '', '192.168.11.3/24')], [('0/0/0', '0', '193.1.1.1/23')]]
        for ind, port in enumerate(ports):
            timer = datetime.now()
            tcs.edit_configuration_on_device_telnet(ip, password, login, '5', input_config[ind], ena, port)
            self.assertTrue(os.path.exists(f'configs/{ip}_{port}.txt'), f'В {port} произошла ошибка.')
            os.remove(f'configs/{ip}_{port}.txt')
            print(f'for port {port} time = {datetime.now() - timer}')

    def test_edit_user_command(self):
        ports = ['32769', '32771', '32772']
        data = ['do show ip route', 'run show route', 'show ipr']

        for i, port in enumerate(ports):
            timer = datetime.now()
            tcs.edit_configuration_on_device_telnet(ip, password, login, '6', data[i], ena, port)
            with open(f'my configs/commands/{ip}_{port}_result.txt', 'r') as f0:
                read = f0.read()
                self.assertIn('192.168', read), f'В {port} произошла ошибка.'
            os.remove(f'my configs/commands/{ip}_{port}_result.txt')
            print(f'for port {port} time = {datetime.now() - timer}')

    def test_edit_welcome_message(self):
        ports = ('32769', '32770', '32771', '32772', '32773', '32774', '32775', '32778', '32779')
        input_config = ['* * * * * * * * * * * * * * * * * *\n'
                        '* This is test banner for my vkr  *\n'
                        '* Vladimir Ilych Lenin is Alive!  *\n'
                        '* * * * * * * * * * * * * * * * * *']
        for ind, port in enumerate(ports):
            timer = datetime.now()
            tcs.edit_configuration_on_device_telnet(ip, password, login, '7', input_config[0], ena, port)
            self.assertTrue(os.path.exists(f'configs/{ip}_{port}.txt'), f'В {port} произошла ошибка.')
            time.sleep(1)
            telnet = telnetlib.Telnet(ip, port)
            telnet.write(b'\x0d')
            time.sleep(2)
            com = telnet.read_very_eager().decode()
            if ':' not in com:
                com = telnet.read_until(b':').decode()
            self.assertIn('Vladimir Ilych', com, f'\nError in port {port}')
            telnet.close()
            os.remove(f'configs/{ip}_{port}.txt')
            print(f'for port {port} time = {datetime.now() - timer}')

    def test_edit_ntp(self):
        ports = ('32769', '32770', '32771', '32772', '32774')
        input_config = ('192.168.1.200', '192.168.1.200', '192.168.1.200', '192.168.1.200', '192.168.1.200')
        timer_ = ['', '', '', '', '']
        for ind, port in enumerate(ports):
            timer_[ind] = datetime.now()
            tcs.edit_configuration_on_device_telnet(ip, password, login, '8', input_config[ind], ena, port)
            timer_[ind] = datetime.now() - timer_[ind]
        for port in ports:
            self.assertTrue(os.path.exists(f'configs/{ip}_{port}.txt'), f'В {port} произошла ошибка.')

        timer = datetime.now()
        telnet = telnetlib.Telnet(ip, ports[0])
        time.sleep(0.5)
        telnet.write(b'\x0d')
        time.sleep(0.7)
        telnet.write(login)
        time.sleep(0.5)
        telnet.write(password)
        time.sleep(0.5)
        telnet.write(b'ena\n')
        time.sleep(0.5)
        telnet.write(ena)
        time.sleep(0.5)
        telnet.read_very_eager()
        telnet.write(b'show ntp config\n')
        time.sleep(0.5)
        com = telnet.read_very_eager().decode()
        telnet.write(b'exit\n')
        telnet.close()
        self.assertIn('ntp server 192.168.1.200', com, f'Нет ntp сервера на {ports[0]}')
        print(f'for port {port} time = {datetime.now() - timer + timer_[0]}')

        timer = datetime.now()
        telnet = telnetlib.Telnet(ip, ports[2])
        telnet.write(b'\x0d')
        time.sleep(0.5)
        telnet.write(login)
        time.sleep(0.5)
        telnet.write(password)
        time.sleep(1)
        telnet.write(b'clear\n')
        time.sleep(1)
        telnet.write(b'cli\n')
        time.sleep(0.5)
        telnet.read_very_eager()
        time.sleep(0.5)
        telnet.write(b'show configuration | match ntp | display set\n')
        time.sleep(1)
        com = telnet.read_very_eager().decode()
        telnet.write(b'exit\n')
        time.sleep(0.5)
        telnet.write(b'exit\n')
        telnet.close()
        self.assertIn('ntp server 192.168.1.200', com, f'Нет ntp сервера на {ports[2]}')
        print(f'for port {port} time = {datetime.now() - timer + timer_[1]}')

        timer = datetime.now()
        telnet = telnetlib.Telnet(ip, ports[3])
        telnet.write(b'\x0d')
        time.sleep(0.5)
        telnet.write(login)
        time.sleep(0.5)
        telnet.write(password)
        time.sleep(1)
        telnet.read_very_eager()
        telnet.write(b'show ntp server\n')
        time.sleep(0.5)
        com = telnet.read_very_eager().decode()
        telnet.write(b'exit\n')
        telnet.close()
        self.assertIn('192.168.1.200', com, f'Нет ntp сервера на {ports[0]}')
        print(f'for port {port} time = {datetime.now() - timer + timer_[2]}')

        for port in ports:
            os.remove(f'configs/{ip}_{port}.txt')

    def test_get_version(self):
        ports = [['32769', 'ios'],
                 ['32770', 'ios'],
                 ['32771', 'junos'],
                 ['32772', 'xos'],
                 ['32773', 'junos'],
                 ['32774', 'junos'],
                 ['32775', 'ios']]
        data = ['cisco ios software, iosv software (vios-adventerprisek9-m), version 15.6(2)t, release software (fc2)',
                'cisco ios software, vios_l2 software (vios_l2-adventerprisek9-m), experimental version 15.2',
                'junos: 14.1r1.10', 'image   : extremexos version 21.1.1.4 by release-manager',
                'junos appid services pic package [14.1r1.10]', 'junos: 15.1x53-d63.9', 'cisco iosv (revision 1.0)']
        for port, d in zip(ports, data):
            timer = datetime.now()
            tcs.get_data_from_device_telnet(ip, login, password, '2', ena, port[0])
            with open(f'versions/{port[1]}_{ip}_{port[0]}.txt', 'r') as f2:
                read = f2.read()
                self.assertIn(d, read)
            print(f'for port {port[0]} time = {datetime.now() - timer}')

    def test_get_configuration(self):
        ports = [['32769', 'ios'],
                 ['32770', 'ios'],
                 ['32771', 'junos'],
                 ['32772', 'xos']]
        for port in ports:
            ta = datetime.now()
            tcs.get_data_from_device_telnet(ip, login, password, '1', ena, port[0])
            print(f'\n! {port} {datetime.now() - ta}')
        timer = datetime.now()
        telnet = telnetlib.Telnet(ip, ports[0][0])
        telnet.write(b'\x0d')
        telnet.read_until(b'e:')
        telnet.write(login)
        telnet.read_until(b'd:')
        telnet.write(password)
        time.sleep(0.5)
        telnet.write(b'ena\n')
        time.sleep(0.5)
        telnet.write(ena)
        time.sleep(0.5)
        telnet.write(b'terminal length 0\n')
        time.sleep(0.5)
        telnet.read_very_eager()
        telnet.write(b'show running-config\n')
        time.sleep(5)
        telnet.read_until(b'Current configuration : ')
        telnet.read_until(b'\n')
        com = telnet.read_very_eager().decode()
        telnet.write(b'exit\n')
        telnet.close()
        with open(f'configs/{ip}_{ports[0][0]}.txt', 'r') as f0:
            for line in f0:
                line = line.replace('\n', '\r\n')
                self.assertIn(line, com, '\nerror in {}'.format(ports[0][0]))
        print(f'for port {ports[0][0]} time = {datetime.now() - timer}')

        timer = datetime.now()
        telnet = telnetlib.Telnet(ip, ports[1][0])
        telnet.write(b'\x0d')
        time.sleep(1)
        telnet.read_until(b'e:')
        telnet.write(login)
        telnet.read_until(b'd:')
        time.sleep(2)
        telnet.write(password)
        time.sleep(0.5)
        telnet.write(b'ena\n')
        time.sleep(0.5)
        telnet.write(ena)
        time.sleep(0.5)
        telnet.write(b'terminal length 0\n')
        time.sleep(0.5)
        telnet.read_very_eager()
        telnet.write(b'show running-config\n')
        time.sleep(10)
        com = telnet.read_very_eager().decode()
        telnet.write(b'exit\n')
        telnet.close()
        with open(f'configs/{ip}_{ports[1][0]}.txt', 'r') as f0:
            for line in f0:
                line = line.replace('\n', '\r\n')
                self.assertIn(line, com, '\nerror in {}'.format(ports[1][0]))
        print(f'for port {ports[1][0]} time = {datetime.now() - timer}')

        timer = datetime.now()
        telnet = telnetlib.Telnet(ip, ports[2][0])
        telnet.write(b'\x0d')
        time.sleep(1)
        telnet.read_until(b'n:')
        telnet.write(login)
        telnet.read_until(b'd:')
        time.sleep(1)
        telnet.write(password)
        time.sleep(1)
        telnet.write(b'clear\n')
        time.sleep(1)
        telnet.write(b'cli\n')
        time.sleep(0.5)
        telnet.write(b'set cli screen-length 0\n')
        time.sleep(0.5)
        telnet.write(b'show configuration | display set\n')
        time.sleep(5)
        com = telnet.read_very_eager().decode()
        telnet.write(b'exit\n')
        time.sleep(0.5)
        telnet.write(b'exit\n')
        telnet.close()
        with open(f'configs/{ip}_{ports[2][0]}.txt', 'r') as f0:
            for line in f0:
                line = line.replace('\n', '\r\n')
                self.assertIn(line, com, '\nerror in {}'.format(ports[2][0]))
        print(f'for port {ports[2][0]} time = {datetime.now() - timer}')

        timer = datetime.now()
        telnet = telnetlib.Telnet(ip, ports[3][0])
        telnet.write(b'\x0d')
        time.sleep(0.5)
        telnet.read_until(b'n:')
        telnet.write(login)
        telnet.read_until(b'd:')
        time.sleep(0.5)
        telnet.write(password)
        time.sleep(1)
        telnet.write(b'disable clipaging\n')
        time.sleep(0.5)
        telnet.write(b'show configuration\n')
        time.sleep(1)
        com = telnet.read_very_eager().decode()
        telnet.write(b'exit\n')
        telnet.close()
        with open(f'configs/{ip}_{ports[3][0]}.txt', 'r') as f0:
            for line in f0:
                line = line.replace('\n', '\r\n')
                line = line.replace('VM.5', 'VM.3')
                self.assertIn(line, com, '\nerror in {}'.format(ports[3][0]))
        print(f'for port {ports[3][0]} time = {datetime.now() - timer}')

    def test_get_routes(self):
        ports = ['32769', '32771', '32772']
        for port in ports:
            timer = datetime.now()
            tcs.get_data_from_device_telnet(ip, login, password, '3', ena, port)
            with open(f'routes/{ip}_{port}.txt', 'r') as f0:
                read = f0.read()
                self.assertIn('192.168', read), f'В {port} произошла ошибка.'
            print(f'for port {port} time = {datetime.now() - timer}')

    def test_custom_command_executor(self):
        timer = datetime.now()
        tcs.custom_command_executor_telnet(ip, password, login, 'test', '32769')
        time.sleep(2)
        telnet = telnetlib.Telnet(ip, '32769')
        telnet.write(b'\x0d')
        time.sleep(1)
        tcs.who_is_telnet(telnet, login, password)
        time.sleep(2)
        telnet.read_very_eager()
        telnet.write(b'show version\n')
        time.sleep(3)
        telnet.write(b'ena\n')
        time.sleep(2)
        telnet.write(ena)
        time.sleep(0.5)
        telnet.write(b'wr mem\n')
        time.sleep(6)
        telnet.write(b'\n')
        telnet.write(b'exit\n')
        time.sleep(0.5)
        com = telnet.read_very_eager().decode()
        telnet.close()
        with open(f'my configs/test/{ip}_32769.txt', 'r') as f2:
            for line in f2:
                line = line.strip()
                if ('GRUB' or 'Router uptime') not in line:
                    self.assertIn(line, com, f'\nСтрока {line}')
        print(f'for port 32769 time = {datetime.now() - timer}')


if __name__ == '__main__':
    unittest.main()
