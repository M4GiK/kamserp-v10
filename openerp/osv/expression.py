#!/usr/bin/env python
# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

""" Domain expression processing

The main duty of this module is to compile a domain expression into a
SQL query. A lot of things should be documented here, but as a first
step in the right direction, some tests in test_osv_expression.yml
might give you some additional information.

For legacy reasons, a domain uses an inconsistent two-levels abstract
syntax (domains are regular Python data structures). At the first
level, a domain is an expression made of terms (sometimes called
leaves) and (domain) operators used in prefix notation. The available
operators at this level are '!', '&', and '|'. '!' is a unary 'not',
'&' is a binary 'and', and '|' is a binary 'or'.  For instance, here
is a possible domain. (<term> stands for an arbitrary term, more on
this later.)::

    ['&', '!', <term1>, '|', <term2>, <term3>]

It is equivalent to this pseudo code using infix notation::

    (not <term1>) and (<term2> or <term3>)

The second level of syntax deals with the term representation. A term
is a triple of the form (left, operator, right). That is, a term uses
an infix notation, and the available operators, and possible left and
right operands differ with those of the previous level. Here is a
possible term::

    ('company_id.name', '=', 'OpenERP')

The left and right operand don't have the same possible values. The
left operand is field name (related to the model for which the domain
applies).  Actually, the field name can use the dot-notation to
traverse relationships.  The right operand is a Python value whose
type should match the used operator and field type. In the above
example, a string is used because the name field of a company has type
string, and because we use the '=' operator. When appropriate, a 'in'
operator can be used, and thus the right operand should be a list.

Note: the non-uniform syntax could have been more uniform, but this
would hide an important limitation of the domain syntax. Say that the
term representation was ['=', 'company_id.name', 'OpenERP']. Used in a
complete domain, this would look like::

    ['!', ['=', 'company_id.name', 'OpenERP']]

and you would be tempted to believe something like this would be
possible::

    ['!', ['=', 'company_id.name', ['&', ..., ...]]]

That is, a domain could be a valid operand. But this is not the
case. A domain is really limited to a two-level nature, and can not
take a recursive form: a domain is not a valid second-level operand.

Unaccent - Accent-insensitive search

OpenERP will use the SQL function 'unaccent' when available for the
'ilike' and 'not ilike' operators, and enabled in the configuration.
Normally the 'unaccent' function is obtained from `the PostgreSQL
'unaccent' contrib module
<http://developer.postgresql.org/pgdocs/postgres/unaccent.html>`_.

.. todo: The following explanation should be moved in some external
         installation guide

The steps to install the module might differ on specific PostgreSQL
versions.  We give here some instruction for PostgreSQL 9.x on a
Ubuntu system.

Ubuntu doesn't come yet with PostgreSQL 9.x, so an alternative package
source is used. We use Martin Pitt's PPA available at
`ppa:pitti/postgresql
<https://launchpad.net/~pitti/+archive/postgresql>`_.

.. code-block:: sh

    > sudo add-apt-repository ppa:pitti/postgresql
    > sudo apt-get update

Once the package list is up-to-date, you have to install PostgreSQL
9.0 and its contrib modules.

.. code-block:: sh

    > sudo apt-get install postgresql-9.0 postgresql-contrib-9.0

When you want to enable unaccent on some database:

.. code-block:: sh

    > psql9 <database> -f /usr/share/postgresql/9.0/contrib/unaccent.sql

Here :program:`psql9` is an alias for the newly installed PostgreSQL
9.0 tool, together with the correct port if necessary (for instance if
PostgreSQL 8.4 is running on 5432). (Other aliases can be used for
createdb and dropdb.)

.. code-block:: sh

    > alias psql9='/usr/lib/postgresql/9.0/bin/psql -p 5433'

You can check unaccent is working:

.. code-block:: sh

    > psql9 <database> -c"select unaccent('hélène')"

Finally, to instruct OpenERP to really use the unaccent function, you have to
start the server specifying the ``--unaccent`` flag.

"""

import logging
import traceback

import openerp.modules
from openerp.osv import fields
from openerp.osv.orm import MAGIC_COLUMNS
import openerp.tools as tools

#.apidoc title: Domain Expressions

# Domain operators.
NOT_OPERATOR = '!'
OR_OPERATOR = '|'
AND_OPERATOR = '&'
DOMAIN_OPERATORS = (NOT_OPERATOR, OR_OPERATOR, AND_OPERATOR)

# List of available term operators. It is also possible to use the '<>'
# operator, which is strictly the same as '!='; the later should be prefered
# for consistency. This list doesn't contain '<>' as it is simpified to '!='
# by the normalize_operator() function (so later part of the code deals with
# only one representation).
# An internal (i.e. not available to the user) 'inselect' operator is also
# used. In this case its right operand has the form (subselect, params).
TERM_OPERATORS = ('=', '!=', '<=', '<', '>', '>=', '=?', '=like', '=ilike',
                  'like', 'not like', 'ilike', 'not ilike', 'in', 'not in',
                  'child_of')

# A subset of the above operators, with a 'negative' semantic. When the
# expressions 'in NEGATIVE_TERM_OPERATORS' or 'not in NEGATIVE_TERM_OPERATORS' are used in the code
# below, this doesn't necessarily mean that any of those NEGATIVE_TERM_OPERATORS is
# legal in the processed term.
NEGATIVE_TERM_OPERATORS = ('!=', 'not like', 'not ilike', 'not in')

TRUE_LEAF = (1, '=', 1)
FALSE_LEAF = (0, '=', 1)

TRUE_DOMAIN = [TRUE_LEAF]
FALSE_DOMAIN = [FALSE_LEAF]

_logger = logging.getLogger(__name__)


