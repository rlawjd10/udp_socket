import socket
import subprocess
import signal
import time
import sys

host = '192.168.0.13'
port = 3030

# DROP 12.1.0.0/16
subprocess.run("docker exec -i -t oai-spgwu /bin/bash -c 'iptables -A FORWARD -s 12.1.0.0/16 -j DROP'", shell=True, check=True)
# ACCEPT 192.168.0.12(TINM)
subprocess.run("docker exec -i -t oai-spgwu /bin/bash -c 'iptables -I FORWARD 1 -s 12.1.0.0/16 -d 192.168.0.12 -j ACCEPT'", shell=True, check=True)

ip_list = []
accept_list = []

# RUN TSHARK - output.json
def run_tshark():
    subprocess.run("tshark -i demo-oai -Y '(ip.src==12.1.0.0/16)&&(ip.dst==192.168.0.12)&&(frame.len eq 98)' -T fields -e ip.src -a 'duration:3' -e json > output.json", shell=True, capture_output=True, text=True)
    
    global ip_list
    
    # 파일에 있는 ip를 중복없이 ip_list에 저장
    f = open("output.json", "r")
    for line in f:
        ip = line.split(",")[-1].strip()
        ip_list.append(ip)
    ip_list = list(set(ip_list))
    f.close()
    
    print(f"run_tshark {ip_list}")
    
    return ip_list

def check_and_update_ip_lists():
    global ip_list
    global accept_list

    f = open("output.json", "r")

    for new_ip in ip_list:
        if new_ip not in accept_list:
            subprocess.run(f"docker exec -i -t oai-spgwu /bin/bash -c 'iptables -I FORWARD 1 -j ACCEPT -s {new_ip}'", shell=True, check=True)
            accept_list.append(new_ip)

    print(f"check accept ip_list :  {ip_list}")
    print(f"check accept accept_list : {accept_list}")

    file_list = []
    for line in f:
        ip = line.split(",")[-1].strip()
        file_list.append(ip)
    file_list = list(set(file_list))
    print(f"check drop file_list : {file_list}")
    for ip in accept_list:
        if ip not in file_list:
            print(f"drop ip :  {ip}")
            subprocess.run(f"docker exec -i -t oai-spgwu /bin/bash -c 'iptables -D FORWARD -j ACCEPT -s {ip}'", shell=True, check=True)
            accept_list.remove(ip)
            ip_list.remove(ip)
                
    print(f"check after drop ip_list : {ip_list}")
    print(f"check after drop accept_list : {accept_list}")

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
        check_and_update_ip_lists()
        time.sleep(5)
        
