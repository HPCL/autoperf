from .generic import Platform as GenericPlatform

class Platform(GenericPlatform):
    name     = "aciss"
    mpi_opts = "--mca btl_tcp_if_include torbr"
