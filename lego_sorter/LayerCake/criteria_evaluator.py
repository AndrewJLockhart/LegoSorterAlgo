"""Criteria evaluator for Lego sorting."""

import logging
from typing import Any, Optional, Union

import pyparsing as pp

from ..rb_parts import RbParts, RbPart
from ..rb_colour import RbColours, RbColour

# Initialize logger for this module
logger = logging.getLogger(__name__)


class CriteriaEvaluator:
    """
    Evaluates boolean criteria strings against Lego/BrickLink metadata.
    
    This class uses a Domain Specific Language (DSL) to allow users to define
    complex matching rules for Lego pieces. It uses pyparsing to build a 
    recursive descent parser for boolean logic.
    """

    def __init__(self, expression: str):
        """
        Initialize with a criteria expression string.
        
        The expression is parsed immediately to ensure it's valid before 
        being used in the sorting machine.
        """
        self.expression = expression
        self.parser = self._build_parser()
        try:
            # We parse the expression once at initialization to catch syntax errors early.
            # This is a 'fail-fast' approach to configuration errors.
            self.parsed_expression = self.parser.parse_string(expression, parse_all=True)
            logger.debug(f"Successfully parsed criteria expression: '{expression}'")
        except pp.ParseException as exc:
            logger.error(f"Failed to parse criteria expression '{expression}' at position {exc.col}: {exc.msg}")
            raise ValueError(f"Invalid criteria expression at character position {exc.col}: {exc.msg}") from exc

    def _build_parser(self):
        """
        Constructs the pyparsing grammar for the criteria DSL.
        
        The grammar supports:
        - Keys: RB_COL, RB_PT, RB_PT_CAT
        - Operators: =, !=
        - Logic: AND, OR, and | (pipe) for multiple values
        - Grouping: Parentheses ()
        """
        # Define keywords
        AND = pp.CaselessKeyword("AND")
        OR = pp.CaselessKeyword("OR")
        LPAR = pp.Suppress("(")
        RPAR = pp.Suppress(")")

        # Define fields
        RB_COL = pp.CaselessKeyword("RB_COL")
        RB_PT = pp.CaselessKeyword("RB_PT")
        RB_PT_CAT = pp.CaselessKeyword("RB_PT_CAT")

        KEY = RB_COL | RB_PT | RB_PT_CAT

        # Define operators
        EQ = pp.Literal("=")
        NEQ = pp.Literal("!=")
        OPERATOR = EQ | NEQ

        # Define values
        # A value is a sequence of words that are not reserved keywords
        # We exclude AND/OR to ensure they are treated as operators
        reserved = AND | OR
        
        # Allowed characters in a word: alphanumeric, comma, underscore, hyphen
        # We explicitly exclude the parentheses from the word characters to avoid consuming them
        word_chars = pp.alphanums + ",_-"
        
        # A word cannot be a reserved keyword
        valid_word = ~reserved + pp.Word(word_chars)
        
        # A value can be multiple words separated by spaces (e.g. "Maersk Blue")
        SINGLE_VALUE = pp.Combine(valid_word + pp.ZeroOrMore(pp.White() + valid_word))
        
        # Support multiple values separated by | (e.g. "Red | Blue")
        PIPE = pp.Suppress("|")
        VALUE = pp.Group(SINGLE_VALUE + pp.ZeroOrMore(PIPE + SINGLE_VALUE))

        # Define the comparison term
        # We use a ParseAction to convert the tokens into a dictionary for easier evaluation
        def parse_comparison(tokens):
            # tokens is [key, op, [value1, value2, ...]]
            # Converting to a dict makes the recursive evaluation in _eval_node much cleaner.
            return {"key": tokens[0], "op": tokens[1], "value": tokens[2].as_list()}

        comparison = (KEY + OPERATOR + VALUE).set_parse_action(parse_comparison)

        # Define the boolean logic using infix_notation
        # This handles operator precedence (AND before OR) and nested parentheses automatically.
        expr = pp.infix_notation(comparison, [
            (AND, 2, pp.OpAssoc.LEFT),
            (OR, 2, pp.OpAssoc.LEFT),
        ])

        return expr

    def evaluate(self, rb_part: Optional[RbPart] = None, rb_col: Optional[Union[RbColour, int]] = None) -> bool:
        """
        Evaluate the criteria against the provided context.

        Args:
            rb_part: Optional Rebrickable Part object.
            rb_col: Optional Rebrickable Colour object or ID.

        Returns:
            True if the criteria is met, False otherwise.
        """
        # Resolve rb_col to Object if it's an int
        # This allows the caller to pass either a rich object or a simple ID.
        if isinstance(rb_col, int):
            try:
                rb_col = RbColours(rb_col)
            except ValueError:
                # If invalid ID, we treat it as None or just keep it to fail checks later
                logger.warning(f"Invalid color ID provided to evaluator: {rb_col}")
                pass

        result = self._eval_node(self.parsed_expression[0], rb_part, rb_col)
        logger.debug(f"Evaluated '{self.expression}' against part={rb_part}, col={rb_col} -> {result}")
        return result

    def __eq__(self, other):
        if not isinstance(other, CriteriaEvaluator):
            return False
        return self.expression == other.expression

    def __repr__(self):
        return f"CriteriaEvaluator('{self.expression}')"

    @property
    def specificity_score(self) -> int:
        """
        Calculate the specificity score of the expression.
        Higher score means more specific (more constraints).
        
        This is used by the sorting algorithm to ensure that pieces are 
        assigned to the most precise bucket available.
        """
        return self._count_constraints(self.parsed_expression[0])

    def _count_constraints(self, node) -> int:
        if isinstance(node, dict):
            val = node.get("value")
            if isinstance(val, list):
                return len(val)
            return 1
        
        if hasattr(node, "asList"):
            node = node.asList()
            
        if isinstance(node, list):
            count = 0
            for item in node:
                if item not in ("AND", "OR"):
                    count += self._count_constraints(item)
            return count
            
        return 0

    def _eval_node(self, node, rb_part, rb_col):
        if isinstance(node, dict):
            return self._check_condition(node["key"], node["op"], node["value"], rb_part, rb_col)

        # Handle list from infixNotation
        if hasattr(node, "asList"):
            node = node.asList()

        if isinstance(node, list):
            if len(node) == 1:
                return self._eval_node(node[0], rb_part, rb_col)

            # Evaluate left-associative logic
            result = self._eval_node(node[0], rb_part, rb_col)
            for i in range(1, len(node), 2):
                op = node[i]
                next_node = node[i + 1]
                val = self._eval_node(next_node, rb_part, rb_col)
                
                if op == "AND":
                    result = result and val
                elif op == "OR":
                    result = result or val
            return result

        return False

    def _check_condition(self, key, op, values, rb_part, rb_col):
        key_upper = key.upper()
        
        # Evaluate each value in the list
        results = []
        for value_str in values:
            match = False
            if key_upper == "RB_COL":
                if isinstance(rb_col, RbColour):
                    # Check against ID
                    if value_str.isdigit() and rb_col.id == int(value_str):
                        match = True
                    # Check against Name
                    elif rb_col.name.lower() == value_str.lower():
                        match = True
            
            elif key_upper == "RB_PT":
                if rb_part is not None and rb_part.part_num == value_str:
                    match = True

            elif key_upper == "RB_PT_CAT":
                if rb_part is not None:
                    # Check against Category ID
                    if value_str.isdigit() and rb_part.category.id == int(value_str):
                        match = True
                    # Check against Category Name
                    elif rb_part.category.name.lower() == value_str.lower():
                        match = True
            
            results.append(match)

        # If op is "=", we return True if ANY value matches.
        # If op is "!=", we return True if NONE of the values match.
        if op == "=":
            return any(results)
        elif op == "!=":
            return not any(results)
        
        return False
