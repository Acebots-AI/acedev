import logging
from typing import Generator, Optional, Sequence, Callable

from github.Repository import Repository
from tree_sitter import Node
from tree_sitter_languages import get_language, get_parser

from acedev.service.model import File, FileChange, PullRequest, Symbol
from acedev.service.parsing import map_code, find_symbol

logger = logging.getLogger(__name__)

# Currently optimized for Python projects
FILES_IGNORE = [
    ".gitignore",
    "Dockerfile",
    ".yaml",
    ".yml",
    ".md",
    ".toml",
    ".txt",
    ".in",
    ".cfg",
    "__init__.py",
    ".ini",
    "poetry.lock",
    ".template",
]


class Project:
    def __init__(self, ghe_repo: Repository) -> None:
        self.ghe_repo = ghe_repo
        self.default_branch = ghe_repo.default_branch
        repo_language = ghe_repo.language.lower()
        self.language = get_language(repo_language)
        self.parser = get_parser(repo_language)

    def __repr__(self) -> str:
        return f"Project({self.ghe_repo.full_name})"

    def get_files(
        self, path: str = "", branch: Optional[str] = None
    ) -> Generator[File, None, None]:
        try:
            for file in self.ghe_repo.get_contents(path, branch or self.default_branch):  # type: ignore[union-attr]
                # TODO: handle images and other non-textual files
                if any(pattern in file.name for pattern in FILES_IGNORE):
                    continue

                if file.type == "dir":
                    yield from self.get_files(path=file.path, branch=branch)
                    continue

                logger.info(
                    f"Processing file: {file.path}. Encoding: {file.encoding}. Size: {file.size}"
                )
                content = file.decoded_content
                yield File(path=file.path, content=content.decode("utf-8"),)
        except Exception as e:
            error_message = f"Failed to get files for {path=} and {branch=}"
            logger.exception(error_message)
            raise ProjectException(error_message) from e

    def get_file(self, path: str, branch: Optional[str] = None) -> File:
        try:
            file = self.ghe_repo.get_contents(path, branch or self.default_branch)  # type: ignore[union-attr]
            content = file.decoded_content
            return File(path=file.path, content=content.decode("utf-8"),)
        except Exception as e:
            error_message = f"Failed to get file {path=}: {e}"
            logger.exception(error_message)
            raise ProjectException(error_message) from e

    def checkout_new_branch(self, branch: str) -> str:
        logger.info(f"Checking out new branch: {branch}")

        if branch in [_branch.name for _branch in self.ghe_repo.get_branches()]:
            raise ProjectException(f"Branch already exists: {branch}")

        try:
            git_ref = self.ghe_repo.create_git_ref(
                ref=f"refs/heads/{branch}",
                sha=self.ghe_repo.get_branch(self.default_branch).commit.sha,
            )
            return git_ref.ref
        except Exception as e:
            error_message = f"Failed to checkout new branch {branch}: {e}"
            logger.exception(error_message)
            raise ProjectException(error_message) from e

    def update_file(self, file: File, branch: str) -> None:
        logger.info(f"Updating file: {file.path}")

        try:
            self.ghe_repo.update_file(
                path=file.path,
                message=f"Update {file.path}",
                content=file.content,
                sha=self.ghe_repo.get_contents(path=file.path, ref=branch).sha,  # type: ignore[union-attr]
                branch=branch,
            )
        except Exception as e:
            error_message = f"Failed to update file {file.path}: {e}"
            logger.exception(error_message)
            raise ProjectException(error_message) from e

    def create_file(self, file: File, branch: str) -> None:
        logger.info(f"Creating file: {file.path}")

        try:
            self.ghe_repo.create_file(
                path=file.path,
                message=f"Create {file.path}",
                content=file.content,
                branch=branch,
            )
        except Exception as e:
            error_message = f"Failed to create file {file.path}: {e}"
            logger.exception(error_message)
            raise ProjectException(error_message) from e

    def delete_file(self, file: File, branch: str) -> None:
        logger.info(f"Deleting file: {file.path}")

        try:
            self.ghe_repo.delete_file(
                path=file.path,
                message=f"Delete {file.path}",
                sha=self.ghe_repo.get_contents(path=file.path, ref=branch).sha,  # type: ignore[union-attr]
                branch=branch,
            )
        except Exception as e:
            error_message = f"Failed to delete file: {file.path}"
            logger.exception(error_message)
            raise ProjectException(error_message) from e

    def create_pull_request(self, title: str, body: str, branch: str) -> PullRequest:
        logger.info(f"Opening PR({title=}, {branch=})")

        for pr in self.ghe_repo.get_pulls(state="open"):
            if pr.head.ref == branch:
                raise ProjectException(f"Pull request already exists for {branch=}")

        try:
            pull_request = self.ghe_repo.create_pull(
                title=title, body=body, head=branch, base=self.default_branch
            )

            return PullRequest(
                title=pull_request.title,
                body=pull_request.body,
                head_ref=pull_request.head.ref,
                url=pull_request.html_url,
                files=[
                    FileChange(
                        status=file.status, filename=file.filename, diff=file.patch
                    )
                    for file in pull_request.get_files()
                ],
            )
        except Exception as e:
            error_message = f"Failed to open Pull Request({title=}, {branch=}): {e}"
            logger.exception(error_message)
            raise ProjectException(error_message) from e

    def get_pull_request(self, _id: int) -> PullRequest:
        try:
            pull_request = self.ghe_repo.get_pull(number=_id)
            return PullRequest(
                title=pull_request.title,
                body=pull_request.body,
                head_ref=pull_request.head.ref,
                url=pull_request.html_url,
                files=[
                    FileChange(
                        status=file.status, filename=file.filename, diff=file.patch
                    )
                    for file in pull_request.get_files()
                ],
            )
        except Exception as e:
            error_message = f"Failed to get PR#{_id}: {e}"
            logger.exception(error_message)
            raise ProjectException(error_message) from e

    def get_pull_request_files(self, _id: int) -> Sequence[FileChange]:
        try:
            pull_request = self.ghe_repo.get_pull(number=_id)
            return [
                FileChange(
                    status=file.status, filename=file.filename, diff=file.patch
                )
                for file in pull_request.get_files()
            ]
        except Exception as e:
            error_message = f"Failed to get PR#{_id} files: {e}"
            logger.exception(error_message)
            raise ProjectException(error_message) from e

    def print_repo_map(self, branch: Optional[str] = None) -> str:
        repo_map = ""
        for file in self.get_files(branch=branch):
            syntax_tree = self.parser.parse(file.content.encode())
            repo_map += f"{file.path}:\n\n"
            repo_map += f"{map_code(syntax_tree, self.language)}\n\n"

        return repo_map

    def print_symbol(self, symbol: str, path: str, branch: Optional[str] = None) -> Symbol:
        file = self.get_file(path, branch)
        syntax_tree = self.parser.parse(file.content.encode())
        node = find_symbol(syntax_tree.root_node, symbol)
        if not node:
            raise ProjectException(f"Symbol {symbol} not found in {path}")
        return Symbol(content=node.text.decode("utf-8"), path=path)

    def update_symbol_in_file(self, symbol: str, path: str, content: str, branch: str) -> None:
        current_file = self.get_file(path, branch)
        current_tree = self.parser.parse(current_file.content.encode())
        current_node = find_symbol(current_tree.root_node, symbol)

        if not current_node:
            raise ProjectException(f"Symbol {symbol} not found in {path}")

        new_tree = self.parser.parse(content.encode())
        new_root_node = new_tree.root_node

        if new_root_node.has_error:
            raise ProjectException(f"Failed to parse new definition for {symbol}: {content}")

        if new_root_node.child_count != 1:
            raise ProjectException(f"New definition contains {new_root_node.child_count} expressions instead of 1")

        new_node = new_root_node.child(0)

        current_node_type = self._node_type(current_node)
        new_node_type = self._node_type(new_node)

        if current_node_type != new_node_type:
            raise ProjectException(f"New definition is {new_node_type} instead of {current_node_type}")

        new_symbol_name = self._symbol_name(new_node)
        if new_symbol_name != symbol:
            raise ProjectException(f"New definition is for {new_symbol_name} instead of {symbol}")

        new_content = self._update_symbol_in_file_content(
            file_content=current_file.content,
            start_point=current_node.start_point,
            end_point=current_node.end_point,
            updated_definition=content)

        new_file = File(path=path, content=new_content)
        self.update_file(new_file, branch)

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

    def add_symbol(self, symbol: str, path: str, content: str, branch: str) -> None:
        """Naively adds a symbol to the end of the file."""
        current_file = self.get_file(path, branch)
        current_tree = self.parser.parse(current_file.content.encode())
        current_node = find_symbol(current_tree.root_node, symbol)

        if current_node:
            raise ProjectException(f"Symbol {symbol} already exists in {path}")

        new_tree = self.parser.parse(content.encode())
        new_root_node = new_tree.root_node

        if new_root_node.has_error:
            raise ProjectException(f"Failed to parse {symbol} definition: {content}")

        if new_root_node.child_count != 1:
            raise ProjectException(f"Symbol definition contains {new_root_node.child_count} expressions instead of 1")

        new_node = new_root_node.child(0)

        new_symbol_name = self._symbol_name(new_node)
        if new_symbol_name != symbol:
            raise ProjectException(f"Symbol definition is for {new_symbol_name} instead of {symbol}")

        new_content = current_file.content + "\n\n" + content
        new_file = File(path=path, content=new_content)
        self.update_file(new_file, branch)

    @staticmethod
    def _update_symbol_in_file_content(
            file_content: str,
            start_point: tuple[int, int],
            end_point: tuple[int, int],
            updated_definition: str
    ) -> str:
        lines = file_content.split('\n')

        # Remove trailing whitespace
        lines = [line.rstrip() for line in lines]

        # Handle start and end lines, considering partial line replacements
        start_line, start_char = start_point
        end_line, end_char = end_point
        updated_lines = updated_definition.split('\n')

        # Before start line unchanged
        new_content = lines[:start_line]

        # Handle partial line at the start if needed TODO: handle indents
        new_content.append(lines[start_line][:start_char] + updated_lines[0].lstrip())
        updated_lines = updated_lines[1:]  # Remove the first line of updated definition since it's merged

        # Insert updated definition lines
        new_content.extend(updated_lines)

        # Handle partial line at the end if needed
        new_content[-1] = new_content[-1] + lines[end_line][end_char:]

        # After end line unchanged
        new_content.extend(lines[end_line+1:])

        return '\n'.join(new_content)

    def add_imports(self, import_statements: list[str], path: str, branch: str) -> None:
        """Naively adds import statements to the top of the file."""

        try:
            file = self.get_file(path, branch)
            new_imports = "\n".join(import_statements)
            new_content = f"{new_imports}\n{file.content}"""
            new_file = File(path=path, content=new_content)
            self.update_file(new_file, branch)
        except Exception as e:
            error_message = f"Failed to add imports {import_statements} to {path} in {branch}: {e}"
            logger.exception(error_message)
            raise ProjectException(error_message) from e

    def replace_imports(self, old_imports: list[str], new_imports: list[str], path: str, branch: str) -> None:
        """Naively replaces import statements in the file."""
        try:
            file = self.get_file(path, branch)
            new_content = file.content
            for old_import, new_import in zip(old_imports, new_imports):
                new_content = new_content.replace(old_import, new_import)
            new_file = File(path=path, content=new_content)
            self.update_file(new_file, branch)
        except Exception as e:
            error_message = f"Failed to replace imports {old_imports} with {new_imports} in {path} in {branch}: {e}"
            logger.exception(error_message)
            raise ProjectException(error_message) from e

    def code_understanding_tools(self) -> dict[str, Callable[..., str]]:
        def get_project_outline(branch: Optional[str] = None):
            """
            Print project outline containing classes, functions, and files.

            Parameters
            ----------
            branch : str, optional
                Name of the branch. Default is the default branch.

            Returns
            -------
            str
                Project outline or failure message.
            """
            try:
                return self.print_repo_map(branch)
            except ProjectException as e:
                return f"Failed to get project outline: {e.message}"

        def get_symbol(symbol: str, path: str, branch: Optional[str] = None):
            """
            Expand the symbol e.g. function, class or method from the project file.

            Parameters
            ----------
            symbol : str
                Name of the symbol.
            path : str
                Path to the project file containing the symbol.
            branch : str, optional
                Name of the branch. Default is the default branch.

            Returns
            -------
            str
                Expanded symbol or failure message.
            """
            try:
                return self.print_symbol(symbol, path, branch).content
            except ProjectException as e:
                return f"Failed to get {symbol} from {path}: {e.message}"

        return {
          get_project_outline.__name__: get_project_outline,
          get_symbol.__name__: get_symbol
        }

    def code_editing_tools(self) -> dict[str, Callable[..., str]]:
        def update_file(path: str, content: str, branch: str):
            """
            Update the file in the branch.

            Parameters
            ----------
            path : str
                Path to the file.
            content : str
                New content of the file.
            branch : str
                Name of the branch.

            Returns
            -------
            str
                Success or failure message.
                Returns failure message if the branch is protected (e.g. main, master).
            """
            if branch == self.default_branch:
                # even if it's not protected, we don't want to push on the default branch
                return f"Failed to update {path} in {branch=}: branch is protected."

            try:
                self.update_file(File(path=path, content=content), branch)
                return f"Updated {path} in {branch}"
            except ProjectException as e:
                return f"Failed to update {path} in {branch}: {e.message}"

        def update_symbol(symbol: str, path: str, content: str, branch: str):
            """
            Update the symbol, e.g. function, class or method in the project file.

            Parameters
            ----------
            symbol : str
                Name of the symbol.
            path : str
                Path to the file.
            content : str
                New definition of the symbol.
            branch : str
                Name of the branch.

            Returns
            -------
            str
                Success or failure message.
                Returns failure message if the branch is protected (e.g. main, master).
                Returns failure message if the symbol is not found.
                Returns failure message if the new definition can not be parsed.
                Returns failure messages if the new definition contains any
                other expressions except symbol definition.
                Returns failure message if the new definition is for another symbol.
            """
            if branch == self.default_branch:
                # even if it's not protected, we don't want to push on the default branch
                return f"Failed to update {symbol} in {path} on {branch=}: branch is protected."

            try:
                self.update_symbol_in_file(symbol, path, content, branch)
                return f"Updated {symbol} in {path} on {branch=}"
            except ProjectException as e:
                return f"Failed to update {symbol} in {path} on {branch=}: {e.message}"

        def create_file(path: str, content: str, branch: str):
            """
            Create the file in the branch.

            Parameters
            ----------
            path : str
                Path to the file.
            content : str
                New content of the file.
            branch : str
                Name of the branch.

            Returns
            -------
            str
                Success or failure message.
                Returns failure message if the branch is protected (e.g. main, master).
            """
            if branch == self.default_branch:
                # even if it's not protected, we don't want to push on the default branch
                return f"Failed to create file {path} on {branch=}: branch is protected."

            try:
                self.create_file(File(path=path, content=content), branch)
                return f"Created {path} in {branch}"
            except ProjectException as e:
                return f"Failed to create {path} in {branch}: {e.message}"

        def checkout_new_branch(branch: str):
            """
            Checkout a new branch.

            Parameters
            ----------
            branch : str
                Name of the branch.

            Returns
            -------
            str
                Success or failure message.
            """
            try:
                self.checkout_new_branch(branch)
                return f"Checked out new branch: {branch}"
            except ProjectException as e:
                return f"Failed to checkout new branch: {branch}: {e.message}"

        def create_pull_request(title: str, body: str, branch: str):
            """
            Create a pull request.

            Parameters
            ----------
            title : str
                Title of the pull request.
            body : str
                Body of the pull request.
            branch : str
                Name of the branch.

            Returns
            -------
            str
                Success or failure message.
            """
            try:
                pull_request = self.create_pull_request(title, body, branch)
                return f"Created pull request: {pull_request.url}"
            except ProjectException as e:
                return f"Failed to create pull request: {title}: {e.message}"

        def add_imports(import_statements: list[str], path: str, branch: str) -> str:
            """
            Add import statements in the project file.

            Parameters
            ----------
            import_statements : list
                List of import statements, e.g. ["import os", "from datetime import datetime"].
            path : str
                Path to the file.
            branch : str
                Name of the branch.

            Returns
            -------
            str
                Success or failure message.
                Returns failure message if the branch is protected (e.g. main, master).
            """
            if branch == self.default_branch:
                # even if it's not protected, we don't want to push on the default branch
                return f"Failed to add imports to {path} on {branch=}: branch is protected."

            try:
                self.add_imports(import_statements, path, branch)
                return f"Added imports {import_statements} to {path} in {branch}"
            except ProjectException as e:
                return f"Failed to add imports {import_statements} to {path} in {branch}: {e.message}"

        def replace_imports(old_import_statement: list[str], new_import_statements: list[str], path: str, branch: str) -> str:
            """
            Replace import statements in the project file.

            Parameters
            ----------
            old_import_statement : list
                List of old import statements, e.g. ["import os", "from datetime import datetime"].
            new_import_statements : list
                List of new import statements, e.g. ["import os", "from datetime import datetime"].
            path : str
                Path to the file.
            branch : str
                Name of the branch.

            Returns
            -------
            str
                Success or failure message.
                Returns failure message if the branch is protected (e.g. main, master).
            """
            if branch == self.default_branch:
                # even if it's not protected, we don't want to push on the default branch
                return f"Failed to replace imports {old_import_statement} with {new_import_statements} in {path} in {branch}: branch is protected."

            try:
                self.replace_imports(old_import_statement, new_import_statements, path, branch)
                return f"Replaced imports {old_import_statement} with {new_import_statements} in {path} in {branch}"
            except ProjectException as e:
                return f"Failed to replace imports {old_import_statement} with {new_import_statements} in {path} in {branch}: {e.message}"

        def add_symbol(symbol: str, path: str, content: str, branch: str) -> str:
            """
            Add symbol, e.g. function, class or method to the project file.

            Parameters
            ----------
            symbol : str
                Name of the symbol.
            path : str
                Path to the file.
            content : str
                Definition of the symbol.
            branch : str
                Name of the branch.

            Returns
            -------
            str
                Success or failure message.
                Returns failure message if the branch is protected (e.g. main, master).
                Returns failure message if the symbol already exists.
                Returns failure message if the symbol definition can not be parsed.
                Returns failure messages if the symbol definition contains any
                other expressions except symbol definition.
                Returns failure message if the new definition is for another symbol.
            """
            if branch == self.default_branch:
                # even if it's not protected, we don't want to push on the default branch
                return f"Failed to add {symbol} to {path} in {branch}: branch is protected."

            try:
                self.add_symbol(symbol, path, content, branch)
                return f"Added {symbol} to {path} in {branch}"
            except ProjectException as e:
                return f"Failed to add {symbol} to {path} in {branch}: {e.message}"

        return {
            # update_file.__name__: update_file,
            update_symbol.__name__: update_symbol,
            create_file.__name__: create_file,
            checkout_new_branch.__name__: checkout_new_branch,
            create_pull_request.__name__: create_pull_request,
            add_imports.__name__: add_imports,
            replace_imports.__name__: replace_imports,
            add_symbol.__name__: add_symbol
        }


class ProjectException(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)
