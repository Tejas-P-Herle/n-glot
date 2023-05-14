"""Read and write to database"""


import json
import os
from selenium import webdriver
from errors import MissingFunctionError

import selenium.webdriver.support.ui as ui
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


from pprint import pprint


class DataBase:
    from_meta = None
    to_meta = None
    from_reserved_kw = None
    conn = None
    cache_package: dict = None
    valid_paths: set = None
    from_lang_name: str = ""
    to_lang_name: str = ""

    def __init__(self):
        """Initiation method of DataBase Class"""
        
        # Initiate class attributes
        self.from_ = {}
        self.to = {}
        self.cache_package = {}
        self.valid_paths = set()

        options = webdriver.ChromeOptions()
        options.add_argument("--incognito")
        options.add_argument("--headless")
        if not os.path.exists(f"package_cache_java_basic"):
            self.driver = webdriver.Chrome(options=options)
            # self.driver.get('http://0.0.0.0:8080/signin.html')
            # input("Waiting for signin...")
            self.driver.get('http://0.0.0.0:8080')
            self.ready_state = "div.className='ready';"

            self.driver.execute_script(
                "div=document.createElement('div');div.id='pyWait';"
                + "document.body.appendChild(div);db_handler=new DBHandler()")

            self.run_sync_js_cmds([
                "console.log(db_handler);",
                "db_handler.signIn('balaramtejas@gmail.com', 'Password').then("
                + "() => { " + self.ready_state + " });",
            ])

        self.languages = self.get_languages()

    def wait_for_selenium(self):
        """Waits for selenium to finish flagged task"""
        
        ui.WebDriverWait(self.driver, timeout=30).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "#pyWait[class='ready']")))
        self.driver.execute_script("div.className='wait';")

    def run_sync_js_cmds(self, js_cmds):
        """Run JS Commands Synchronously"""

        self.driver.execute_script("div.className='wait';")
        for cmd in js_cmds:
            self.driver.execute_script(cmd)
        self.wait_for_selenium()
    
    def __del__(self):
        """Delete DataBase Instace"""

        if hasattr(self, "driver") and self.driver is not None:
            self.driver.close()

    def get_async_result(self, async_cmd):
        """Get Result of asynchronous command"""
        
        # Run commands synchronously
        self.run_sync_js_cmds([
            async_cmd
            + ".then((data)=>{async_res=data;" + self.ready_state + "},"
            + "(error)=>{console.error(error);async_res=null;"
            + self.ready_state + "});"
        ])
        return self.driver.execute_script("return async_res;")

    def get_languages(self):
        """Get list of available languages"""

        base = "/home/tejaspherle/Programming/n-glot/ILC_cnv_dbs/cnv_dbs/"
        languages = {}
        for lang in ["java", "python"]:
            ext = "java" if lang == "java" else "py"
            with open(base + f"{lang}_{ext}.db") as file:
                languages[lang] = json.load(file)["meta"]
        return languages
        
        # Get available files from conversion database
        return self.get_async_result("db_handler.get_langs_meta()")

    def get_lang_package(self, lang, package_name="basic"):
        """Get Basic Functions of given Language"""

        # Get basic function for conversion db
        try:
            with open(f"package_cache_{lang}_{package_name}") as file:
                package = json.load(file)
        except FileNotFoundError:
            package = self.get_async_result(
                f"db_handler.get_package('{lang}', '{package_name}')")
            with open(f"package_cache_{lang}_{package_name}", "w") as file:
                json.dump(package, file, indent=2)
        self.cache_package.update({
            f"languages/{lang}{path[1:]}": val for path, val in package.items()
        })
        return package

    def parse_from_package(self, package: dict):
        """Parse info from package of from language"""

        from_info = {}
        from_prefix = f"from/"
        reserved_prefix = "reserved/"
        len_reserved = len(reserved_prefix)
        self.valid_paths.update(
            {f"languages/{self.from_lang_name}/{path[1:]}"
             for path in package.pop("valid_paths")})
        for path, doc_info in package.items():
            path = path[2:]
            if path.startswith(from_prefix):
                path = path[5:]
            if path.startswith(reserved_prefix):
                path = path[len_reserved:]
            path = path.replace("Coll-Bridge/", "")
            path_split = path.split("/")
            if path_split[0] != "to":
                doc_info["path"] = path
                self.add_branch(from_info, path_split, doc_info)
                from_info[path_split[-1]] = doc_info
        return from_info

    @staticmethod
    def add_branch(tree, path, data):
        """Add data to tree at end of path"""

        curr_branch = tree
        for seg in path[:-1]:
            if seg not in curr_branch:
                curr_branch[seg] = {}
            curr_branch = curr_branch[seg]
        curr_branch[path[-1]] = data

    def parse_to_package(self, package: dict):
        """Parse info from package of from language"""

        to_info = {}
        to_prefix = f"to/Coll-Bridge/{self.from_lang_name}/"
        len_prefix = len(to_prefix)
        reserved_prefix = "reserved/"
        len_reserved = len(reserved_prefix)
        self.valid_paths.update(
            {f"languages/{self.to_lang_name}/{path[1:]}"
             for path in package.pop("valid_paths")})

        for path, doc_info in package.items():
            path = path[2:]
            if path.startswith(to_prefix):
                path = path[len_prefix:]
            if path.startswith(reserved_prefix):
                path = path[len_reserved:]
            path = path.replace("Coll-Bridge/", "")
            path_split = path.split("/")
            if path_split[0] != "from" or path_split == ["from", "get_type"]:

                # TODO: Rename convs to misc, and correct other renaming
                if "misc" in path_split:
                    path_split[path_split.index("misc")] = "convs"
                if "obj_mod" in path_split:
                    path_split[path_split.index("obj_mod")] = "obj_mod_convs"
                if "func_call" in path_split:
                    path_split[path_split.index("func_call")] = \
                        "func_call_convs"

                doc_info["path"] = path
                self.add_branch(to_info, path_split, doc_info)
                to_info[path_split[-1]] = doc_info
        return to_info

    @staticmethod
    def path_to_args(root, path=""):
        """Convert Reference Path to Arguments String"""
    
        path_str = '/Coll-Bridge/'.join(path.split("/")) if path else ""
        args_list = f"{root.rstrip('/')}/{path_str}".rstrip("/").split("/")
        return '"' + '","'.join(args_list) + '"'
    
    def get_conv(self, reference):
        """Get Conversion"""

        local_ref = reference.replace("Coll-Bridge/", "")
        local_ref_list = local_ref.split("/")
        local_ref_list[0] = "cnv_dbs"
        local_ref_list[1] = ("javafuncs"
                             if local_ref_list[1] == "java" else "pyfuncs")
        local_ref_list[2] = "core_" + local_ref_list[2]
        local_ref = "/".join(local_ref_list)
        base = "/home/tejaspherle/Programming/n-glot/ILC_cnv_dbs/"
        local_ref = base + local_ref + ".py"

        try:
            with open(local_ref) as file:
                resp = {"path": reference, "code": file.read()}
                return resp
        except FileNotFoundError:
            return

        reference = reference.replace(".", "-")
        if reference not in self.valid_paths:
            return None
        if reference in self.cache_package:
            return self.cache_package[reference]
        ref_args = self.path_to_args(reference)
        resp = self.get_async_result(f"db_handler.get_doc_data({ref_args})")
        self.cache_package[reference] = resp
        resp["path"] = reference
        return resp

    @classmethod
    def get_word_map_applier(cls):
        with open("word_map_applier.py") as code_file:
            return code_file.read()

    @staticmethod
    def get_module_env(code_str):
        """Get Module Environment"""

        module_env = {}
        exec(code_str, module_env)
        return module_env

    def get_docs(self, root, path):
        """Get all docs from path from root"""

        root_split = (root + "/" + path).split("/")
        root_split_base = root_split.copy()
        root_split[0] = "cnv_dbs"
        root_split[1] = "javafuncs" if root_split[1] == "java" else "pyfuncs"
        root_split[2] = "core_" + root_split[2]
        base = "/home/tejaspherle/Programming/n-glot/ILC_cnv_dbs/"
        ref_path = "/".join(root_split_base)
        docs = {}
        for file in os.listdir(base + "/".join(root_split)):
            file_str = file.rstrip(".py")
            ref = ref_path + "/" + file_str
            conv = self.get_conv(ref)
            if conv is not None:
                docs[file_str] = conv
        return docs
        
        coll_path = self.path_to_args(root, path)
        return self.get_async_result(f"db_handler.get_docs_json({coll_path})")

    @staticmethod
    def save_data(filepath, data, d_type="json"):
        """Save data in given filepath"""

        with open(filepath + "." + d_type, "w") as file:
            file.write(data)

    @staticmethod
    def get_files_in_dir(dir_):
        """Get all files in directory"""

        for file in next(os.walk(dir_))[2]:
            yield os.path.splitext(file)[0]

    def get_from_funcs_path(self):
        """Returns location of from-language functions"""
        
        return "languages/{}".format(self.from_meta["name"])

    def get_to_funcs_path(self):
        """Returns location of to-language functions"""

        return "languages/{}".format(self.to_meta["name"])

    def get_base_path(self):
        """Get base path to from_lang conversions of set to language"""

        return "{}/to/Coll-Bridge/{}/Coll-Bridge".format(
            self.get_to_funcs_path(), self.from_lang_name)

    def get_eq_conv(self, from_type):
        """Get equivalent conversion for given from_type"""

        return self.get_conv(f"{self.get_base_path()}/eq_types/{from_type}")

    def get_lib_obj(self, lib_path):
        """Get Conversion functions of lib_path"""
        
        lib_base_path = "{}/lib_convs".format(self.get_base_path())

        if not lib_path:
            return lib_base_path

        for part in lib_path[:-1]:
            lib_base_path += f"/Coll-Bridge/{part}"
        lib_base_path += "/" + lib_path[-1]

        return self.get_conv(lib_base_path)

    def get_kw_conv(self, keyword):
        """Get Keyword Conversion"""

        return self.get_conv("{}/keyword_triggers/{}".format(
            self.get_base_path(), keyword))

    def get_opr_conv(self, opr, lhs_type, rhs_type):
        """Get Operator conversion for given parameters"""

        try:
            base = f"{self.get_base_path()}/operator_overloads"
            if rhs_type is not None:
                conv = self.get_conv(f"{base}/Coll-Bridge/->{rhs_type}/{opr}")
                if conv:
                    return conv
            if lhs_type is not None:
                conv = self.get_conv(f"{base}/Coll-Bridge/{lhs_type}/{opr}")
                if conv:
                    return conv
            return self.get_conv(f"{base}/{opr}")
        except (ModuleNotFoundError, AttributeError):
            return

    def setup(self, lang_from_name, lang_to_name):
        """Setup Database"""

        self.from_lang_name = lang_from_name
        self.to_lang_name = lang_to_name

        # Read and save data
        self.from_ = self.languages[lang_from_name]
        self.to = self.languages[lang_to_name]

        # Get basic conversion functions
        self.from_["from"] = self.parse_from_package(self.get_lang_package(
            lang_from_name))
        self.from_["get_type"] = self.from_["from"].pop("get_type")
        self.to["to"] = self.parse_to_package(self.get_lang_package(
            lang_to_name))
        self.to["get_type"] = self.to["to"].pop("from")["get_type"]

        # print("PACKAGES")
        # pprint(self.from_["from"])
        # pprint(self.to["to"])

        # Save reserved keywords data
        self.from_reserved_kw = self.from_["reserved_kw"]
        self.from_meta = self.from_
        self.to_meta = self.to
        self.from_meta["name"] = lang_from_name
        self.to_meta["name"] = lang_to_name

        # Get basic type classifiers of both languages
        root_from = self.get_from_funcs_path()
        # self.from_["get_type"] = self.get_conv(f"{root_from}/from/get_type")
        root_to = self.get_to_funcs_path()
        # self.to["get_type"] = self.get_conv(f"{root_to}/from/get_type")

    def write_to_cnv_db(self, data):
        """Write to conversion Databases"""

        # TODO implement json write method

        # REMOVE THIS LINE
        print("DATA", data)

        err = "Write to conversion data base is not implemented"
        raise NotImplementedError(err)

