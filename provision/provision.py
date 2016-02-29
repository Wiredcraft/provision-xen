import os
import stat
import sys
import shutil
import shlex
import subprocess
import tempfile

from jinja2 import Template
from templates import XEN_CONFIG_TPL, XEN_CONFIG_LVM_TPL, DEB_IFACE_TPL, RH_IFACE_TPL, IPTABLES_TPL

def _run(command, message='', continue_on_failure=False, should_fail=False):
    '''
    Execute a command, display message, resume or not on failure
    '''
    print '%s ...' % (message),
    cmd = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    while type(cmd.poll()) == type(None):
        pass

    if cmd.returncode != 0:
        if should_fail:
            print '[OK]'
        else:
            print '[Error]'
            print 'command: %s' % command
            print 'stdout: %s' % cmd.stdout.read()
            print 'stderr: %s' % cmd.stderr.read()
            if not continue_on_failure:
                sys.exit(cmd.returncode)
    else:
        print '[OK]'


def prepare_xen_config(server, dest='.'):
    '''
    Prepare the Xen config file
    '''
    server.update({'dest': os.path.realpath(dest)})

    if server.get('lvm'):
        template = Template(XEN_CONFIG_LVM_TPL)
    else:
        template = Template(XEN_CONFIG_TPL)
    return template.render(server)

def mount_images(disk):
    '''
    Mount a disk file in loopback mode or mount a block device,
    and return the folder.
    '''
    tempfolder = tempfile.mkdtemp()
    mode = os.stat(disk).st_mode

    # If it is a block device
    if stat.S_ISBLK(mode):
        _run('mount %s %s' % (disk, tempfolder), message='Mounting block device: %s' % disk)
    else:
        _run('mount -o loop %s %s' % (disk, tempfolder), message='Mounting image %s in loopback' % disk)
    return tempfolder

def umount_images(mount_point):
    '''
    Mount a disk file in loopback mode, and return the folder
    '''
    _run('umount %s' % (mount_point), message='Unmounting %s' % mount_point)

def get_distrib_family(base):
    '''
    Look at the folder structure in the base folder and define the distrib 
    '''
    if os.path.exists(os.path.join(base, 'etc/sysconfig')):
        return 'redhat'
    elif os.path.exists(os.path.join(base, 'etc/network/interfaces')):
        return 'debian'
    else:
        return False


def build(server=None, createonly=False, templates='', dest='.'):
    '''
    Provided with a server definition; build the server
    '''
    if not server:
        raise RuntimeError('Invalid server definition')

    dest_folder = os.path.join(os.path.realpath(dest), server.get('name'))
    config_file = os.path.join(dest_folder, server.get('name') +'.cfg')
    if os.path.exists(config_file):
        raise RuntimeError('Xen config file already exist')

    _run('xl list %s' % server.get('name'), 
        message='Checking if there is already a running server with the same name',
        should_fail=True)

    template_folder = os.path.join(os.path.realpath(templates), server.get('image'))
    if not os.path.exists(os.path.join(template_folder, 'disk.img')):
        raise RuntimeError('Missing template image')
    
    try:
        os.makedirs(dest_folder)
    except OSError as e:
        # File exist
        if e.errno == 17:
            pass
        else:
            raise e

    # Copy the config file
    config = prepare_xen_config(server)
    with open(config_file, 'w') as f:
        f.write(config)

    if server.get("lvm"):
        _run(
            'lvcreate -L %sG -n xen-sbux-%s-disk wcl-vg' % (
                float(server.get('disk')),
                server.get('name'),
            )
        )
        _run(
            'lvcreate -L %sG -n xen-sbux-%s-swap wcl-vg' % (
                float(server.get('swap')),
                server.get('name'),
            )
        )
        _run(
            'mkswap /dev/wcl-vg/xen-sbux-%s-swap' % server.get('name')
        )
        _run(
            'dd if=%s of=/dev/wcl-vg/xen-sbux-%s-disk bs=1M' % (
                os.path.join(template_folder, 'disk.img'),
                server.get('name')
            )
        )
        _run(
            'resize2fs /dev/wcl-vg/xen-sbux-%s-disk' % server.get('name'),
            message='Resizing the disk'
        )
        _run(
            'ln -s /dev/wcl-vg/xen-sbux-%s-disk %s' % (
                server.get('name'),
                os.path.join(dest_folder, 'disk.img'),
            )
        )
        _run(
            'ln -s /dev/wcl-vg/xen-sbux-%s-swap %s' % (
                server.get('name'),
                os.path.join(dest_folder, 'swap.img'),
            )
        )

    else:
        # Copy/resize the disk files
        shutil.copy(os.path.join(template_folder, 'disk.img'), os.path.join(dest_folder, 'disk.img'))
        _run('e2fsck -f -p %s' % (os.path.join(dest_folder, 'disk.img')),
            message='Checking the filesystem')

        _run(
            'resize2fs %s %sM' % (
                os.path.join(dest_folder, 'disk.img'),
                int(float(server.get('disk'))*1024)
            ),
            message='Resizing the disk'
        )

        # Handle SWAP
        _run('dd if=/dev/zero of=%s bs=%s seek=%s count=0' % (
                    os.path.join(dest_folder, 'swap.img'),
                    1024*1024,
                    int(float(server.get('swap'))*1024),
                ),
            message='Creating the SWAP disk')
        _run('mkswap %s' % (
                    os.path.join(dest_folder, 'swap.img')
                ),
            message='Setup the SWAP area with mkswap')

    # Do the image update
    mount_point = mount_images(os.path.join(dest_folder, 'disk.img'))

    os_family = get_distrib_family(mount_point)
    if os_family == 'redhat':
        for iface in server.get('interfaces'):
            with open(os.path.join(mount_point, 'etc/sysconfig/network-scripts/ifcfg-'+ iface.get('name')), 'w') as f:
                template = Template(RH_IFACE_TPL)
                print '  - Preparing config for interface: %s' % iface.get('name')
                f.write(template.render(iface))
    elif os_family == 'debian':
        with open(os.path.join(mount_point, 'etc/network/interfaces'), 'w') as f:
            template = Template(DEB_IFACE_TPL)
            print '  - Preparing config for interfaces: %s' % ', '.join([iface.get('name') for iface in server.get('interfaces')])
            f.write(template.render(server))

        # Prepare iptables if needed... (mostly for routers)
        if server.get('firewall'):
            with open(os.path.join(mount_point, 'etc/iptables.rules'), 'w') as f:
                template = Template(IPTABLES_TPL)
                print '  - Preparing Firewall rules'
                f.write(template.render(server.get('firewall')))
            with open(os.path.join(mount_point, 'etc/network/if-pre-up.d/iptables'), 'w') as f:
                print '  - Preparing Firewall restore script'
                f.write('#!/bin/sh\n/sbin/iptables-restore < /etc/iptables.rules')
            print '  - Setting proper permissions for firewall files'
            os.chmod(os.path.join(mount_point, 'etc/network/if-pre-up.d/iptables'), stat.S_IRUSR | stat.S_IXUSR)
            os.chmod(os.path.join(mount_point, 'etc/iptables.rules'), stat.S_IRUSR)

    else:
        print "Unknown os - no network configured"

    if server.get('hostname'):
        with open(os.path.join(mount_point, 'etc/hostname'), 'w') as f:
            print '  - Preparing hostname'
            f.write(server.get('hostname'))

    umount_images(mount_point)

    if not createonly:
        _run('xl create %s' % (config_file), message='Launching the server')

    os.rmdir(mount_point)