# --------------------------------------------------
# Generic domain manipulation
# --------------------------------------------------

def normalize_domain(domain):
    """Returns a normalized version of ``domain_expr``, where all implicit '&' operators
       have been made explicit. One property of normalized domain expressions is that they
       can be easily combined together as if they were single domain components.
    """
    assert isinstance(domain, (list, tuple)), "Domains to normalize must have a 'domain' form: a list or tuple of domain components"
    if not domain:
        return TRUE_DOMAIN
    result = []
    expected = 1                            # expected number of expressions
    op_arity = {NOT_OPERATOR: 1, AND_OPERATOR: 2, OR_OPERATOR: 2}
    for token in domain:
        if expected == 0:                   # more than expected, like in [A, B]
            result[0:0] = [AND_OPERATOR]             # put an extra '&' in front
            expected = 1
        result.append(token)
        if isinstance(token, (list, tuple)):  # domain term
            expected -= 1
        else:
            expected += op_arity.get(token, 0) - 1
    assert expected == 0
    return result


def combine(operator, unit, zero, domains):
    """Returns a new domain expression where all domain components from ``domains``
       have been added together using the binary operator ``operator``. The given
       domains must be normalized.

       :param unit: the identity element of the domains "set" with regard to the operation
                    performed by ``operator``, i.e the domain component ``i`` which, when
                    combined with any domain ``x`` via ``operator``, yields ``x``.
                    E.g. [(1,'=',1)] is the typical unit for AND_OPERATOR: adding it
                    to any domain component gives the same domain.
       :param zero: the absorbing element of the domains "set" with regard to the operation
                    performed by ``operator``, i.e the domain component ``z`` which, when
                    combined with any domain ``x`` via ``operator``, yields ``z``.
                    E.g. [(1,'=',1)] is the typical zero for OR_OPERATOR: as soon as
                    you see it in a domain component the resulting domain is the zero.
       :param domains: a list of normalized domains.
    """
    result = []
    count = 0
    for domain in domains:
        if domain == unit:
            continue
        if domain == zero:
            return zero
        if domain:
            result += domain
            count += 1
    result = [operator] * (count - 1) + result
    return result


def AND(domains):
    """AND([D1,D2,...]) returns a domain representing D1 and D2 and ... """
    return combine(AND_OPERATOR, TRUE_DOMAIN, FALSE_DOMAIN, domains)


def OR(domains):
    """OR([D1,D2,...]) returns a domain representing D1 or D2 or ... """
    return combine(OR_OPERATOR, FALSE_DOMAIN, TRUE_DOMAIN, domains)


def distribute_not(domain):
    """ Distribute any '!' domain operators found inside a normalized domain.

    Because we don't use SQL semantic for processing a 'left not in right'
    query (i.e. our 'not in' is not simply translated to a SQL 'not in'),
    it means that a '! left in right' can not be simply processed
    by __leaf_to_sql by first emitting code for 'left in right' then wrapping
    the result with 'not (...)', as it would result in a 'not in' at the SQL
    level.

    This function is thus responsible for pushing any '!' domain operators
    inside the terms themselves. For example::

         ['!','&',('user_id','=',4),('partner_id','in',[1,2])]
            will be turned into:
         ['|',('user_id','!=',4),('partner_id','not in',[1,2])]

    """
    def negate(leaf):
        """Negates and returns a single domain leaf term,
        using the opposite operator if possible"""
        left, operator, right = leaf
        mapping = {
            '<': '>=',
            '>': '<=',
            '<=': '>',
            '>=': '<',
            '=': '!=',
            '!=': '=',
        }
        if operator in ('in', 'like', 'ilike'):
            operator = 'not ' + operator
            return [(left, operator, right)]
        if operator in ('not in', 'not like', 'not ilike'):
            operator = operator[4:]
            return [(left, operator, right)]
        if operator in mapping:
            operator = mapping[operator]
            return [(left, operator, right)]
        return [NOT_OPERATOR, (left, operator, right)]

    def distribute_negate(domain):
        """Negate the domain ``subtree`` rooted at domain[0],
        leaving the rest of the domain intact, and return
        (negated_subtree, untouched_domain_rest)
        """
        if is_leaf(domain[0]):
            return negate(domain[0]), domain[1:]
        if domain[0] == AND_OPERATOR:
            done1, todo1 = distribute_negate(domain[1:])
            done2, todo2 = distribute_negate(todo1)
            return [OR_OPERATOR] + done1 + done2, todo2
        if domain[0] == OR_OPERATOR:
            done1, todo1 = distribute_negate(domain[1:])
            done2, todo2 = distribute_negate(todo1)
            return [AND_OPERATOR] + done1 + done2, todo2
    if not domain:
        return []
    if domain[0] != NOT_OPERATOR:
        return [domain[0]] + distribute_not(domain[1:])
    if domain[0] == NOT_OPERATOR:
        done, todo = distribute_negate(domain[1:])
        return done + distribute_not(todo)


# --------------------------------------------------
# Generic leaf manipulation
# --------------------------------------------------

def _quote(to_quote):
    if '"' not in to_quote:
        return '"%s"' % to_quote
    return to_quote


def generate_table_alias(src_table_alias, joined_tables=[]):
    """ Generate a standard table alias name. An alias is generated as following:
        - the base is the source table name (that can already be an alias)
        - then, each joined table is added in the alias using a 'link field name'
          that is used to render unique aliases for a given path
        - returns a tuple composed of the alias, and the full table alias to be
          added in a from condition
        Examples:
        - src_table_alias='res_users', join_tables=[]:
            alias = ('res_users','"res_users"')
        - src_model='res_users', join_tables=[(res.partner, 'parent_id')]
            alias = ('res_users__parent_id', '"res_partner" as "res_users__parent_id"')

        :param model src_model: model source of the alias
        :param list join_tables: list of tuples
            (dst_model, link_field)

        :return tuple: (table alias, alias statement for from clause with quotes added)
    """
    alias = src_table_alias
    if not joined_tables:
        return ('%s' % alias, '%s' % _quote(alias))
    for link in joined_tables:
        alias += '__' + link[1]
    return ('%s' % alias, '%s as %s' % (_quote(joined_tables[-1][0]), _quote(alias)))


