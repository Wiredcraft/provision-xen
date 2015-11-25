
import os
import shutil
import subprocess
import tempfile

from jinja2 import Template
from templates import XEN_CONFIG_TPL, DEB_IFACE_TPL, RH_IFACE_TPL


def prepare_xen_config(server, dest='.'):
    '''
    Prepare the Xen config file
    '''
    server.update({'dest': os.path.realpath(dest)})
    template = Template(XEN_CONFIG_TPL)
    return template.render(server)

def mount_images(disk):
    '''
    Mount a disk file in loopback mode, and return the folder
    '''
    tempfolder = tempfile.mkdtemp()
    command = 'mount -o loop %s %s' % (disk, tempfolder)
    print command
    subprocess.Popen(command)
    return tempfolder

def umount_images(mount_point):
    '''
    Mount a disk file in loopback mode, and return the folder
    '''
    subprocess.Popen('umount %s' % (mount_point))

def get_distrib_family(base):
    '''
    Look at the folder structure in the base folder and define the distrib 
    '''
    if os.path.exists(os.path.join(base, 'etc/sysconfig')):
        return 'redhat'
    if os.path.exists(os.path.join(base, 'etc/network/interfaces')):
        return 'debian'
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

    # Copy/resize the disk files
    shutil.copy(os.path.join(template_folder, 'disk.img'), os.path.join(dest_folder, 'disk.img'))
    subprocess.Popen('/sbin/e2fsck -f %s' % (os.path.join(dest_folder, 'disk.img')))
    subprocess.Popen('/sbin/resize2fs %s %sG' % (os.path.join(dest_folder, 'disk.img'), server.get('disk')))

    # Handle SWAP
    subprocess.Popen('dd if=/dev/zero of=%s bs=%s seek=%s count=0' % (
            os.path.join(dest_folder, 'swap.img'),
            1024*1024,
            server.get('swap')*1024
        ))
    subprocess.Popen('/sbin/mkswap %s' % (
            os.path.join(dest_folder, 'swap.img')
        ))

    # Do the image update
    mount_point = mount_images(os.path.join(dest_folder, 'disk.img'))
    os_family = get_distrib_family(mount_point)
    if os_family == 'redhat':
        for iface in server.get('interfaces'):
            with open(os.path.join(mount_point, 'etc/sysconfig/network-scripts/ifcfg-'+ iface.get('name')), 'w') as f:
                template = Template(RH_IFACE_TPL)
                f.write(template.render(iface))
    elif os_family == 'debian':
        with open(os.path.join(mount_point, 'etc/network/interfaces'), 'w') as f:
            template = Template(DEB_IFACE_TPL)
            f.write(template.render(server.get('interfaces')))
    else:
        print "Unknown os - no network configured"

    if server.get('hostname'):
        with open(os.path.join(mount_point, 'etc/hostname'), 'w') as f:
            f.write(server.get('hostname'))

    umount_images(mount_point)

    if not createonly:
        subprocess.Popen('sudo /usr/sbin/xl create %s' % (config_file))