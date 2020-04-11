import sys
import os
import configparser
import logging

class Config:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cfg_parser = configparser.ConfigParser()

    def parse(self, options=None):
        """
        Parse configuration file(s). Options are case-sensitive
        Args:
            options: command-line options

        Returns:
            The configparser instance
        """

        config_files = ['autoperf.cfg',
                      '.autoperf.cfg',
                      os.path.expanduser('~/.autoperf.cfg')]

        if options and options.cfgfile:
            for filename in options.cfgfile.split(','):
                if os.path.exists(fileame):
                    config_files += filename
                else:
                    raise IOError("Configuration file %s does not exist." % filename)

        found = self.cfg_parser.read(config_files)

        self.logger.info("Successfully parsed the following config files: %s" % ', '.join(found))
        # missing = set(candidates) - set(found)

        if not found:
            raise configparser.Error('Cannot find a valid config file (searched for %s)' % ', '.join(config_files))
        else:
            config_file = found[0]

        parsed = self.cfg_parser.read(config_file)
        if len(parsed) == 0:
            raise configparser.Error('Can not find config file')

        params = dict()

        params['DEFAULT'] = dict(self.cfg_parser.items('DEFAULT'))
        for section in self.cfg_parser.sections():
            params[section] = dict(self.cfg_parser.items(section))

        self.logger.info("--- Done parsing config files (%s)..." % config_file)

        return self

    def _strip_comments(self, line):
        """
        Strip the comment from the end of the line
        """
        for c in [';','#']:
            if line.find(c) > 0:
                return line.split(c)[0].rstrip()
            else:
                continue
        return line

    def _find(self, section, option):
        """
        Recurse up to find the first existing [section, option] combination in
        the section hierarchy. Raise an exception if nothing was found.
        """
        if self.cfg_parser.has_option(section, option):
            return [section, option]

        # fall through to the super section
        super_section = section.rpartition('.')[0]
        if not super_section:
            raise configparser.Error("Can not find option '%s' under section '%s'"
                                     % (option, section))
        else:
            return self._find(super_section, option)


    def _unpack_spec(self, spec):
        """
        Unpack 'spec' into '[section, option]' following the section
        hierarchy.
        """
        if self.cfg_parser.has_section(spec):
            raise configparser.Error("Can not find option '%s'" % spec)

        section, dot, option = spec.rpartition('.')

        if section is '':
            raise configparser.Error("Can not find option '%s'" % spec)
        else:
            return self._find(section, option)


    def set(self, spec, value):

        section, dot, option = spec.rpartition('.')
        if not self.cfg_parser.has_section(section):
            self.cfg_parser.add_section(section)

        # Extract the comment (if any) from the value
        val, doc = value.split(';')
        value = val.rstrip()

        self.cfg_parser.set(section, option, str(value))


    def get_section(self, section):

        if self.has_section(section):
            items = self.cfg_parser.items(section)
        else:
            items = []

        super_section = section.rpartition('.')[0]
        if super_section is '':
            return items
        else:
            return get_section(super_section) + items


    def get(self, spec, default=None, datatype=None):
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

        try:
            section, option = self._unpack_spec(spec)
            if datatype is None:
                return self._strip_comments(self.cfg_parser.get(section, option))
            elif datatype is "int":
                return self._strip_comments(self.cfg_parser.getint(section, option))
            elif datatype is "float":
                return self._strip_comments(self.cfg_parser.getfloat(section, option))
            elif datatype is "boolean":
                return self._strip_comments(self.cfg_parser.getboolean(section, option))
            else:
                raise configparser.Error("invalid data type")
        except configparser.Error:
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

    exp_code_re = re.compile(r'^\s*([\w_]+){(.*)}$')


    def get_list(secname):
        """
        Generate the experiment names
        """
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
                    raise configparser.Error("Invalid expression in experiment list: %s" % m.group(2))
            else:
                if 'threads' in list(locals().keys()) and isinstance(threads, list):
                    for t in threads:
                        name = m.group(1) + '.' + str(t)
                        newlist.append(name)
                        # print ("set: Experiments.%s.threads" % name, t)
                        set("Experiments.%s.threads" % name, t)
                else:
                    newlist.append(exp)
        return newlist

