from pathlib import Path
from argparse import ArgumentParser
from typing import Iterable
from ament_index_python import get_package_share_directory
from jinja2 import Environment, FileSystemLoader
from dataclasses import dataclass
from rcl_interfaces.msg import ParameterType

@dataclass
class Message:
    name: str
    message: dict
    
@dataclass
class Service:
    name: str
    request: dict
    response: dict

@dataclass
class Action:
    name: str
    goal: dict
    result: dict
    feedback: dict


def get_spec_files(path: Path, glob: str) -> list:
    """Get all the spec files in a directory.

    Args:
        path (Path): Path to the directory containing the spec files.
        glob (str): Glob pattern to match the spec files.

    Returns:
        list: List of spec files.
    """
    return [f for f in path.glob(glob) if f.is_file()]

def prepare_output_dir(output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)

def split_line(line: str):
    """Split a line into a tuple of type and name.

    Args:
        line (str): The line to split.

    Returns:
        tuple: The type and name of the line.
    """
    line = line.replace('\n', '')
    if line.startswith("#") or "=" in line or len(line) == 0:
        return None, None
    if "#" in line:
        line = line.split("#")[0]
    split = line.split(" ")
    split[0] = split[0].replace("/", ".")
        
    return split[0], split[1]


def process_msg_file(msg_file: Path):
    """Process a message file."""
    name = msg_file.stem
    message = {}
    file = msg_file.open()
    for line in file:
        if '=' in line:
            continue
        line = line.replace('\n', '')
        if len(line) == 0:
            continue
        typename, variablename = split_line(line)
        if typename is None:
            continue
        if variablename is None:
            continue
        message[variablename] = typename
    file.close()
    return name, message

def process_srv_file(srv_file: Path):
    """Process a message file."""
    name = srv_file.stem
    request = {}
    response = {}
    file = srv_file.open()
    resp = False
    for line in file:
        if '---' in line:
            resp = True
            continue
        typename, variablename = split_line(line)
        if typename is None:
            continue
        if variablename is None:
            continue
        if resp:
            response[variablename] = typename
        else:
            request[variablename] = typename
    file.close()
    return name, request, response

def process_action_file(action_file: Path):
    """Process an aciton file."""
    name = action_file.stem
    goal = {}
    result = {}
    feedback = {}
    file = action_file.open()
    border = 0
    for line in file:
        if '---' in line:
            border += 1
            continue
        typename, variablename = split_line(line)
        if typename is None:
            continue
        if variablename is None:
            continue
        if border == 0:
            goal[variablename] = typename
        if border == 1:
            result[variablename] = typename
        if border == 2:
            feedback[variablename] = typename
    file.close()
    return name, goal, result, feedback

def process_msg_dir(msg_path: Path):
    msg_files = get_spec_files(msg_path, "*.msg")
    msgs = []
    for msg_file in msg_files:
        name, message = process_msg_file(msg_file)
        msg = Message(name, message)
        msgs.append(msg)
    return msgs

def process_srv_dir(msg_path: Path):
    srv_files = get_spec_files(msg_path, "*.srv")
    srvs = []
    for srv_file in srv_files:
        name, request, response = process_srv_file(srv_file)
        srv = Service(name, request, response)
        srvs.append(srv)
    return srvs

def process_action_dir(msg_path: Path):
    action_files = get_spec_files(msg_path, "*.action")
    actions = []
    for action_file in action_files:
        name, goal, result, feedback = process_action_file(action_file)
        action = Action(name, goal, result, feedback)
        actions.append(action)
    return actions

from ros2node.api import TopicInfo

def fix_topic_types(topics: Iterable[TopicInfo]):
    for topic in topics:
        topic.types[0] = topic.types[0].replace("/msg/", ".")
        topic.types[0] = topic.types[0].replace("/srv/", ".")
        topic.types[0] = topic.types[0].replace("/action/", ".")
        #topic.name = topic.name.replace("/", "")

def get_parameter_type_string(parameter_type):
    mapping = {
        ParameterType.PARAMETER_BOOL: 'bool',
        ParameterType.PARAMETER_INTEGER: 'int',
        ParameterType.PARAMETER_DOUBLE: 'double',
        ParameterType.PARAMETER_STRING: 'string',
        ParameterType.PARAMETER_BYTE_ARRAY: 'byte[]',
        ParameterType.PARAMETER_BOOL_ARRAY: 'bool[]',
        ParameterType.PARAMETER_INTEGER_ARRAY: 'int[]',
        ParameterType.PARAMETER_DOUBLE_ARRAY: 'double[]',
        ParameterType.PARAMETER_STRING_ARRAY: 'stirng[]',
        ParameterType.PARAMETER_NOT_SET: 'not set',
    }
    return mapping[parameter_type]