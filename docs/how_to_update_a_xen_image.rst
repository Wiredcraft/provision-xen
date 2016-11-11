How to update a Xen image
=========================

Pre-requisite
-------------

You need a "working" xen image / template.

Quick steps
-----------

Quick highlight of the steps:
- find the base image
- copy the image file into a new file
- extend the size of the file (using `resize2fs` or `dd`)
- extend the filesystem / partition
- mount the filesystem on the disk
- chroot the mounted folder
- do the required operations (e.g. yum update / yum install ...)
- exit chroot
- resize / shrink filesystem

Et Voila!

Steps
-----

Copy the new file
`````````````````

.. code-block:: bash
    cp base_image.img new_image.img


Extend the file size
````````````````````

Obviously - you need to increase the size of the file - not decrease - or you'll loose data.

In the example below, we're gonna increase the disk space up to 4GB, by writing 1 byte at the 4G distance from the beginning of the file.

The next command is to confirm the size of the file.

.. code-block:: bash
    # Use dd OR
    dd if=/dev/zero of=new_image.img count=1 seek=4G bs=1

    # Use resize2fs directly with the new size
    resize2fs new_image.img 4G

    ls -la new_image.img


Extent the partition / filesystem
`````````````````````````````````

Depending what your file is made of, you may have to extend the partition AND the filesystem (if your file is acting ``as a disk``), or only extend the filesystem (if your file is acting ``as a partition``).

.. code-block:: bash
    # This should show you the new size of the "file"
    fdisk -l new_image.img

    # Extend the filesystem to the new max size
    resize2fs new_image.img

Mount the filesystem
````````````````````

.. code-block:: bash
    # Mount the filesystem as a loopback device
    mount -o loop new_image.img /some/folder

    # Check the content
    ls /some/folder

Chroot to the filesystem
````````````````````````

Since you want to operate on the filesystem, you want to access it and be "as close as" possible from the OS in between.

**Note**: you may want to mount the /proc filesystem and maybe /dev as well for some commands to work as expected.

.. code-block:: bash
    # Not absolutely required - but sometime useful
    mount -o bind /proc /some/folder/proc
    mount -o bind /dev /some/folder/dev

    # Then access your OS
    chroot /some/folder

    # See the change in root - and the newly available commands
    # For example - you might now see `yum` even if you are on 
    # an underlying ubuntu box


Do the operations
`````````````````

Do whatever you need to do; e.g.
- yum update
- apt-get update / upgrade
- install this and that ....

Eventually - since you want to use this image as a new template, make sure you clean everything up!

.. code-block:: bash
    # Check what takes space and remove useless stuff (e.g. old kernel)
    du -sh */.

    # Clean the repos from all the cache
    yum clean all

Exit the chroot
```````````````

.. code-block:: bash
    # Hardcore
    exit

    # Unmount all mounted filesystems
    umount /some/folder/dev
    umount /some/folder/proc
    umount /some/folder

Resize / shrink filesystem
``````````````````````````

You are gonna need to ensure the data are all at the "beginning" of the disk so you can effectively redice the size without loosing data

.. code-block:: bash
    # Sanitize the disk
    e2fsck -f new_image.img

    # Resize the partition to its minimal size
    resize2fs -M new_image.img