def normalize_leaf(element):
    """ Change a term's operator to some canonical form, simplifying later
        processing. """
    if not is_leaf(element):
        return element
    left, operator, right = element
    original = operator
    operator = operator.lower()
    if operator == '<>':
        operator = '!='
    if isinstance(right, bool) and operator in ('in', 'not in'):
        _logger.warning("The domain term '%s' should use the '=' or '!=' operator." % ((left, original, right),))
        operator = '=' if operator == 'in' else '!='
    if isinstance(right, (list, tuple)) and operator in ('=', '!='):
        _logger.warning("The domain term '%s' should use the 'in' or 'not in' operator." % ((left, original, right),))
        operator = 'in' if operator == '=' else 'not in'
    return (left, operator, right)


def is_operator(element):
    """Test whether an object is a valid domain operator. """
    return isinstance(element, basestring) and element in DOMAIN_OPERATORS


# TODO change the share wizard to use this function.
def is_leaf(element, internal=False):
    """ Test whether an object is a valid domain term:
        - is a list or tuple
        - with 3 elements
        - second element if a valid op

        :param tuple element: a leaf in form (left, operator, right)
        :param boolean internal: allow or not the 'inselect' internal operator
            in the term. This should be always left to False.
    """
    INTERNAL_OPS = TERM_OPERATORS + ('<>',)
    if internal:
        INTERNAL_OPS += ('inselect',)
    return (isinstance(element, tuple) or isinstance(element, list)) \
        and len(element) == 3 \
        and element[1] in INTERNAL_OPS


# --------------------------------------------------
# SQL utils
# --------------------------------------------------

def select_from_where(cr, select_field, from_table, where_field, where_ids, where_operator):
    # todo: merge into parent query as sub-query
    res = []
    if where_ids:
        if where_operator in ['<', '>', '>=', '<=']:
            cr.execute('SELECT "%s" FROM "%s" WHERE "%s" %s %%s' % \
                (select_field, from_table, where_field, where_operator),
                (where_ids[0],))  # TODO shouldn't this be min/max(where_ids) ?
            res = [r[0] for r in cr.fetchall()]
        else:  # TODO where_operator is supposed to be 'in'? It is called with child_of...
            for i in range(0, len(where_ids), cr.IN_MAX):
                subids = where_ids[i:i + cr.IN_MAX]
                cr.execute('SELECT "%s" FROM "%s" WHERE "%s" IN %%s' % \
                    (select_field, from_table, where_field), (tuple(subids),))
                res.extend([r[0] for r in cr.fetchall()])
    return res


def select_distinct_from_where_not_null(cr, select_field, from_table):
    cr.execute('SELECT distinct("%s") FROM "%s" where "%s" is not null' % (select_field, from_table, select_field))
    return [r[0] for r in cr.fetchall()]


# --------------------------------------------------
# ExtendedLeaf class for managing leafs and contexts
# -------------------------------------------------

