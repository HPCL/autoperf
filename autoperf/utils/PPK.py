import re
import sys
import gzip
import numpy as np

import subprocess

from struct    import *
from itertools import product

from MathExp   import MathExp
from MetricSet import MetricSet
from metadata  import *

class _Error(Exception):
    """Base class for exceptions in this module"""
    pass

class InvalidPPKError(_Error):
    def __init__(self, filename):
        _Error.__init__(self, "`%s` is not in the correct PPK format" % filename)

class NoSuchThreadError(_Error):
    def __init__(self, thread):
        _Error.__init__(self, "Thread# %d does not exist" % thread)

class NoSuchEventError(_Error):
    def __init__(self, event):
        _Error.__init__(self, "Event `%s` does not exist" % event)

class NoSuchMetricError(_Error):
    def __init__(self, metric):
        _Error.__init__(self, "Metric `%s` does not exist" % metric)

class InvalidDerivedMetricError(_Error):
    def __init__(self, metric):
        _Error.__init__(self, "Metric `%s` already exist" % metric)

class InvalidFunctionNameError(_Error):
    def __init__(self, name):
        _Error.__init__(self, "Failed to parse function name `%s`" % name)

class InvalidEventError(_Error):
    def __init__(self, name):
        _Error.__init__(self, "Failed to parse event name `%s`" % name)

class FunctionName:
    """
    This represents a full qualified function name in the profile data,
    which looks like:

      [TYPE] SIGNATURE [{FILENAME} {LINENO}]

    However, current implementation of TAU introduces a lot of exceptions.
    For example: function name we get by instrumention doesn't have the
    '[TYPE]' part; MPI_*() doesn't have the '[{FILENAME}...]' part. If we
    failed to resolve PC when doing sampling, it can even just be an
    address looks like '0x12345678'.

    This makes the code messy. Be careful.
    """
    def __init__(self, name):
        self.fullname = name

        # the top level profiler
        if name == ".TAU application":
            self.type = "ROOT"
            self.filename = None
            self.lineno   = None
            self.signature = ".TAU application"
            self.resolved  = True
            return
        
        if name == "[CONTEXT] .TAU application":
            self.type = "TOPLEVEL"
            self.filename = None
            self.lineno   = None
            self.signature = "TOPLEVEL"
            self.resolved  = True
            return

        # unresolved address
        match = re.match(r"^0x[0-9a-f]+", name)
        if match:
            self.type = "SAMPLE"
            self.filename = None
            self.lineno   = None
            self.signature = name
            self.resolved  = False
            return
        
        # CALLSITE, UNWIND, CONTEXT, SAMPLE, SUMMARY
        match = re.search(r"^\[(.*?)\]", name)
        if match:
            self.type = match.group(1)
        else:
            self.type = "INSTRU"

        # get filename and line number
        # 
        # [{filename} {num}-{num}] for instrumented profile
        # [{filename} {num}] for sampling
        # [{filename}] for SUMMARY
        match = re.search(r"\[\{(.*?)\}(.*?)\]$", name)
        if match:
            self.filename = match.group(1)
            self.lineno   = match.group(2)
        else:
            self.filename = None
            self.lineno   = None

        # get function signature
        if self.type is "INSTRU":
            # <signature> [{filename} {num}-{num}]
            match = re.search(r"^(.*?)(\[\{.*?\} .*?\])*$", name)
            self.signature = match.group(1).strip()
        else:
            while True:
                # [...] ... UNRESOLVED [...]
                match = re.search(r"^\[.*?\].* UNRESOLVED \[[^\[\]]*?\]$", name)
                if match:
                    self.signature = 'UNRESOLVED'
                    break

                # ...] <signature> [{filename} ...
                match = re.search(r"\]([^\[\]]*?)(\[\{.*?\}.*?\])*$", name)
                if match:
                    self.signature = match.group(1).strip()
                    break

                raise InvalidFunctionNameError(name)

        if "UNRESOLVED" in self.signature:
            self.resolved = False
        else:
            self.resolved = True

