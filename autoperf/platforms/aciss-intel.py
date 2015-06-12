from .generic import Platform as GenericPlatform

class Platform(GenericPlatform):
    name     = "aciss-intel"

    def __init__(self, experiment):
        GenericPlatform.__init__(self, experiment)