class ExtendedLeaf(object):

    def __init__(self, leaf, table, context_stack=None):
        """ Initialize the ExtendedLeaf

            :attr [string, tuple] leaf: operator or tuple-formatted domain
                expression
            :attr object table: table object
            :attr list _tables: list of chained table objects, updated when
                adding joins
            :attr tuple elements: manipulation-friendly leaf
            :attr object field: field obj, taken from table, not necessarily
                found (inherits, 'id')
            :attr list field_path: exploded left of elements
                (partner_id.name -> ['partner_id', 'name'])
            :attr object relational_table: distant table for relational fields
        """
        assert table, 'Invalid leaf creation without table'
        self.context_stack = context_stack or []
        # validate the leaf
        self.leaf = leaf
        # normalize the leaf's operator
        self.normalize_leaf()
        # set working variables; handle the context stack and previous tables
        self.table = table
        self._tables = []
        for item in self.context_stack:
            self._tables.append(item[0])
        self._tables.append(table)
        # check validity
        self.check_leaf()

    def __str__(self):
        return '<osv.ExtendedLeaf: %s on %s (ctx: %s)>' % (str(self.leaf), self.table._table, ','.join(self._get_context_debug()))

    # --------------------------------------------------
    # Join / Context manipulation
    #   running examples:
    #   - res_users.name, like, foo: name is on res_partner, not on res_users
    #   - res_partner.bank_ids.name, like, foo: bank_ids is a one2many with _auto_join
    #   - res_partner.state_id.name, like, foo: state_id is a many2one with _auto_join
    # A join:
    #   - link between src_table and dst_table, using src_field and dst_field
    #       i.e.: inherits: res_users.partner_id = res_partner.id
    #       i.e.: one2many: res_partner.id = res_partner_bank.partner_id
    #       i.e.: many2one: res_partner.state_id = res_country_state.id
    #   - done in the context of a field
    #       i.e.: inherits: 'partner_id'
    #       i.e.: one2many: 'bank_ids'
    #       i.e.: many2one: 'state_id'
    #   - table names use aliases: initial table followed by the context field
    #     names, joined using a '__'
    #       i.e.: inherits: res_partner as res_users__partner_id
    #       i.e.: one2many: res_partner_bank as res_partner__bank_ids
    #       i.e.: many2one: res_country_state as res_partner__state_id
    #   - join condition use aliases
    #       i.e.: inherits: res_users.partner_id = res_users__partner_id.id
    #       i.e.: one2many: res_partner.id = res_partner__bank_ids.parr_id
    #       i.e.: many2one: res_partner.state_id = res_partner__state_id.id
    # Variables explanation:
    #   - src_table: working table before the join
    #       -> res_users, res_partner, res_partner
    #   - dst_table: working table after the join
    #       -> res_partner, res_partner_bank, res_country_state
    #   - src_table_link_name: field name used to link the src table, not
    #     necessarily a field (because 'id' is not a field instance)
    #       i.e.: inherits: 'partner_id', found in the inherits of the current table
    #       i.e.: one2many: 'id', not a field
    #       i.e.: many2one: 'state_id', the current field name
    #   - dst_table_link_name: field name used to link the dst table, not
    #     necessarily a field (because 'id' is not a field instance)
    #       i.e.: inherits: 'id', not a field
    #       i.e.: one2many: 'partner_id', _fields_id of the current field
    #       i.e.: many2one: 'id', not a field
    #   - context_field_name: field name used as a context to make the alias
    #       i.e.: inherits: 'partner_id': found in the inherits of the current table
    #       i.e.: one2many: 'bank_ids': current field name
    #       i.e.: many2one: 'state_id': current field name
    # --------------------------------------------------

    def generate_alias(self):
        links = [(context[1]._table, context[4]) for context in self.context_stack]
        alias, alias_statement = generate_table_alias(self._tables[0]._table, links)
        return alias

    def add_join_context(self, table, lhs_col, table_col, link):
        """ See above comments for more details. A join context is a tuple like:
                ``(lhs, table, lhs_col, col, link)``
            where
            - lhs is the source table (self.table)
            - table is the destination table
            - lsh_col is the source table column name used for the condition
            - table_col is the destination table column name used for the condition
            - link is the field name source of the join used as context to
                generate the destination table alias

            After adding the join, the table of the current leaf is updated.
        """
        self.context_stack.append((self.table, table, lhs_col, table_col, link))
        self._tables.append(table)
        self.table = table

    def get_join_conditions(self):
        conditions = []
        alias = self._tables[0]._table
        for context in self.context_stack:
            previous_alias = alias
            alias += '__' + context[4]
            conditions.append('"%s"."%s"="%s"."%s"' % (previous_alias, context[2], alias, context[3]))
        return conditions

    def get_tables(self):
        tables = set()
        alias = self._tables[0]._table
        for context in self.context_stack:
            alias += '__' + context[4]
            table_full_alias = '"%s" as "%s"' % (context[1]._table, alias)
            tables.add(table_full_alias)
        return tables

    def _get_context_debug(self):
        names = ['"%s"."%s"="%s"."%s" (%s)' % (item[0]._table, item[2], item[1]._table, item[3], item[4]) for item in self.context_stack]
        return names

    # --------------------------------------------------
    # Leaf manipulation
    # --------------------------------------------------

    def check_leaf(self):
        """ Leaf validity rules:
            - a valid leaf is an operator or a leaf
            - a valid leaf has a field objects unless
                - it is not a tuple
                - it is an inherited field
                - left is id, operator is 'child_of'
                - left is in MAGIC_COLUMNS
        """
        if not is_operator(self.leaf) and not is_leaf(self.leaf, True):
            raise ValueError("Invalid leaf %s" % str(self.leaf))

    def is_operator(self):
        return is_operator(self.leaf)

    def is_true_leaf(self):
        return self.leaf == TRUE_LEAF

    def is_false_leaf(self):
        return self.leaf == FALSE_LEAF

    def is_leaf(self, internal=False):
        return is_leaf(self.leaf, internal=internal)

    def normalize_leaf(self):
        self.leaf = normalize_leaf(self.leaf)
        return True


