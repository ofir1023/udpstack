import os
import subprocess

class UDPEchoServer:
  def __init__(self, adapter_name: str, adapter_ip: str, server_ip: str, server_port: int):
    os.system('ip netns add udp_echo_server_ns')
    os.system(f'ip link add {adapter_name} type veth peer name tap2')
    os.system('ip link set tap2 netns udp_echo_server_ns')
    os.system(f'ip link set dev {adapter_name} up')
    os.system('ip netns exec udp_echo_server_ns ip link set dev tap2 up')
    os.system(f'ip addr add {adapter_ip}/24 dev tap1')
    os.system(f'ip netns exec udp_echo_server_ns ip addr add {server_ip}/24 dev tap2')
    self.process = subprocess.Popen(f'ip netns exec ns2 ncat -e /bin/cat -k -u -l {server_port}', shell=True)

  def __enter__(self):
    return self
  
  def __exit__(self, exc_type, exc_value, exc_traceback):
    self.close()

  def close(self):
    self.process.terminate()
    os.system('ip netns delete udp_echo_server_ns')
