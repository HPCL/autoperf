import re

from os      import listdir
from os.path import join, isdir

class _CPUInfo:
    def __eq__(self, other):
        return self.model == other.model

    def __ne__(self, other):
        return not self.__eq__(other)

    def __init__(self, cpuid, procinfo):
        self.id    = cpuid
        self.cache = dict()

        # get cache info
        sysfs = "/sys/devices/system/cpu/cpu%d" % cpuid
        for d in listdir(join(sysfs, "cache")):
            index = join(sysfs, "cache", d)

            with open(join(index, "level")) as f:
                level = f.read().strip()

            with open(join(index, "type")) as f:
                type = f.read().strip()

            with open(join(index, "size")) as f:
                size = f.read().strip()
                m = re.match(r'(\d+)K', size)
                size = int(m.group(1))

            key = "L%d_" % int(level)

            # I/D cache
            if type == "Data":
                self.cache[key+"D"] = size
            elif type == "Instruction":
                self.cache[key+"I"] = size

            # synthesize total cache size from I/D
            if key in self.cache:
                self.cache[key] += size
            else:
                self.cache[key] = size

        # get topology info
        with open(join(sysfs, "topology", "physical_package_id")) as f:
            self.physical_id = int(f.read())

        # get other info from /proc/cpuinfo
        for line in procinfo.split('\n'):
            m = re.match(r"model name\s*: (.*)", line)
            if m is not None:
                self.model = m.group(1)

            m = re.match(r"cpu cores\s*: (.*)", line)
            if m is not None:
                self.cores = int(m.group(1))

            m = re.match(r"physical id\s*: (.*)", line)
            if m is not None:
                if self.physical_id != int(m.group(1)):
                    raise Exception("Inconsistant info between /sys and /proc")

def _get_cpu_info():
    metadata = dict()

    with open("/proc/cpuinfo") as f:
        procinfo = f.read().split('\n\n')

    procinfo = [info for info in procinfo if info != '']

    # CPU core / thread number
    metadata["META_CORE_NUM"] = len(procinfo)

    cpuinfo     = [ ]
    physical_id = set()
    for cpuid in range(len(procinfo)):
        cpuinfo.append(_CPUInfo(cpuid, procinfo[cpuid]))

    for cpuid in range(len(procinfo)):
        a = cpuinfo[cpuid]
        b = cpuinfo[(cpuid+1)%len(procinfo)]
        if a != b:
            raise Exception("Different CPU models are installed")
        else:
            physical_id.add(a.physical_id)


    # cache size in kB
    for key in cpuinfo[0].cache:
        metadata["META_" + key + "SIZE"] = cpuinfo[0].cache[key]

    # physical CPU number
    metadata["META_CPU_NUM"] = len(physical_id)

    # CPU model
    metadata["META_CPU_MODEL"] = cpuinfo[0].model

    return metadata

def _get_memory_info():
    metadata = dict()

    with open("/proc/meminfo") as f:
        meminfo = f.read().split('\n')

    for line in meminfo:
        m = re.match(r"MemTotal:\s*(\d+) kB", line)
        if m is not None:
            # system total memory in kB
            metadata["META_MEM_SIZE"] = int(m.group(1))
            break

    return metadata

def get_sys_info():
    cpu    = _get_cpu_info()
    memory = _get_memory_info()

    return dict(cpu.items() + memory.items())

if __name__ == "__main__":
    info = get_sys_info()
    for key in info:
        print ("{0:20}: {1}".format(key, info[key]))
