import os
import subprocess
import time
import psutil

class UDPEchoServer:
  def __init__(self, adapter_name: str, adapter_mac: str, server_ip: str, server_port: int):
    os.system('ip netns add udp_echo_server_ns')
    os.system(f'ip link add {adapter_name} type veth peer name tap2')
    os.system('ip link set tap2 netns udp_echo_server_ns')
    os.system(f'ip link set dev {adapter_name} up')
    os.system('ip netns exec udp_echo_server_ns ip link set dev tap2 up')
    os.system(f'ip link set dev {adapter_name} address {adapter_mac}')
    os.system(f'ip netns exec udp_echo_server_ns ip addr add {server_ip}/24 dev tap2')
    os.system('ip netns exec udp_echo_server_ns ethtool --offload tap2 rx off tx off')
    os.system('ip netns exec udp_echo_server_ns ethtool -K tap2 gso off')
    self.process = subprocess.Popen(f'ip netns exec udp_echo_server_ns ncat -e /bin/cat -k -u -l {server_port}', shell=True)

  def __enter__(self):
    return self
  
  def __exit__(self, exc_type, exc_value, exc_traceback):
    self.close()

  def close(self):
    self.kill_process_and_children(self.process.pid)
    time.sleep(1)
    os.system('ip netns delete udp_echo_server_ns')

  def kill_process_and_children(self, pid: int, sig: int = 15):
    try:
        proc = psutil.Process(pid)
    except psutil.NoSuchProcess:
        return

    for child_process in proc.children(recursive=True):
        child_process.send_signal(sig)

    proc.send_signal(sig)

