from .generic import Platform as GenericPlatform

class Platform(GenericPlatform):
    name     = "aciss"

    def __init__(self, experiment):
        GenericPlatform.__init__(self, experiment)

        if self.launcher == "mpirun" or self.launcher == "mpiexec":
            self.launcher_opts += "--mca btl_tcp_if_include torbr"
