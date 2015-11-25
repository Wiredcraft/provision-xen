# Provision-xen

Simple tool to spawn VM based on templates available in the server.

# Pre-requisite

- Xen server
- Bridges (it does not create on the fly)
- Template files (use xen-create-image from xen-tools package); any valid server image is good
- Root access - since we manipulate the images, resize, etc. 

# Install

```
pip install git+https://github.com/wiredcraft/provision-xen.git
```

# Run

```
provision create ........
```

Full list of options / parameters via

```
provision --help
```

# Next

- Add JSON config file instead of CLI params
- better use of subprocess (kinda dirty)
- unit testing
- configure / delete action
- drop root requirement?
- wrapper to spawn full environment, manage bridges, etc.
- ability to list valid distribs and flavors
- API based service