class Event:
    """
    This represents an event that we attach collected data to. The
    corresponding entity in TAU is the FunctionInfo object.

    Basic form when running instrumentation:

      FunctionName

    Added by callpath:

      FunctionA => ... => FunctionB => FunctionC

    Added by callsite:

      FunctionA => ... => [CALLSITE] FunctionB => FunctionC

      [CALLSITE] FunctionName

    Basic form when running sampling:

      .TAU application => [CONTEXT] .TAU application => [SAMPLE] FunctionName

      .TAU application => [CONTEXT] .TAU application

      [CONTEXT] .TAU application

    Added by unwind:

      .TAU application => [CONTEXT] .TAU application => [UNWIND] FunctionA =>
                   ... => [UNWIND] FunctionB => [SAMPLE] FunctionC


      .TAU application => [CONTEXT] .TAU application => [UNWIND] FunctionA =>
                   ... => [UNWIND] FunctionB

      ......
      ......

      .TAU application => [CONTEXT] .TAU application => [UNWIND] FunctionA

      [UNWIND] FunctionA

      ......
      ......

      [UNWIND] FunctionB
    
    If we run both instrumentation and sampling, plus all feature enabled, all
    structures above could bend together and create some messy monster. For
    example:

      FunctionA => FunctionB => ... => FunctionC => [CONTEXT] FunctonC =>
      [UNWIND] FunctionD => ... => [UNWIND] FunctionE => [SAMPLE] FunctionF
    """
    def __init__(self, fullname, hotspots=[]):
        self.groups    = [ ]
        self.fullname  = fullname
        self.shortname = None
        self.callstack = [FunctionName(s.strip()) for s in fullname.split("=>")]

        # check whether this is a derived event
        if len(self.callstack) == 1:
            if '[SAMPLE]'  in fullname or '[UNWIND]'   in fullname or \
               '[CONTEXT]' in fullname or '[CALLSITE]' in fullname or \
               '[SUMMARY]' in fullname or  '.TAU application' == fullname:
                self.isDerived = True
            else:
                self.isDerived = False
        else:
            if '[CONTEXT]' in fullname: # created by sampling
                if '[SAMPLE]' in fullname:
                    self.isDerived = False
                else:
                    self.isDerived = True
            else:               # created by instrumentation with callpath
                self.isDerived = False

        # backtrace the callstack, find first resolved function name,
        # take it as our short name
        first_resolved = None
        first_hotspot  = None
        for f in reversed(self.callstack):
            if f.resolved:
                # find out the first resolved site
                if first_resolved is None:
                    first_resolved = f.signature

                # find out the first hotspot site, which is not
                # necessarily the first resolved site
                if first_hotspot is None and f.filename is not None:
                    for spot in hotspots:
                        match = re.search(spot, f.filename)
                        if match:
                            first_hotspot = f.signature

        # favor the hotspot
        if first_hotspot:
            self.shortname = first_hotspot
        elif first_resolved:
            self.shortname = first_resolved

        if self.shortname is None and not self.isDerived:
            raise InvalidEventError(fullname)

    def addGroup(self, groupName):
        self.groups.append(groupName)

class Node:
    def __init__(self, ppk, nodeId):
        self.ppk    = ppk
        self.nodeId = nodeId

        self.contexts = { }     # contextId -> Context

    def addContext(self, contextId):
        if contextId not in self.contexts.keys():
            self.contexts[contextId] = Context(self.ppk, self.nodeId, contextId)
            self.ppk.contexts.append(self.contexts[contextId])

        return self.contexts[contextId]

class Context:
    def __init__(self, ppk, nodeId, contextId):
        self.ppk       = ppk
        self.nodeId    = nodeId
        self.contextId = contextId

        self.threads   = { }    # threadId -> Thread

    def addThread(self, threadId):
        if threadId not in self.threads.keys():
            self.threads[threadId] = Thread(self.ppk, self.nodeId, \
                                            self.contextId, threadId)
            self.ppk.threads.append(self.threads[threadId])

        return self.threads[threadId]

