import socket
import subprocess
import os
import signal
import time
import sys
import json

host = '192.168.0.13'
port = 3030

# DROP 12.1.0.0/16
subprocess.run("docker exec -i -t oai-spgwu /bin/bash -c 'iptables -A FORWARD -s 12.1.0.0/16 -j DROP'", shell=True, check=True)
# ACCEPT 192.168.0.12(TINM)
subprocess.run("docker exec -i -t oai-spgwu /bin/bash -c 'iptables -I FORWARD 1 -s 12.1.0.0/16 -d 192.168.0.12 -j ACCEPT'", shell=True, check=True)

def run_tshark():
    subprocess.run("tshark -i demo-oai -Y '(ip.src==12.1.0.0/16)&&(ip.dst==192.168.0.12)&&(frame.len eq 98)' -T fields -e ip.src -a 'duration:3' -e json > output.json", shell=True, capture_output=True, text=True)
    
    ip_list = []
    
    f = open("output.json", "r")
    for line in f:
        print(line.split(",")[-1])
        ip = line.split(",")[-1].strip()
        ip_list.append(ip)
    ip_list = list(set(ip_list))
    f.close()

    return ip_list
    
def update_ip_list(ip_list, new_ip):
    if new_ip not in ip_list:
        ip_list.append(new_ip)
        print(f"Added IP: {new_ip} to the list.")
    else:
        print(f"IP: {new_ip} already exists in the list.")

def check_and_update_ip_lists(tshark_output):
    tshark_ips = json.loads(tshark_output)
    for ip_list in ip_lists:
        for ip in tshark_ips:
            update_ip_list(ip_list, ip)


# SIGINT HANDLER FUNCTION
def handler(signum, frame):
    print("\nPRESS CTRL + C")
    
    # iptables reset
    subprocess.run("docker exec -i -t oai-spgwu /bin/bash -c 'iptables -F'", shell=True, check=True)

    #강제 종료
    sys.exit(0)


# SIGINT
signal.signal(signal.SIGINT, handler)


# UDP_SOCKET_PROGRAMMING
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((host, port))

print(f"UDP 서버가 {host}:{port}에서 실행 중입니다.")

while True:
    data, client_address = server_socket.recvfrom(1024)

    data = data.decode('utf-8')
    print(f"클라이언트로부터 수신: {data}")

    while(True):
        ip_lists = run_tshark()
        print(ip_lists)
        #check_and_update_ip_lists()
        time.sleep(5)


'''

['12.1.1.2\t\n']

'''