class expression(object):
    """ Parse a domain expression
        Use a real polish notation
        Leafs are still in a ('foo', '=', 'bar') format
        For more info: http://christophe-simonis-at-tiny.blogspot.com/2008/08/new-new-domain-notation.html
    """

    def __init__(self, cr, uid, exp, table, context):
        """ Initialize expression object and automatically parse the expression
            right after initialization.

            :param exp: expression (using domain ('foo', '=', 'bar' format))
            :param table: root table object

            :attr list result: list that will hold the result of the parsing
                as a list of ExtendedLeaf
            :attr list joins: list of join conditions, such as
                (res_country_state."id" = res_partner."state_id")
            :attr root_table: base table for the query
            :attr list expression: the domain expression, that will be normalized
                and prepared
        """
        self.has_unaccent = openerp.modules.registry.RegistryManager.get(cr.dbname).has_unaccent
        self.result = []
        self.joins = []
        self.root_table = table

        # normalize and prepare the expression for parsing
        self.expression = distribute_not(normalize_domain(exp))

        # parse the domain expression
        self.parse(cr, uid, context=context)

    # ----------------------------------------
    # Leafs management
    # ----------------------------------------

    def get_tables(self):
        """ Returns the list of tables for SQL queries, like select from ... """
        tables = []
        for leaf in self.result:
            for table in leaf.get_tables():
                if table not in tables:
                    tables.append(table)
        table_name = '"%s"' % self.root_table._table
        if table_name not in tables:
            tables.append(table_name)
        return tables

    # ----------------------------------------
    # Parsing
    # ----------------------------------------

    def parse(self, cr, uid, context):
        """ Transform the leaves of the expression

            The principle is to pop elements from the left of a leaf stack. Each
            leaf is processed. The processing is a if/elif list of various cases
            that appear in the leafs (many2one, function fields, ...). Two results
            can appear at the end of a leaf processing:
            - the leaf is modified or new leafs introduced in the domain: they
              are added at the left of the stack, to be processed next
            - the leaf is added to the result

            Some var explanation:
                :var obj working_table: table object, table containing the field
                    (the name provided in the left operand)
                :var list field_path: left operand seen as a path (foo.bar -> [foo, bar])
                :var obj relational_table: relational table of a field (field._obj)
                    ex: res_partner.bank_ids -> res_partner_bank
        """

        def to_ids(value, relational_table, context=None, limit=None):
            """ Normalize a single id or name, or a list of those, into a list of ids
                :param {int,long,basestring,list,tuple} value:
                    if int, long -> return [value]
                    if basestring, convert it into a list of basestrings, then
                    if list of basestring ->
                        perform a name_search on relational_table for each name
                        return the list of related ids
            """
            names = []
            if isinstance(value, basestring):
                names = [value]
            elif value and isinstance(value, (tuple, list)) and all(isinstance(item, basestring) for item in value):
                names = value
            elif isinstance(value, (int, long)):
                return [value]
            if names:
                name_get_list = [name_get[0] for name in names for name_get in relational_table.name_search(cr, uid, name, [], 'ilike', context=context, limit=limit)]
                return list(set(name_get_list))
            return list(value)

        def child_of_domain(left, ids, left_model, parent=None, prefix='', context=None):
            """ Return a domain implementing the child_of operator for [(left,child_of,ids)],
                either as a range using the parent_left/right tree lookup fields
                (when available), or as an expanded [(left,in,child_ids)] """
            if left_model._parent_store and (not left_model.pool._init):
                # TODO: Improve where joins are implemented for many with '.', replace by:
                # doms += ['&',(prefix+'.parent_left','<',o.parent_right),(prefix+'.parent_left','>=',o.parent_left)]
                doms = []
                for o in left_model.browse(cr, uid, ids, context=context):
                    if doms:
                        doms.insert(0, OR_OPERATOR)
                    doms += [AND_OPERATOR, ('parent_left', '<', o.parent_right), ('parent_left', '>=', o.parent_left)]
                if prefix:
                    return [(left, 'in', left_model.search(cr, uid, doms, context=context))]
                return doms
            else:
                def recursive_children(ids, model, parent_field):
                    if not ids:
                        return []
                    ids2 = model.search(cr, uid, [(parent_field, 'in', ids)], context=context)
                    return ids + recursive_children(ids2, model, parent_field)
                return [(left, 'in', recursive_children(ids, left_model, parent or left_model._parent_name))]

        def create_substitution_leaf(leaf, new_elements, new_table=None):
            if new_table is None:
                new_table = leaf.table
            new_context_stack = [tuple(context) for context in leaf.context_stack]
            new_leaf = ExtendedLeaf(new_elements, new_table, context_stack=new_context_stack)
            return new_leaf

        def pop():
            return self.stack.pop()

        def push(leaf):
            self.stack.append(leaf)

        def push_result(leaf):
            self.result.append(leaf)

        self.result = []
        self.stack = [ExtendedLeaf(leaf, self.root_table) for leaf in self.expression]
        # process from right to left; expression is from left to right
        self.stack.reverse()

        while self.stack:
            # Get the next leaf to process
            leaf = pop()

            # Get working variables
            working_table = leaf.table
            if leaf.is_operator():
                left, operator, right = leaf.leaf, None, None
            elif leaf.is_true_leaf() or leaf.is_false_leaf():
                # because we consider left as a string
                left, operator, right = ('%s' % leaf.leaf[0], leaf.leaf[1], leaf.leaf[2])
            else:
                left, operator, right = leaf.leaf
            field_path = left.split('.', 1)
            field = working_table._columns.get(field_path[0])
            if field and field._obj:
                relational_table = working_table.pool.get(field._obj)
            else:
                relational_table = None

            # ----------------------------------------
            # SIMPLE CASE
            # 1. leaf is an operator
            # 2. leaf is a true/false leaf
            # -> add directly to result
            # ----------------------------------------

            if leaf.is_operator() or leaf.is_true_leaf() or leaf.is_false_leaf():
                push_result(leaf)

            # ----------------------------------------
            # FIELD NOT FOUND
            # -> from inherits'd fields -> work on the related table, and add
            #    a join condition
            # -> ('id', 'child_of', '..') -> use a 'to_ids'
            # -> but is one on the _log_access special fields, add directly to
            #    result
            #    TODO: make these fields explicitly available in self.columns instead!
            # -> else: crash
            # ----------------------------------------

            elif not field and field_path[0] in working_table._inherit_fields:
                # comments about inherits'd fields
                #  { 'field_name': ('parent_model', 'm2o_field_to_reach_parent',
                #                    field_column_obj, origina_parent_model), ... }
                next_table = working_table.pool.get(working_table._inherit_fields[field_path[0]][0])
                leaf.add_join_context(next_table, working_table._inherits[next_table._name], 'id', working_table._inherits[next_table._name])
                push(leaf)

            elif not field and left == 'id' and operator == 'child_of':
                ids2 = to_ids(right, working_table, context)
                dom = child_of_domain(left, ids2, working_table)
                for dom_leaf in reversed(dom):
                    new_leaf = create_substitution_leaf(leaf, dom_leaf, working_table)
                    push(new_leaf)

            elif not field and field_path[0] in MAGIC_COLUMNS:
                push_result(leaf)

            elif not field:
                raise ValueError("Invalid field %r in leaf %r" % (left, str(leaf)))

            # ----------------------------------------
            # PATH SPOTTED
            # -> many2one or one2many with _auto_join:
            #    - add a join, then jump into linked field: field.remaining on
            #      src_table is replaced by remaining on dst_table, and set for re-evaluation
            #    - if a domain is defined on the field, add it into evaluation
            #      on the relational table
            # -> many2one, many2many, one2many: replace by an equivalent computed
            #    domain, given by recursively searching on the remaining of the path
            # -> note: hack about fields.property should not be necessary anymore
            #    as after transforming the field, it will go through this loop once again
            # ----------------------------------------

            elif len(field_path) > 1 and field._type == 'many2one' and field._auto_join:
                # res_partner.state_id = res_partner__state_id.id
                leaf.add_join_context(relational_table, field_path[0], 'id', field_path[0])
                push(create_substitution_leaf(leaf, (field_path[1], operator, right), relational_table))

            elif len(field_path) > 1 and field._type == 'one2many' and field._auto_join:
                # res_partner.id = res_partner__bank_ids.partner_id
                leaf.add_join_context(relational_table, 'id', field._fields_id, field_path[0])
                domain = field._domain(working_table) if callable(field._domain) else field._domain
                push(create_substitution_leaf(leaf, (field_path[1], operator, right), relational_table))
                if domain:
                    domain = normalize_domain(domain)
                    for elem in reversed(domain):
                        push(create_substitution_leaf(leaf, elem, relational_table))
                    push(create_substitution_leaf(leaf, AND_OPERATOR, relational_table))

            elif len(field_path) > 1 and field._auto_join:
                raise NotImplementedError('_auto_join attribute not supported on many2many field %s' % (left))

            elif len(field_path) > 1 and field._type == 'many2one':
                right_ids = relational_table.search(cr, uid, [(field_path[1], operator, right)], context=context)
                leaf.leaf = (field_path[0], 'in', right_ids)
                push(leaf)

            # Making search easier when there is a left operand as field.o2m or field.m2m
            elif len(field_path) > 1 and field._type in ['many2many', 'one2many']:
                right_ids = relational_table.search(cr, uid, [(field_path[1], operator, right)], context=context)
                table_ids = working_table.search(cr, uid, [(field_path[0], 'in', right_ids)], context=dict(context, active_test=False))
                leaf.leaf = ('id', 'in', table_ids)
                push(leaf)

            # -------------------------------------------------
            # FUNCTION FIELD
            # -> not stored: error if no _fnct_search, otherwise handle the result domain
            # -> stored: management done in the remaining of parsing
            # -------------------------------------------------

            elif isinstance(field, fields.function) and not field.store and not field._fnct_search:
                # this is a function field that is not stored
                # the function field doesn't provide a search function and doesn't store
                # values in the database, so we must ignore it : we generate a dummy leaf
                leaf.leaf = TRUE_LEAF
                _logger.error(
                    "The field '%s' (%s) can not be searched: non-stored "
                    "function field without fnct_search",
                    field.string, left)
                # avoid compiling stack trace if not needed
                if _logger.isEnabledFor(logging.DEBUG):
                    _logger.debug(''.join(traceback.format_stack()))
                push(leaf)

            elif isinstance(field, fields.function) and not field.store:
                # this is a function field that is not stored
                fct_domain = field.search(cr, uid, working_table, left, [leaf.leaf], context=context)
                if not fct_domain:
                    leaf.leaf = TRUE_LEAF
                    push(leaf)
                else:
                    # we assume that the expression is valid
                    # we create a dummy leaf for forcing the parsing of the resulting expression
                    for domain_element in reversed(fct_domain):
                        push(create_substitution_leaf(leaf, domain_element, working_table))
                    # self.push(create_substitution_leaf(leaf, TRUE_LEAF, working_table))
                    # self.push(create_substitution_leaf(leaf, AND_OPERATOR, working_table))

            # Applying recursivity on field(one2many)
            elif field._type == 'one2many' and operator == 'child_of':
                ids2 = to_ids(right, relational_table, context)
                if field._obj != working_table._name:
                    dom = child_of_domain(left, ids2, relational_table, prefix=field._obj)
                else:
                    dom = child_of_domain('id', ids2, working_table, parent=left)
                for dom_leaf in reversed(dom):
                    push(create_substitution_leaf(leaf, dom_leaf, working_table))

            elif field._type == 'one2many':
                call_null = True

                if right is not False:
                    if isinstance(right, basestring):
                        ids2 = [x[0] for x in relational_table.name_search(cr, uid, right, [], operator, context=context, limit=None)]
                        if ids2:
                            operator = 'in'
                    else:
                        if not isinstance(right, list):
                            ids2 = [right]
                        else:
                            ids2 = right
                    if not ids2:
                        if operator in ['like', 'ilike', 'in', '=']:
                            #no result found with given search criteria
                            call_null = False
                            push(create_substitution_leaf(leaf, FALSE_LEAF, working_table))
                    else:
                        ids2 = select_from_where(cr, field._fields_id, relational_table._table, 'id', ids2, operator)
                        if ids2:
                            call_null = False
                            o2m_op = 'not in' if operator in NEGATIVE_TERM_OPERATORS else 'in'
                            push(create_substitution_leaf(leaf, ('id', o2m_op, ids2), working_table))

                if call_null:
                    o2m_op = 'in' if operator in NEGATIVE_TERM_OPERATORS else 'not in'
                    push(create_substitution_leaf(leaf, ('id', o2m_op, select_distinct_from_where_not_null(cr, field._fields_id, relational_table._table)), working_table))

            elif field._type == 'many2many':
                rel_table, rel_id1, rel_id2 = field._sql_names(working_table)
                #FIXME
                if operator == 'child_of':
                    def _rec_convert(ids):
                        if relational_table == working_table:
                            return ids
                        return select_from_where(cr, rel_id1, rel_table, rel_id2, ids, operator)

                    ids2 = to_ids(right, relational_table, context)
                    dom = child_of_domain('id', ids2, relational_table)
                    ids2 = relational_table.search(cr, uid, dom, context=context)
                    push(create_substitution_leaf(leaf, ('id', 'in', _rec_convert(ids2)), working_table))
                else:
                    call_null_m2m = True
                    if right is not False:
                        if isinstance(right, basestring):
                            res_ids = [x[0] for x in relational_table.name_search(cr, uid, right, [], operator, context=context)]
                            if res_ids:
                                operator = 'in'
                        else:
                            if not isinstance(right, list):
                                res_ids = [right]
                            else:
                                res_ids = right
                        if not res_ids:
                            if operator in ['like', 'ilike', 'in', '=']:
                                #no result found with given search criteria
                                call_null_m2m = False
                                push(create_substitution_leaf(leaf, FALSE_LEAF, working_table))
                            else:
                                operator = 'in'  # operator changed because ids are directly related to main object
                        else:
                            call_null_m2m = False
                            m2m_op = 'not in' if operator in NEGATIVE_TERM_OPERATORS else 'in'
                            push(create_substitution_leaf(leaf, ('id', m2m_op, select_from_where(cr, rel_id1, rel_table, rel_id2, res_ids, operator) or [0]), working_table))

                    if call_null_m2m:
                        m2m_op = 'in' if operator in NEGATIVE_TERM_OPERATORS else 'not in'
                        push(create_substitution_leaf(leaf, ('id', m2m_op, select_distinct_from_where_not_null(cr, rel_id1, rel_table)), working_table))

            elif field._type == 'many2one':
                if operator == 'child_of':
                    ids2 = to_ids(right, relational_table, context)
                    if field._obj != working_table._name:
                        dom = child_of_domain(left, ids2, relational_table, prefix=field._obj)
                    else:
                        dom = child_of_domain('id', ids2, working_table, parent=left)
                    for dom_leaf in reversed(dom):
                        push(create_substitution_leaf(leaf, dom_leaf, working_table))
                else:
                    def _get_expression(relational_table, cr, uid, left, right, operator, context=None):
                        if context is None:
                            context = {}
                        c = context.copy()
                        c['active_test'] = False
                        #Special treatment to ill-formed domains
                        operator = (operator in ['<', '>', '<=', '>=']) and 'in' or operator

                        dict_op = {'not in': '!=', 'in': '=', '=': 'in', '!=': 'not in'}
                        if isinstance(right, tuple):
                            right = list(right)
                        if (not isinstance(right, list)) and operator in ['not in', 'in']:
                            operator = dict_op[operator]
                        elif isinstance(right, list) and operator in ['!=', '=']:  # for domain (FIELD,'=',['value1','value2'])
                            operator = dict_op[operator]
                        res_ids = [x[0] for x in relational_table.name_search(cr, uid, right, [], operator, limit=None, context=c)]
                        if operator in NEGATIVE_TERM_OPERATORS:
                            res_ids.append(False)  # TODO this should not be appended if False was in 'right'
                        return (left, 'in', res_ids)
                    # resolve string-based m2o criterion into IDs
                    if isinstance(right, basestring) or \
                            right and isinstance(right, (tuple, list)) and all(isinstance(item, basestring) for item in right):
                        push(create_substitution_leaf(leaf, _get_expression(relational_table, cr, uid, left, right, operator, context=context), working_table))
                    else:
                        # right == [] or right == False and all other cases are handled by __leaf_to_sql()
                        push_result(leaf)

            else:
                # other field type
                # add the time part to datetime field when it's not there:
                if field._type == 'datetime' and right and len(right) == 10:

                    if operator in ('>', '>='):
                        right += ' 00:00:00'
                    elif operator in ('<', '<='):
                        right += ' 23:59:59'

                    push(create_substitution_leaf(leaf, (left, operator, right), working_table))

                elif field.translate:
                    need_wildcard = operator in ('like', 'ilike', 'not like', 'not ilike')
                    sql_operator = {'=like': 'like', '=ilike': 'ilike'}.get(operator, operator)
                    if need_wildcard:
                        right = '%%%s%%' % right

                    subselect = '( SELECT res_id'          \
                             '    FROM ir_translation'  \
                             '   WHERE name = %s'       \
                             '     AND lang = %s'       \
                             '     AND type = %s'
                    instr = ' %s'
                    #Covering in,not in operators with operands (%s,%s) ,etc.
                    if sql_operator in ['in', 'not in']:
                        instr = ','.join(['%s'] * len(right))
                        subselect += '     AND value ' + sql_operator + ' ' + " (" + instr + ")"   \
                             ') UNION ('                \
                             '  SELECT id'              \
                             '    FROM "' + working_table._table + '"'       \
                             '   WHERE "' + left + '" ' + sql_operator + ' ' + " (" + instr + "))"
                    else:
                        subselect += '     AND value ' + sql_operator + instr +   \
                             ') UNION ('                \
                             '  SELECT id'              \
                             '    FROM "' + working_table._table + '"'       \
                             '   WHERE "' + left + '" ' + sql_operator + instr + ")"

                    params = [working_table._name + ',' + left,
                              context.get('lang', False) or 'en_US',
                              'model',
                              right,
                              right,
                             ]
                    push(create_substitution_leaf(leaf, ('id', 'inselect', (subselect, params)), working_table))

                else:
                    push_result(leaf)

        # ----------------------------------------
        # END OF PARSING FULL DOMAIN
        # ----------------------------------------

        # Generate joins
        joins = set()
        for leaf in self.result:
            joins |= set(leaf.get_join_conditions())
        self.joins = list(joins)

    def __leaf_to_sql(self, eleaf):
        table = eleaf.table
        leaf = eleaf.leaf
        left, operator, right = leaf

        # final sanity checks - should never fail
        assert operator in (TERM_OPERATORS + ('inselect',)), \
            "Invalid operator %r in domain term %r" % (operator, leaf)
        assert leaf in (TRUE_LEAF, FALSE_LEAF) or left in table._all_columns \
            or left in MAGIC_COLUMNS, "Invalid field %r in domain term %r" % (left, leaf)

        table_alias = '"%s"' % (eleaf.generate_alias())

        if leaf == TRUE_LEAF:
            query = 'TRUE'
            params = []

        elif leaf == FALSE_LEAF:
            query = 'FALSE'
            params = []

        elif operator == 'inselect':
            query = '(%s."%s" in (%s))' % (table_alias, left, right[0])
            params = right[1]

        elif operator in ['in', 'not in']:
            # Two cases: right is a boolean or a list. The boolean case is an
            # abuse and handled for backward compatibility.
            if isinstance(right, bool):
                _logger.warning("The domain term '%s' should use the '=' or '!=' operator." % (leaf,))
                if operator == 'in':
                    r = 'NOT NULL' if right else 'NULL'
                else:
                    r = 'NULL' if right else 'NOT NULL'
                query = '(%s."%s" IS %s)' % (table_alias, left, r)
                params = []
            elif isinstance(right, (list, tuple)):
                params = right[:]
                check_nulls = False
                for i in range(len(params))[::-1]:
                    if params[i] == False:
                        check_nulls = True
                        del params[i]

                if params:
                    if left == 'id':
                        instr = ','.join(['%s'] * len(params))
                    else:
                        instr = ','.join([table._columns[left]._symbol_set[0]] * len(params))
                    query = '(%s."%s" %s (%s))' % (table_alias, left, operator, instr)
                else:
                    # The case for (left, 'in', []) or (left, 'not in', []).
                    query = 'FALSE' if operator == 'in' else 'TRUE'

                if check_nulls and operator == 'in':
                    query = '(%s OR %s."%s" IS NULL)' % (query, table_alias, left)
                elif not check_nulls and operator == 'not in':
                    query = '(%s OR %s."%s" IS NULL)' % (query, table_alias, left)
                elif check_nulls and operator == 'not in':
                    query = '(%s AND %s."%s" IS NOT NULL)' % (query, table_alias, left)  # needed only for TRUE.
            else:  # Must not happen
                raise ValueError("Invalid domain term %r" % (leaf,))

        elif right == False and (left in table._columns) and table._columns[left]._type == "boolean" and (operator == '='):
            query = '(%s."%s" IS NULL or %s."%s" = false )' % (table_alias, left, table_alias, left)
            params = []

        elif (right is False or right is None) and (operator == '='):
            query = '%s."%s" IS NULL ' % (table_alias, left)
            params = []

        elif right == False and (left in table._columns) and table._columns[left]._type == "boolean" and (operator == '!='):
            query = '(%s."%s" IS NOT NULL and %s."%s" != false)' % (table_alias, left, table_alias, left)
            params = []

        elif (right is False or right is None) and (operator == '!='):
            query = '%s."%s" IS NOT NULL' % (table_alias, left)
            params = []

        elif (operator == '=?'):
            if (right is False or right is None):
                # '=?' is a short-circuit that makes the term TRUE if right is None or False
                query = 'TRUE'
                params = []
            else:
                # '=?' behaves like '=' in other cases
                query, params = self.__leaf_to_sql((left, '=', right), table)

        elif left == 'id':
            query = '%s.id %s %%s' % (table_alias, operator)
            params = right

        else:
            need_wildcard = operator in ('like', 'ilike', 'not like', 'not ilike')
            sql_operator = {'=like': 'like', '=ilike': 'ilike'}.get(operator, operator)

            if left in table._columns:
                format = need_wildcard and '%s' or table._columns[left]._symbol_set[0]
                if self.has_unaccent and sql_operator in ('ilike', 'not ilike'):
                    query = '(unaccent(%s."%s") %s unaccent(%s))' % (table_alias, left, sql_operator, format)
                else:
                    query = '(%s."%s" %s %s)' % (table_alias, left, sql_operator, format)
            elif left in MAGIC_COLUMNS:
                    query = "(%s.\"%s\" %s %%s)" % (table_alias, left, sql_operator)
                    params = right
            else:  # Must not happen
                raise ValueError("Invalid field %r in domain term %r" % (left, leaf))

            add_null = False
            if need_wildcard:
                if isinstance(right, str):
                    str_utf8 = right
                elif isinstance(right, unicode):
                    str_utf8 = right.encode('utf-8')
                else:
                    str_utf8 = str(right)
                params = '%%%s%%' % str_utf8
                add_null = not str_utf8
            elif left in table._columns:
                params = table._columns[left]._symbol_set[1](right)

            if add_null:
                query = '(%s OR %s."%s" IS NULL)' % (query, table_alias, left)

        if isinstance(params, basestring):
            params = [params]
        return (query, params)

    def to_sql(self):
        stack = []
        params = []
        # Process the domain from right to left, using a stack, to generate a SQL expression.
        self.result.reverse()
        for leaf in self.result:
            if leaf.is_leaf(internal=True):
                q, p = self.__leaf_to_sql(leaf)
                params.insert(0, p)
                stack.append(q)
            elif leaf.leaf == NOT_OPERATOR:
                stack.append('(NOT (%s))' % (stack.pop(),))
            else:
                ops = {AND_OPERATOR: ' AND ', OR_OPERATOR: ' OR '}
                q1 = stack.pop()
                q2 = stack.pop()
                stack.append('(%s %s %s)' % (q1, ops[leaf.leaf], q2,))

        assert len(stack) == 1
        query = stack[0]
        joins = ' AND '.join(self.joins)
        if joins:
            query = '(%s) AND %s' % (joins, query)

        return (query, tools.flatten(params))

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
