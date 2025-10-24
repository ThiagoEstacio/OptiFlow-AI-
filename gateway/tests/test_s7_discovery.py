"""
Tests for S7 Discovery Components

Tests include:
- DB Browser functionality
- Symbol Importer (CSV parsing)
- Address parsing
- Validation
"""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.discovery.s7_db_browser import (
    S7DBBrowser,
    DBInfo,
    DBStructure
)

from app.services.discovery.s7_symbol_importer import (
    S7SymbolImporter,
    S7Symbol
)


class TestS7DBBrowser:
    """Test cases for S7 DB Browser."""

    @pytest.fixture
    def mock_s7_client(self):
        """Create mock S7 client."""
        with patch('app.services.discovery.s7_db_browser.S7Client') as mock:
            client_instance = MagicMock()
            client_instance.connect = MagicMock(return_value=True)
            client_instance.is_connected = MagicMock(return_value=True)
            client_instance.disconnect = MagicMock()
            mock.return_value = client_instance
            yield client_instance

    def test_browser_initialization(self):
        """Test browser initializes correctly."""
        browser = S7DBBrowser("192.168.1.100", rack=0, slot=1)

        assert browser.ip_address == "192.168.1.100"
        assert browser.rack == 0
        assert browser.slot == 1

    def test_connect_success(self, mock_s7_client):
        """Test successful connection."""
        browser = S7DBBrowser("192.168.1.100")

        result = browser.connect()

        assert result is True

    def test_list_dbs(self, mock_s7_client):
        """Test listing Data Blocks."""
        # Mock read_db to return data for DB1, DB2, DB10 only
        def mock_read_db(db_num, start, size):
            if db_num in [1, 2, 10]:
                return b'\x00' * size
            return None

        mock_s7_client.read_db = MagicMock(side_effect=mock_read_db)

        browser = S7DBBrowser("192.168.1.100")
        browser._client = mock_s7_client

        dbs = browser.list_dbs(start_db=1, end_db=20, max_dbs=10)

        assert len(dbs) == 3
        assert all(isinstance(db, DBInfo) for db in dbs)

        db_numbers = [db.db_number for db in dbs]
        assert 1 in db_numbers
        assert 2 in db_numbers
        assert 10 in db_numbers

    def test_get_db_size(self, mock_s7_client):
        """Test determining DB size."""
        # Mock read_db to succeed up to offset 99, fail at 100
        def mock_read_db(db_num, offset, size):
            if offset < 100:
                return b'\x00' * size
            return None

        mock_s7_client.read_db = MagicMock(side_effect=mock_read_db)

        browser = S7DBBrowser("192.168.1.100")
        browser._client = mock_s7_client

        size = browser._get_db_size(10)

        # Should find size around 100
        assert size > 0
        assert size <= 100

    def test_get_db_structure(self, mock_s7_client):
        """Test getting DB structure."""
        mock_s7_client.read_db = MagicMock(return_value=b'\x00' * 100)

        browser = S7DBBrowser("192.168.1.100")
        browser._client = mock_s7_client
        browser._get_db_size = MagicMock(return_value=100)

        structure = browser.get_db_structure(10, read_data=True)

        assert structure is not None
        assert isinstance(structure, DBStructure)
        assert structure.db_number == 10
        assert structure.size == 100
        assert len(structure.raw_data) == 100

    def test_infer_structure_basic(self):
        """Test basic structure inference."""
        browser = S7DBBrowser("192.168.1.100")

        # Create sample data with patterns
        data = bytearray(20)
        data[0] = 1  # Could be BOOL
        data[4:8] = b'\x00\x00\x41\xC8'  # REAL value

        offset_map = browser._infer_structure(len(data), bytes(data))

        assert isinstance(offset_map, dict)
        assert len(offset_map) > 0

    def test_read_db_value(self, mock_s7_client):
        """Test reading specific DB value."""
        mock_result = MagicMock()
        mock_result.value = 25.5
        mock_result.quality = "Good"

        mock_s7_client.read_address = MagicMock(return_value=mock_result)

        browser = S7DBBrowser("192.168.1.100")
        browser._client = mock_s7_client

        value = browser.read_db_value(10, 0, "REAL")

        assert value == 25.5

    def test_build_address(self):
        """Test building S7 address string."""
        browser = S7DBBrowser("192.168.1.100")

        # Test different data types
        assert browser._build_address(10, 0, "BOOL") == "DB10.DBX0.0"
        assert browser._build_address(10, 0, "BYTE") == "DB10.DBB0"
        assert browser._build_address(10, 0, "WORD") == "DB10.DBW0"
        assert browser._build_address(10, 0, "REAL") == "DB10.DBREAL0"

    @pytest.mark.asyncio
    async def test_list_dbs_async(self, mock_s7_client):
        """Test async DB listing."""
        mock_s7_client.read_db = MagicMock(return_value=b'\x00')

        browser = S7DBBrowser("192.168.1.100")
        browser._client = mock_s7_client

        dbs = await browser.list_dbs_async(start_db=1, end_db=5, max_dbs=10)

        assert isinstance(dbs, list)

    def test_context_manager(self, mock_s7_client):
        """Test browser as context manager."""
        with S7DBBrowser("192.168.1.100") as browser:
            pass  # Just test it doesn't error

        mock_s7_client.disconnect.assert_called()


