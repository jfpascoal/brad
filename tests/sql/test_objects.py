import re
import unittest
from decimal import Decimal

from bread.sql.objects import Row, SqlType, Integer, BigInt, Numeric, Boolean, Date, Text, Column, PrimaryKey, \
    ForeignKey, Unique, Check, Table, FkActions, GeneratedIdentityOptions


class TestRowObject(unittest.TestCase):
    """
    Tests the Row data container for correct initialization and access.
    """

    def test_row_initialization_and_access(self):
        """
        Row can be initialized and accessed like an object and dict.
        """
        row = Row(id=1, name="Test")
        self.assertEqual(1, row.id)
        self.assertEqual("Test", row['name'])
        self.assertIsNone(row['non_existent'])
        self.assertEqual({'id', 'name'}, set(row.columns()))
        self.assertEqual({'id': 1, 'name': 'Test'}, row.get_dict())

    def test_row_from_dict(self):
        """
        Row can be initialized from a dictionary.
        """
        data = {'foo': 42, 'bar': 'baz'}
        row = Row(data)
        self.assertEqual(42, row.foo)
        self.assertEqual('baz', row['bar'])
        self.assertEqual(data, row.get_dict())


class TestColumnObject(unittest.TestCase):
    """
    Tests the Column schema definition object and SQL output.
    """

    def test_integer_column_to_sql(self):
        """
        Integer column SQL generation.
        """
        col = Column('id', Integer(), not_null=True)
        self.assertEqual('"id" INTEGER NOT NULL', col.to_sql())

    def test_numeric_column_to_sql(self):
        """
        Numeric column SQL generation with default precision/scale.
        """
        col = Column('price', Numeric(), not_null=True)
        self.assertEqual('"price" NUMERIC(19, 4) NOT NULL', col.to_sql())

    def test_text_column_with_default(self):
        """
        Text column with default value SQL generation.
        """
        col = Column('name', Text(), not_null=True, default='N/A')
        self.assertEqual('"name" TEXT NOT NULL DEFAULT \'N/A\'', col.to_sql())
        
    def test_column_with_invalid_default(self):
        """
        Column with invalid default value raises TypeError.
        """
        with self.assertRaises(TypeError):
            Column('is_active', Boolean(), default=123)

    def test_generated_identity_column(self):
        """
        Generated identity column SQL generation.
        """
        col = Column('id', Integer(), generated_identity=GeneratedIdentityOptions.ALWAYS)
        self.assertEqual('"id" INTEGER GENERATED ALWAYS AS IDENTITY', col.to_sql())

    def test_generated_identity_requires_integer_or_bigint(self):
        """
        Only Integer or BigInt types can be generated identity columns.
        """
        with self.assertRaises(TypeError):
            Column('bad', Text(), generated_identity=GeneratedIdentityOptions.BY_DEFAULT)



class TestConstraintObjects(unittest.TestCase):
    """
    Tests constraint objects for correct SQL output.
    """

    def test_primary_key_to_sql(self):
        """
        PrimaryKey constraint SQL generation.
        """
        pk = PrimaryKey(columns=['date', 'account_id'])
        self.assertEqual('PRIMARY KEY ("date", "account_id")', pk.to_sql())

    def test_foreign_key_to_sql(self):
        """
        ForeignKey constraint SQL generation with delete/update actions.
        """
        fk = ForeignKey(
            columns=['account_id'],
            ref_table='account',
            ref_columns=['id'],
            on_delete=FkActions.CASCADE,
            on_update=FkActions.NO_ACTION
        )
        expected_sql = ('FOREIGN KEY ("account_id") REFERENCES "account" ("id")'
                        ' ON DELETE CASCADE ON UPDATE NO ACTION')
        self.assertEqual(expected_sql, fk.to_sql())

    def test_unique_to_sql(self):
        """
        Unique constraint SQL generation.
        """
        uq = Unique(columns=['name', 'provider_id'])
        self.assertEqual('UNIQUE ("name", "provider_id")', uq.to_sql())

    def test_check_constraint_to_sql(self):
        """
        Check constraint SQL generation.
        """
        check = Check('age > 0')
        self.assertEqual('CHECK (age > 0)', check.to_sql())


class TestTableObject(unittest.TestCase):
    """
    Tests the Table schema definition object and SQL output.
    """

    def setUp(self):
        """
        Set up a sample table for testing.
        """
        self.table = Table('test_table').set_columns(
            Column('id', BigInt(), generated_identity=GeneratedIdentityOptions.BY_DEFAULT),
            Column('name', Text(), not_null=True),
            Column('is_active', Boolean(), default=True)
        ).set_constraint(
            PrimaryKey(['id'])
        ).set_constraint(
            Unique(['name'])
        )

    def test_get_create_statement(self):
        """
        The generated CREATE TABLE statement should contain all columns and constraints.
        """
        sql = self.table.get_create_statement()
        trimmed_sql = re.sub(r'\s+', ' ', sql).strip()
        expected_sql = ('CREATE TABLE IF NOT EXISTS "test_table" '
                        '("id" BIGINT GENERATED BY DEFAULT AS IDENTITY, '
                        '"name" TEXT NOT NULL, '
                        '"is_active" BOOLEAN DEFAULT TRUE, '
                        'PRIMARY KEY ("id"), '
                        'UNIQUE ("name"));')
        self.assertEqual(expected_sql, trimmed_sql)
        

    def test_get_insert_statement_with_data(self):
        """
        The generated INSERT statement should match the table columns and use %s placeholders.
        """
        self.table.insert_data(
            Row(id=1, name="First"),
            Row(id=2, name="Second", is_active=True)
        )
        statement = self.table.get_insert_statement()
        self.assertIsNotNone(statement)
        sql, data = statement
        self.assertEqual('INSERT INTO "test_table" ("id", "name", "is_active") VALUES (%s, %s, %s)', sql)
        self.assertEqual(2, len(data))
        self.assertEqual((1, "First", None), data[0])
        self.assertEqual((2, "Second", True), data[1])

    def test_get_insert_statement_no_data(self):
        """
        If no data is present, get_insert_statement should return None.
        """
        self.table.data = []
        self.assertIsNone(self.table.get_insert_statement())