PS C:\Users\User> ssh -i C:\Users\User\ssh-server root@78.46.234.142
Welcome to Ubuntu 24.04.2 LTS (GNU/Linux 6.8.0-58-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/pro

 System information as of Wed Jun  4 10:15:29 AM UTC 2025

  System load:  0.0               Processes:             131
  Usage of /:   7.8% of 37.23GB   Users logged in:       0
  Memory usage: 33%               IPv4 address for eth0: 78.46.234.142
  Swap usage:   0%                IPv6 address for eth0: 2a01:4f8:1c1a:f500::1


Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

1 additional security update can be applied with ESM Apps.
Learn more about enabling ESM Apps service at https://ubuntu.com/esm


*** System restart required ***
Last login: Wed Jun  4 00:19:18 2025 from 87.123.247.48
root@ubuntu-2gb-nbg1-1:~# ls
root@ubuntu-2gb-nbg1-1:~# docker ps
CONTAINER ID   IMAGE       COMMAND                  CREATED        STATUS        PORTS                                       NAMES
9afb327fa3b2   n8nio/n8n   "tini -- /docker-ent…"   10 hours ago   Up 10 hours   0.0.0.0:5678->5678/tcp, :::5678->5678/tcp   n8n_n8n_1
root@ubuntu-2gb-nbg1-1:~# client_loop: send disconnect: Connection reset
PS C:\Users\User> ssh -i C:\Users\User\ssh-server root@78.46.234.142
Welcome to Ubuntu 24.04.2 LTS (GNU/Linux 6.8.0-58-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/pro

 System information as of Thu Jun  5 01:51:07 PM UTC 2025

  System load:  0.0               Processes:             132
  Usage of /:   7.9% of 37.23GB   Users logged in:       0
  Memory usage: 33%               IPv4 address for eth0: 78.46.234.142
  Swap usage:   0%                IPv6 address for eth0: 2a01:4f8:1c1a:f500::1

 * Strictly confined Kubernetes makes edge and IoT secure. Learn how MicroK8s
   just raised the bar for easy, resilient and secure K8s cluster deployment.

   https://ubuntu.com/engage/secure-kubernetes-at-the-edge

Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

1 additional security update can be applied with ESM Apps.
Learn more about enabling ESM Apps service at https://ubuntu.com/esm


*** System restart required ***
Last login: Wed Jun  4 10:15:29 2025 from 87.123.247.44
root@ubuntu-2gb-nbg1-1:~# docker ps
CONTAINER ID   IMAGE       COMMAND                  CREATED        STATUS        PORTS                                       NAMES
9afb327fa3b2   n8nio/n8n   "tini -- /docker-ent…"   37 hours ago   Up 37 hours   0.0.0.0:5678->5678/tcp, :::5678->5678/tcp   n8n_n8n_1
root@ubuntu-2gb-nbg1-1:~# docker ps inspect
"docker ps" accepts no arguments.
See 'docker ps --help'.

Usage:  docker ps [OPTIONS]

List containers
root@ubuntu-2gb-nbg1-1:~# docker inspect 9afb327fa3b2
[
    {
        "Id": "9afb327fa3b24b59cf47829a8660e3aeea6ccaa728c84614993532291156750d",
        "Created": "2025-06-04T00:29:11.835692279Z",
        "Path": "tini",
        "Args": [
            "--",
            "/docker-entrypoint.sh"
        ],
        "State": {
            "Status": "running",
            "Running": true,
            "Paused": false,
            "Restarting": false,
            "OOMKilled": false,
            "Dead": false,
            "Pid": 11178,
            "ExitCode": 0,
            "Error": "",
            "StartedAt": "2025-06-04T00:29:11.967775083Z",
            "FinishedAt": "0001-01-01T00:00:00Z"
        },
        "Image": "sha256:0bcd42d640ba4e345bf1195b2ff6b70722054a8bb43b45dee83c61c2dd40107d",
        "ResolvConfPath": "/var/lib/docker/containers/9afb327fa3b24b59cf47829a8660e3aeea6ccaa728c84614993532291156750d/resolv.conf",
        "HostnamePath": "/var/lib/docker/containers/9afb327fa3b24b59cf47829a8660e3aeea6ccaa728c84614993532291156750d/hostname",
        "HostsPath": "/var/lib/docker/containers/9afb327fa3b24b59cf47829a8660e3aeea6ccaa728c84614993532291156750d/hosts",
        "LogPath": "/var/lib/docker/containers/9afb327fa3b24b59cf47829a8660e3aeea6ccaa728c84614993532291156750d/9afb327fa3b24b59cf47829a8660e3aeea6ccaa728c84614993532291156750d-json.log",
        "Name": "/n8n_n8n_1",
        "RestartCount": 0,
        "Driver": "overlay2",
        "Platform": "linux",
        "MountLabel": "",
        "ProcessLabel": "",
        "AppArmorProfile": "docker-default",
        "ExecIDs": null,
        "HostConfig": {
            "Binds": [
                "n8n_n8n_data:/home/node/.n8n:rw"
            ],
            "ContainerIDFile": "",
            "LogConfig": {
                "Type": "json-file",
                "Config": {}
            },
            "NetworkMode": "n8n_default",
            "PortBindings": {
                "5678/tcp": [
                    {
                        "HostIp": "",
                        "HostPort": "5678"
                    }
                ]
            },
            "RestartPolicy": {
                "Name": "unless-stopped",
                "MaximumRetryCount": 0
            },
            "AutoRemove": false,
            "VolumeDriver": "",
            "VolumesFrom": [],
            "ConsoleSize": [
                0,
                0
            ],
            "CapAdd": null,
            "CapDrop": null,
            "CgroupnsMode": "private",
            "Dns": null,
            "DnsOptions": null,
            "DnsSearch": null,
            "ExtraHosts": null,
            "GroupAdd": null,
            "IpcMode": "private",
            "Cgroup": "",
            "Links": null,
            "OomScoreAdj": 0,
            "PidMode": "",
            "Privileged": false,
            "PublishAllPorts": false,
            "ReadonlyRootfs": false,
            "SecurityOpt": null,
            "UTSMode": "",
            "UsernsMode": "",
            "ShmSize": 67108864,
            "Runtime": "runc",
            "Isolation": "",
            "CpuShares": 0,
            "Memory": 0,
            "NanoCpus": 0,
            "CgroupParent": "",
            "BlkioWeight": 0,
            "BlkioWeightDevice": null,
            "BlkioDeviceReadBps": null,
            "BlkioDeviceWriteBps": null,
            "BlkioDeviceReadIOps": null,
            "BlkioDeviceWriteIOps": null,
            "CpuPeriod": 0,
            "CpuQuota": 0,
            "CpuRealtimePeriod": 0,
            "CpuRealtimeRuntime": 0,
            "CpusetCpus": "",
            "CpusetMems": "",
            "Devices": null,
            "DeviceCgroupRules": null,
            "DeviceRequests": null,
            "MemoryReservation": 0,
            "MemorySwap": 0,
            "MemorySwappiness": null,
            "OomKillDisable": null,
            "PidsLimit": null,
            "Ulimits": null,
            "CpuCount": 0,
            "CpuPercent": 0,
            "IOMaximumIOps": 0,
            "IOMaximumBandwidth": 0,
            "MaskedPaths": [
                "/proc/asound",
                "/proc/acpi",
                "/proc/kcore",
                "/proc/keys",
                "/proc/latency_stats",
                "/proc/timer_list",
                "/proc/timer_stats",
                "/proc/sched_debug",
                "/proc/scsi",
                "/sys/firmware",
                "/sys/devices/virtual/powercap"
            ],
            "ReadonlyPaths": [
                "/proc/bus",
                "/proc/fs",
                "/proc/irq",
                "/proc/sys",
                "/proc/sysrq-trigger"
            ]
        },
        "GraphDriver": {
            "Data": {
                "LowerDir": "/var/lib/docker/overlay2/f3ea4db40f6cd2ad64672c84ea94a405083af8aba7a812d90b262891114db2c9-init/diff:/var/lib/docker/overlay2/7f614dce69a70c001dba8d039e0aada06ebd11d8937dc1cc13f08cf1d21ca180/diff:/var/lib/docker/overlay2/bbf5750e35674345524190bdfe76e1b95372acdba57e69f0cdf93dee0e638c6b/diff:/var/lib/docker/overlay2/3099553e12b8bbf9adced54dd1f8c54a681ac31a109e2587a2c806cd48464521/diff:/var/lib/docker/overlay2/8dbf0edbde715a51f91404ee8c81010a71b4068921fe8532c7eab155305bbd64/diff:/var/lib/docker/overlay2/ae52f27ea4bc0013c94d654478e9bff6441a87a813ebfc0b62a031eeed53510f/diff:/var/lib/docker/overlay2/29c797e30525f424f5c5974ff8232abbb50a15c31ba943a29575fced8985a69a/diff:/var/lib/docker/overlay2/0ce8607b0e805a978218dc2c5fcc53fa0f7bc7674dd7d9bbc5dcb44d89c15976/diff:/var/lib/docker/overlay2/263ba5b390e7d5f845489a4f2103c6ecc267d26195443950dea307f4f6a6e980/diff:/var/lib/docker/overlay2/61594ec73cbd884cd771164f23109d9dbc4d0be371cd6f510c591c9ebffa85cb/diff:/var/lib/docker/overlay2/940d4cd2e779488357f08b77ec53f6eb2afdd103ff4882427b1cc2add3e35e9a/diff:/var/lib/docker/overlay2/26c9cf255fae88cac1b4a58947131092717c53687558a7a86582f13461078a39/diff:/var/lib/docker/overlay2/752c5fe1431f1d08b75c5c0937c8a611d10579c617d04f86fb5be0478fd63d18/diff:/var/lib/docker/overlay2/35797c8d831ca7953f0a05d4ee1d0fb84fa48cd253dbff430d8eaa39e5c556f9/diff",
                "MergedDir": "/var/lib/docker/overlay2/f3ea4db40f6cd2ad64672c84ea94a405083af8aba7a812d90b262891114db2c9/merged",
                "UpperDir": "/var/lib/docker/overlay2/f3ea4db40f6cd2ad64672c84ea94a405083af8aba7a812d90b262891114db2c9/diff",
                "WorkDir": "/var/lib/docker/overlay2/f3ea4db40f6cd2ad64672c84ea94a405083af8aba7a812d90b262891114db2c9/work"
            },
            "Name": "overlay2"
        },
        "Mounts": [
            {
                "Type": "volume",
                "Name": "n8n_n8n_data",
                "Source": "/var/lib/docker/volumes/n8n_n8n_data/_data",
                "Destination": "/home/node/.n8n",
                "Driver": "local",
                "Mode": "rw",
                "RW": true,
                "Propagation": ""
            }
        ],
        "Config": {
            "Hostname": "9afb327fa3b2",
            "Domainname": "",
            "User": "node",
            "AttachStdin": false,
            "AttachStdout": false,
            "AttachStderr": false,
            "ExposedPorts": {
                "5678/tcp": {}
            },
            "Tty": false,
            "OpenStdin": false,
            "StdinOnce": false,
            "Env": [
                "N8N_BASIC_AUTH_ACTIVE=true",
                "N8N_BASIC_AUTH_USER=User",
                "N8N_BASIC_AUTH_PASSWORD=123123",
                "N8N_HOST=n8n.unit-y-ai.io",
                "N8N_PORT=5678",
                "N8N_PROTOCOL=https",
                "WEBHOOK_URL=https://n8n.unit-y-ai.io/",
                "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
                "NODE_VERSION=20.19.2",
                "YARN_VERSION=1.22.22",
                "NODE_ICU_DATA=/usr/local/lib/node_modules/full-icu",
                "NODE_ENV=production",
                "N8N_RELEASE_TYPE=stable",
                "SHELL=/bin/sh"
            ],
            "Cmd": null,
            "Image": "n8nio/n8n",
            "Volumes": {
                "/home/node/.n8n": {}
            },
            "WorkingDir": "/home/node",
            "Entrypoint": [
                "tini",
                "--",
                "/docker-entrypoint.sh"
            ],
            "OnBuild": null,
            "Labels": {
                "com.docker.compose.config-hash": "d18e28e24f5a653a58cd9d1858f338a8423a9e6557d3a12f5ae85abe367f593c",
                "com.docker.compose.container-number": "1",
                "com.docker.compose.oneoff": "False",
                "com.docker.compose.project": "n8n",
                "com.docker.compose.project.config_files": "docker-compose.yml",
                "com.docker.compose.project.working_dir": "/opt/unity/n8n",
                "com.docker.compose.service": "n8n",
                "com.docker.compose.version": "1.29.2",
                "org.opencontainers.image.description": "Workflow Automation Tool",
                "org.opencontainers.image.source": "https://github.com/n8n-io/n8n",
                "org.opencontainers.image.title": "n8n",
                "org.opencontainers.image.url": "https://n8n.io",
                "org.opencontainers.image.version": ""
            }
        },
        "NetworkSettings": {
            "Bridge": "",
            "SandboxID": "6ca818600005fad5e30d0b07f9b675e21167851b2b9a8f6be7d9f96039cf708b",
            "SandboxKey": "/var/run/docker/netns/6ca818600005",
            "Ports": {
                "5678/tcp": [
                    {
                        "HostIp": "0.0.0.0",
                        "HostPort": "5678"
                    },
                    {
                        "HostIp": "::",
                        "HostPort": "5678"
                    }
                ]
            },
            "HairpinMode": false,
            "LinkLocalIPv6Address": "",
            "LinkLocalIPv6PrefixLen": 0,
            "SecondaryIPAddresses": null,
            "SecondaryIPv6Addresses": null,
            "EndpointID": "",
            "Gateway": "",
            "GlobalIPv6Address": "",
            "GlobalIPv6PrefixLen": 0,
            "IPAddress": "",
            "IPPrefixLen": 0,
            "IPv6Gateway": "",
            "MacAddress": "",
            "Networks": {
                "n8n_default": {
                    "IPAMConfig": null,
                    "Links": null,
                    "Aliases": [
                        "n8n",
                        "9afb327fa3b2"
                    ],
                    "MacAddress": "02:42:ac:12:00:02",
                    "DriverOpts": null,
                    "NetworkID": "b259a24f909e6d4bfc5c84c79a2a54cc37b45009f95eab56c372fcdf7f21e823",
                    "EndpointID": "bdd44db4634e4de98ce19e492c2fa1be0916d4f28c040ad94bfbef6665d4278e",
                    "Gateway": "172.18.0.1",
                    "IPAddress": "172.18.0.2",
                    "IPPrefixLen": 16,
                    "IPv6Gateway": "",
                    "GlobalIPv6Address": "",
                    "GlobalIPv6PrefixLen": 0,
                    "DNSNames": [
                        "n8n_n8n_1",
                        "n8n",
                        "9afb327fa3b2"
                    ]
                }
            }
        }
    }
