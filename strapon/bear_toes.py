import os, os.path, string, pprint, zipfile
import urllib.request
from cryptography.fernet import Fernet


working_copy_path = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                 os.pardir,
                                                 os.pardir))

class AttrParams(dict):
    _ordered_keys = None
    @property
    def ordered_keys(self):
        if self._ordered_keys is not None:
            return self._ordered_keys
        ordered = []
        digit_key_lut = {}
        maxwidth = 0
        widest = None

        for param_key in self.keys():
            just_digits = False
            for ch in param_key:
                if ch not in string.digits:
                    break
            else:
                just_digits = True

            if not just_digits:
                ordered.append(param_key)
                continue

            digit_key = param_key.lstrip('0') if param_key != '0' else param_key
            key_width = len(digit_key)
            if widest is None or maxwidth < key_width:
                widest = param_key
                maxwidth = key_width

            digit_key_lut[param_key] = digit_key

        for param_key in digit_key_lut.keys():
            digit_key = digit_key_lut[param_key]
            padto = maxwidth - len(digit_key)
            if 0 < padto:
                digit_key = digit_key_lut[param_key] = digit_key.zfill(padto)
            ordered.append(digit_key)

        ordered.sort()

        for param_key in digit_key_lut.keys():
            digit_key = digit_key_lut[param_key]
            prio = ordered.index(digit_key)
            ordered[prio] = param_key

        self._ordered_keys = ordered
        return ordered

    def __init__(self, **source_dict):
        super().__init__(**source_dict)
        for key in source_dict.keys():
            value = self[key]
            if isinstance(value, dict):
                value = AttrParams(**value)
                self[key] = value
            if key[0] in string.digits:
                key = '_'+key
            setattr(self, key, value)

class JumpingBearLeg:
    ENTRY_ENV_KEY = 'bear-toes-2-lick'

    toes_counted = {} # by env_prefix
    extra_symbols = {'WD': working_copy_path}
    extra_symbols_with_params = None # with params

    _resolved_field_count = 0
    @classmethod
    def count_a_toe(cls, toe):
        cls.toes_counted[toe.env_prefix] = toe

    @classmethod
    def main(cls, *lick_list):
        if len(lick_list) == 0:
            lick_list = cls.get_lick_list()
        cls.process_toe_param_references()
        for toe_nick in lick_list:
            cls.toes_counted[toe_nick].lick_toe()
        pass

    @classmethod
    def get_lick_list(cls):
        raw_list = os.environ.get(cls.ENTRY_ENV_KEY)
        if not raw_list:
            raise Exception('Missing cli arguments and command list env variable')
        return raw_list.split()

    @classmethod
    def process_toe_param_references(cls):
        # process symbols in param values (expecting dot syntax)
        param_symbols = cls.extra_symbols.copy()
        for toe_prefix, toe in cls.toes_counted.items():
            if toe.params is not None:
                param_symbols[toe_prefix] = toe.params
        cls._resolved_field_count = 1
        while cls._resolved_field_count > 0:
            cls._resolved_field_count = 0
            cls.resolve_param_symbols(param_symbols, param_symbols)

        for toe_prefix, toe in cls.toes_counted.items():
            toe._post_process_params()

        cls.extra_symbols_with_params = param_symbols

    @classmethod
    def resolve_param_symbols(cls, current_level, param_symbols):
        for dict_key in current_level.keys():
            if dict_key in cls.extra_symbols:
                continue
            attr_name = dict_key
            if dict_key[0] in string.digits:
                attr_name = '_'+dict_key

            param_value = getattr(current_level, attr_name, None) or current_level[dict_key]
            if isinstance(param_value, AttrParams):
                cls.resolve_param_symbols(param_value, param_symbols)
            elif isinstance(param_value, str):
                after = param_value.format(**param_symbols)
                if after != param_value:
                    cls._resolved_field_count += 1
                    current_level[dict_key] = after
                    setattr(current_level, attr_name, after)


class JumpStartAction:
    _rstrip_words = ['beartoe', 'toe'] # order matters, _auto_prefix only strips the first
    _pprep = {} # param-pre-processors
    _pprop = {} # param-post-processors

    env_prefix = None

    params = None
    _dot_key_params = None

    @classmethod
    def _auto_prfx(cls):
        if cls.env_prefix is None:
            letters = []
            cls_name = cls.__name__
            lcn = cls_name.lower()
            for to_strip in cls._rstrip_words:
                if lcn.endswith(to_strip):
                    cls_name = cls_name[:-len(to_strip)]
                    break
            for ch in cls_name:
                if letters and ch in string.ascii_uppercase:
                    letters.append('_')
                letters.append(ch.lower())
            cls.env_prefix = ''.join(letters)

    @classmethod
    def enrich_from_env(cls):
        cls._auto_prfx()
        cls._setup_param_processors()
        pfl = len(cls.env_prefix)
        for env_key, env_value in os.environ.items():
            env_key = env_key.lower()
            if not env_key.startswith(cls.env_prefix):
                continue
            param_key = env_key[pfl:]
            cls.put_param(param_key, env_value)

        if cls.params:
            cls.params = AttrParams(**cls.params)

    @classmethod
    def put_param(cls, key, value):
        if key in cls._pprep:
            value = cls._pprep[key](value)
        if cls._dot_key_params is None:
            cls._dot_key_params = {}
            cls.params = {}

        # pckg.0.gdid = 'adjadj'
        # pckg.0.local = '/path/to/put
        cls._dot_key_params[key] = value

        levels = key.split('.')
        leaf_key = levels.pop()
        curr_host = cls.params
        for level_key in levels:
            if level_key not in curr_host:
                curr_host[level_key] = {}
            curr_host = curr_host[level_key]
        curr_host[leaf_key] = value

    @classmethod
    def _post_process_params(cls):
        if cls.params is None or len(cls._pprop) == 0:
            return
        for param_key, post_proc in cls._pprop.items():
            if param_key in cls.params:
                post_proc(param_key, cls.params[param_key])

    @classmethod
    def _setup_param_processors(cls):
        # override if want to preprocess/postprocess params
        pass

    @classmethod
    def lick_toe(cls):
        raise NotImplementedError

