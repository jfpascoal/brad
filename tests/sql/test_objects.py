import unittest
from unittest.mock import patch, MagicMock

from brad.sql.objects import Row, Column, PrimaryKey, \
    ForeignKey, Unique, Check, Table, FkActions, GeneratedIdOptions
from brad.sql.types import Integer, BigInt, Numeric, Boolean, Text


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
        with self.assertRaises(AttributeError):
            row['non_existent']
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
        col = Column('id', Integer(), generated_identity=GeneratedIdOptions.ALWAYS)
        self.assertEqual('"id" INTEGER GENERATED ALWAYS AS IDENTITY', col.to_sql())

    def test_generated_identity_requires_integer_or_bigint(self):
        """
        Only Integer or BigInt types can be generated identity columns.
        """
        with self.assertRaises(TypeError):
            Column('bad', Text(), generated_identity=GeneratedIdOptions.BY_DEFAULT)


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
            Column('id', BigInt(), generated_identity=GeneratedIdOptions.BY_DEFAULT),
            Column('name', Text(), not_null=True),
            Column('is_active', Boolean(), default=True)
        ).set_constraint(
            PrimaryKey(['id'])
        ).set_constraint(
            Unique(['name'])
        )

    def test_table_initialization(self):
        """
        Test that Table initializes correctly with name, columns, constraints, and seed data.
        """
        self.assertEqual('test_table', self.table.name)
        self.assertEqual(3, len(self.table.columns))
        self.assertEqual(2, len(self.table.constraints))
        self.assertEqual([], self.table.seed)

    def test_set_columns_fluent_interface(self):
        """
        Test that set_columns supports method chaining.
        """
        table = Table('test').set_columns(Column('id', BigInt()))
        self.assertIsInstance(table, Table)
        self.assertEqual(1, len(table.columns))
        self.assertEqual('id', table.columns[0].name)

    def test_set_constraint_fluent_interface(self):
        """
        Test that set_constraint supports method chaining.
        """
        table = Table('test').set_constraint(PrimaryKey(['id']))
        self.assertIsInstance(table, Table)
        self.assertEqual(1, len(table.constraints))

    def test_set_seed_fluent_interface(self):
        """
        Test that set_seed supports method chaining.
        """
        seed_data = [Row(id=1, name="Test")]
        table = Table('test').set_seed(*seed_data)
        self.assertIsInstance(table, Table)
        self.assertEqual(seed_data, table.seed)

    def test_get_writable_columns(self):
        """
        Test that get_writable_columns excludes GENERATED ALWAYS columns.
        """
        table = Table('test').set_columns(
            Column('id', BigInt(), generated_identity=GeneratedIdOptions.ALWAYS),
            Column('auto_id', BigInt(), generated_identity=GeneratedIdOptions.BY_DEFAULT),
            Column('name', Text(), not_null=True),
            Column('optional', Text())
        )

        writable_columns = table.get_writable_columns()
        expected_columns = ['auto_id', 'name', 'optional']
        self.assertEqual(expected_columns, writable_columns)

    @patch('brad.sql.objects.logger')
    def test_create_table(self, mock_logger):
        """
        Test that create method generates correct SQL and executes it.
        """
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        result = self.table.create(mock_connection)

        # Should return self for chaining
        self.assertEqual(self.table, result)

        # Should execute CREATE TABLE statement
        mock_cursor.execute.assert_called_once()
        executed_sql = mock_cursor.execute.call_args[0][0]
        self.assertIn('CREATE TABLE IF NOT EXISTS "test_table"', executed_sql)
        self.assertIn('"id" BIGINT GENERATED BY DEFAULT AS IDENTITY', executed_sql)
        self.assertIn('"name" TEXT NOT NULL', executed_sql)
        self.assertIn('PRIMARY KEY ("id")', executed_sql)

    @patch('brad.sql.objects.logger')
    def test_drop_table(self, mock_logger):
        """
        Test that drop method generates correct SQL and executes it.
        """
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        result = self.table.drop(mock_connection)

        # Should return self for chaining
        self.assertEqual(self.table, result)

        # Should execute DROP TABLE statement
        mock_cursor.execute.assert_called_once_with('DROP TABLE IF EXISTS "test_table" CASCADE;')

    def test_validate_row_success(self):
        """
        Test that _validate_row returns True for valid rows.
        """
        valid_row = Row(name="Test Name", is_active=True)
        self.assertTrue(self.table._validate_row(valid_row))

    @patch('brad.sql.objects.logger')
    def test_validate_row_missing_required_column(self, mock_logger):
        """
        Test that _validate_row returns False when required columns are missing.
        """
        invalid_row = Row(is_active=True)  # Missing required 'name' column
        self.assertFalse(self.table._validate_row(invalid_row))
        mock_logger.warning.assert_called()

    @patch('brad.sql.objects.logger')
    def test_validate_row_wrong_type(self, mock_logger):
        """
        Test that _validate_row returns False when column types are wrong.
        """
        invalid_row = Row(name=123, is_active=True)  # name should be string
        self.assertFalse(self.table._validate_row(invalid_row))
        mock_logger.warning.assert_called()

    @patch('brad.sql.objects.logger')
    def test_validate_row_null_in_not_null_column(self, mock_logger):
        """
        Test that _validate_row returns False when NULL is provided for NOT NULL columns.
        """
        invalid_row = Row(name=None, is_active=True)  # name is NOT NULL
        self.assertFalse(self.table._validate_row(invalid_row))
        mock_logger.warning.assert_called()

    @patch('brad.sql.objects.logger')
    def test_insert_valid_rows(self, mock_logger):
        """
        Test that insert method works correctly with valid rows.
        """
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        rows = [Row(name="Test1", is_active=True), Row(name="Test2", is_active=False)]
        result = self.table.insert(mock_connection, rows)

        # Should return self for chaining
        self.assertEqual(self.table, result)

        # Should execute INSERT statement
        mock_cursor.executemany.assert_called_once()
        executed_sql = mock_cursor.executemany.call_args[0][0]
        self.assertIn('INSERT INTO "test_table"', executed_sql)

    @patch('brad.sql.objects.logger')
    def test_insert_empty_rows(self, mock_logger):
        """
        Test that insert method handles empty row list gracefully.
        """
        mock_connection = MagicMock()

        result = self.table.insert(mock_connection, [])

        # Should return self for chaining
        self.assertEqual(self.table, result)
        mock_logger.info.assert_called_with("No rows to insert into table 'test_table'.")

    @patch('brad.sql.objects.logger')
    def test_insert_handles_exception(self, mock_logger):
        """
        Test that insert method handles database exceptions properly.
        """
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.executemany.side_effect = Exception("Database error")

        rows = [Row(name="Test", is_active=True)]

        with self.assertRaises(Exception):
            self.table.insert(mock_connection, rows)

        mock_logger.error.assert_called_once()