class Thread:
    def __init__(self, ppk, nodeId, contextId, threadId):
        self.ppk        = ppk
        self.nodeId     = nodeId
        self.contextId  = contextId
        self.threadId   = threadId

        # raw data
        self.metadata          = { } # thread specific metadata
        self.functionProfiles  = { } # functionName -> FunctionProfile
        self.userEventProfiles = { } # userEventName -> UserEventProfile

        # aggregated data
        self.aggProfiles = { } # shortname -> Profile

    def addMetadata(self, name, value):
        self.metadata[name] = value

    def addFunctionProfile(self, name, profile):
        self.functionProfiles[name] = profile

        # aggregate data if this profile is not derived
        if not profile.isDerived:
            if profile.shortname not in self.aggProfiles:
                p = Profile(self.ppk, self.nodeId, self.contextId, \
                            self.threadId, profile.shortname)
                self.aggProfiles[profile.shortname] = p
                if profile.shortname not in self.ppk.aggEvents:
                    self.ppk.aggEvents.append(profile.shortname)
            else:
                p = self.aggProfiles[profile.shortname]

            p += profile

    def addUserEventProfile(self, name, profile):
        self.userEventProfiles[name] = profile

    def getDataPoint(self, event, metric, flavor):
        if event not in self.functionProfiles.keys():
            raise NoSuchEventError(event)

        profile = self.functionProfiles[event]

        return profile.getDataPoint(metric, flavor)

class Profile:
    """A generic profile data container"""

    def __init__(self, ppk, nodeId, contextId, threadId, name):
        self.ppk        = ppk
        self.nodeId     = nodeId
        self.contextId  = contextId
        self.threadId   = threadId
        self.fullname   = name
        self.metrics    = ppk.metrics

        self.numCalls  = 0
        self.numSubr   = 0
        self.exclusive = dict.fromkeys(self.metrics, 0)
        self.inclusive = dict.fromkeys(self.metrics, 0)

    def __iadd__(self, other):
        """'+=' operator, accumulate profile data"""

        self.numCalls += other.numCalls
        self.numSubr  += other.numSubr
        for m in other.metrics:
            if m not in self.metrics:
                self.exclusive[m]  = other.exclusive[m]
                self.inclusive[m]  = other.inclusive[m]
                self.metrics.append(m)
            else:
                self.exclusive[m] += other.exclusive[m]
                self.inclusive[m] += other.inclusive[m]

    def getDataPoint(self, metric, flavor):
        """
        Get a collected `metric` reading from this profile.

        Args:
          metric (string): Name of the metric
          flavor (int):    PPK.EXCLUSIVE or PPK.INCLUSIVE

        Returns:
          float: the metric reading
        """
        if metric not in self.metrics:
            raise NoSuchMetricError(metric)

        if flavor == PPK.EXCLUSIVE:
            return self.exclusive[metric]
        elif flavor == PPK.INCLUSIVE:
            return self.inclusive[metric]
        else:
            raise Error("Invalid parameter")

    def updateDerivedMetric(self, ms, meta):
        """
        Calc and update derived metrics into profile data

        Args:
          ms (object): MetricSet
          meta (map) : a map of system metadata
        """
        excSymtab = dict(self.exclusive.items() + meta.items())
        incSymtab = dict(self.inclusive.items() + meta.items())

        excVals = ms.eval(excSymtab)
        incVals = ms.eval(incSymtab)

        for (name, value) in excVals.items():
            self.exclusive[name] = value

        for (name, value) in incVals.items():
            self.inclusive[name] = value

class FunctionProfile(Profile):
    """
    Raw profile data container, which could be a genuine data or
    derived data.

    Genuine data:
      1. All data collected by instrumentation
      2. For sampling:
         A => ... => [CONTEXT] B => ... => [SAMPLE] C
         A => ... => [CONTEXT] B => ... => 0x01234567

    Derived data:
      [SAMPLE] A
      [UNWIND] A
      A => ... => [CONTEXT] B
      A => ... => [CONTEXT] B => ... => [UNWIND] C
    """
    def __init__(self, ppk, nodeId, contextId, threadId, functionId):
        self.functionId = functionId
        self.event      = ppk.events[functionId]
        self.groups     = self.event.groups
        self.shortname  = self.event.shortname
        self.isDerived  = self.event.isDerived

        Profile.__init__(self, ppk, nodeId, contextId, threadId, self.event.fullname)