# ez meg okosodhat rarakhato tulkepp barmire, ami callable, vagy van callable attribja
def bear_toe(env_prefix=None):
    tcls = None
    if issubclass(env_prefix, JumpStartAction):
        tcls = env_prefix
        env_prefix = None

    def toedeco(toe):
        # register class as a bear toe
        if not issubclass(toe, JumpStartAction):
            raise Exception('Only subclasses of "JumpStartAction" are allowed for now!')
        toe.enrich_from_env()
        JumpingBearLeg.count_a_toe(toe)
        return toe

    if tcls:
        return toedeco(tcls)
    return toedeco
###################################################
# actual, usable stuff:

@bear_toe
class DriveByToe(JumpStartAction):

    @classmethod
    def get_pckg_remote_local(cls, pckg_key):
        if pckg_key not in cls.params.pckg:
            return None, None
        pckg_info = cls.params.pckg[pckg_key]
        pckg_url = f'https://drive.google.com/open?id={pckg_info.id}'
        pckg_url = f'https://drive.google.com/uc?export=download&id={pckg_info.id}'
        staff_name = pckg_info.get('alias') or pckg_info.id + '.download'
        pckg_path = os.path.join(pckg_info.local, staff_name)
        return pckg_url, pckg_path

    @classmethod
    def lick_toe(cls):
        # print('licking "driveby"')
        for pckg_key in cls.params.pckg.ordered_keys:
            pckg_info = cls.params.pckg[pckg_key]
            if not os.path.exists(pckg_info.local):
                os.makedirs(pckg_info.local)

        for pckg_key in cls.params.pckg.ordered_keys:
            pckg_url, pckg_path = cls.get_pckg_remote_local(pckg_key)
            if not os.path.exists(pckg_path):
                urllib.request.urlretrieve(pckg_url, pckg_path)
        pass


@bear_toe
class UngluckToe(JumpStartAction):
    @classmethod
    def lick_toe(cls):
        print('licking "ungluck"')
        for pckg_key in cls.params.pckg.keys():
            pckg_info = cls.params.pckg[pckg_key]
            target_path = pckg_path = zip_path = None
            if isinstance(pckg_info, AttrParams):
                pckg_path = pckg_info.get('source')
                target_path = pckg_info.get('target')
            elif isinstance(pckg_info, str):
                target_path = pckg_info

            if pckg_path is None:
                pckg_url, pckg_path = DriveByToe.get_pckg_remote_local(pckg_key)
            if pckg_path is None or not os.path.exists(pckg_path):
                raise Exception(f'Missing pckg to ungluck, with key: "{pckg_key}"')

            # plusz esetleg gluckpack-ben van egy leiro
            # amit kiolvasgatunk belole, es az alapjan tomoritjuk ki
            # pack_file = zipfile.ZipFile(pckg_path, 'r', zipfile.ZIP_DEFLATED)
            # if target_path is None:
            #     pack_file.trytoread instructions from pckg

            if target_path is None:
                raise Exception(f'Missing target_path to ungluck pckg to, with key: "{pckg_key}"')

            if 'decrypt' in pckg_info:
                decrypt_key = pckg_info.get('decrypt').encode(encoding='ascii')
                cipher_suite = Fernet(decrypt_key)
                with open(pckg_path, 'rb') as zf:
                    pack_bytes = zf.read()
                zip_bytes = cipher_suite.decrypt(pack_bytes)
                zip_path = pckg_path + '.tmp'
                with open(zip_path, 'wb') as zf:
                    zf.write(zip_bytes)
            print('ungluck', pckg_path, target_path, zip_path)
            os.makedirs(target_path, exist_ok=True)
            pack_file = zipfile.ZipFile(zip_path or pckg_path, 'r', zipfile.ZIP_DEFLATED)
            pack_file.extractall(path=target_path)
            pack_file.close()
        pass


@bear_toe
class RunJobToe(JumpStartAction):
    @classmethod
    def lick_toe(cls):
        print('licking "run_job"')
        pass