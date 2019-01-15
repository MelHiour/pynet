# -*- coding: utf-8 -*-

import yaml
import subprocess
from pprint import pprint
import concurrent.futures
import netmiko 
import itertools

def ping_ip_address(ip):
    pinger = subprocess.run(['ping', '-c', '2', '-n', ip], stdout=subprocess.DEVNULL)
    if pinger.returncode == 0:
        return {'alive':ip}
    else:
        return {'dead':ip}

def ping_ip_threads(ips, limit=3, type = 'process'):
    if type == 'process': 
        with concurrent.futures.ProcessPoolExecutor(max_workers=limit) as executor:
            pinger_result = list(executor.map(ping_ip_address, ips))
    elif type == 'thread':
        with concurrent.futures.ThreadPoolExecutor(max_workers=limit) as executor:
            pinger_result = list(executor.map(ping_ip_address, ips))
    else:
        return ('Specify correct threading option. type = thread|process')
    ip_list = {'alive':[], 'dead':[]}
    for item in pinger_result:
        if 'alive' in item.keys():
            ip_list['alive'].append(item['alive'])
        else:
            ip_list['dead'].append(item['dead'])
    return ip_list

def ios_connection_establisher(host, creds_file, command_file): 
    print('Unpacking {} file'.format(creds_file))
    with open(creds_file) as file:
        creds = yaml.load(file)
    exeption_counter = 1
    print('Starting for loops for usernames and passwords') 
    for username in creds['usernames']:
        for password in creds['passwords']:
            print('Connecting to {}'.format(host))
            print(username, password)
            device_params = {'device_type': 'cisco_ios', 'ip': host, 'username': username, 'password': password,'secret': password}
            try:
                with netmiko.ConnectHandler(**device_params) as ssh:
                    if ssh.check_config_mode():
                        print('Currently in enable mode')
                    else:
                        print('Doing enable')
                        ssh.enable()
                    print('Sending commands from {}'.format(command_file))
                    result = ssh.send_config_from_file(command_file)
                    print('The result of operations is:')
                    pprint(result)
                reconfigured = host
            except netmiko.ssh_exception.NetMikoAuthenticationException:
                print('NetMikoAuthenticationException accurs: {} time(s)'.format(exeption_counter))
                exeption_counter = exeption_counter + 1
                pass
    return reconfigured



def devices_from_file(device_file):
    with open(device_file) as file:
        result = file.read().split('\n')
    return result[0:-1]

if __name__ == '__main__':
    devices = devices_from_file('devices')
    ip_list = ping_ip_threads(devices)
    for ip in ip_list['alive']:
        result = ios_connection_establisher(ip, 'creds.yml', 'commands')
        print(result)
