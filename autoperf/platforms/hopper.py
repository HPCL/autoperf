from .generic import Platform as GenericPlatform

class Platform(GenericPlatform):
    name         = "hopper"
    mpi_launcher = "aprun"
