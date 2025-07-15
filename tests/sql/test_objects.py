import unittest
from decimal import Decimal

from bread.sql.objects import Row, Column, PrimaryKey, ForeignKey, Unique, Table


class TestRowObject(unittest.TestCase):
    """Tests the Row data container."""

    def test_row_initialization_and_access(self):
        """Tests that Row can be initialized and accessed like an object and dict."""
        row = Row(id=1, name="Test")
        self.assertEqual(row.id, 1)
        self.assertEqual(row['name'], "Test")
        self.assertIsNone(row['non_existent'])
        self.assertEqual(set(row.columns()), {'id', 'name'})
        self.assertEqual(row.get_dict(), {'id': 1, 'name': 'Test'})


class TestColumnObject(unittest.TestCase):
    """Tests the Column schema definition object."""

    def test_simple_column_to_sql(self):
        """Tests basic SQL generation for a column."""
        src_typ = str
        tgt_typ = Column._PY_TO_SQL_TYPE[src_typ]
        col = Column('name', src_typ, not_null=True, default="'N/A'")
        self.assertEqual(col.to_sql(), f'"name" {tgt_typ} NOT NULL DEFAULT \'N/A\'')


    def test_decimal_column_to_sql(self):
        """Tests SQL generation for a Decimal column."""
        src_typ = Decimal
        tgt_typ = Column._PY_TO_SQL_TYPE[src_typ]
        col = Column('price', src_typ, not_null=True)
        self.assertEqual(col.to_sql(), f'"price" {tgt_typ} NOT NULL')


    def test_primary_key_column_to_sql(self):
        """Tests SQL generation for a primary key column."""
        src_typ = int
        tgt_typ = Column._PY_TO_SQL_TYPE[src_typ]
        col = Column('id', src_typ, row_id=True)
        self.assertEqual(col.to_sql(), f'"id" {tgt_typ} PRIMARY KEY')

    def test_autoincrement_column_to_sql(self):
        """Tests SQL generation for an autoincrementing primary key."""
        src_typ = int
        tgt_typ = Column._PY_TO_SQL_TYPE[src_typ]
        col = Column('id', src_typ, row_id=True, autoincrement=True)
        self.assertEqual(col.to_sql(), f'"id" {tgt_typ} PRIMARY KEY AUTOINCREMENT')

    def test_autoincrement_requires_int(self):
        """Tests that autoincrement raises a TypeError for non-integer columns."""
        with self.assertRaises(TypeError):
            Column('id', str, autoincrement=True)



class TestConstraintObjects(unittest.TestCase):
    """Tests the various constraint schema definition objects."""

    def test_primary_key_to_sql(self):
        """Tests PrimaryKey constraint SQL generation."""
        pk = PrimaryKey(columns=['date', 'account_id'])
        self.assertEqual(pk.to_sql(), 'PRIMARY KEY ("date", "account_id")')

    def test_foreign_key_to_sql(self):
        """Tests ForeignKey constraint SQL generation with delete/update actions."""
        fk = ForeignKey(
            columns=['account_id'],
            ref_table='account',
            ref_columns=['id'],
            on_delete=ForeignKey.CASCADE
        )
        expected_sql = ('FOREIGN KEY ("account_id") REFERENCES "account" ("id")'
                        ' ON DELETE CASCADE ON UPDATE NO ACTION')
        self.assertEqual(fk.to_sql(), expected_sql)

    def test_unique_to_sql(self):
        """Tests Unique constraint SQL generation."""
        uq = Unique(columns=['name', 'provider_id'])
        self.assertEqual(uq.to_sql(), 'UNIQUE ("name", "provider_id")')


class TestTableObject(unittest.TestCase):
    """Tests the Table schema definition object."""

    def setUp(self):
        """Set up a sample table for testing."""
        self.table = Table('test_table').set_columns(
            Column('id', int, row_id=True, autoincrement=True),
            Column('name', str, not_null=True),
            Column('value', Decimal)
        ).set_constraint(
            Unique(['name'])
        )

    def test_get_create_statement(self):
        """Tests that the generated CREATE TABLE statement is correct."""
        sql = self.table.get_create_statement()
        self.assertIn('CREATE TABLE IF NOT EXISTS "test_table"', sql)
        self.assertIn('"id" INTEGER PRIMARY KEY AUTOINCREMENT', sql)
        self.assertIn('"name" TEXT NOT NULL', sql)
        self.assertIn('"value" DECIMAL', sql)
        self.assertIn('UNIQUE ("name")', sql)

    def test_get_insert_statement_with_data(self):
        """Tests that the generated INSERT statement is correct when data is present."""
        self.table.insert_data(
            Row(id=1, name="First"),
            Row(id=2, name="Second", value=Decimal('10.5'))
        )
        statement = self.table.get_insert_statement()
        self.assertIsNotNone(statement)
        sql, data = statement
        self.assertEqual(sql, "INSERT INTO \"test_table\" (\"id\", \"name\", \"value\") VALUES (?, ?, ?)")
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0], (1, "First", None))
        self.assertEqual(data[1], (2, "Second", Decimal('10.5')))

    def test_get_insert_statement_no_data(self):
        """Tests that no INSERT statement is generated when there is no data."""
        self.assertIsNone(self.table.get_insert_statement())