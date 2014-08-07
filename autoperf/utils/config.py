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

    print " *** Parsing config files (%s)..." % config_file,
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
    hierarchy. 'option' is None if a section is named 'spec'.
    """
    global cfg_parser

    if cfg_parser.has_section(spec):
        return [spec, None]
    
    section, dot, option = spec.rpartition('.')

    if section is '':
        raise ConfigParser.NoSectionError(spec)
    else:
        return _find(section, option)

def _get_section(section):
    global cfg_parser

    if cfg_parser.has_section(section):
        items = cfg_parser.items(section)
    else:
        items = [ ]

    super_section = section.rpartition('.')[0]
    if super_section is '':
        return items
    else:
        return _get_section(super_section) + items

def get(spec):
    """
    Get an option or a whole section from config file.

    spec: "section"        - return all the options in "section" as a dict
          "section.option" - return the string value of "option" in "section"
    """
    global params
    global cfg_parser

    section, option = _unpack_spec(spec)

    if option is None:
        return dict(_get_section(section))
    else:
        return cfg_parser.get(section, option)

def getint(spec):
    """
    Get an option as an integer.
    """
    global cfg_parser

    section, option = _unpack_spec(spec)

    if option is None:
        raise ConfigParser.Error("Wrong option spec")

    return cfg_parser.getint(section, option)

def getfloat(spec):
    """
    Get an option as a float
    """
    global cfg_parser

    section, option = _unpack_spec(spec)

    if option is None:
        raise ConfigParser.Error("Wrong option spec")

    return cfg_parser.getfloat(section, option)

def getboolean(spec):
    """
    Get an option as a boolean
    """
    global cfg_parser

    section, option = _unpack_spec(spec)

    if option is None:
        raise ConfigParser.Error("Wrong option spec")

    return cfg_parser.getboolean(section, option)


if __name__ == '__main__':
    parse(sys.argv[1])
    print repr(get(sys.argv[2]))
