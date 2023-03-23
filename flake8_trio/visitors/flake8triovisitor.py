"""Contains the base class that all error classes inherit from."""

from __future__ import annotations

import ast
from abc import ABC
from typing import TYPE_CHECKING, Any, Union

import libcst as cst
from libcst.metadata import PositionProvider

from ..base import Error, Statement

if TYPE_CHECKING:
    from collections.abc import Iterable

    from ..runner import SharedState

    HasLineCol = Union[
        ast.expr, ast.stmt, ast.arg, ast.excepthandler, ast.alias, Statement
    ]


class Flake8TrioVisitor(ast.NodeVisitor, ABC):
    # abstract attribute by not providing a value
    error_codes: dict[str, str]  # pyright: reportUninitializedInstanceVariable=false

    def __init__(self, shared_state: SharedState):
        super().__init__()
        self.outer: dict[ast.AST, dict[str, Any]] = {}
        self.novisit = False
        self.__state = shared_state

        self.options = self.__state.options
        self.typed_calls = self.__state.typed_calls

        # mark variables that shouldn't be saved/loaded in self.get_state
        self.nocopy = {
            "_Flake8TrioVisitor__state",
            "error_codes",
            "nocopy",
            "novisit",
            "options",
            "outer",
            "typed_calls",
        }

    # `variables` can be saved/loaded, but need a setter to not clear the reference
    @property
    def variables(self) -> dict[str, str]:
        return self.__state.variables

    @variables.setter
    def variables(self, value: dict[str, str]) -> None:
        self.__state.variables.clear()
        self.__state.variables.update(value)

    def visit(self, node: ast.AST):
        """Visit a node."""
        # construct visitor for this node type
        visitor = getattr(self, "visit_" + node.__class__.__name__, None)

        # if we have a visitor for it, visit it
        # it will set self.novisit if it manually visits children
        self.novisit = False

        if visitor is not None:
            visitor(node)

        # if it doesn't set novisit, let the regular NodeVisitor iterate through
        # subfields
        if not self.novisit:
            super().generic_visit(node)

        # if an outer state was saved in this node restore it after visiting children
        self.set_state(self.outer.pop(node, {}))

        # set novisit so external runner doesn't visit this node with this class
        self.novisit = True

    def visit_nodes(self, *nodes: ast.AST | Iterable[ast.AST]):
        for arg in nodes:
            if isinstance(arg, ast.AST):
                self.visit(arg)
            else:
                for node in arg:
                    self.visit(node)

    def error(
        self,
        node: HasLineCol,
        *args: str | Statement | int,
        error_code: str | None = None,
    ):
        if error_code is None:
            assert (
                len(self.error_codes) == 1
            ), "No error code defined, but class has multiple codes"
            error_code = next(iter(self.error_codes))
        # don't emit an error if this code is disabled in a multi-code visitor
        elif error_code[:7] not in self.options.enabled_codes:
            return

        self.__state.problems.append(
            Error(
                # 7 == len('TRIO...'), so alt messages raise the original code
                error_code[:7],
                node.lineno,
                node.col_offset,
                self.error_codes[error_code],
                *args,
            )
        )

    def get_state(self, *attrs: str, copy: bool = False) -> dict[str, Any]:
        if not attrs:
            # get all attributes, unless they're marked as nocopy
            attrs = tuple(set(self.__dict__.keys()) - self.nocopy)
        res: dict[str, Any] = {}
        for attr in attrs:
            value = getattr(self, attr)
            if copy and hasattr(value, "copy"):
                value = value.copy()
            res[attr] = value
        return res

    def set_state(self, attrs: dict[str, Any], copy: bool = False):
        for attr, value in attrs.items():
            setattr(self, attr, value)

    def save_state(self, node: ast.AST, *attrs: str, copy: bool = False):
        state = self.get_state(*attrs, copy=copy)
        if node in self.outer:
            # not currently used, and not gonna bother adding dedicated test
            # visitors atm
            self.outer[node].update(state)  # pragma: no cover
        else:
            self.outer[node] = state

    def walk(self, *body: ast.AST) -> Iterable[ast.AST]:
        for b in body:
            yield from ast.walk(b)

    @property
    def library(self) -> tuple[str, ...]:
        return self.__state.library if self.__state.library else ("trio",)

    @property
    def library_str(self) -> str:
        if len(self.library) == 1:
            return self.library[0]
        return "[" + "|".join(self.library) + "]"

    def add_library(self, name: str) -> None:
        if name not in self.__state.library:
            self.__state.library = self.__state.library + (name,)


class Flake8TrioVisitor_cst(cst.CSTTransformer, ABC):
    # abstract attribute by not providing a value
    error_codes: dict[str, str]  # pyright: reportUninitializedInstanceVariable=false
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self, shared_state: SharedState):
        super().__init__()
        self.outer: dict[cst.CSTNode, dict[str, Any]] = {}
        self.__state = shared_state

        self.options = self.__state.options

    def get_state(self, *attrs: str, copy: bool = False) -> dict[str, Any]:
        # require attrs, since we inherit a *ton* of stuff which we don't want to copy
        assert attrs
        res: dict[str, Any] = {}
        for attr in attrs:
            value = getattr(self, attr)
            if copy and hasattr(value, "copy"):
                value = value.copy()
            res[attr] = value
        return res

    def set_state(self, attrs: dict[str, Any], copy: bool = False):
        for attr, value in attrs.items():
            if copy and hasattr(value, "copy"):  # pragma: no cover
                # not used by visitors yet
                value = value.copy()
            setattr(self, attr, value)

    def save_state(self, node: cst.CSTNode, *attrs: str, copy: bool = False):
        state = self.get_state(*attrs, copy=copy)
        if node in self.outer:
            self.outer[node].update(state)
        else:
            self.outer[node] = state

    def restore_state(self, node: cst.CSTNode):
        self.set_state(self.outer.pop(node, {}))

    def error(
        self,
        node: cst.CSTNode,
        *args: str | Statement | int,
        error_code: str | None = None,
    ):
        if error_code is None:
            assert (
                len(self.error_codes) == 1
            ), "No error code defined, but class has multiple codes"
            error_code = next(iter(self.error_codes))
        # don't emit an error if this code is disabled in a multi-code visitor
        # TODO: write test for only one of 910/911 enabled/autofixed
        elif error_code[:7] not in self.options.enabled_codes:
            return  # pragma: no cover
        pos = self.get_metadata(PositionProvider, node).start

        self.__state.problems.append(
            Error(
                # 7 == len('TRIO...'), so alt messages raise the original code
                error_code[:7],
                pos.line,
                pos.column,
                self.error_codes[error_code],
                *args,
            )
        )

    def should_autofix(self, code: str | None = None):
        if code is None:
            assert len(self.error_codes) == 1
            code = next(iter(self.error_codes))
        return code in self.options.autofix_codes

    @property
    def library(self) -> tuple[str, ...]:
        return self.__state.library if self.__state.library else ("trio",)

    # library_str not used in cst yet

    def add_library(self, name: str) -> None:
        if name not in self.__state.library:
            self.__state.library = self.__state.library + (name,)
