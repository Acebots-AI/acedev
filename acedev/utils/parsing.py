import logging
from typing import Optional

from tree_sitter import Language, Node, Tree

logger = logging.getLogger(__name__)

CLASS_CAPTURE = 'class'
FUNC_CAPTURE = 'func'
IMPORT_CAPTURE = 'import'
EXPRESSION_CAPTURE = 'expression'


def print_capture(node: Node, capture_name: str) -> str:
    result = ""

    match capture_name:
        case _ if capture_name == CLASS_CAPTURE:
            class_name = node.child_by_field_name('name')
            result = f'\nclass {class_name.text.decode("utf-8")}:\n'

        case _ if capture_name == FUNC_CAPTURE:
            func_name = node.child_by_field_name('name').text.decode("utf-8")
            params = node.child_by_field_name('parameters').text.decode("utf-8")
            body = node.child_by_field_name('body')
            return_type = node.child_by_field_name('return_type')
            declaration = f'def {func_name}{params}' + (f' -> {return_type.text.decode("utf-8")}' if return_type else '')

            indent = node.start_point[1]
            result += ' ' * indent + declaration

            if body.child(0).text.decode("utf-8").startswith('"""'):
                docstring = body.child(0).text.decode("utf-8")
                result += '\n' + ' ' * indent + docstring

            result += '\n\n'

        case _ if capture_name == IMPORT_CAPTURE:
            result = node.text.decode("utf-8") + '\n'

        case _ if capture_name == EXPRESSION_CAPTURE:
            if node.parent.type != "block": # I'm not sure if this is the best way to check if it's a top-level expression
                result = node.text.decode("utf-8") + '\n'

        case _:
            logger.warning(f"Unexpected capture name: {capture_name}")

    return result


def map_code(ast: Tree, language: Language) -> str:
    pattern = f"""
    (import_statement) @{IMPORT_CAPTURE}
    (import_from_statement) @{IMPORT_CAPTURE}
    (expression_statement) @{EXPRESSION_CAPTURE}
    (class_definition) @{CLASS_CAPTURE}
    (function_definition) @{FUNC_CAPTURE}
    """

    query = language.query(pattern)
    captures = query.captures(ast.root_node)

    result = ""
    for node, capture_name in captures:
        result += print_capture(node, capture_name)

    return result


def find_symbol(node: Node, symbol: str) -> Optional[Node]:
    """
    Find the definition of a symbol in the code.

    Args:
    - tree: The Abstract Syntax Tree (AST) of the code to search.
    - symbol: The name of the symbol to find.

    Returns:
    - A string representing the definition of the symbol.
    """
    node_name = node.child_by_field_name('name')
    if node_name and node_name.text.decode("utf-8") == symbol:
        return node

    if node.child_count == 0:
        return None

    for child in node.children:
        result = find_symbol(child, symbol)
        if result:
            return result