class TestS7SymbolImporter:
    """Test cases for S7 Symbol Importer."""

    def test_importer_initialization(self):
        """Test importer initializes correctly."""
        importer = S7SymbolImporter()

        assert len(importer._symbols) == 0

    def test_import_csv_tia_portal_format(self):
        """Test importing from TIA Portal CSV format."""
        csv_content = """Name,Address,Type,Comment
MotorSpeed,DB10.DBREAL0,Real,Motor speed in RPM
MotorTemp,DB10.DBREAL4,Real,Motor temperature
MotorRunning,DB10.DBX8.0,Bool,Motor running status"""

        importer = S7SymbolImporter()
        symbols = importer.import_from_csv(csv_content)

        assert len(symbols) == 3
        assert all(isinstance(s, S7Symbol) for s in symbols)

        # Check first symbol
        motor_speed = symbols[0]
        assert motor_speed.name == "MotorSpeed"
        assert motor_speed.address == "DB10.DBREAL0"
        assert motor_speed.data_type == "REAL"
        assert motor_speed.db_number == 10
        assert motor_speed.offset == 0

    def test_import_csv_step7_format(self):
        """Test importing from Step7 CSV format."""
        csv_content = """Symbol,Tag Address,Data Type,Description
Temperature_1,DB1.DBW0,INT,Temperature sensor 1
Pressure_1,DB1.DBD2,REAL,Pressure sensor 1
Valve_Open,DB1.DBX6.0,BOOL,Valve open command"""

        importer = S7SymbolImporter()
        symbols = importer.import_from_csv(csv_content)

        assert len(symbols) == 3

        # Check second symbol
        pressure = symbols[1]
        assert pressure.name == "Pressure_1"
        assert pressure.data_type == "REAL"
        assert pressure.db_number == 1
        assert pressure.offset == 2

    def test_import_csv_with_units(self):
        """Test importing CSV with unit information."""
        csv_content = """Name,Address,Type,Unit,Min,Max,Comment
Temperature,DB10.DBREAL0,Real,°C,-50,150,Temperature sensor
Pressure,DB10.DBREAL4,Real,bar,0,10,Pressure sensor"""

        importer = S7SymbolImporter()
        symbols = importer.import_from_csv(csv_content)

        assert len(symbols) == 2

        temp = symbols[0]
        assert temp.unit == "°C"
        assert temp.min_value == -50.0
        assert temp.max_value == 150.0

    def test_detect_csv_columns(self):
        """Test CSV column detection."""
        importer = S7SymbolImporter()

        # Test TIA Portal style
        fieldnames = ["Name", "Address", "Type", "Comment"]
        col_map = importer._detect_csv_columns(fieldnames)

        assert col_map['name'] == "Name"
        assert col_map['address'] == "Address"
        assert col_map['type'] == "Type"
        assert col_map['comment'] == "Comment"

        # Test Step7 style
        fieldnames = ["Symbol", "Tag Address", "Data Type", "Description"]
        col_map = importer._detect_csv_columns(fieldnames)

        assert col_map['name'] == "Symbol"
        assert col_map['address'] == "Tag Address"
        assert col_map['type'] == "Data Type"
        assert col_map['comment'] == "Description"

    def test_parse_address_db_bool(self):
        """Test parsing DB BOOL address."""
        importer = S7SymbolImporter()

        parsed = importer._parse_address("DB10.DBX0.5")

        assert parsed is not None
        db_num, area, offset, bit_offset = parsed
        assert db_num == 10
        assert area == 'DB'
        assert offset == 0
        assert bit_offset == 5

    def test_parse_address_db_real(self):
        """Test parsing DB REAL address."""
        importer = S7SymbolImporter()

        parsed = importer._parse_address("DB10.DBREAL4")

        assert parsed is not None
        db_num, area, offset, bit_offset = parsed
        assert db_num == 10
        assert offset == 4
        assert bit_offset is None

    def test_parse_address_input(self):
        """Test parsing Input address."""
        importer = S7SymbolImporter()

        parsed = importer._parse_address("I0.5")

        assert parsed is not None
        db_num, area, offset, bit_offset = parsed
        assert db_num is None
        assert area == 'I'
        assert offset == 0
        assert bit_offset == 5

    def test_parse_address_invalid(self):
        """Test parsing invalid address."""
        importer = S7SymbolImporter()

        parsed = importer._parse_address("INVALID_ADDRESS")

        assert parsed is None

    def test_validate_symbols_success(self):
        """Test validation of valid symbols."""
        csv_content = """Name,Address,Type
Tag1,DB10.DBREAL0,Real
Tag2,DB10.DBREAL4,Real"""

        importer = S7SymbolImporter()
        symbols = importer.import_from_csv(csv_content)

        validation = importer.validate_symbols(symbols)

        assert validation['total'] == 2
        assert validation['valid'] == 2
        assert validation['invalid'] == 0

    def test_validate_symbols_duplicates(self):
        """Test validation detects duplicates."""
        csv_content = """Name,Address,Type
Tag1,DB10.DBREAL0,Real
Tag1,DB10.DBREAL4,Real"""  # Duplicate name

        importer = S7SymbolImporter()
        symbols = importer.import_from_csv(csv_content)

        validation = importer.validate_symbols(symbols)

        assert validation['invalid'] > 0
        assert any("Duplicate" in error for error in validation['errors'])

    def test_get_symbols_by_db(self):
        """Test filtering symbols by DB number."""
        csv_content = """Name,Address,Type
Tag1,DB10.DBREAL0,Real
Tag2,DB20.DBREAL0,Real
Tag3,DB10.DBREAL4,Real"""

        importer = S7SymbolImporter()
        importer.import_from_csv(csv_content)

        db10_symbols = importer.get_symbols_by_db(10)

        assert len(db10_symbols) == 2
        assert all(s.db_number == 10 for s in db10_symbols)

    def test_get_symbols_by_area(self):
        """Test filtering symbols by memory area."""
        csv_content = """Name,Address,Type
DBTag,DB10.DBREAL0,Real
InputTag,I0.0,Bool
OutputTag,Q0.0,Bool"""

        importer = S7SymbolImporter()
        importer.import_from_csv(csv_content)

        db_symbols = importer.get_symbols_by_area('DB')
        input_symbols = importer.get_symbols_by_area('I')

        assert len(db_symbols) == 1
        assert len(input_symbols) == 1

    def test_export_to_dict(self):
        """Test exporting symbols to dictionary."""
        csv_content = """Name,Address,Type
Tag1,DB10.DBREAL0,Real"""

        importer = S7SymbolImporter()
        importer.import_from_csv(csv_content)

        data = importer.export_to_dict()

        assert 'symbol_count' in data
        assert 'symbols' in data
        assert data['symbol_count'] == 1

    def test_clear_symbols(self):
        """Test clearing imported symbols."""
        csv_content = """Name,Address,Type
Tag1,DB10.DBREAL0,Real"""

        importer = S7SymbolImporter()
        importer.import_from_csv(csv_content)

        assert len(importer.get_symbols()) == 1

        importer.clear()

        assert len(importer.get_symbols()) == 0


# Integration tests
@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("INTEGRATION_TESTS") != "1",
    reason="Integration tests disabled"
)
class TestS7DiscoveryIntegration:
    """Integration tests for S7 discovery."""

    PLC_IP = os.getenv("TEST_S7_IP", "192.168.1.100")

    def test_real_db_listing(self):
        """Test listing DBs from real PLC."""
        browser = S7DBBrowser(self.PLC_IP)

        try:
            result = browser.connect()
            assert result is True

            dbs = browser.list_dbs(start_db=1, end_db=100, max_dbs=10)

            # Should return list (may be empty if no DBs)
            assert isinstance(dbs, list)

        finally:
            browser.disconnect()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
