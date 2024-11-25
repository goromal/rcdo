import paramiko
from scp import SCPClient
import os

def parse_remote_hosts(remote_host, ssh_config): # TODO utilize SSH config
    hops = []
    host_specs = remote_host.split("+")
    for host_spec in host_specs:
        if "@" in host_spec:
            user = host_spec.split("@")[0]
        else:
            raise Exception("Must specify an SSH username")
        if ":" in host_spec:
            pwd = host_spec.split("@")[1].split(":")[1]
            host = host_spec.split("@")[1].split(":")[0]
        else:
            raise Exception("Must specify an SSH password")
        hops.append((user, pwd, host))
    return hops

def create_ssh_client(hostname, username, password, port=22, proxy=None):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, port, username, password, sock=proxy)
    return ssh

def create_proxy(ssh_client, target_host, target_port=22): # TODO verify
    """Creates a proxy for the next hop using the existing SSH client."""
    transport = ssh_client.get_transport()
    proxy = transport.open_channel("direct-tcpip", (target_host, target_port), ("", 0))
    return proxy

def run_remote_command(ssh, command):
    stdin, stdout, stderr = ssh.exec_command(command)
    stdout_output = stdout.read().decode('utf-8')
    stderr_output = stderr.read().decode('utf-8')
    return stdout_output, stderr_output

def copy_file_from_remote(ssh, remote_path, local_path):
    with SCPClient(ssh.get_transport()) as scp:
        scp.get(remote_path, local_path)

def run_local_command(ssh, command):
    pass # TODO

class RemoteWorker(object):
    def __init__(
        self, remote_host: str, cmd: str, input_spec, output_spec, ssh_config, verbose: bool
    ):
        self.verbose = verbose
        self.cmd = cmd
        self.input_spec = input_spec
        self.output_spec = output_spec
        self.ssh_clients = []
        self.ssh_config = paramiko.config.SSHConfig()

        try:
            with open(os.path.expanduser(ssh_config), "r") as f:
                self.ssh_config.parse(f)
        except:
            if self.verbose:
                print(f"WARNING: failed to load SSH config {ssh_config}")

        hops = parse_remote_hosts(remote_host, self.ssh_config)
        proxy = None
        for hop in hops:
            if self.verbose:
                print(f"Creating SSH client {hop[0]}@{hop[2]} with pass {hop[1]}...")
            ssh = create_ssh_client(hop[2], hop[0], hop[1], proxy=proxy)
            self.ssh_clients.append(ssh)
            proxy = create_proxy(ssh, hop[2])
        
        self.target_ssh = self.ssh_clients[-1]

    def run_local(self):
        raise NotImplementedError("Local commands not supported yet!")

    def run_remote(self):
        stdout, stderr = run_remote_command(self.target_ssh, self.cmd)
        
        if stdout:
            print("Command output:")
            print(stdout)
        if stderr:
            print("Command error:")
            print(stderr)
        
        if self.input_spec is not None:
            if self.output_spec is None:
                output_spec = "result"
            else:
                output_spec = self.output_spec
            copy_file_from_remote(self.target_ssh, self.input_spec, output_spec)
            if self.verbose:
                print(f"File copied to {output_spec}.")
        elif self.verbose:
            print(f"Foregoing any file transfer.")

    def cleanup(self):
        for ssh in reversed(self.ssh_clients):
            ssh.close()
