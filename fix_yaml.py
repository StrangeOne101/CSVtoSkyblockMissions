from ruamel.yaml import YAML
from ruamel.yaml.constructor import SafeConstructor
import ruamel.yaml.nodes
from collections import defaultdict
from collections.abc import Hashable
import sys

def construct_mapping(self, node, deep=True):
        """deep is True when creating an object/mapping recursively,
        in that case want the underlying elements available during construction
        """
        if not isinstance(node, ruamel.yaml.nodes.MappingNode):
            raise ConstructorError(
                None, None, f'expected a mapping node, but found {node.id!s}', node.start_mark,
            )
        total_mapping = self.yaml_base_dict_type()
        if getattr(node, 'merge', None) is not None:
            todo = [(node.merge, False), (node.value, False)]
        else:
            todo = [(node.value, True)]
        for values, check in todo:
            mapping: Dict[Any, Any] = self.yaml_base_dict_type()
            for key_node, value_node in values:
                # keys can be list -> deep
                key = self.construct_object(key_node, deep=True)
                # lists are not hashable, but tuples are
                if not isinstance(key, Hashable):
                    if isinstance(key, list):
                        key = tuple(key)
                if not isinstance(key, Hashable):
                    raise ConstructorError(
                        'while constructing a mapping',
                        node.start_mark,
                        'found unhashable key',
                        key_node.start_mark,
                    )

                value = self.construct_object(value_node, deep=deep)
                if key in mapping:
                    pat = key + '_undup_{}'
                    index = 0
                    while True:
                        nkey = pat.format(index)
                        if nkey not in mapping:
                            key = nkey
                            break
                        index += 1
                mapping[key] = value
            total_mapping.update(mapping)
        return total_mapping


SafeConstructor.add_constructor(u'tag:yaml.org,2002:map', construct_mapping)
yaml = YAML(typ='safe')

def merge_dicts(d1, d2):
    for key, value in d2.items():
        if key in d1:
            if isinstance(d1[key], dict) and isinstance(value, dict):
                merge_dicts(d1[key], value)
            elif isinstance(d1[key], list) and isinstance(value, list):
                d1[key].extend(value)
            else:
                d1[key] = value
        else:
            d1[key] = value

def fix_yaml_indentation(yaml_content):
    lines = yaml_content.split('\n')
    fixed_lines = []
    indent = 0

    for line in lines:
        stripped_line = line.lstrip()
        if stripped_line.startswith('- '):
            fixed_lines.append(' ' * (indent + 4) + stripped_line)
        else:
            indent = len(line) - len(stripped_line)
            fixed_lines.append(line)

    return '\n'.join(fixed_lines)

def recursive_find(d):
        if isinstance(d, dict):
            popKeys = []
            for key, value in d.items():
                if isinstance(key, str) and '_undup_' in key:
                    k = key.split('_undup_')[0]
                    print(f"Combining duplicate tree: {k}")
                    merge_dicts(d[k], value)
                    popKeys.append(key)
                recursive_find(value)
            for key in popKeys:
                d.pop(key, None)
        elif isinstance(d, list):
            for item in d:
                recursive_find(item)


def fix_yaml_indentation_and_combine_trees(yaml_content):
    fixed_yaml_content = fix_yaml_indentation(yaml_content)
    try:
        # Load the YAML content to check for syntax errors
        data = yaml.load(fixed_yaml_content)
        yaml.dump(data, open('temp.yml', 'w'))
        with open('temp.yml', 'r') as temp:
            data = YAML().load(temp)

        recursive_find(data)
        
        # Combine duplicate trees
        combined_data = defaultdict(dict)
        for key, value in data.items():
            if key in combined_data or '_undup_' in key:
                print(f"Combining duplicate tree: {key}")
                key = key.split('_undup_')[0]
                merge_dicts(combined_data[key], value)
            else:
                combined_data[key] = value
        
        # Dump the YAML content with proper indentation
        fixed_yaml_content = dict(combined_data)
        
        return fixed_yaml_content
    except yaml.YAMLError as exc:
        print(f"Error parsing YAML: {exc}")
        return None

# Example usage
with open('missions.yml', 'r') as file:
    yaml_content = file.read()

fixed_yaml_content = fix_yaml_indentation_and_combine_trees(yaml_content)

if fixed_yaml_content:
    YAML().dump(fixed_yaml_content, open('missions.yml', 'w'))
    #with open('missions.yml', 'w') as file:
        #file.write(fixed_yaml_content)
    print("Fixed YAML content has been written to missions.yml")
else:
    print("Failed to fix YAML content.")