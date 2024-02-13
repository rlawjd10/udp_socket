import socket
import subprocess
import os
import signal
import time
import sys

host = '192.168.0.13'
port = 3030

# DROP 12.1.0.0/16 (iptables rule)
subprocess.run("docker exec -i -t oai-spgwu /bin/bash -c 'iptables -A FORWARD -s 12.1.0.0/16 -j DROP'", shell=True, check=True)
subprocess.run("docker exec -i -t oai-spgwu /bin/bash -c 'iptables -I FORWARD 1 -s 12.1.0.0/16 -d 192.168.0.12 -j ACCEPT'", shell=True, check=True)

# TSHARK
def ip_tshark():
    try:
        # tshark autostop condition : duration 1
        result = os.popen("tshark -i demo-oai -Y '(ip.src==12.1.0.0/16)&&(ip.dst==192.168.0.12)&&(frame.len eq 98)' -T fields -e ip.src -a 'duration:1'").read()
        
        # ip checking
        print(result.split(",")[-1])

        ip_addr = result.split(",")[-1]
        subprocess.run(f"docker exec -i -t oai-spgwu /bin/bash -c 'iptables -I FORWARD 1 -j ACCEPT -s {ip_addr}'", shell=True, check=True)
        
        #subprocess.run("tshark -i demo-oai -Y '(ip.src==12.1.0.0/16)&&(ip.dst==192.168.0.12)&&(frame.len eq 98)' -T fields -e ip.src -a 'duration:10'", shell=True, check=True)
        try:
            result = subprocess.run("tshark -i demo-oai -Y '(ip.src==12.1.0.0/16)&&(ip.dst==192.168.0.12)&&(frame.len eq 98)' -T fields -e ip.src -c 10", shell=True, check=True, capture_output=True, text=True, timeout=10)
            for packet in result.stdout.split('\n'):
                if packet.strip():
                    print("Received packet from:", packet.strip())
        except subprocess.TimeoutExpired:
            print("Timeout occurred. Not enough packets received.")

        # IP를 return하거나 전역변수에 IP 넣고 관리하는게 나을 듯
        return print("tshark success")
        
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        return []


# SIGINT HANDLER FUNCTION
def handler(signum, frame):
    print("PRESS CTRL + C")
    
    # iptables reset
    subprocess.run("docker exec -i -t oai-spgwu /bin/bash -c 'iptables -F'", shell=True, check=True)

    #강제 종료
    sys.exit(0)


# SIGINT
signal.signal(signal.SIGINT, handler)


# UDP_SOCKET PROGRAMMING
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((host, port))

print(f"UDP 서버가 {host}:{port}에서 실행 중입니다.")

while True:
    data, client_address = server_socket.recvfrom(1024)

    data = data.decode('utf-8')
    print(f"클라이언트로부터 수신: {data}")

    if data.strip() == 'success':
        try:
            ip_tshark()
        except subprocess.CalledProcessError as e:
            print(f"스크립트 입력 중 에러 발생")
