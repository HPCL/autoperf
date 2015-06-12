import sys
import ConfigParser

done = False

def parse(config_file):
    """
    Parse the config_file. Option names are case sensitive.
    """
    global done
    global params
    global cfg_parser

    cfg_parser = ConfigParser.ConfigParser()

    # option name is case sensitive
    cfg_parser.optionxform = str

    print "*** Parsing config files (%s)..." % config_file,
    parsed = cfg_parser.read(config_file)
    if len(parsed) == 0:
        raise ConfigParser.Error('Can not find config file')
    
    params = dict()

    params['DEFAULT'] = dict(cfg_parser.items('DEFAULT'))
    for section in cfg_parser.sections():
        params[section] = dict(cfg_parser.items(section))

    print "done"
    sys.stdout.flush()

    done = True

def _find(section, option):
    """
    Climb up to find the first exist [section, option] combination in
    the section hierarchy. Raise an exception if find nothing.
    """
    global cfg_parser

    if cfg_parser.has_option(section, option):
        return [section, option]

    # fall through to the supper section
    super_section = section.rpartition('.')[0]
    if super_section is '':
        raise ConfigParser.Error("Can not find option '%s' under section '%s'"
                                 % (option, section))
    else:
        return _find(super_section, option)
        
def _unpack_spec(spec):
    """
    Unpack 'spec' into '[section, option]' following the section
    hierarchy.
    """
    global cfg_parser

    if cfg_parser.has_section(spec):
        raise ConfigParser.Error("Can not find option '%s'" % spec)
    
    section, dot, option = spec.rpartition('.')

    if section is '':
        raise ConfigParser.Error("Can not find option '%s'" % spec)
    else:
        return _find(section, option)

def set(spec, value):
    global cfg_parser

    section, dot, option = spec.rpartition('.')
    if not cfg_parser.has_section(section):
        cfg_parser.add_section(section)
    cfg_parser.set(section, option, str(value))

def get_section(section):
    global cfg_parser

    if cfg_parser.has_section(section):
        items = cfg_parser.items(section)
    else:
        items = [ ]

    super_section = section.rpartition('.')[0]
    if super_section is '':
        return items
    else:
        return get_section(super_section) + items

def get(spec, default=None, datatype=None):
    """
    Get the value of an single option

    Args:
      spec (string): The full name of the option, i.e <section_full_name>.<option_name>
      default: The default value for the option
      datatype (string): type of the option value, i.e. None, "int", "float" or "boolean"

    Returns:
      The value of a single option

    Exceptions:
      ConfigParser.Error if can not get option value by 'spec', and
      'defualt' is not given
    """
    global cfg_parser

    try:
        section, option = _unpack_spec(spec)
        if datatype is None:
            return cfg_parser.get(section, option)
        elif datatype is "int":
            return cfg_parser.getint(section, option)
        elif datatype is "float":
            return cfg_parser.getfloat(section, option)
        elif datatype is "boolean":
            return cfg_parser.getboolean(section, option)
        else:
            raise ConfigParser.Error("invalid data type")
    except ConfigParser.Error:
        if default is None:
            raise
        else:
            return default

def getint(spec, default=None):
    """
    Get an option as an integer.
    """
    return get(spec, default, "int")

def getfloat(spec, default=None):
    """
    Get an option as a float
    """
    return get(spec, default, "float")

def getboolean(spec, default=None):
    """
    Get an option as a boolean
    """
    return get(spec, default, "boolean")

import re
exp_code_re = re.compile('^\s*([\w_]+){(.*)}$')

def get_list(secname):
    """
    Generate the experiment names
    """
    global cfg_parser
    exp_strings = get(secname).split()
    newlist = []
    for exp in exp_strings:
        if exp.find('{') < 0:
            newlist.append(exp)
            continue
        m = exp_code_re.match(exp)
        if m:
            try:
                exec(m.group(2))
            except:
                print "Invalid expression in experiment list: %s" % m.group(2)
                exit(1)
            else:
                if 'threads' in locals().keys() and isinstance(threads,list):
                    for t in threads: 
			name = m.group(1) + '.' + str(t)
 			newlist.append(name)
			#print "set: Experiments.%s.threads" % name, t
			set("Experiments.%s.threads" % name, t)
                else:
                    newlist.append(exp)
    return newlist

if __name__ == '__main__':
    parse(sys.argv[1])
    print repr(getint(sys.argv[2]))
