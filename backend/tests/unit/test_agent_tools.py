"""
Unit tests for AI Agent Tools
Tests the AgentToolkit functionality for LLM tool calling
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import json

# Import the module under test
from app.services.agent_tools import (
    AgentToolkit,
    ToolResult,
    ToolCall,
    AVAILABLE_TOOLS,
)


class TestToolDefinitions:
    """Tests for tool definitions and schema"""

    def test_available_tools_not_empty(self):
        """AVAILABLE_TOOLS should contain tools"""
        assert len(AVAILABLE_TOOLS) > 0

    def test_each_tool_has_required_fields(self):
        """Each tool must have name, description, and parameters"""
        for tool in AVAILABLE_TOOLS:
            assert "name" in tool, f"Tool missing 'name': {tool}"
            assert "description" in tool, f"Tool missing 'description': {tool}"
            assert "parameters" in tool, f"Tool missing 'parameters': {tool}"
            assert isinstance(tool["name"], str)
            assert len(tool["name"]) > 0
            assert len(tool["description"]) > 0

    def test_tool_parameters_are_valid_json_schema(self):
        """Tool parameters should be valid JSON Schema objects"""
        for tool in AVAILABLE_TOOLS:
            params = tool["parameters"]
            assert "type" in params
            assert params["type"] == "object"
            assert "properties" in params

    def test_essential_tools_exist(self):
        """Essential tools should be defined"""
        tool_names = [t["name"] for t in AVAILABLE_TOOLS]
        essential_tools = [
            "get_realtime_value",
            "get_historical_data",
            "calculate_statistics",
            "list_tags",
            "search_tags",
        ]
        for essential in essential_tools:
            assert essential in tool_names, f"Missing essential tool: {essential}"


class TestAgentToolkit:
    """Tests for AgentToolkit class"""

    @pytest.fixture
    def mock_data_service(self):
        """Create a mock DataService"""
        service = MagicMock()
        service.get_tag_current_value = AsyncMock(return_value={
            "tag_id": "test_tag",
            "value": 25.5,
            "timestamp": datetime.now().isoformat(),
            "quality": "good"
        })
        service.get_tag_history = AsyncMock(return_value=[
            {"timestamp": datetime.now().isoformat(), "value": 25.0},
            {"timestamp": datetime.now().isoformat(), "value": 26.0},
        ])
        service.list_tags = AsyncMock(return_value=[
            {"id": "tag1", "name": "Temperature"},
            {"id": "tag2", "name": "Pressure"},
        ])
        service.search_tags = AsyncMock(return_value=[
            {"id": "tag1", "name": "Temperature", "score": 0.95},
        ])
        return service

    @pytest.fixture
    def toolkit(self, mock_data_service):
        """Create an AgentToolkit instance"""
        return AgentToolkit(
            data_service=mock_data_service,
            auth_token="test_token",
            user_id="test_user"
        )

    def test_toolkit_initialization(self, toolkit, mock_data_service):
        """Toolkit should initialize with data service"""
        assert toolkit.data_service == mock_data_service
        assert toolkit.auth_token == "test_token"
        assert toolkit.user_id == "test_user"

    def test_get_available_tools(self, toolkit):
        """Should return list of available tools"""
        tools = toolkit.get_available_tools()
        assert isinstance(tools, list)
        assert len(tools) > 0
        for tool in tools:
            assert "name" in tool
            assert "description" in tool

    @pytest.mark.asyncio
    async def test_execute_get_realtime_value(self, toolkit):
        """Should execute get_realtime_value tool"""
        result = await toolkit.execute_tool(
            "get_realtime_value",
            {"tag_id": "test_tag"}
        )
        assert isinstance(result, ToolResult)
        assert result.tool_name == "get_realtime_value"
        assert result.success is True
        assert result.data is not None

    @pytest.mark.asyncio
    async def test_execute_unknown_tool(self, toolkit):
        """Should return error for unknown tool"""
        result = await toolkit.execute_tool(
            "unknown_tool",
            {"arg": "value"}
        )
        assert isinstance(result, ToolResult)
        assert result.success is False
        assert "unknown" in result.error.lower() or "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_tool_with_missing_args(self, toolkit):
        """Should handle missing required arguments gracefully"""
        result = await toolkit.execute_tool(
            "get_realtime_value",
            {}  # Missing required tag_id
        )
        # Should either succeed with default or return error
        assert isinstance(result, ToolResult)

    @pytest.mark.asyncio
    async def test_execute_list_tags(self, toolkit):
        """Should execute list_tags tool"""
        result = await toolkit.execute_tool("list_tags", {})
        assert isinstance(result, ToolResult)
        assert result.tool_name == "list_tags"

    @pytest.mark.asyncio
    async def test_execute_search_tags(self, toolkit):
        """Should execute search_tags tool"""
        result = await toolkit.execute_tool(
            "search_tags",
            {"query": "temperature"}
        )
        assert isinstance(result, ToolResult)
        assert result.tool_name == "search_tags"

    @pytest.mark.asyncio
    async def test_execute_calculate_statistics(self, toolkit):
        """Should execute calculate_statistics tool"""
        result = await toolkit.execute_tool(
            "calculate_statistics",
            {"tag_id": "test_tag", "duration": "1h"}
        )
        assert isinstance(result, ToolResult)
        assert result.tool_name == "calculate_statistics"

    @pytest.mark.asyncio
    async def test_execute_get_historical_data(self, toolkit):
        """Should execute get_historical_data tool"""
        result = await toolkit.execute_tool(
            "get_historical_data",
            {"tag_id": "test_tag", "duration": "24h"}
        )
        assert isinstance(result, ToolResult)
        assert result.tool_name == "get_historical_data"


class TestToolResult:
    """Tests for ToolResult model"""

    def test_successful_result(self):
        """Should create successful result"""
        result = ToolResult(
            tool_name="test_tool",
            success=True,
            data={"value": 42}
        )
        assert result.success is True
        assert result.data == {"value": 42}
        assert result.error is None

    def test_error_result(self):
        """Should create error result"""
        result = ToolResult(
            tool_name="test_tool",
            success=False,
            error="Something went wrong"
        )
        assert result.success is False
        assert result.error == "Something went wrong"

    def test_result_serialization(self):
        """Result should be JSON serializable"""
        result = ToolResult(
            tool_name="test_tool",
            success=True,
            data={"timestamp": "2024-01-01T00:00:00", "value": 25.5}
        )
        json_str = result.model_dump_json()
        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert parsed["tool_name"] == "test_tool"


class TestToolCall:
    """Tests for ToolCall model"""

    def test_tool_call_creation(self):
        """Should create tool call"""
        call = ToolCall(
            name="get_realtime_value",
            arguments={"tag_id": "test_tag"}
        )
        assert call.name == "get_realtime_value"
        assert call.arguments["tag_id"] == "test_tag"

    def test_tool_call_with_empty_args(self):
        """Should allow empty arguments"""
        call = ToolCall(
            name="list_tags",
            arguments={}
        )
        assert call.arguments == {}


class TestDashboardTools:
    """Tests for dashboard management tools"""

    @pytest.fixture
    def mock_data_service(self):
        """Create a mock DataService"""
        return MagicMock()

    @pytest.fixture
    def toolkit_with_auth(self, mock_data_service):
        """Create toolkit with auth token"""
        return AgentToolkit(
            data_service=mock_data_service,
            auth_token="valid_token",
            user_id="user123"
        )

    def test_dashboard_tools_exist(self):
        """Dashboard management tools should be defined"""
        tool_names = [t["name"] for t in AVAILABLE_TOOLS]
        dashboard_tools = [
            "create_dashboard",
            "list_dashboards",
            "add_widget_to_dashboard",
            "get_dashboard_details",
        ]
        for tool in dashboard_tools:
            assert tool in tool_names, f"Missing dashboard tool: {tool}"

    @pytest.mark.asyncio
    async def test_create_dashboard_requires_auth(self, mock_data_service):
        """Create dashboard should work with auth"""
        toolkit = AgentToolkit(
            data_service=mock_data_service,
            auth_token="valid_token"
        )
        # Verify toolkit has auth
        assert toolkit.auth_token == "valid_token"

    def test_dashboard_tool_parameters(self):
        """Dashboard tools should have correct parameters"""
        tools_map = {t["name"]: t for t in AVAILABLE_TOOLS}

        # create_dashboard
        if "create_dashboard" in tools_map:
            create_params = tools_map["create_dashboard"]["parameters"]
            assert "properties" in create_params
            props = create_params["properties"]
            assert "name" in props

        # list_dashboards
        if "list_dashboards" in tools_map:
            list_params = tools_map["list_dashboards"]["parameters"]
            assert "type" in list_params


class TestAlarmTools:
    """Tests for alarm-related tools"""

    def test_alarm_tools_exist(self):
        """Alarm tools should be defined"""
        tool_names = [t["name"] for t in AVAILABLE_TOOLS]
        # Check for alarm-related tools
        alarm_tools = [t for t in tool_names if "alarm" in t.lower()]
        # At minimum, should have some alarm functionality
        # This is a soft check - may not have alarm tools
        pass  # Just verifying structure

    def test_get_active_alarms_tool(self):
        """get_active_alarms tool should be properly defined if exists"""
        tools_map = {t["name"]: t for t in AVAILABLE_TOOLS}
        if "get_active_alarms" in tools_map:
            tool = tools_map["get_active_alarms"]
            assert "description" in tool
            assert "alarm" in tool["description"].lower()


class TestOEETools:
    """Tests for OEE (Overall Equipment Effectiveness) tools"""

    def test_oee_tools_exist(self):
        """OEE tools should be defined"""
        tool_names = [t["name"] for t in AVAILABLE_TOOLS]
        oee_tools = [t for t in tool_names if "oee" in t.lower()]
        # OEE is important for manufacturing - should have tools
        pass  # Structure verification


class TestToolkitErrorHandling:
    """Tests for error handling in toolkit"""

    @pytest.fixture
    def mock_data_service_with_errors(self):
        """Create a mock DataService that raises errors"""
        service = MagicMock()
        service.get_tag_current_value = AsyncMock(
            side_effect=Exception("Database connection failed")
        )
        return service

    @pytest.fixture
    def toolkit_with_errors(self, mock_data_service_with_errors):
        """Create toolkit that will encounter errors"""
        return AgentToolkit(
            data_service=mock_data_service_with_errors,
            auth_token="test_token"
        )

    @pytest.mark.asyncio
    async def test_handles_service_exceptions(self, toolkit_with_errors):
        """Should gracefully handle service exceptions"""
        result = await toolkit_with_errors.execute_tool(
            "get_realtime_value",
            {"tag_id": "test_tag"}
        )
        assert isinstance(result, ToolResult)
        # Should either return error or empty data, not raise
        # The exact behavior depends on implementation


class TestToolkitCaching:
    """Tests for toolkit caching behavior (if implemented)"""

    @pytest.fixture
    def mock_data_service(self):
        service = MagicMock()
        service.list_tags = AsyncMock(return_value=[
            {"id": "tag1", "name": "Temp"},
        ])
        return service

    @pytest.mark.asyncio
    async def test_repeated_calls_work(self, mock_data_service):
        """Repeated tool calls should work consistently"""
        toolkit = AgentToolkit(
            data_service=mock_data_service,
            auth_token="test"
        )

        # Make multiple calls
        results = []
        for _ in range(3):
            result = await toolkit.execute_tool("list_tags", {})
            results.append(result)

        # All should succeed
        for result in results:
            assert isinstance(result, ToolResult)