class UserEventProfile:
    def __init__(self, ppk, userEventId, nodeId, contextId, threadId):
        self.ppk         = ppk
        self.userEventId = userEventId
        self.nodeId      = nodeId
        self.contextId   = contextId
        self.threadId    = threadId

        self.userEventName = ppk.userEvents[userEventId]

        self.numSamples = 0
        self.minValue   = 0
        self.maxValue   = 0
        self.meanValue  = 0
        self.sumSquared = 0

class PPK:
    """
    PPK file parser which mimic the implementation in
    PackedProfileDataSource of the perfdmf.

    See perfdmf:PackedProfileDataSource.java
    """

    AGG  = 0
    SUM  = 1
    MAX  = 2
    MIN  = 3
    STD  = 4
    MEAN = 5

    EXCLUSIVE = 0
    INCLUSIVE = 1
    
    def __init__(self, filename, hotspots):
        self.pos        = 0       # r/w position pointer
        self.filename   = filename
        self.hotspots   = hotspots

        self.metadata   = { }     # map of metadata name->value
        self.metrics    = [ ]     # list of metric names
        self.groups     = [ ]     # list of group names
        self.events     = [ ]     # list of Event
        self.userEvents = [ ]     # list of user event name

        self.nodes      = { }     # nodeId -> Node
        self.contexts   = [ ]     # list of all Context
        self.threads    = [ ]     # list of all Thread

        # raw data
        self.rawArray          = None
        self.functionProfiles  = [ ] # list of all FunctionProfile
        self.userEventProfiles = [ ] # list of all UserEventProfile

        # aggregated data
        self.aggExcArray     = { } # exclusive data
        self.aggIncArray     = { } # inclusive data

        self.aggEvents = [ ] # list of all function shortname after aggregation

        f = gzip.open(filename, 'rb')
        self.contents = f.read()
        f.close()

        cookie1 = self._readChar()
        cookie2 = self._readChar()
        cookie3 = self._readChar()

        if not (cookie1 is 'P' and cookie2 is 'P' and cookie3 is 'K'):
            raise InvalidPPKError(filename)

        self.version    = self._readInt()
        self.compatible = self._readInt()

        if self.compatible > 2:
            raise Exception("This packed profile is not compatible, "\
                            "please upgrade\nVersion: %x > 2" % self.compatible)

        if self.version >= 2:
            # older versions will skip over this many bytes
            self.pad1 = self._readInt()

            self.bytesToSkip = self._readInt()
            self._skipBytes(self.bytesToSkip)

            # process metadata
            numTrialMetaData = self._readInt()
            for i in range(numTrialMetaData):
                name  = self._readUTF()
                value = self._readUTF()
                self.metadata[name] = value

            # process thread metadata
            numThreads = self._readInt()
            for i in range(numThreads):
                nodeId    = self._readInt()
                contextId = self._readInt()
                threadId  = self._readInt()

                thread = self._addThread(nodeId, contextId, threadId)

                numMetadata = self._readInt()
                for j in range(numMetadata):
                    name  = self._readUTF()
                    value = self._readUTF()
                    thread.addMetadata(name, value)
        else:
            self.bytesToSkip = self._readInt()
            self._skipBytes(self.bytesToSkip)

        # process metrics
        numMetrics = self._readInt()
        for i in range(numMetrics):
             self.metrics.append(self._readUTF())

        # process groups
        numGroups = self._readInt()
        for i in range(numGroups):
            self.groups.append(self._readUTF())

        #process functions
        numFunctions = self._readInt()
        for i in range(numFunctions):
            functionName = self._readUTF()
            event        = Event(functionName, hotspots)

            numThisGroups = self._readInt()
            for j in range(numThisGroups):
                event.addGroup(self.groups[self._readInt()])

            self.events.append(event)

        # process user events
        numUserEvents = self._readInt()
        for i in range(numUserEvents):
            self.userEvents.append(self._readUTF())

        # process thread data
        numThreads = self._readInt()
        for i in range(numThreads):
            nodeId    = self._readInt()
            contextId = self._readInt()
            threadId  = self._readInt()

            thread = self._addThread(nodeId, contextId, threadId)

            # get function profiles
            numFunctionProfiles = self._readInt()
            for j in range(numFunctionProfiles):
                functionId = self._readInt()
                profile = FunctionProfile(self, nodeId, contextId, \
                                          threadId, functionId)
                profile.numCalls = self._readDouble()
                profile.numSubr  = self._readDouble()

                for k in range(numMetrics):
                    profile.exclusive[self.metrics[k]] = self._readDouble()
                    profile.inclusive[self.metrics[k]] = self._readDouble()

                self.functionProfiles.append(profile)
                thread.addFunctionProfile(profile.fullname, profile)

            # get user event profiles
            numUserEventProfiles = self._readInt()
            for j in range(numUserEventProfiles):
                userEventId = self._readInt()
                profile = UserEventProfile(self, userEventId, nodeId, \
                                           contextId, threadId)
                profile.numSamples = self._readInt()
                profile.minValue   = self._readDouble()
                profile.maxValue   = self._readDouble()
                profile.meanValue  = self._readDouble()
                profile.sumSquared = self._readDouble()

                self.userEventProfiles.append(profile)
                thread.addUserEventProfile(profile.userEventName, profile)

        if self.pos < len(self.contents):
            raise InvalidPPKError(filename)

    def addMetadata(self, name, value):
        self.metadata[name] = value

    def dump(self, ppkfile):
        self.pack_format = ">"
        self.pack_data   = [ ]

        self._writeChar('P')
        self._writeChar('P')
        self._writeChar('K')

        self._writeInt(self.version)
        self._writeInt(self.compatible)

        if self.version >= 2:
            self._writeInt(self.pad1)

            self._writeInt(self.bytesToSkip)
            self._writePad(self.bytesToSkip)

            # process metadata
            self._writeInt(len(self.metadata.keys()))
            for name, value in self.metadata.items():
                self._writeUTF(name)
                self._writeUTF(value)

            # process thread metadata
            self._writeInt(len(self.threads))
            for thread in self.threads:
                self._writeInt(thread.nodeId)
                self._writeInt(thread.contextId)
                self._writeInt(thread.threadId)

                self._writeInt(len(thread.metadata.keys()))
                for name, value in thread.metadata.items():
                    self._writeUTF(name)
                    self._writeUTF(value)
        else:
            self._writeInt(self.bytesToSkip)
            self._writePad(self.bytesToSkip)

        # process metrics
        self._writeInt(len(self.metrics))
        for metric in self.metrics:
            self._writeUTF(metric)

        # process groups
        self._writeInt(len(self.groups))
        for group in self.groups:
            self._writeUTF(group)

        #process functions
        self._writeInt(len(self.events))
        for event in self.events:
            self._writeUTF(event.fullname)

            self._writeInt(len(event.groups))
            for group in event.groups:
                self._writeInt(self.groups.index(group))


        # process user events
        self._writeInt(len(self.userEvents))
        for event in self.userEvents:
            self._writeUTF(event)

        # process thread data
        fpBegin = 0;
        upBegin = 0;
        self._writeInt(len(self.threads))
        for thread in self.threads:
            self._writeInt(thread.nodeId)
            self._writeInt(thread.contextId)
            self._writeInt(thread.threadId)

            print "Handle thread %d ..." % thread.threadId

            # write function profiles
            fpNum = len(thread.functionProfiles.keys())
            self._writeInt(fpNum)
            for profile in self.functionProfiles[fpBegin:fpBegin+fpNum]:
                self._writeInt(profile.functionId)
                self._writeDouble(profile.numCalls)
                self._writeDouble(profile.numSubr)

                for metric in self.metrics:
                    self._writeDouble(profile.exclusive[metric])
                    self._writeDouble(profile.inclusive[metric])
            fpBegin += fpNum

            # write user event profiles
            upNum = len(thread.userEventProfiles.keys())
            self._writeInt(upNum)
            for profile in self.userEventProfiles[upBegin:upBegin+upNum]:
                self._writeInt(profile.userEventId)
                self._writeInt(profile.numSamples)
                self._writeDouble(profile.minValue)
                self._writeDouble(profile.maxValue)
                self._writeDouble(profile.meanValue)
                self._writeDouble(profile.sumSquared)
            upBegin += upNum

        f = gzip.open(ppkfile, 'wb')
        f.write(pack(self.pack_format, *self.pack_data))
        f.close()

    def _readChar(self):
        rv = unpack("Bc", self.contents[self.pos:self.pos+2])
        self.pos += 2

        return rv[1]

    def _writeChar(self, char):
        self.pack_format += "Bc"
        self.pack_data.append(0)
        self.pack_data.append(char)

    def _readUnsignedShort(self):
        rv = unpack(">H", self.contents[self.pos:self.pos+2])
        self.pos += 2

        return rv[0]

    def _writeUnsignedShort(self, us):
        self.pack_format += "H"
        self.pack_data.append(us)

    def _readInt(self):
        rv = unpack(">i", self.contents[self.pos:self.pos+4])
        self.pos += 4

        return rv[0]

    def _writeInt(self, i):
        self.pack_format += "i"
        self.pack_data.append(i)

    def _readDouble(self):
        rv = unpack(">d", self.contents[self.pos:self.pos+8])
        self.pos += 8

        return rv[0]

    def _writeDouble(self, d):
        self.pack_format += "d"
        self.pack_data.append(d)

    def _readUTF(self):
        len = self._readUnsignedShort()
        rv = unpack("%ds" % len, self.contents[self.pos:self.pos+len])
        self.pos += len

        return rv[0]

    def _writeUTF(self, utf):
        self.pack_format += "H%ds" % len(utf)
        self.pack_data.append(len(utf))
        self.pack_data.append(utf)

    def _skipBytes(self, bytesToSkip):
        self.pos += bytesToSkip

    def _writePad(self, length):
        if (length > 0):
            self.pack_format += "%dB" % length
            self.pack_data.extend([0x55] * length)

    def _addNode(self, nodeId):
        if nodeId not in self.nodes:
            self.nodes[nodeId] = Node(self, nodeId)

        return self.nodes[nodeId]

    def _addThread(self, nodeId, contextId, threadId):
        node    = self._addNode(nodeId)
        context = node.addContext(contextId)
        thread  = context.addThread(threadId)

        return thread

    def _getAggData(self, event, metric, type, flavor):
        if event not in self.aggEvents or metric not in self.metrics:
            return 0

        e = self.aggEvents.index(event)
        m = self.metrics.index(metric)

        if flavor == PPK.INCLUSIVE:
            array = self.aggIncArray
        elif flavor == PPK.EXCLUSIVE:
            array = self.aggExcArray

        return array[type][e, m]

    def getDataPoint(self, thread, event, metric, flavor):
        if thread >= len(self.threads):
            raise NoSuchThreadError(thread)

        return self.threads[thread].getDataPoint(event, metric, flavor)

    def attachMetricSet(self, ms):
        """
        Calculate and add derived metrics into the data set.

        Args:
          ms (object): MetricSet

        Returns:
          None
        """
        if not ms.nmetrics <= set(self.metrics):
            raise Exception("MetricSet is bigger than PPK metrics")

        self.metrics.extend(ms.dmetrics)

        metaSym   = get_sys_info()

        # handle raw data
        for profile in self.functionProfiles:
            profile.updateDerivedMetric(ms, metaSym)

        # handle aggregated data
        for thread in self.threads:
            for profile in thread.aggProfiles.itervalues():
                profile.updateDerivedMetric(ms, metaSym)

    def populateAggData(self):
        """Populate aggregated data into a numpy array"""

        dimN = len(self.nodes)
        dimC = 0
        dimT = 0
        dimE = len(self.aggEvents)
        dimM = len(self.metrics)

        for n in self.nodes.itervalues():
            dimC = max(dimC, len(n.contexts))

        for c in self.contexts:
            dimT = max(dimT, len(c.threads))
        
        self.aggExcArray[PPK.AGG] = np.zeros([dimN, dimC, dimT, dimE, dimM])
        self.aggIncArray[PPK.AGG] = np.zeros([dimN, dimC, dimT, dimE, dimM])
        for n,c,t,e,m in product(range(dimN), range(dimC), \
                                 range(dimT), range(dimE), range(dimM)):
            try:
                excData = self.nodes[n].\
                          contexts[c].\
                          threads[t].\
                          aggProfiles[self.aggEvents[e]].\
                          exclusive[self.metrics[m]]
            except KeyError, IndexError:
                excData = 0
            finally:
                self.aggExcArray[PPK.AGG][n,c,t,e,m] = excData
            
            try:
                incData = self.nodes[n].\
                          contexts[c].\
                          threads[t].\
                          aggProfiles[self.aggEvents[e]].\
                          inclusive[self.metrics[m]]
            except KeyError, IndexError:
                incData = 0
            finally:
                self.aggIncArray[PPK.AGG][n,c,t,e,m] = incData

        self.aggExcArray[PPK.SUM]  = self.aggExcArray[PPK.AGG].sum((0, 1, 2))
        self.aggExcArray[PPK.MAX]  = self.aggExcArray[PPK.AGG].max((0, 1, 2))
        self.aggExcArray[PPK.MIN]  = self.aggExcArray[PPK.AGG].min((0, 1, 2))
        self.aggExcArray[PPK.STD]  = self.aggExcArray[PPK.AGG].std((0, 1, 2))
        self.aggExcArray[PPK.MEAN] = self.aggExcArray[PPK.AGG].mean((0, 1, 2))

        self.aggIncArray[PPK.SUM]  = self.aggIncArray[PPK.AGG].sum((0, 1, 2))
        self.aggIncArray[PPK.MAX]  = self.aggIncArray[PPK.AGG].max((0, 1, 2))
        self.aggIncArray[PPK.MIN]  = self.aggIncArray[PPK.AGG].min((0, 1, 2))
        self.aggIncArray[PPK.STD]  = self.aggIncArray[PPK.AGG].std((0, 1, 2))
        self.aggIncArray[PPK.MEAN] = self.aggIncArray[PPK.AGG].mean((0, 1, 2))

    def aggEventsIter(self):
        for e in self.aggEvents:
            yield e

    def metricIter(self):
        for m in self.metrics:
            yield m

    def getAggExcSum(self, event, metric):
        return self._getAggData(event, metric, PPK.SUM, PPK.EXCLUSIVE)
        
    def getAggExcMax(self, event, metric):
        return self._getAggData(event, metric, PPK.MAX, PPK.EXCLUSIVE)
        
    def getAggExcMin(self, event, metric):
        return self._getAggData(event, metric, PPK.MIN, PPK.EXCLUSIVE)
        
    def getAggExcStd(self, event, metric):
        return self._getAggData(event, metric, PPK.STD, PPK.EXCLUSIVE)
        
    def getAggExcMean(self, event, metric):
        return self._getAggData(event, metric, PPK.MEAN, PPK.EXCLUSIVE)
        
    def getAggIncSum(self, event, metric):
        return self._getAggData(event, metric, PPK.SUM, PPK.INCLUSIVE)
        
    def getAggIncMax(self, event, metric):
        return self._getAggData(event, metric, PPK.MAX, PPK.INCLUSIVE)
        
    def getAggIncMin(self, event, metric):
        return self._getAggData(event, metric, PPK.MIN, PPK.INCLUSIVE)
        
    def getAggIncStd(self, event, metric):
        return self._getAggData(event, metric, PPK.STD, PPK.INCLUSIVE)
        
    def getAggIncMean(self, event, metric):
        return self._getAggData(event, metric, PPK.MEAN, PPK.INCLUSIVE)

if __name__ == "__main__":
    ppk = PPK(sys.argv[1], "whatever")
    ppk.addMetadata("AP_CONFIG", "deadbeef")
    ppk.dump('foo.ppk')
