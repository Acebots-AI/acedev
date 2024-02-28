import logging
from dataclasses import dataclass
from typing import Sequence, Optional

from tree_sitter import Parser, Language, Node, Tree

from acedev.service.gitrepository import GitRepository
from acedev.service.model import File, Symbol

CLASS_CAPTURE = "class"
FUNC_CAPTURE = "func"
IMPORT_CAPTURE = "import"
EXPRESSION_CAPTURE = "expression"

logger = logging.getLogger(__name__)


@dataclass
class SymbolManipulator:
    git_repository: GitRepository
    parser: Parser
    language: Language

    def get_project_outline(self, files: Sequence[File]) -> str:
        repo_map = ""
        for file in files:
            syntax_tree = self.parser.parse(file.content.encode())
            repo_map += f"{file.path}:\n"
            repo_map += f"{self._map_code(syntax_tree, self.language)}\n"

        return repo_map.rstrip()

    def get_symbol(self, symbol: str, file: File) -> Symbol:
        syntax_tree = self.parser.parse(file.content.encode())
        node = self._find_symbol(syntax_tree.root_node, symbol)
        if not node:
            raise SymbolManipulatorException(
                f"Symbol {symbol} not found in {file.path}"
            )
        return Symbol(content=node.text.decode("utf-8"), path=file.path)

    def update_symbol(self, symbol: str, content: str, file: File) -> File:
        current_tree = self.parser.parse(file.content.encode())
        current_node = self._find_symbol(current_tree.root_node, symbol)

        if not current_node:
            raise SymbolManipulatorException(
                f"Symbol {symbol} not found in {file.path}"
            )

        new_tree = self.parser.parse(content.encode())
        new_root_node = new_tree.root_node

        if new_root_node.has_error:
            raise SymbolManipulatorException(
                f"Failed to parse new definition for {symbol}: {content}"
            )

        if new_root_node.child_count != 1:
            raise SymbolManipulatorException(
                f"New definition contains {new_root_node.child_count} expressions instead of 1"
            )

        new_node = new_root_node.child(0)

        current_node_type = self._node_type(current_node)
        new_node_type = self._node_type(new_node)

        if current_node_type != new_node_type:
            raise SymbolManipulatorException(
                f"New definition is {new_node_type} instead of {current_node_type}"
            )

        new_symbol_name = self._symbol_name(new_node)
        if new_symbol_name != symbol:
            raise SymbolManipulatorException(
                f"New definition is for {new_symbol_name} instead of {symbol}"
            )

        new_content = self._update_symbol_in_file_content(
            file_content=file.content,
            start_point=current_node.start_point,
            end_point=current_node.end_point,
            updated_definition=content,
        )

        return File(path=file.path, content=new_content)

    def add_symbol(self, symbol: str, content: str, file: File) -> File:
        """Naively adds a symbol to the end of the file."""
        current_tree = self.parser.parse(file.content.encode())
        current_node = self._find_symbol(current_tree.root_node, symbol)

        if current_node:
            raise SymbolManipulatorException(
                f"Symbol {symbol} already exists in {file.path}"
            )

        new_tree = self.parser.parse(content.encode())
        new_root_node = new_tree.root_node

        if new_root_node.has_error:
            raise SymbolManipulatorException(
                f"Failed to parse {symbol} definition: {content}"
            )

        if new_root_node.child_count != 1:
            raise SymbolManipulatorException(
                f"Symbol definition contains {new_root_node.child_count} expressions instead of 1"
            )

        new_node = new_root_node.child(0)

        new_symbol_name = self._symbol_name(new_node)
        if new_symbol_name != symbol:
            raise SymbolManipulatorException(
                f"Symbol definition is for {new_symbol_name} instead of {symbol}"
            )

        new_content = file.content + "\n\n" + content

        if not new_content.endswith("\n"):
            new_content += "\n"

        return File(path=file.path, content=new_content)

    @staticmethod
    def add_imports(import_statements: list[str], file: File) -> File:
        """Naively adds import statements to the top of the file."""

        new_imports = "\n".join(import_statements)
        new_content = f"{new_imports}\n{file.content}"
        return File(path=file.path, content=new_content)

    @staticmethod
    def replace_imports(
        old_imports: list[str], new_imports: list[str], file: File
    ) -> File:
        """Naively replaces import statements in the file."""
        new_content = file.content
        for old_import, new_import in zip(old_imports, new_imports):
            new_content = new_content.replace(old_import, new_import)
        return File(path=file.path, content=new_content)

    @staticmethod
    def _node_type(node: Node) -> str:
        if node.type == "decorated_definition":
            return node.child(1).type
        return node.type

    @staticmethod
    def _symbol_name(node: Node) -> str:
        if node.type == "decorated_definition":
            return node.child(1).child_by_field_name("name").text.decode("utf-8")
        return node.child_by_field_name("name").text.decode("utf-8")

    @staticmethod
    def _update_symbol_in_file_content(
        file_content: str,
        start_point: tuple[int, int],
        end_point: tuple[int, int],
        updated_definition: str,
    ) -> str:
        lines = file_content.split("\n")

        # Remove trailing whitespace
        lines = [line.rstrip() for line in lines]

        # Handle start and end lines, considering partial line replacements
        start_line, start_char = start_point
        end_line, end_char = end_point
        updated_lines = updated_definition.split("\n")

        # Before start line unchanged
        new_content = lines[:start_line]

        # Handle partial line at the start if needed TODO: handle indents
        new_content.append(lines[start_line][:start_char] + updated_lines[0].lstrip())
        updated_lines = updated_lines[
            1:
        ]  # Remove the first line of updated definition since it's merged

        # Insert updated definition lines
        new_content.extend(updated_lines)

        # Handle partial line at the end if needed
        new_content[-1] = new_content[-1] + lines[end_line][end_char:]

        # After end line unchanged
        new_content.extend(lines[end_line + 1 :])

        return "\n".join(new_content)

    @staticmethod
    def _print_capture(node: Node, capture_name: str) -> str:
        result = ""

        match capture_name:
            case _ if capture_name == CLASS_CAPTURE:
                class_name = node.child_by_field_name("name")
                result = f'class {class_name.text.decode("utf-8")}:\n'

            case _ if capture_name == FUNC_CAPTURE:
                func_name = node.child_by_field_name("name").text.decode("utf-8")
                params = node.child_by_field_name("parameters").text.decode("utf-8")
                body = node.child_by_field_name("body")
                return_type = node.child_by_field_name("return_type")
                declaration = ""
                if node.parent.type == "decorated_definition":
                    declaration += f"{node.parent.child(0).text.decode('utf-8')}\n"
                declaration += f"def {func_name}{params}" + (
                    f' -> {return_type.text.decode("utf-8")}' if return_type else ""
                )

                indent = node.start_point[1]
                result += " " * indent + declaration

                if body.child(0).text.decode("utf-8").startswith('"""'):
                    docstring = body.child(0).text.decode("utf-8")
                    result += "\n" + " " * indent + docstring

                result += "\n"

            case _ if capture_name == IMPORT_CAPTURE:
                result = node.text.decode("utf-8") + "\n"

            case _ if capture_name == EXPRESSION_CAPTURE:
                if (
                    node.parent.type != "block"
                ):  # I'm not sure if this is the best way to check if it's a top-level expression
                    result = node.text.decode("utf-8") + "\n"

            case _:
                logger.warning(f"Unexpected capture name: {capture_name}")

        return result

    def _map_code(self, ast: Tree, language: Language) -> str:
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
            result += self._print_capture(node, capture_name)

        return result

    def _find_symbol(self, node: Node, symbol: str) -> Optional[Node]:
        """
        Find the definition of a symbol in the code.

        Args:
        - tree: The Abstract Syntax Tree (AST) of the code to search.
        - symbol: The name of the symbol to find.

        Returns:
        - A string representing the definition of the symbol.
        """
        node_name = node.child_by_field_name("name")
        if node_name and node_name.text.decode("utf-8") == symbol:
            return node

        if node.child_count == 0:
            return None

        for child in node.children:
            result = self._find_symbol(child, symbol)
            if result:
                return result


class SymbolManipulatorException(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
