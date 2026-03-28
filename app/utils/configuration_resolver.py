class ConfigurationResolver:
    """
    A class to resolve `link` entries in a nested configuration structure.
    Supports navigation through dictionaries, lists, and `children`.
    """

    def __init__(self, config):
        self.config = config

    def resolve_links(self):
        """
        Resolves all `link` entries in the configuration.
        """
        self._recursive_resolve(self.config, self.config)

    def __load_children(self,path):
        """
        Check if explicitly children should be loaded and not parent
        """
        return path.split('.').pop() == "children"
        
    def _replace_in_dict_by_dict(self, dict_origine, old_key, new_dict):
        if old_key in dict_origine:
            # Entferne den alten Key
            old_value = dict_origine.pop(old_key)
            # Füge die neuen Key-Value-Paare hinzu
            dict_origine.update(new_dict)

    def _replace_in_list_by_list(self, list_origine, old_element, new_elements):
        index = list_origine.index(old_element)
        list_origine[index:index+1] = new_elements

    def _replace_element_in_list(self, list_origine, old_element, new_element):
        index = list_origine.index(old_element)
        list_origine[index] = new_element

    def _recursive_resolve(self, current_config, root_config):
        """
        Recursively resolves `link` entries in the configuration.
        """
        if isinstance(current_config, dict):
            for key, value in list(current_config.items()):
                if key == "children":
                    if value is None or not isinstance(value, list):
                        raise ValueError(f"Expected 'children' to be a list, but got {type(value).__name__} instead.")
                    for item in value:
                        if "link" in item:
                            loaded_link = self._find_entry(root_config, self._mapped_key(item['link']), False)
                            if isinstance(loaded_link, list):
                                self._replace_in_list_by_list(value,item,loaded_link)
                            else:
                                self._replace_element_in_list(value,item,loaded_link)  
                        else:
                            self._recursive_resolve(value, root_config)            
                elif key == "link":
                    try:
                        loaded = self._find_entry(root_config, self._mapped_key(value), False)
                        if isinstance(loaded, list) and len(loaded) > 2:
                            loaded = self._find_entry(root_config, self._mapped_key(value), False)  
                        current_config.clear()
                        current_config.update(loaded)
                    except Exception as e: 
                        raise ValueError(
                            f"Error resolving link '{value}': {str(e)}. "
                            f"Current part: {key}, Current config: {current_config}" + (f", Loaded: {loaded}" if 'loaded' in locals() or 'loaded' in globals() else "")
                        )
                else:
                    self._recursive_resolve(value, root_config)
        elif isinstance(current_config, list):
            for item in current_config:
                self._recursive_resolve(item, root_config)

    def _get_children(self,current):
        if isinstance(current, dict) and ("children" in current and current["children"]):
            current = current["children"]
        return current

    def _mapped_key(self,name):
        return name.replace(" ", "").lower()
        
    def _find_by_name(self,current, part):
        return next(
                    (item for item in current if isinstance(item, dict) and self._mapped_key(item.get("name", "")) == part),
                    None
                )

    def _find_entry(self, config, path, children):
        """
        Finds an entry in the configuration by a dot-separated path.
        Supports both dictionaries and lists with `children` navigation.
        """
        parts = path.split('.')
        current = config
        for part in parts:
            if isinstance(current, list):
                # If children explicit declared just load children
                if part != "children":
                    # Look for a matching name in the list
                    found = self._find_by_name(current,part)
                    if found:
                        current = found
                        print(
                            f"Matching entry for '{part}' in list. Path so far: {' > '.join(parts[:parts.index(part)+1])}. "
                            f"Current list: {current}"
                        )
                    else:
                        raise ValueError(
                            f"No matching entry for '{part}' in list. Path so far: {' > '.join(parts[:parts.index(part)+1])}. "
                            f"Current list: {current}"
                        )
            elif isinstance(current, dict):
                # Case-insensitive dictionary lookup
                key = next((k for k in current if self._mapped_key(k) == part), None)
                # If no fitting key was found search in the children
                if key is None:
                    if "children" not in current:
                        raise KeyError(
                        f"No 'children' found in current dictionary. Path so far: {' > '.join(parts[:parts.index(part)+1])}. "
                        f"Current dictionary: {current}"
                    )
                    # The following line seems buggy; Why is children loaded allways and not just when children is set?
                    current = self._find_by_name(current["children"],part)
                    
                    if not current:
                        raise KeyError(
                            f"Key '{part}' not found in dictionary. Path so far: {' > '.join(parts[:parts.index(part)+1])}. "
                            f"Current dictionary: {current}"
                        )
                else: 
                    current = current[key]
                
            else:
                raise ValueError(
                    f"Invalid path segment '{part}'. Current type: {type(current)}. "
                    f"Path so far: {' > '.join(parts[:parts.index(part)+1])}"
                )
            if children:
                current = self._get_children(current)

        return current

    def get_config(self):
        """
        Returns the resolved configuration.
        """
        return self.config
