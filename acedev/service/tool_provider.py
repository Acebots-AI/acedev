from dataclasses import dataclass
from typing import Callable, Optional

from acedev.service.github_service import GitHubService, GitHubServiceException
from acedev.service.gitrepository import GitRepository, GitRepositoryException
from acedev.service.model import File
from acedev.service.symbol_manipulator import SymbolManipulator, SymbolManipulatorException


@dataclass
class ToolProvider:
    git_repository: GitRepository
    github_service: GitHubService
    symbol_manipulator: SymbolManipulator

    def get_default_branch(self):
        """
        Get the default branch of the project.

        Returns
        -------
        str
            Default branch of the project.
        """
        return self.git_repository.default_branch

    def get_project_outline(self, branch: Optional[str] = None):
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
            Returns failure message if the branch does not exist.
        """
        try:
            if branch and not self.git_repository.branch_exists(branch):
                return f"Failed to get project outline: {branch=} does not exist."

            files = list(self.git_repository.get_files(branch=branch or self.git_repository.default_branch))
            return self.symbol_manipulator.get_project_outline(files)
        except (GitRepositoryException, SymbolManipulatorException) as e:
            return f"Failed to get project outline: {e.message}"

    def get_symbol(self, symbol: str, path: str, branch: Optional[str] = None):
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
            Returns failure message if the branch does not exist.
        """
        try:
            if branch and not self.git_repository.branch_exists(branch):
                return f"Failed to get {symbol} from {path}: {branch=} does not exist."

            file = self.git_repository.get_file(path=path, branch=branch or self.git_repository.default_branch)
            return self.symbol_manipulator.get_symbol(symbol=symbol, file=file).content
        except (GitRepositoryException, SymbolManipulatorException) as e:
            return f"Failed to get {symbol} from {path}: {e.message}"

    def code_understanding_tools(self) -> dict[str, Callable[..., str]]:

        return {
            self.get_default_branch.__name__: self.get_default_branch,
            self.get_project_outline.__name__: self.get_project_outline,
            self.get_symbol.__name__: self.get_symbol
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
            try:
                if branch == self.git_repository.default_branch:
                    # even if it's not protected, we don't want to push on the default branch
                    return f"Failed to update {path}: {branch=} is protected."

                if not self.git_repository.branch_exists(branch):
                    return f"Failed to update {path}: {branch=} does not exist."

                self.git_repository.update_file(file=File(path=path, content=content), branch=branch)
                return f"Updated {path} in {branch}"
            except GitRepositoryException as e:
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
            try:
                if branch == self.git_repository.default_branch:
                    # even if it's not protected, we don't want to push on the default branch
                    return f"Failed to update {symbol} in {path}: {branch=} is protected."

                if not self.git_repository.branch_exists(branch):
                    return f"Failed to update {symbol} in {path}: {branch=} does not exist."

                file = self.git_repository.get_file(path=path, branch=branch)
                new_file = self.symbol_manipulator.update_symbol(symbol=symbol, content=content, file=file)
                self.git_repository.update_file(file=new_file, branch=branch)
                return f"Updated {symbol} in {path} on {branch=}"
            except (GitRepositoryException, SymbolManipulatorException) as e:
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

            try:
                if branch == self.git_repository.default_branch:
                    # even if it's not protected, we don't want to push on the default branch
                    return f"Failed to create file {path}: {branch=} is protected."

                if not self.git_repository.branch_exists(branch):
                    return f"Failed to create {path}: {branch=} does not exist."

                self.git_repository.create_file(File(path=path, content=content), branch)
                return f"Created {path} in {branch}"
            except GitRepositoryException as e:
                return f"Failed to create {path} in {branch}: {e.message}"

        def create_new_branch(branch: str):
            """
            Create a new branch.

            Parameters
            ----------
            branch : str
                Name of the branch.

            Returns
            -------
            str
                Success or failure message.
                Returns failure message if the branch already exists.
            """
            try:
                self.git_repository.create_new_branch(branch)
                return f"Created new branch {branch}"
            except GitRepositoryException as e:
                return f"Failed to create new {branch=}: {e.message}"

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
                Returns failure message if the branch doesn't exist.
                Returns failure message if the pull request already exists.
            """
            try:
                if not self.git_repository.branch_exists(branch):
                    return f"Failed to create pull request: {branch=} does not exist."

                pull_request = self.github_service.create_pull_request(title, body, branch)
                return f"Created pull request: {pull_request.url}"
            except GitHubServiceException as e:
                return f"Failed to create pull request: {e.message}"

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
                Returns failure message if the branch does not exist.
            """

            try:
                if branch == self.git_repository.default_branch:
                    # even if it's not protected, we don't want to push on the default branch
                    return f"Failed to add imports to {path}: {branch=} is protected."

                if not self.git_repository.branch_exists(branch):
                    return f"Failed to add imports to {path}: {branch=} does not exist."

                file = self.git_repository.get_file(path=path, branch=branch)
                new_file = self.symbol_manipulator.add_imports(import_statements=import_statements, file=file)
                self.git_repository.update_file(file=new_file, branch=branch)
                return f"Added imports {import_statements} to {path} in {branch}"
            except (GitRepositoryException, SymbolManipulatorException) as e:
                return f"Failed to add imports {import_statements} to {path} in {branch}: {e.message}"

        def replace_imports(
                old_import_statement: list[str], new_import_statements: list[str], path: str, branch: str) -> str:
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
                Returns failure message if the branch does not exist.
            """

            try:
                if branch == self.git_repository.default_branch:
                    # even if it's not protected, we don't want to push on the default branch
                    return f"Failed to replace imports {old_import_statement} with {new_import_statements} in {path}: \
                            {branch=} is protected."

                if not self.git_repository.branch_exists(branch):
                    return f"Failed to replace imports {old_import_statement} with {new_import_statements} in {path}: \
                            {branch=} does not exist."

                # TODO: check if path exists

                file = self.git_repository.get_file(path=path, branch=branch)
                new_file = self.symbol_manipulator.replace_imports(
                    old_imports=old_import_statement,
                    new_imports=new_import_statements,
                    file=file)
                self.git_repository.update_file(file=new_file, branch=branch)
                return f"Replaced imports {old_import_statement} with {new_import_statements} in {path} on {branch}"
            except (GitRepositoryException, SymbolManipulatorException) as e:
                return f"Failed to replace imports {old_import_statement} with {new_import_statements} in {path} on {branch}: {e.message}"

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

            try:
                if branch == self.git_repository.default_branch:
                    # even if it's not protected, we don't want to push on the default branch
                    return f"Failed to add {symbol} to {path}: {branch=} is protected."

                if not self.git_repository.branch_exists(branch):
                    return f"Failed to add {symbol} to {path}: {branch=} does not exist."

                file = self.git_repository.get_file(path=path, branch=branch)
                new_file = self.symbol_manipulator.add_symbol(symbol=symbol, content=content, file=file)
                self.git_repository.update_file(file=new_file, branch=branch)
                return f"Added {symbol} to {path} on {branch}"
            except (GitRepositoryException, SymbolManipulatorException) as e:
                return f"Failed to add {symbol} to {path} on {branch}: {e.message}"

        return {
            # update_file.__name__: update_file,
            update_symbol.__name__: update_symbol,
            create_file.__name__: create_file,
            create_new_branch.__name__: create_new_branch,
            create_pull_request.__name__: create_pull_request,
            add_imports.__name__: add_imports,
            replace_imports.__name__: replace_imports,
            add_symbol.__name__: add_symbol
        }
