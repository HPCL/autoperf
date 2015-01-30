from .generic import Platform as GenericPlatform

class Platform(GenericPlatform):
    name     = "nersc"
    launcher = "aprun"
