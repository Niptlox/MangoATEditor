import os
from configparser import ConfigParser
from typing import Any


def config_save():
    with open(config_filename, 'w') as configfile:
        config.write(configfile)


config_filename = os.getcwd() + r'/././settings.ini'
print("config_filename", config_filename)
# with open(config_filename, "r") as f:
#     print(f.read())
config = ConfigParser()
config.read(config_filename)


class __Settings:
    config = config
    section = ""
    variables = {}

    def __init__(self):
        self.load_vars()

    @classmethod
    def set(cls, var_name, var_value):
        # print(cls.section, var_name, var_value)
        config.set(cls.section, var_name, str(var_value))
        config_save()
        if var_name in cls.__dict__:
            if isinstance(var_value, str):
                var_value = '"' + var_value + '"'
            exec(f"cls.{var_name} = {var_value}")
        print(cls.__dict__[var_name])

    @classmethod
    def get(cls, var_name, var_type=str, list_sep=",", format_str=True):
        if var_type is str:
            if format_str:
                return "'" + config.get(cls.section, var_name) + "'"
            return config.get(cls.section, var_name)
        if var_type is bool:
            return config.getboolean(cls.section, var_name)
        if var_type is int:
            return config.getint(cls.section, var_name)
        if var_type is float:
            return config.getfloat(cls.section, var_name)
        if var_type is list:
            return config.get(cls.section, var_name).split(list_sep)
        raise Exception(f"Get that is type? {var_type}")

    @classmethod
    def load_vars_from_variables(cls):
        for var_name, var_type in cls.variables.items():
            exec(f"cls.{var_name} = {cls.get(var_name, var_type)}", locals(), globals())

    @classmethod
    def load_vars(cls):
        for var_name, var_cls in tuple(cls.__dict__.items()):
            if isinstance(var_cls, ConfigVar) or var_cls in [ConfigVar]:
                exec(f"cls.__{var_name} = var_cls", locals(), globals())
                exec(f"cls.{var_name} = {cls.get(var_name, var_cls.var_type)}", locals(), globals())



class ConfigVar:
    var_type = str

    def __init__(self, var_type: Any = str, default=None):
        self.var_type = var_type
        self.default = default


class TranslatorCnf(__Settings):
    section = "translator"

    debug = ConfigVar(bool)
    header_image = ConfigVar(str)
    to_zip = ConfigVar(bool)
    create_vector_image = ConfigVar(bool)
    translate_vector_image = ConfigVar(bool)
    base64_vector_image = ConfigVar(bool)
    translate_language = ConfigVar(str)
    save_cleaned_image = ConfigVar(bool)
    translate_font = ConfigVar(str)
    translated_path = ConfigVar(str)
    # rapid,google,youdao,baidu,deepl,papago,gpt3,gpt3.5,none,original,offline,nllb,nllb_big,sugoi,jparacrawl,jparacrawl_big,m2m100,m2m100_big
    translator_type = ConfigVar(str)

    del_not_in_original = ConfigVar(bool)
    ignore_del = ConfigVar(str)


TranslatorCnf.load_vars()


